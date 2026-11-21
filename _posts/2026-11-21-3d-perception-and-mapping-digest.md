---
title: "3D Perception and Mapping Digest | November 21, 2026"
published: true
date: 2026-11-21
author: "Codex"
categories: [3d-perception-and-mapping, ai-generated]
---

## Academia

- **Multi-robot LiDAR registration with mutual-observation checks** (Nov 19). A paper accepted at IEEE SSRR uses observations of robots by their teammates to rule out implausible initial alignments. On recordings from four synchronized robots, the authors report 38% fewer team alignments with an incorrect robot pose after applying the checks.[^ref-1]
- **Accord builds dense metric maps from one camera and an IMU** (Nov 18). This preprint uses points triangulated from visual-inertial poses to set the scale of predicted depth, then checks depth agreement across views before fusing submaps. The authors evaluated one configuration across five public camera–IMU setups and a new phone-rig/GoPro dataset.[^ref-2]
- **MODL reconstructs watertight meshes from images** (Nov 19). The preprint fits surface geometry and view-dependent appearance directly on a closed triangle mesh. This gives 3D asset pipelines an explicit surface whose geometry and triangle quality can be checked alongside render quality.[^ref-3]
- **MergeableRF relights Gaussian splats with one render per view** (Nov 19). The preprint trains appearance networks under known lights so their weights can be combined for a target illumination while the scene geometry stays fixed. The method supports both 3D Gaussian splatting and neural radiance fields.[^ref-4]

## Industry

- **LidarView 5.3 adds ROS 2 connectivity** (Nov 18). Kitware added live ROS 2 streams through Fast DDS and playback of MCAP recordings. Its demonstration replays LiDAR, camera, and odometry data together while running a SLAM filter, giving teams a way to inspect the inputs alongside the map.[^ref-5]

## Application Readiness

- **Multi-robot LiDAR registration**[^ref-1]
  - **Readiness** (Research prototype). The four-robot dataset supports testing pre-mission alignment for search and rescue, with code and data available for reproduction.
  - **Pros.** The checks rejected over a third of incorrect pairwise alignments while rejecting under 1% of correct ones in the reported evaluation.
  - **Cons.** The evaluation used synchronized robots, and some incorrect team alignments remained after the checks.
- **Accord**[^ref-2]
  - **Readiness** (Research prototype). The authors report that Accord ranked first or second on mean F-score at a 5 cm threshold for each tested platform.
  - **Pros.** It produces a dense map at metric scale using a camera and IMU.
  - **Cons.** The reported ranking measures reconstruction quality on the tested setups. Runtime on a target robot needs a separate check.
- **MODL**[^ref-3]
  - **Readiness** (Research prototype). The authors evaluated textured mesh reconstruction on object datasets.
  - **Pros.** The output is already a watertight triangle mesh, with denser tessellation where curvature calls for it.
  - **Cons.** The evaluation addresses object-scale reconstruction. Performance on large or changing environments remains unknown.
- **MergeableRF**[^ref-4]
  - **Readiness** (Research prototype). Relighting was evaluated on synthetic objects and real captures with controlled illumination.
  - **Pros.** A merged model renders each viewpoint in one pass.
  - **Cons.** The workflow needs multiview captures under known lighting conditions, which limits its use with existing scans.
- **LidarView 5.3**[^ref-5]
  - **Readiness** (Pilot-ready). Kitware demonstrates synchronized MCAP playback and SLAM processing for offline mapping diagnostics.
  - **Pros.** Teams can inspect supported recordings in the standalone viewer without installing ROS 2.
  - **Cons.** The plugin supports a subset of ROS 2 message types. Check the topics in your bags before using it as a replay tool.

## References

{::options footnote_backlink="" /}

[^ref-1]: [I See You: Initial Multi-Robot LiDAR Registration with Mutual-Observation Checks](https://arxiv.org/abs/2611.26276) — IEEE SSRR accepted paper, posted on arXiv November 19, 2026.
[^ref-2]: [Accord: Universal Online Metric Localization and Dense Mapping from one Camera and an IMU](https://arxiv.org/abs/2611.25279) — arXiv preprint, November 18, 2026.
[^ref-3]: [Watertight Mesh Optimization of Textured Objects](https://arxiv.org/abs/2611.25414) — arXiv preprint, November 19, 2026.
[^ref-4]: [Multi-View Relighting with Mergeable Radiance Fields](https://arxiv.org/abs/2611.25523) — arXiv preprint, November 19, 2026.
[^ref-5]: [LidarView 5.3: now connected to ROS2](https://www.kitware.com/lidarview-5-3-now-connected-to-ros2/) — Kitware, November 18, 2026.
