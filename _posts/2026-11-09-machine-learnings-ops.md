---
title: Machine Learning Ops in Robotics
published: true
date: 2026-11-09
author: zgxsin
---

* TOC
{:toc}

## From a good benchmark score to a working robot

Training a detector that reaches a good mean average precision (mAP) on a benchmark takes an afternoon. Getting the same detector to run on a robot, at a fixed rate, inside a power budget, on images from cameras and places it has never seen, and to keep it working as the fleet grows, is most of the work. **Machine Learning Operations (MLOps)** is the name for that work: the data, tooling and processes that take a model from training to production and keep it healthy there.

Robotics adds constraints that web MLOps does not have:

- **Edge compute.** The model runs on an embedded graphics processing unit (GPU) such as a Jetson, shared with simultaneous localization and mapping (SLAM), planning and control, not on a server that can scale out.
- **Hard real time.** A detection that arrives 300 ms late is a detection of where the obstacle used to be.
- **Physical consequences.** A false negative can mean a collision, so rollouts must be conservative and reversible.
- **Open world.** The robot drives into lighting, weather, sites and objects that are not in the training set. The data distribution shifts with every new customer.
- **Bandwidth.** Robots record far more data than can be uploaded, so choosing what to keep is part of the pipeline.

This post walks through the full workflow with one running example: **deploy a 2D object detector (a You Only Look Once, or YOLO-family, model) on a Robot Operating System 2 (ROS 2) robot with an NVIDIA Jetson**, and turn its 2D boxes into 3D obstacle positions for the planner.

{% include figures/ml-lifecycle-loop.html %}

The top row runs offline. The bottom row runs on the robot. The dashed green arrow is what makes it MLOps instead of a one-off project: failures seen in the field become training data for the next model, the so-called **data flywheel**.

## Step 1: Define the task and the budget

Write the requirements down before collecting a single image. They decide the model size, the input resolution and what "good enough" means.

| Question | Example answer |
| --- | --- |
| What classes, and why? | `person`, `forklift`, `pallet`, `door`; persons trigger a speed limit, the rest feed the costmap |
| Which sensors? | Front and rear RGB-D (color plus depth) cameras, 1280x720, 15 frames per second (fps) |
| Rate and latency? | 10 Hz per camera, under 100 ms photon to message |
| Compute share? | At most 30% of the Orin GPU, the rest belongs to SLAM and the elevation map |
| Operating domain? | Indoor industrial halls, outdoor yards, day and night, rain |
| Acceptance metric? | Person recall above 0.95 within 5 m, mAP@0.5 above 0.80 on the site test set |
| Failure behavior? | If the detector stops publishing, the robot falls back to geometric obstacle detection |

The last two rows matter most. A single headline mAP hides the cases that hurt; the acceptance metric should be tied to the safety function the model serves. And the rest of the stack must not trust the model blindly: a learned detector is an additional signal on top of geometric perception, not a replacement for it.

## Step 2: Collect data

### Real data from the robot

The best training data comes from the target cameras mounted on the target robot, because it has the right lens distortion, exposure behavior, mounting height and motion blur. With ROS this means recording rosbags and extracting frames:

```bash
ros2 bag record /front_camera/color/image_raw /front_camera/color/camera_info /tf /tf_static
```

Three rules save a lot of trouble later:

1. **Subsample in time.** At 15 fps, consecutive frames are almost identical. Take one frame per second, or one frame when the robot has moved more than a fixed distance.
2. **Cover the domain on purpose.** Record each site, time of day, weather and lighting condition from Step 1. Keep a spreadsheet of what is covered.
3. **Split by session, not by frame.** If frames from the same recording end up in both the training and the test set, the test score measures memorization. Assign whole recordings, or better whole sites, to train, validation or test.

### Public and synthetic data

Start from a model pretrained on a large public dataset such as Common Objects in Context (COCO), which already covers `person` and many everyday objects. For classes that are rare or dangerous to stage, **synthetic data** helps: a simulator such as Isaac Sim with Replicator renders scenes and writes perfect labels, and **domain randomization** varies lighting, textures, object poses, camera pose and backgrounds so the model learns the object instead of the simulator's look. NVIDIA reports an off-the-shelf detector trained on randomized synthetic indoor scenes that detects doors in a real building. Studies that compare real-only, synthetic-only and mixed training find that synthetic data works best **mixed with real data**, not as a replacement.

## Step 3: Label and version the data

Labeling is usually the most expensive step. A typical setup:

- **Tool.** [Computer Vision Annotation Tool (CVAT)](https://www.cvat.ai/) (open source, self-hostable) or a hosted service. Export to the format the trainer expects (YOLO text files, COCO JavaScript Object Notation (JSON)).
- **Model-assisted labeling.** Run the current best model, or a large foundation model, to pre-annotate. Humans then correct boxes instead of drawing them, which is several times faster. Correct it carefully: annotators tend to accept wrong pre-labels.
- **Labeling guide.** A written guide with pictures: is a person behind glass a `person`? Is a half-visible pallet labeled? How tight is a box? Inconsistent labels put a ceiling on mAP that no model can break.
- **Quality control.** Have a second annotator review a random sample, and look at the frames where the trained model and the label disagree most; many of them are label errors.
- **Versioning.** Datasets change every iteration, so version them like code. [Data Version Control (DVC)](https://dvc.org/) stores the images in object storage and a small pointer file in git; tools such as [FiftyOne](https://voxel51.com/fiftyone/) help browse and slice the data. Every trained model must record the exact dataset version it saw.

## Step 4: Train

Fine-tune a pretrained detector rather than training from scratch. With Ultralytics this is a few lines:

```python
from ultralytics import YOLO

model = YOLO("yolov8s.pt")            # COCO-pretrained weights
model.train(
    data="robot_dataset.yaml",        # paths to train/val splits and class names
    epochs=100,
    imgsz=640,                        # must match the inference resolution
    batch=32,
)
```

Choices that matter for a robot:

- **Model size.** Pick the smallest variant that meets the acceptance metric (n for nano, s for small, m for medium, ...). Each step up roughly doubles the compute. The latency budget in Step 7 decides, not the leaderboard.
- **Input resolution.** Small objects far away need more pixels; 640 px is the common default. Train at the resolution you will run at.
- **Augmentation.** Motion blur, brightness, contrast and noise mimic real camera behavior. Avoid augmentations that create impossible views, such as vertical flips for a camera that never flips.
- **Experiment tracking.** Log hyperparameters, dataset version, git commit, metrics and the resulting weights to a tracker such as MLflow, Weights & Biases or ClearML. Six months later, "which data was the model on robot 12 trained on?" must have an answer.

## Step 5: Evaluate

### The standard metric: mAP

A predicted box is matched to a ground-truth box by **Intersection over Union** (IoU):

$$
\text{IoU}(A, B) = \frac{\text{area}(A \cap B)}{\text{area}(A \cup B)}.
$$

A prediction is a **true positive** (TP) if its IoU with an unmatched ground-truth box of the same class exceeds a threshold, otherwise a **false positive** (FP). Ground-truth boxes that nothing matched are **false negatives** (FN).

{% include figures/detection-iou-pr.html %}

Two ratios summarize these counts. **Precision** is $\text{TP} / (\text{TP} + \text{FP})$: of the boxes the model reported, how many were real. **Recall** is $\text{TP} / (\text{TP} + \text{FN})$: of the real objects, how many the model found.

Every prediction carries a confidence score, and only predictions above a **confidence threshold** are kept. Sweeping that threshold trades precision against recall and traces a **precision-recall curve**. This is an evaluation step, not part of training: the model runs once on the test set with a very low threshold, the detections are sorted by confidence, and each cut-off point in that list gives one point on the curve. The trade-off comes from what moves when the threshold changes. The denominator of recall, $\text{TP} + \text{FN}$, is the number of ground-truth objects, which is fixed. So lowering the threshold can only keep recall the same or raise it: every extra prediction either finds another object or adds nothing. The denominator of precision is the number of kept predictions, which grows as the threshold drops. A well-trained detector gives its highest scores to its most obvious, mostly correct detections. As the threshold falls, it admits less certain predictions, and a growing share of them are background clutter or duplicate boxes, so FP grows faster than TP and precision falls. At a very high threshold the model reports only a few confident boxes: precision is high, but most objects are missed. At a very low threshold it reports almost everything: recall approaches its maximum, and the false positives pull precision down. The curve is not perfectly smooth, because precision jumps up briefly each time one more true positive is admitted. So before taking the area under the curve, benchmarks first smooth out these zigzags: precision at each recall is replaced by the best precision at that recall or higher, which turns the curve into a staircase that never goes up. AP is the area under that staircase.

**Average precision** (AP) is the area under it, computed per class, and **mAP** is the mean over classes. PASCAL Visual Object Classes (VOC) uses a single IoU threshold of 0.5 (mAP@0.5). COCO averages over ten thresholds from 0.50 to 0.95 (mAP@0.5:0.95), which also rewards tight boxes. A model with high mAP@0.5 but low mAP@0.75 finds objects but localizes them loosely; for a robot that converts boxes into 3D positions, loose boxes mean wrong distances.

### What a robot actually needs

mAP on the whole test set is necessary but not sufficient. Also measure:

- **Per-slice metrics.** Break results down by site, lighting, distance band and object size. An average of 0.85 can hide a night-time recall of 0.4.
- **The operating point.** On the robot a single confidence threshold is used. Report precision and recall **at that threshold**, for the safety-relevant class, in the relevant distance range.
- **Temporal stability.** Run the model on full sequences, not single frames. A detection that flickers on and off makes the costmap flicker too.
- **Regression against the previous model.** A new model must be at least as good on the frozen test set and on the curated set of past field failures.

If the model is not good enough, the fix is almost always in the data (Step 2 and 3), not in the architecture. This is the red arrow in the lifecycle figure.

## Step 6: Optimize and export for the edge

A PyTorch checkpoint needs Python and the PyTorch runtime, and it does not use the edge GPU efficiently. The standard path on NVIDIA hardware is **PyTorch to Open Neural Network Exchange (ONNX) to TensorRT**:

{% include figures/model-export-pipeline.html %}

**Export to ONNX.** ONNX is a framework-neutral graph format. Fix the input shape to the deployment resolution:

```python
from ultralytics import YOLO
YOLO("runs/detect/train/weights/best.pt").export(format="onnx", imgsz=640, opset=17, simplify=True)
```

**Build a TensorRT engine on the target.** TensorRT fuses layers, picks the fastest kernel for each layer on this exact GPU and lowers the precision. The engine is tied to the GPU model and the TensorRT version, so build it on the Jetson (or in a continuous integration (CI) job on identical hardware), never copy it from the workstation:

```bash
# on the Jetson
trtexec --onnx=model.onnx --saveEngine=model_fp16.engine --fp16
```

Ultralytics can also export an engine directly with `format="engine"`; check the export docs of your version for the precision argument.

**Choose the precision.** The options are 32-bit floating point (FP32), 16-bit floating point (FP16) and 8-bit integer (INT8). INT8 comes in two flavors: post-training quantization (PTQ) and quantization-aware training (QAT).

| Precision | Speed | Accuracy | What it needs |
| --- | --- | --- | --- |
| FP32 | baseline | reference | nothing |
| FP16 | large speedup on Tensor Cores | usually indistinguishable | nothing, start here |
| INT8 (PTQ) | faster again, less memory | often a small drop, model dependent | a **calibration set** of a few hundred representative images |
| INT8 (QAT) | same as PTQ if the quantize/dequantize (Q/DQ) nodes fuse | recovers most of the PTQ drop | retraining with fake quantization |

For INT8 post-training quantization, TensorRT runs the calibration images through the network, records the activation range of each layer and picks the scale that loses the least information. The calibration images must come from the deployment distribution: calibrating on daylight images and running at night is a classic accuracy loss. Accuracy-sensitive parts, typically the detection head, can be kept in FP16 while the backbone runs in INT8.

**Verify after every conversion.** Run the same images through PyTorch, ONNX and TensorRT and compare boxes and scores, then rerun the mAP evaluation with the engine. The most common bug is not numerical: it is a preprocessing mismatch (blue-green-red (BGR) versus red-green-blue (RGB) channel order, letterbox versus stretch resize, 0 to 1 versus 0 to 255 normalization) between the training code and the robot code.

## Step 7: Integrate into ROS 2

### The node graph

On the robot, inference becomes a set of ROS 2 nodes. NVIDIA's Isaac ROS splits it into three stages, which is a good structure even without Isaac ROS:

{% include figures/ros2-detection-graph.html %}

- **Encoder.** Converts the image to the tensor the network expects. It must reproduce the training preprocessing exactly.
- **Inference.** Runs the engine. Isaac ROS provides a TensorRT node and a Triton node; a custom C++ node with the TensorRT application programming interface (API) or ONNX Runtime also works.
- **Decoder.** Model-specific: turns raw output tensors into boxes, applies the confidence threshold and **non-maximum suppression** (NMS) to merge duplicate boxes, and publishes `vision_msgs/Detection2DArray`.

Isaac ROS uses NVIDIA Isaac Transport for ROS (NITROS) to pass images between these nodes on the GPU without copying them to the central processing unit (CPU), which matters at high resolution. Without it, run the stages as components in one process so ROS 2 can use intra-process communication.

A minimal decoder publishing standard messages looks like this. Note the header: copying the image timestamp and frame is what lets downstream nodes look up the correct transform.

```python
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

def to_msg(image_msg, boxes, scores, class_ids, class_names):
    out = Detection2DArray()
    out.header = image_msg.header            # same stamp and camera frame as the image
    for (x1, y1, x2, y2), score, cid in zip(boxes, scores, class_ids):
        det = Detection2D()
        det.header = image_msg.header
        det.bbox.center.position.x = (x1 + x2) / 2.0
        det.bbox.center.position.y = (y1 + y2) / 2.0
        det.bbox.size_x = float(x2 - x1)
        det.bbox.size_y = float(y2 - y1)
        hyp = ObjectHypothesisWithPose()
        hyp.hypothesis.class_id = class_names[cid]
        hyp.hypothesis.score = float(score)
        det.results.append(hyp)
        out.detections.append(det)
    return out
```

### From a 2D box to a 3D obstacle

A planner needs positions in the map, not pixels. With a depth image aligned to the color image and the pinhole intrinsics $(f_x, f_y, c_x, c_y)$ from `camera_info`, a pixel $(u, v)$ with depth $Z$ back-projects to the camera frame as

$$
X = \frac{(u - c_x)\, Z}{f_x}, \qquad Y = \frac{(v - c_y)\, Z}{f_y}, \qquad Z = Z.
$$

Then transform the point with TF (the ROS transform library) from the camera frame into `odom` or `map` at the image timestamp. Practical details:

- **Do not read the depth at the box center.** The center of a person's box can be the background between their legs. Take the median depth of the inner part of the box, or of the pixels inside a segmentation mask.
- **Check the alignment.** Depth and color come from different sensors; use the depth stream registered to the color frame, or the 3D position will be off at object edges.
- **Carry uncertainty.** Stereo depth error grows with the square of the distance. Put it in the covariance of the `PoseWithCovariance` in `Detection3DArray` so the tracker can weight it.
- **Track over time.** A simple multi-object tracker (for example a Kalman filter per object with association by distance) smooths flicker and gives velocities.

### The latency budget

{% include figures/perception-latency-budget.html %}

The network is usually only a third of the end-to-end latency. Measure the whole chain with timestamps: the image header stamp is the capture time, so `now - header.stamp` at the consumer is the true age of a detection. Also check that the GPU share fits next to the other GPU users, and that the Jetson power mode and thermal throttling do not change the numbers after twenty minutes of operation.

## Step 8: Validate before it touches the fleet

- **Rosbag replay.** Replay recorded bags through the exact on-robot launch file and container. This is the cheapest end-to-end test and can run in CI on Jetson hardware.
- **Closed-loop simulation.** Run the full stack in simulation to see how the planner reacts to detections, including false positives that make the robot stop for nothing.
- **Hardware-in-the-loop soak test.** Run on a real robot for hours: latency percentiles (the 99th percentile, p99, not just the mean), GPU memory, temperature, dropped frames.
- **Failure injection.** Kill the detector node and confirm that the fallback from Step 1 engages.

## Step 9: Deploy safely

### Package the model as one versioned unit

The model's behavior depends on more than its weights. Ship them together and version them together:

- engine file (or the ONNX plus a build step on first boot), with the TensorRT and JetPack version it was built for
- preprocessing parameters: input size, letterbox, color order, normalization
- class names and IDs
- confidence and NMS thresholds
- the dataset version and training run ID it came from

Embed the model version in the output, for example in a diagnostics topic, so every detection in a recording can be traced to the exact model that produced it. In practice the bundle lives in a container image or a versioned package deployed by the fleet's update system.

### Roll out in stages

{% include figures/staged-rollout.html %}

- **Shadow mode.** The new model runs next to the production model on real robots, but only its outputs are logged; it does not influence the robot. Disagreements between the two are exactly the frames worth looking at. For safety-relevant perception this is the right first step, because it has no actuation risk.
- **Canary.** A few robots use the new model for real, ideally at sites the team can watch. The evaluation window must be long enough to see rare events: a robot that sees a forklift ten times a day needs days, not hours.
- **Waves and rollback.** Roll out to the rest of the fleet in waves. Keep the previous model on the device so a rollback is a configuration switch, not a download.

## Step 10: Monitor and close the loop

Once deployed, the model's input distribution keeps changing: new sites, new seasons, a dirty lens, a new type of forklift. Nobody labels production data, so monitoring relies on proxies:

- **Health:** inference latency, publish rate, GPU temperature and memory.
- **Output statistics:** detections per frame and confidence distributions per class and site. A sudden shift often means a camera or site problem, sometimes a real distribution shift.
- **Disagreement signals:** the learned detector reports nothing where geometric perception sees an obstacle, or the tracker loses a track that should have persisted, or a human operator intervened.

These signals become **triggers** that save a short clip of sensor data around the event, since uploading everything is not possible. The saved clips go back to Step 2: they are labeled with priority, added to the training set and, the important part, to a growing **regression set** of known hard cases. This is **hard example mining**, and selecting frames where the model was uncertain is **active learning**. Tesla called the same loop its data engine: cases where the network performed poorly are sourced from the fleet, labeled and added to training, and each new model then meets harder cases.

{% include figures/data-engine-loop.html %}

## Summary: the tool chain

| Stage | Typical tools |
| --- | --- |
| Data recording | `ros2 bag`, on-robot trigger logic, MCAP (the default ROS 2 bag file format) |
| Synthetic data | Isaac Sim + Replicator, domain randomization |
| Labeling | CVAT, model-assisted pre-labels, written labeling guide |
| Data versioning and browsing | DVC, FiftyOne |
| Training and tracking | Ultralytics / PyTorch, MLflow, Weights & Biases or ClearML |
| Export and optimization | ONNX, TensorRT (`trtexec`), FP16 or INT8 with calibration |
| On-robot inference | Isaac ROS (encoder, TensorRT or Triton node, decoder), or a custom node with TensorRT or ONNX Runtime |
| Messages | `vision_msgs/Detection2DArray`, `Detection3DArray`, TF |
| Deployment | Containers, fleet over-the-air (OTA) update with shadow, canary and rollback |
| Monitoring | Latency and output statistics, drift proxies, hard example mining |

The model architecture is the part that changes least from one robot to the next. Most of the effort goes into the data loop around it, the conversion and integration, and the guard rails that keep a statistical component safe on a machine that moves.

## References

- NVIDIA, [Isaac ROS Object Detection](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_object_detection/index.html) and [Isaac ROS DNN Inference](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_dnn_inference/index.html).
- NVIDIA, [Isaac ROS YOLOv8](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_object_detection/isaac_ros_yolov8/index.html): ONNX export and TensorRT engine for ROS 2.
- NVIDIA, [Implementing robotics applications with ROS 2 and AI on Jetson](https://developer.nvidia.com/blog/implementing-robotics-applications-with-ros-2-and-ai-on-jetson-platform-2/).
- Ultralytics, [Model export](https://docs.ultralytics.com/modes/export/) and [TensorRT integration](https://docs.ultralytics.com/integrations/tensorrt/).
- Seeed Studio, [Deploy YOLOv8 on NVIDIA Jetson using TensorRT](https://wiki.seeedstudio.com/YOLOv8-TRT-Jetson/).
- Liu et al., [YolactEdge: Real-time Instance Segmentation on the Edge](https://arxiv.org/abs/2012.12259): mixed INT8/FP16 precision on Jetson.
- NVIDIA, [Closing the Sim2Real Gap with Isaac Sim and Isaac Replicator](https://developer.nvidia.com/blog/closing-the-sim2real-gap-with-nvidia-isaac-sim-and-nvidia-isaac-replicator/).
- [CVAT documentation](https://docs.cvat.ai/docs/getting_started/overview/) and [an annotation workflow with CVAT, FiftyOne and DVC](https://iblog.ridge-i.com/entry/2023/06/14/094050).
- [COCO evaluation metrics explained](https://www.picsellia.com/post/coco-evaluation-metrics-explained).
- ROS, [vision_msgs](https://docs.ros.org/en/humble/p/vision_msgs).
- [Fleet shadow-mode rollout and rollback for vehicle ML](https://prachub.com/concepts/fleet-shadow-mode-rollout-and-rollback-for-vehicle-ml) and [OTA model updates for robots](https://amarrmb.github.io/robotics-glossary/concepts/learning/ota-model-update).
- [Data flywheel](https://www.ultralytics.com/glossary/data-flywheel), Ultralytics glossary.
