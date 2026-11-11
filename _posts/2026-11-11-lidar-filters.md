---
title: "LiDAR Perception: From Raw Points to Tracked Obstacles"
published: false
date: 2026-11-11
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

## Overview

A LiDAR gives a robot direct, metric 3D geometry, independent of lighting. Turning that geometry into "there is a pedestrian 12 m ahead, walking left at 1.2 m/s" takes a chain of steps, and most field failures trace back to one of the unglamorous early ones: a wrong extrinsic, a missing timestamp, a filter tuned for a different sensor.

This post follows the data through that chain in the order it is processed, then works through three system design questions and two coding exercises that come up in perception interviews.

{% include figures/lidar-pipeline.html %}

Calibration is not a runtime step, but every later stage consumes its result, so it comes first.

## How a LiDAR measures

### Time of flight

A pulsed LiDAR emits a short laser pulse and measures the round-trip time $\Delta t$ of the echo:

$$
r = \frac{c \, \Delta t}{2}.
$$

With $c \approx 3 \times 10^8$ m/s, 1 ns of timing error is 15 cm of range, so the receiver electronics, not the optics, set the range precision (typically 1 to 3 cm). Each return also carries an **intensity** (or calibrated **reflectivity**), the strength of the echo.

**FMCW** (frequency-modulated continuous wave) LiDARs instead chirp the laser frequency and measure the beat frequency between outgoing and returning light. They measure range and, through the Doppler shift, **radial velocity per point**, and they are largely immune to interference from other LiDARs. They are still rare on robots, but per-point velocity makes motion segmentation almost free.

### Scanning patterns

| Type | How it scans | Typical spec | Consequence |
| --- | --- | --- | --- |
| Mechanical spinning (Ouster, Hesai, Velodyne) | A column of 16 to 128 lasers rotates at 10 or 20 Hz | 360 deg horizontal, 30 to 90 deg vertical | Dense rings, sparse between rings; points within one sweep have different timestamps |
| MEMS / solid state | A mirror steers a few beams over a fixed field of view | 120 deg x 25 deg | No moving parts, limited FOV, need several to cover 360 deg |
| Non-repetitive (Livox) | Rosette pattern that never repeats | Coverage grows with integration time | Sparse in 10 ms, dense in 1 s; no ring structure |
| Flash | Illuminates the whole scene at once onto a detector array | Short range | No motion distortion within a frame |

### What a point contains

A driver typically publishes, per point: `x, y, z`, `intensity`, `ring` (laser index), `t` (offset from the scan start, in ns), and for some sensors `ambient` light, `range` and the return number when the sensor reports multiple echoes (strongest and last return).

For a spinning sensor the points form an **organized cloud**: a range image with one row per ring and one column per azimuth step. Pixel $(u, v)$ of the image holds the point with

$$
u = \text{ring}, \qquad v = \left\lfloor \frac{\phi + \pi}{2\pi} \, W \right\rfloor, \qquad \phi = \operatorname{atan2}(y, x),
$$

where $W$ is the number of columns (for example 1024 or 2048). In the range image, neighbors are found in $O(1)$ instead of through a [k-d tree](/2024/10/01/kd-tree/), which is why many fast algorithms (ground removal, clustering, LOAM feature extraction) work on it. Keep the organized structure as long as possible, and drop invalid pixels only at the end.

### Resolution is anisotropic

A spinning LiDAR mounted at height $h$ with vertical beam spacing $\Delta\theta$ hits the ground at distance $d = h / \tan\theta$. Differentiating gives the spacing between consecutive rings on the ground:

$$
\Delta d \approx \frac{d^2}{h} \, \Delta\theta.
$$

The horizontal spacing within a ring is only $d \, \Delta\phi$. For a 128-beam sensor ($\Delta\theta \approx \Delta\phi \approx 0.35°$) at $h = 1$ m and $d = 10$ m, rings are **61 cm** apart on the ground while points within a ring are **6 cm** apart. Fixed-radius neighborhoods therefore behave very differently along and across rings, and this one fact explains why many textbook filters fail at range.

### Error sources

| Effect | What you see | Handled in |
| --- | --- | --- |
| Range noise | Surfaces 2 to 5 cm thick | Downsampling, plane fitting |
| Mixed pixels at depth edges | "Veil" of points between foreground and background | Edge / shadow filter |
| Specular and glass surfaces | Missing returns, or mirrored ghost geometry behind the glass | Map-level consistency; hard |
| Retroreflectors (signs, vests) | Blooming: points smeared around the target | Intensity filter |
| Rain, snow, dust, fog | Sparse low-intensity points near the sensor | Range-dependent outlier removal, last return |
| Dark or wet surfaces | Low or no return, holes in the ground | Treat missing as unknown, not free |
| Motion during the sweep | Bent walls, doubled objects | Deskewing |
| Robot body in view | Points on the robot itself | Self filter |
| Other LiDARs | Interference: random spurious points | Sensor-side coding, outlier removal |

## Calibration

Every sensor's data must be expressed in a common frame. Using the notation of [rigid body transformation](/2022/08/07/rigid-body-transformation/), a point measured in the LiDAR frame $L$ goes to the body frame $B$ with $\mathbf{p}\_B = \mathbf{T}\_{BL} \, \mathbf{p}\_L$.

{% include figures/lidar-calibration-frames.html caption="Solid arrows: the extrinsics used at runtime. Dashed: how each sensor pair is calibrated." %}

### What gets calibrated

- **Intrinsics**: per-beam elevation and azimuth offsets, range offsets. Done by the manufacturer for modern sensors; check them only if planes look stepped ring by ring.
- **Extrinsics** $\mathbf{T}\_{BL}$: six parameters per sensor. CAD gives a starting point, but brackets and mounting tolerances leave errors of a few millimeters and tenths of a degree.
- **Time offset** $t\_d$ between the sensor clock and the rest of the system. Covered in the next section.

The rotational part matters most: an error of 1 deg moves a point at 10 m by $10 \cdot \tan 1° \approx 17$ cm, enough to double a wall in the map or to put an obstacle in the wrong cell.

### Methods

| Pair | Method | Notes |
| --- | --- | --- |
| LiDAR to LiDAR | ICP / GICP on the overlapping region, initialized from CAD | Needs overlap and enough structure in all directions (not a long corridor) |
| LiDAR to IMU or body | Hand-eye calibration $\mathbf{A}\_k \mathbf{X} = \mathbf{X} \mathbf{B}\_k$, or a continuous-time batch optimization over a trajectory | Needs rotation about at least two non-parallel axes; planar driving leaves the vertical offset unobservable |
| LiDAR to camera | Target-based (board with known geometry, plane and edge correspondences), or targetless (align depth edges to image edges, mutual information of intensity) | Validate by projecting points into the image |

### Hand-eye calibration

**Where the name comes from.** The problem was first posed for robot arms (Shiu and Ahmad 1989, Tsai and Lenz 1989). A camera, the **eye**, is bolted to the gripper, the **hand**, and the transform between the two is unknown. The arm knows how its hand moved from the joint encoders and forward kinematics. The camera knows how it moved by observing a fixed checkerboard before and after. Neither sensor sees the other, yet the two motions must be consistent, because hand and eye are rigidly attached. Finding the hand-to-eye transform from those paired motions is hand-eye calibration. The name stuck for any pair of rigidly mounted sensors that can each measure their own motion: LiDAR and IMU, LiDAR and wheel odometry, two LiDARs, or a LiDAR and a camera with no overlapping view.

{% include figures/hand-eye-calibration.html caption="Left: the original setup, a camera (eye) on a robot gripper (hand). Right: the same constraint for any two rigidly attached sensors." %}

**The equation.** Let $\mathbf{X} = \mathbf{T}\_{12}$ be the unknown pose of sensor 2 in the frame of sensor 1. Because the sensors are rigidly attached, $\mathbf{T}\_{W2}(t) = \mathbf{T}\_{W1}(t) \, \mathbf{X}$ at every time $t$. Between two times $i$ and $j$, sensor 1 moves by $\mathbf{A} = \mathbf{T}\_{W1}(t\_i)^{-1} \mathbf{T}\_{W1}(t\_j)$, which comes from its own odometry, registration or kinematics. Sensor 2 moves by

$$
\mathbf{B} = \mathbf{T}\_{W2}(t\_i)^{-1} \mathbf{T}\_{W2}(t\_j) = \mathbf{X}^{-1} \mathbf{T}\_{W1}(t\_i)^{-1} \mathbf{T}\_{W1}(t\_j) \, \mathbf{X} = \mathbf{X}^{-1} \mathbf{A} \mathbf{X},
$$

so every motion pair $k$ gives $\mathbf{A}\_k \mathbf{X} = \mathbf{X} \mathbf{B}\_k$. The world frame cancels out: each sensor only has to estimate its own motion, in its own frame, and the sensors never need to observe a common target. That is the main appeal for robots, where sensors often share no field of view.

**Splitting rotation and translation.** With $\mathbf{X} = (\mathbf{R}\_X, \mathbf{t}\_X)$, the equation separates into

$$
\mathbf{R}\_{A\_k} \mathbf{R}\_X = \mathbf{R}\_X \mathbf{R}\_{B\_k}, \qquad
(\mathbf{R}\_{A\_k} - \mathbf{I}) \, \mathbf{t}\_X = \mathbf{R}\_X \mathbf{t}\_{B\_k} - \mathbf{t}\_{A\_k}.
$$

The rotation part says the two sensors rotate by the same angle, about axes related by $\mathbf{R}\_X$: if $\mathbf{a}\_k$ and $\mathbf{b}\_k$ are the rotation axes of $\mathbf{R}\_{A\_k}$ and $\mathbf{R}\_{B\_k}$, then $\mathbf{a}\_k = \mathbf{R}\_X \mathbf{b}\_k$. That is one direction correspondence per motion pair, solved like point set alignment with an SVD (see [SVD and PCA](/2026/03/06/svd-and-pca/)) or as a linear least squares problem in quaternions. The translation part is then linear in $\mathbf{t}\_X$. A joint nonlinear least squares refinement over all pairs (see [Hessian and Gauss-Newton](/2025/11/03/hessian-gaussian-newton/)) usually follows.

**What the motion must contain.**

- **At least two rotations about non-parallel axes.** One axis correspondence leaves $\mathbf{R}\_X$ free to spin about that axis.
- **Rotation, not only translation.** $\mathbf{R}\_{A\_k} - \mathbf{I}$ is singular along the rotation axis, so the component of $\mathbf{t}\_X$ along that axis is unobservable. A ground robot that only yaws therefore cannot recover the vertical offset between its sensors; take it from CAD or a separate measurement.
- **Accurate, time-aligned motion estimates.** The calibration is only as good as $\mathbf{A}\_k$ and $\mathbf{B}\_k$, and a time offset between the sensors looks like a rotation error. Use segments where both odometries are reliable, and estimate the time offset jointly if it is not known.

For LiDAR to IMU, the gyroscope measures rotation well but the IMU's translation drifts within seconds, so in practice the rotation is solved hand-eye style and the full extrinsic and time offset are refined in a continuous-time batch optimization or online inside the LiDAR-inertial odometry filter. With a monocular camera, $\mathbf{t}\_{B\_k}$ is known only up to scale, which adds one unknown scale factor to the translation equations.

### Validation in the field

Calibration drifts after impacts and maintenance, so check it continuously:

- Ground plane fitted separately in each LiDAR should agree in height and tilt.
- Overlapping LiDARs should register to each other with a near-identity correction.
- Planes in an accumulated map should be thin. A thick or doubled wall is the first visible symptom of a bad rotation or time offset.

## Time synchronization and motion compensation

### Clocks

Each point must be associated with the robot pose at the instant it was measured. That requires all sensors to share one time base.

{% include figures/lidar-clock-sync.html %}

- **PTP (IEEE 1588)** with hardware timestamping synchronizes clocks over Ethernet to well under a microsecond. Most automotive-grade LiDARs support it.
- **PPS + NMEA** from a GNSS receiver: a pulse marks the second, a serial message names it.
- **NTP** gives millisecond-level agreement; too coarse for deskewing at speed.
- **Host receive time** is not a measurement time. It includes buffering, network and driver latency, which also jitters. Use it only as a last resort, and then estimate the offset online.

Also agree on what the message header stamp means: the start, the middle, or the end of the sweep. Drivers differ, and getting it wrong is a constant offset of half a scan period (50 ms at 10 Hz).

How much timing error is acceptable? At a yaw rate of 1 rad/s, a 10 ms offset rotates the cloud by 0.01 rad, which moves a point at 10 m by 10 cm. At 1 m/s it also shifts everything by 1 cm.

### Motion distortion

A spinning LiDAR takes 100 ms for one sweep at 10 Hz. If the robot moves during the sweep, points measured at different times are expressed in different sensor poses, but the driver publishes them in a single frame. Walls bend, and at the **seam** where the sweep ends and starts, the first and last points no longer meet.

{% include figures/lidar-motion-distortion.html caption="One sweep while the robot drives and turns. Raw points are all expressed in the end-of-scan pose. Increase the yaw rate: rotation, not translation, dominates the distortion at range." %}

### Deskewing

For a point $\mathbf{p}\_i$ measured at time $t\_i$, deskewing re-expresses it in the sensor frame at a reference time $t\_r$ (usually the scan end):

$$
\mathbf{p}\_i' = \mathbf{T}\_{WL}(t\_r)^{-1} \, \mathbf{T}\_{WL}(t\_i) \, \mathbf{p}\_i.
$$

The only hard part is getting $\mathbf{T}\_{WL}(t)$ at every point time. Options, from simplest to best:

1. **Constant velocity** from the last two registration results: $\mathbf{T}(t) = \mathbf{T}(t\_r) \operatorname{Exp}\big((t - t\_r)\,\boldsymbol{\xi}\big)$ with twist $\boldsymbol{\xi}$. KISS-ICP does this and it works well for smooth vehicle motion.
2. **IMU integration** between scans: rotation from the gyroscope is accurate over 100 ms; translation needs the velocity estimate from the odometry filter. This is the standard in LiDAR-inertial odometry (FAST-LIO, LIO-SAM). See [IMU preintegration](/2023/10/30/imu-preintegration/).
3. **Continuous-time trajectory** (B-spline or Gaussian process) estimated jointly with registration. Best for aggressive motion such as legged robots or handheld scanners.

{% include figures/lidar-deskew-timeline.html %}

Practical points:

- The deskew must **wait** until IMU samples past the scan end have arrived. Budget for this in latency.
- Deskew **before** downsampling: a voxel centroid mixes points with different timestamps.
- Sort or bin points by time and interpolate poses at a few hundred knots, rather than integrating per point.
- Without per-point timestamps (some drivers drop them), reconstruct the time from the azimuth for spinning sensors: $t\_i = t\_0 + T \cdot \phi\_i / 2\pi$, with care at the seam.

## Preprocessing and filters

Filters remove points that are invalid, irrelevant or harmful, and reduce the point count so later stages meet their latency budget. Order them by cost: cheap per-point tests first, so expensive neighborhood filters see fewer points.

{% include figures/lidar-filter-chain.html %}

Different consumers need different chains. Odometry wants a uniformly downsampled cloud and tolerates some outliers; obstacle detection must not lose small objects and should not downsample aggressively; mapping wants dynamic objects removed.

### Per-point filters

- **Invalid points.** No return gives NaN or zero range. Remove them, or keep the pixel marked invalid in the organized cloud. A missing return is information: it means "unknown", not "free".
- **Range gate.** A minimum range (0.3 to 1 m) removes self-hits, dust next to the window and near-field blooming. A maximum range removes points too sparse and noisy to be useful.
- **Self filter.** A crop box around the robot body is enough for a rigid vehicle. A legged robot or a manipulator moves its own body through the field of view, so use the robot model with the current joint states and remove points inside the (padded) link meshes.
- **Field-of-view masks.** Fixed angular sectors blocked by mounts or cargo.
- **Intensity gate.** Very high intensity marks retroreflectors and their blooming halo; very low intensity close to the sensor is typical for rain and snow.

### Neighborhood filters

**Statistical outlier removal (SOR).** For each point compute the mean distance $\bar{d}\_i$ to its $k$ nearest neighbors. Across the cloud, these have mean $\mu$ and standard deviation $\sigma$. Remove points with $\bar{d}\_i > \mu + \alpha \sigma$. Cost $O(N k \log N)$ with a k-d tree.

**Radius outlier removal (ROR).** Remove points with fewer than $m$ neighbors within radius $r$. Simple, but because density drops with $d^2$, a radius tuned for near points deletes valid far points.

**Dynamic radius outlier removal (DROR).** Scale the search radius with range, $r\_i = \max(r\_{\min}, \beta \, d\_i \, \Delta\phi)$, so the expected neighbor count stays constant. Designed for snow, where flakes are isolated points close to the sensor. Combining it with an intensity test (LIOR, DSOR variants) improves precision further.

**Edge (mixed pixel) filter.** When a beam straddles a depth edge, the return lies between foreground and background. In the range image, compare each point with its neighbor in the same ring: if the angle between the beam and the line to the neighbor is very small, the surface is either seen at a grazing angle or the point is a mixed pixel, and LOAM-style pipelines discard it.

### Voxel downsampling

A voxel grid groups points by the integer key $\big(\lfloor x/s \rfloor, \lfloor y/s \rfloor, \lfloor z/s \rfloor\big)$ and replaces each occupied voxel by one representative: the centroid, the first point, or the point nearest the centroid. It bounds the point count, evens out the density between near and far, and averages noise. The code is in the [coding section](#exercise-voxel-downsampling).

{% include figures/voxel-downsample.html caption="Voxel centroid downsampling of a 2D scan. Near the sensor many points collapse into one, far away almost none do. Large voxels pull centroids off corners and curved surfaces: use the nearest actual point when exact geometry matters." %}

Choosing the voxel size $s$:

- Odometry: 0.2 to 1.0 m depending on the environment scale. KISS-ICP ties it to the maximum range.
- Obstacle detection: smaller than the smallest obstacle you must see, or skip downsampling for the near field.
- Centroids are biased at corners and edges. If normals or edges matter, keep the point nearest the centroid.

### Filter summary

| Filter | Removes | Key parameters | Cost | Pitfall |
| --- | --- | --- | --- | --- |
| Range gate | Self-hits, far noise | min, max range | $O(N)$ | Min range too large hides close obstacles |
| Self filter | Robot body | Box or link meshes + padding | $O(N)$ | Stale joint states leave leg points |
| Intensity gate | Blooming, weather | thresholds | $O(N)$ | Dark objects have low intensity too |
| SOR | Isolated noise | $k$, $\alpha$ | $O(N k \log N)$ | Global statistics, mixes near and far |
| ROR | Isolated noise | $r$, $m$ | $O(N \log N)$ | Removes valid far points |
| DROR | Snow, rain | $\beta$, $r\_{\min}$, $m$ | $O(N \log N)$ | Removes small far objects |
| Edge filter | Mixed pixels | Angle threshold | $O(N)$ on range image | Also removes grazing-angle surfaces |
| Voxel grid | Redundant points | $s$ | $O(N)$ | Loses small objects, mixes timestamps |

## Obstacle detection

### Ground segmentation

Ground points are often half of the cloud, and they connect every object to every other object. Remove them before clustering, or every cluster becomes one.

Methods, from simplest to most robust:

1. **Height threshold.** Ground is everything below $z < z\_{\text{thr}}$ in the body frame. Fails on slopes, under pitching motion and on curbs, and always deletes the lowest part of every obstacle.
2. **Single plane fit with RANSAC.** Fit $\mathbf{n}^\top \mathbf{p} + d = 0$ to the cloud, take inliers as ground. Handles a tilted sensor, fails on terrain that is not one plane. RANSAC needs $k = \log(1 - P) / \log(1 - w^3)$ iterations to find an all-inlier sample with probability $P$, given inlier ratio $w$.
3. **Local slope along each azimuth column.** Walk outward through the rings of one column (Himmelsbach et al., Bogoslavskyi and Stachniss). A point is ground if the slope from the last ground point is below a threshold. Handles ramps and is $O(N)$ on the range image.
4. **Region-wise plane fitting.** Divide the ground into polar bins (Patchwork++ uses concentric zones with bins that grow with range), fit a plane per bin with PCA, and accept it if it is upright, low and flat enough. Robust on rough terrain and fast.
5. **Learned semantic segmentation** (RangeNet++, Cylinder3D). Best on the data it was trained on, needs labels and a GPU.

{% include figures/ground-segmentation.html caption="One azimuth column. The height threshold labels the upper ramp as obstacle, and the lower half of the crate as ground. The slope test follows the ramp; raise its threshold far enough and it starts accepting the bottom of the crate face." %}

For legged robots and off-road vehicles, "ground versus obstacle" is the wrong question: a 15 cm step is an obstacle for a wheelchair and a stair for a quadruped. Those systems build an elevation map and compute **traversability** (slope, roughness, step height) per cell instead. See [3D map representations](/2026/06/13/3d-map-representations/).

### Clustering

The remaining non-ground points are grouped into objects.

**Euclidean clustering** (PCL's `EuclideanClusterExtraction`): pick an unvisited point, grow a cluster by breadth-first search over all neighbors within tolerance $\epsilon$, repeat. Discard clusters with too few or too many points. With a k-d tree it costs $O(N \log N)$.

The choice of $\epsilon$ runs straight into the anisotropic resolution above: small $\epsilon$ splits far objects into fragments, large $\epsilon$ merges near objects that stand close together. Scaling the tolerance with range fixes most of the first problem.

{% include figures/euclidean-clustering.html caption="Euclidean clustering of non-ground points. Try to find a fixed tolerance that keeps the two pedestrians apart and the container in one piece, then switch to the range-scaled tolerance. The container side seen at a grazing angle still breaks up: its point spacing grows with range and with the incidence angle." %}

Faster alternatives:

- **Range image clustering** (Bogoslavskyi and Stachniss): two neighboring pixels with ranges $d\_1 \geq d\_2$ and angular separation $\psi$ belong to the same object if $\beta = \operatorname{atan2}(d\_2 \sin\psi, \, d\_1 - d\_2 \cos\psi)$ exceeds a threshold (about 10 deg). The angle is independent of range, so the threshold is too. $O(N)$ with connected components on the image.
- **2D grid connected components**: project non-ground points into a bird's-eye-view occupancy grid and label connected cells. Very fast, loses overhangs.
- **DBSCAN**: Euclidean clustering with a core-point density requirement, so isolated noise does not bridge two clusters.

### Box fitting and detection

A cluster becomes an object with a bounding box, a heading and a class.

- **Box fitting.** PCA gives a poor heading for partially seen objects, because a LiDAR sees one or two sides only. **L-shape fitting** (Zhang et al. 2017) searches the heading that best explains the visible points as two perpendicular edges, which matches how vehicles appear.
- **Geometric classification** by size and shape (height, footprint, point count) separates pedestrians, vehicles and poles in simple environments.
- **Learned 3D detectors** (PointPillars, CenterPoint, VoxelNeXt) output oriented boxes with class and score directly, including the unseen extent of the object (amodal boxes). They classify far better, but only for classes in their training data.

A robust system runs both: the learned detector for known classes and accurate boxes, and geometric clustering as a class-agnostic safety layer that reports anything solid in the path, even if no network has ever seen it.

### Tracking

A detector answers "what is here now". Planning needs "where will it be", which requires velocity, and that comes from tracking detections over time.

{% include figures/lidar-tracking-loop.html %}

1. **Predict** each track to the scan timestamp with a motion model: constant velocity for pedestrians, constant turn rate and velocity (CTRV) for vehicles, inside a [Kalman filter](/2026/04/25/kalman-filter/) (EKF or UKF for the nonlinear CTRV).
2. **Gate**: ignore pairs whose innovation $\mathbf{y}$ is improbable, $\mathbf{y}^\top \mathbf{S}^{-1} \mathbf{y} > \chi^2\_{k, 0.99}$ (9.21 for a 2D position).
3. **Associate**: solve the assignment problem on the gated costs with the Hungarian algorithm (global nearest neighbor). JPDA or MHT handle dense scenes with ambiguous assignments at higher cost.
4. **Update** the matched tracks.
5. **Manage** track lifecycles:

{% include figures/lidar-track-lifecycle.html %}

LiDAR-specific issues:

- **The measured centroid moves with the viewpoint.** As a car passes, the visible side changes and the cluster centroid slides along the car, which a naive tracker reads as acceleration. Track a box reference point (the visible corner or the box center from L-shape fitting) instead.
- **Heading ambiguity.** A box heading is defined only up to 180 deg; resolve it from the velocity direction once the object moves.
- **Splits and merges.** A clustering error turns one object into two detections or two into one. Track management must tolerate a few frames of this without spawning or killing tracks.
- **Ego-motion.** Predict and associate in a world-fixed frame using [ego-motion](/2023/06/30/ego-motion-estimation/) from odometry, otherwise the robot's own turn looks like every object moving.

## System design questions

### Fuse multiple fixed LiDARs and track vehicles through overlapping coverage

Think of a port gate or an intersection with four pole-mounted LiDARs.

**Requirements first.** Coverage area and overlap, required position accuracy, maximum vehicle speed, ID consistency through the whole area, update rate and latency, and what happens during sensor outages.

**Calibration and time.** Survey each sensor into a common site frame, refine pairwise with ICP on the overlaps, and monitor it against static landmarks (poles, building corners), because poles sway and brackets loosen. Synchronize all sensors with PTP.

**Exploit that the sensors are fixed.** The background never changes. Build a background model per sensor (a voxel occupancy or a per-pixel range image accumulated over minutes) and keep only foreground points that are closer than the background. This removes ground, buildings and parked containers in one $O(N)$ step and is far more robust than generic ground segmentation.

**Where to fuse:**

| Level | How | Pros | Cons |
| --- | --- | --- | --- |
| Early (points) | Merge foreground points from all sensors, then cluster and detect once | Full shape of vehicles seen from several sides; one tracker | Needs accurate calibration and sync; bandwidth; a central failure point |
| Mid (detections) | Each sensor detects, a central tracker associates all detections | Robust to calibration errors of a few cm; scales | Duplicate detections in overlaps must be merged |
| Late (tracks) | Each sensor tracks, track-to-track fusion | Sensors independent | Correlated estimates (use covariance intersection), ID handover logic |

A good default is **early fusion of foreground points** when the sensors are on one network with good sync, falling back to detection-level fusion. Fusing before tracking means there is one track per vehicle in the site frame, so "handover" between sensors disappears: the track simply receives measurements from whichever sensors see the vehicle.

{% include figures/lidar-fixed-fusion.html %}

**Hard cases.** Long trucks span several sensors and are seen in pieces: cluster in the merged cloud, and keep size estimates in the track state. Occlusion by other vehicles: coast tracks with growing covariance, and use object size and position for re-identification. A sensor goes down: the tracker must know the coverage map, so it does not delete tracks in an area nobody can see.

### Monitor perception failures and provide dependable obstacle information

The key distinction is between "no obstacle" and "I cannot see". A perception system is dependable when it **knows** which of the two it is reporting.

**Failure modes and monitors:**

| Failure | Monitor |
| --- | --- |
| Sensor dead or driver crashed | Message rate and age watchdog |
| Stale or wrong timestamps | Compare header stamp to the synchronized clock; check monotonicity |
| Window blocked (mud, snow, sticker) | Per-sector point count and near-range returns vs. expected |
| Degraded by weather | Fraction of low-intensity near points, return rate |
| Calibration drift | Ground plane per sensor, cross-sensor overlap residual |
| Pipeline overload | End-to-end latency, dropped frames, queue lengths |
| Detector misses | Cross-check learned detections against the geometric layer; track continuity statistics |

**Dependable output.**

- Publish free space **and** unknown space, not only an object list. An occupancy grid with three states lets the planner slow down for what it cannot see.
- Attach validity per sector and a timestamp to every output. A planner using an obstacle list must be able to tell that the rear sector is blind.
- Keep a simple, deterministic safety path (doer/checker): points in a protective field around the vehicle, minimal processing, no learning, triggering a stop. The complex stack optimizes behavior; the simple path bounds the worst case.
- Define degraded modes: reduced speed when a sensor is degraded, stop when a safety-relevant sector is blind.

{% include figures/lidar-monitoring.html %}

Then close the loop: log every monitor trigger with the raw data, review false alarms and misses, and add the cases to the regression set. The [MLOps in robotics](/2026/11/08/machine-learnings-ops/) post covers that data loop.

### Design a perception pipeline for an autonomous truck around pedestrians and containers

**Requirements.** Start from the stopping distance. At 25 km/h (7 m/s), with 0.3 s of system latency and 2 m/s² of comfortable deceleration:

$$
d\_{\text{stop}} = v \, t\_{\text{lat}} + \frac{v^2}{2a} = 7 \cdot 0.3 + \frac{49}{4} \approx 14.4 \text{ m}.
$$

Add margin for tracking confirmation and false-alarm suppression, and the requirement becomes: detect a pedestrian at 40 m ahead, with 99.9+% recall within the stopping envelope, end-to-end latency under 200 ms, and no blind zone around the truck when starting to move.

Then check the sensor can do it: a 0.4 m wide, 1.7 m tall pedestrian at 40 m with 0.2 deg horizontal and 0.35 deg vertical resolution gives about 3 columns by 7 rings, 20 points. Enough to detect, marginal to classify.

**Sensor coverage.**

- Long-range LiDARs front and rear, mounted high to see over nearby containers.
- Short-range wide-FOV LiDARs at the corners of the cab and trailer: a truck's largest risk is a pedestrian next to the wheels at start-up.
- Radar for velocity and robustness in rain and dust; cameras for classification (pedestrian versus pole) and for reading signs.
- Containers form canyons: a pedestrian can step out from behind a stack. Model occluded regions explicitly and limit speed near them.

**Pipeline.**

{% include figures/lidar-truck-pipeline.html %}

**Uncertainty and the planner interface.** Each object carries a box, a velocity, a covariance, class probabilities and an existence probability. The planner should inflate obstacles by their position covariance, use the class to pick a prediction model (pedestrians can change direction instantly; containers do not move), and treat unknown space near its path conservatively.

**Failure handling.** As in the previous question: per-sensor health, sector validity, a geometric safety layer that does not depend on the learned detector, and defined degraded modes.

**Latency budget.**

| Stage | Budget |
| --- | --- |
| Sweep accumulation (mean point age at 10 Hz) | 50 ms |
| Driver, transport, deskew wait | 10 ms |
| Filters and ground segmentation | 10 ms |
| Detector (GPU) and clustering, in parallel | 30 ms |
| Fusion and tracking | 5 ms |
| Planner interface | 5 ms |
| **Total, perception** | **about 110 ms** |

Two ways to cut it: process the sweep in sectors as they arrive rather than waiting for the full scan, and run the cheap geometric safety layer on the earliest data while the detector is still running.

## C++

### Essential concepts for point cloud code

| Concept | Why it matters in a LiDAR pipeline |
| --- | --- |
| Contiguous memory (`std::vector`, `reserve`) | A cloud is 100k to 2M points per second; per-point allocations and cache misses dominate runtime |
| AoS vs. SoA | Array of structs (`std::vector<Point>`) is convenient; struct of arrays (separate `x`, `y`, `z` vectors) vectorizes better |
| Move semantics, return by value | Return clouds by value (move or copy elision), take inputs by `const&`, never copy by accident |
| Ownership (`unique_ptr`, `shared_ptr<const T>`) | ROS 2 intra-process communication passes a `unique_ptr` without copying; shared read-only clouds avoid locks |
| RAII | Locks, file handles, GPU buffers released on every path, including exceptions |
| Hash maps (`std::unordered_map`) | Voxel grids and spatial hashing; needs a custom hash for the key |
| `std::floor` vs. truncation | `static_cast<int>(-0.5)` is 0, not -1; voxel keys around zero collide without `floor` |
| `float` precision | 24-bit mantissa: at 5,000,000 m (UTM northing) the spacing between floats is 0.5 m. Keep coordinates local, or use `double` |
| Integer time | Store timestamps as `int64_t` nanoseconds; `double` seconds since 1970 resolve only about 0.5 µs |
| Concurrency | Data races are undefined behavior. Use `std::mutex` with `std::scoped_lock`, `std::atomic` for flags, and ROS 2 callback groups for parallel callbacks |
| Eigen | Fixed-size types (`Eigen::Matrix3f`) live on the stack; watch alignment for fixed-size vectorizable members before C++17 |

### Coding exercises

#### Exercise: voxel downsampling

*Group 3D points into voxels and return each voxel's centroid.*

Hash each point to its integer voxel key, accumulate sums and counts per key, then emit the means. $O(N)$ time, $O(V)$ memory for $V$ occupied voxels.

```cpp
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <vector>

struct Point {
  float x{};
  float y{};
  float z{};
};

struct VoxelKey {
  std::int32_t ix{};
  std::int32_t iy{};
  std::int32_t iz{};

  bool operator==(const VoxelKey& other) const {
    return ix == other.ix && iy == other.iy && iz == other.iz;
  }
};

struct VoxelKeyHash {
  std::size_t operator()(const VoxelKey& key) const {
    // Spatial hash with large primes (Teschner et al. 2003). Unsigned overflow is well defined.
    return (static_cast<std::size_t>(key.ix) * 73856093U) ^
           (static_cast<std::size_t>(key.iy) * 19349663U) ^
           (static_cast<std::size_t>(key.iz) * 83492791U);
  }
};

struct Accumulator {
  double sumX{};
  double sumY{};
  double sumZ{};
  std::size_t count{};
};

std::vector<Point> voxelDownsample(const std::vector<Point>& cloud, float voxelSize) {
  std::vector<Point> result;
  if (cloud.empty() || !(voxelSize > 0.0F)) {
    return result;
  }
  const double inverseSize{1.0 / voxelSize};

  std::unordered_map<VoxelKey, Accumulator, VoxelKeyHash> voxels;
  voxels.reserve(cloud.size());
  for (const Point& p : cloud) {
    if (!std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z)) {
      continue;
    }
    // floor, not a cast: a cast truncates toward zero and merges voxels -1 and 0.
    const VoxelKey key{static_cast<std::int32_t>(std::floor(p.x * inverseSize)),
                       static_cast<std::int32_t>(std::floor(p.y * inverseSize)),
                       static_cast<std::int32_t>(std::floor(p.z * inverseSize))};
    Accumulator& acc = voxels[key];
    acc.sumX += p.x;
    acc.sumY += p.y;
    acc.sumZ += p.z;
    ++acc.count;
  }

  result.reserve(voxels.size());
  for (const auto& [key, acc] : voxels) {
    const double n{static_cast<double>(acc.count)};
    result.push_back(Point{static_cast<float>(acc.sumX / n), static_cast<float>(acc.sumY / n),
                           static_cast<float>(acc.sumZ / n)});
  }
  return result;
}
```

Follow-up points an interviewer will probe:

- **Accumulate in `double`.** Summing thousands of `float` coordinates loses precision.
- **Key overflow.** A coordinate of $10^7$ m with $s = 0.001$ m overflows `int32_t`. Clamp the input range or use 64-bit keys.
- **Output order** follows the hash map and is not deterministic across runs or standard libraries. If determinism matters (tests, replay), compute a linear index per point, sort the indices, and reduce runs of equal keys. That variant is also more cache-friendly for large clouds.
- **Other representatives**: the point nearest the centroid (keeps real geometry), or averaging intensity and time along with position.
- **Tests**: empty input, one point, points exactly on voxel boundaries, negative coordinates near zero, NaNs, all points in one voxel.

#### Exercise: timestamp association

*Given sorted LiDAR and IMU timestamps, find the nearest IMU sample for each scan, rejecting matches beyond a tolerance.*

Both lists are sorted, so the nearest IMU index never moves backwards as the scan time increases. A two-pointer sweep is $O(m + n)$.

{% include figures/timestamp-association.html %}

```cpp
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

// Timestamps in nanoseconds; both inputs sorted ascending.
std::vector<std::optional<std::size_t>> associateNearest(const std::vector<std::int64_t>& scanTimes,
                                                         const std::vector<std::int64_t>& imuTimes,
                                                         std::int64_t tolerance) {
  std::vector<std::optional<std::size_t>> matches(scanTimes.size());
  if (imuTimes.empty()) {
    return matches;
  }
  const auto distance = [](std::int64_t a, std::int64_t b) { return a > b ? a - b : b - a; };

  std::size_t j{0};
  for (std::size_t i{0}; i < scanTimes.size(); ++i) {
    const std::int64_t t{scanTimes[i]};
    // The distance to t falls, then rises along the sorted IMU list: advance while it does not rise.
    while (j + 1 < imuTimes.size() && distance(imuTimes[j + 1], t) <= distance(imuTimes[j], t)) {
      ++j;
    }
    if (distance(imuTimes[j], t) <= tolerance) {
      matches[i] = j;
    }
  }
  return matches;
}
```

Follow-up points:

- **Why not `double` seconds**: see the table above. Integer nanoseconds compare exactly.
- **Ties** go to the later sample here (`<=`). State the choice.
- **Alternative**: `std::lower_bound` per scan is $O(m \log n)$ and simpler when scans are few or not sorted.
- **Real systems interpolate** instead of picking the nearest sample: for deskewing you need the two IMU samples bracketing each point time, and the scan must wait until the later one has arrived.
- **Streaming version**: the same logic over a ring buffer of IMU samples, dropping samples older than the current scan start.
- **Tests**: empty inputs, all scans before the first IMU sample, exact matches, equal distances, tolerance boundary, duplicate timestamps.

## References

- J. Zhang and S. Singh, "LOAM: Lidar Odometry and Mapping in Real-time", RSS 2014.
- W. Xu et al., "FAST-LIO2: Fast Direct LiDAR-Inertial Odometry", IEEE T-RO 2022.
- T. Shan et al., "LIO-SAM: Tightly-coupled Lidar Inertial Odometry via Smoothing and Mapping", IROS 2020.
- Y. C. Shiu and S. Ahmad, "Calibration of Wrist-Mounted Robotic Sensors by Solving Homogeneous Transform Equations of the Form AX = XB", IEEE Trans. Robotics and Automation, 1989.
- R. Y. Tsai and R. K. Lenz, "A New Technique for Fully Autonomous and Efficient 3D Robotics Hand/Eye Calibration", IEEE Trans. Robotics and Automation, 1989.
- I. Vizzo et al., "KISS-ICP: In Defense of Point-to-Point ICP", IEEE RA-L 2023.
- M. Himmelsbach et al., "Fast Segmentation of 3D Point Clouds for Ground Vehicles", IEEE IV 2010.
- I. Bogoslavskyi and C. Stachniss, "Fast Range Image-Based Segmentation of Sparse 3D Laser Scans for Online Operation", IROS 2016.
- S. Lee et al., "Patchwork++: Fast and Robust Ground Segmentation Solving Partial Under-Segmentation Using 3D Point Cloud", IROS 2022.
- N. Charron et al., "De-noising of Lidar Point Clouds Corrupted by Snowfall", CRV 2018.
- X. Zhang et al., "Efficient L-Shape Fitting for Vehicle Detection Using Laser Scanners", IEEE IV 2017.
- A. H. Lang et al., "PointPillars: Fast Encoders for Object Detection from Point Clouds", CVPR 2019.
- T. Yin et al., "Center-based 3D Object Detection and Tracking", CVPR 2021.
- A. Milioto et al., "RangeNet++: Fast and Accurate LiDAR Semantic Segmentation", IROS 2019.
- X. Weng et al., "3D Multi-Object Tracking: A Baseline and New Evaluation Metrics", IROS 2020.
- M. Teschner et al., "Optimized Spatial Hashing for Collision Detection of Deformable Objects", VMV 2003.
- R. B. Rusu and S. Cousins, "3D is here: Point Cloud Library (PCL)", ICRA 2011.
- IEEE 1588-2019, Precision Clock Synchronization Protocol for Networked Measurement and Control Systems.
