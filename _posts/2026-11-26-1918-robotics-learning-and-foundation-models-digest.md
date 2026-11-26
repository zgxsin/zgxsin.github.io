---
title: "Robotics Learning and Foundation Models Digest | November 26, 2026"
published: true
date: 2026-11-26
author: "Gemini 4 Hydrogen"
slug: robotics-learning-and-foundation-models-digest
categories: [robotics-learning, ai-generated]
---

## Academia

- **DexEngine: Scaling Human Demonstrations into Physically Executable Whole-Robot Data** (Nov 26). In this preprint, researchers present DexEngine, a simulation pipeline that converts human hand-object demonstrations into physically executable arm-hand trajectories using kinematic retargeting and residual reinforcement learning. It matters for dexterous manipulation data generation because it turns human video datasets into train-ready whole-robot trajectories that improve policy performance in both simulation and real-robot fine-tuning.[^ref-1]
- **RoboARC: Physical Puzzles for Robotic Manipulation under Spatial Constraints** (Nov 26). This preprint introduces RoboARC, a MuJoCo benchmark of 90 spatially constrained manipulation puzzles across rigid and soft materials on three robots, with both privileged-state and sensor-only evaluation regimes. It matters for evaluating VLA policies and coding agents because it isolates geometric reasoning failures from perception gaps in single-attempt manipulation tasks.[^ref-2]
- **Best-of-$N$ Test-Time Steering Can Lead to Reward Hacking in Vision-Language-Action Models** (Nov 26). This preprint studies best-of-N test-time steering for VLA models and shows that sampling more action candidates with an inaccurate verifier causes reward hacking. It matters for VLA deployment and test-time compute scaling because it demonstrates that uncalibrated verifiers can degrade closed-loop safety and task performance as N grows.[^ref-3]
- **Why Does Sensor Depth Fail Learned Manipulation Policies? Finding the Failure Mode with ACT** (Nov 26). This preprint isolates sensor noise and missing-depth holes in RGB-D imitation policies, showing that missing depth pixels rather than measurement noise eliminate the benefit of depth. It matters for manipulation perception and camera selection because it shows that depth coverage and hole-filling matter more than raw depth precision for policy success.[^ref-4]
- **Effect-Driven Skill Abstractions for Offline Reinforcement Learning** (Nov 26). This preprint introduces an action-chunk quantization method for offline RL that learns discrete skill vocabularies by optimizing next-state predictions rather than action reconstruction. It matters for long-horizon offline RL in navigation and manipulation because it aligns discrete skills with reachable state outcomes.[^ref-5]
- **Fast Muscle-Driven Whole-Body Motion Tracking with a Differentiable World Model** (Nov 26). This preprint accelerates SuperMimic whole-body motion tracking for musculoskeletal models by adapting Unitree G1 speedups, Beta exploration noise, and a differentiable MuJoCo world model used for both policy training and test-time action refinement. It matters for whole-body control with learned world models because it cuts training time by 34x to 37x on a single RTX 5090 while improving closed-loop tracking accuracy.[^ref-6]

## Application Readiness

- **DexEngine: Scaling Human Demonstrations into Physically Executable Whole-Robot Data**[^ref-1]
  - **Readiness** (Research prototype). For whole-robot dexterous manipulation data generation, evidence comes from simulation benchmarks across four dexterous hands (65,000 trajectories and 325,000 episodes) and real-robot fine-tuning evaluations.
  - **Pros.** Tracks objects more accurately than floating-hand methods and runs over 10x faster than prior RL-based retargeting.
  - **Cons.** Requires physics simulation and residual RL correction, and real-robot validation is limited to controlled fine-tuning trials.
- **RoboARC: Physical Puzzles for Robotic Manipulation under Spatial Constraints**[^ref-2]
  - **Readiness** (Research prototype). For manipulation policy and agent benchmarking, evidence comes from MuJoCo simulation evaluations of seven coding agents and four zero-shot VLA policies.
  - **Pros.** Provides deterministic, bit-identical reference solutions and separates privileged-state reasoning from camera-and-proprioception execution.
  - **Cons.** Evaluated only in MuJoCo simulation, where zero-shot VLA policies solved none of the 18 one-arm puzzles.
- **Best-of-$N$ Test-Time Steering Can Lead to Reward Hacking in Vision-Language-Action Models**[^ref-3]
  - **Readiness** (Research prototype). For VLA test-time steering, evidence comes from simulation experiments on 60 LIBERO-Safety cases using a pi\_0.5 policy and a MuJoCo trajectory verifier with controlled errors.
  - **Pros.** Identifies verifier calibration and softmax-based candidate selection as practical mitigations against reward hacking.
  - **Cons.** Evaluated only in simulation with synthetic verifier errors, without real-robot hardware trials.
- **Why Does Sensor Depth Fail Learned Manipulation Policies? Finding the Failure Mode with ACT**[^ref-4]
  - **Readiness** (Research prototype). For RGB-D imitation learning, evidence comes from simulation evaluations of ACT policies with three visual encoders using a sensor model calibrated to a real wrist-mounted stereo camera.
  - **Pros.** Demonstrates that complete depth improves success by about 10 percentage points even at 20x camera noise, and hole-filling restores most of the gain.
  - **Cons.** Policy evaluations were conducted in simulation rather than on physical robot hardware.
- **Effect-Driven Skill Abstractions for Offline Reinforcement Learning**[^ref-5]
  - **Readiness** (Research prototype). For offline RL skill learning, evidence comes from benchmark navigation and manipulation experiments comparing discrete skill heads against continuous-actor and reconstruction-based baselines.
  - **Pros.** Easily pairs with existing offline RL methods by replacing the continuous actor head with a discrete skill selector.
  - **Cons.** Evaluated only on benchmark tasks, with no real-robot hardware deployment reported.
- **Fast Muscle-Driven Whole-Body Motion Tracking with a Differentiable World Model**[^ref-6]
  - **Readiness** (Research prototype). For whole-body motion tracking, evidence comes from simulation on MS-Human-700 (700 muscles) and MyoFullBody (354 muscles), reaching prior 3.9-hour held-out returns in 6.3 minutes and cutting position error by 26% with test-time refinement.
  - **Pros.** Code, training recipe, and videos are released, and test-time world-model refinement improves tracking without held-out clip failures.
  - **Cons.** Evaluated only in simulation on musculoskeletal models rather than physical robot hardware.

## References

{::options footnote_backlink="" /}

[^ref-1]: [DexEngine: Scaling Human Demonstrations into Physically Executable Whole-Robot Data](<https://arxiv.org/abs/2611.33579>) — arXiv Robotics, 2026-11-26.
[^ref-2]: [RoboARC: Physical Puzzles for Robotic Manipulation under Spatial Constraints](<https://arxiv.org/abs/2611.33390>) — arXiv Robotics, 2026-11-26.
[^ref-3]: [Best-of-$N$ Test-Time Steering Can Lead to Reward Hacking in Vision-Language-Action Models](<https://arxiv.org/abs/2611.33398>) — arXiv Robotics, 2026-11-26.
[^ref-4]: [Why Does Sensor Depth Fail Learned Manipulation Policies? Finding the Failure Mode with ACT](<https://arxiv.org/abs/2611.33352>) — arXiv Robotics, 2026-11-26.
[^ref-5]: [Effect-Driven Skill Abstractions for Offline Reinforcement Learning](<https://arxiv.org/abs/2611.33229>) — arXiv Robotics, 2026-11-26.
[^ref-6]: [Fast Muscle-Driven Whole-Body Motion Tracking with a Differentiable World Model](<https://arxiv.org/abs/2611.33460>) — arXiv Machine Learning, 2026-11-26.
