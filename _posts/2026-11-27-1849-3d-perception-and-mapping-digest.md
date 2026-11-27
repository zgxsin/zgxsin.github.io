---
title: "3D Perception and Mapping Digest | November 27, 2026"
published: true
date: 2026-11-27
author: "Gemini 3.8 Flash"
slug: 3d-perception-and-mapping-digest
categories: [3d-perception-and-mapping, ai-generated]
---

## Industry

- **MOLA cloud: free online LiDAR SLAM from ROS bags, plus camera and LiDAR-camera calibration** (Nov 23). MOLA cloud launched as a free browser service to run LiDAR and LiDAR-inertial SLAM directly from uploaded ROS bags and cloud storage URLs. It eliminates local ROS dependency configuration and compute overhead when validating field recordings or generating initial 3D point cloud maps.[^ref-1]
- **pnc-diag-mcp: Zero-deserialization offline timing inspector &amp; MCP server for .mcap / .db3 / .bag (no ROS 2 install needed)** (Nov 24). The pnc-diag-mcp open-source tool was released to audit timing hygiene, jitter, and timestamp integrity in ROS bags without payload deserialization or a local ROS install. It streamlines diagnosing dropped LiDAR scans, odometry jitter spikes, and clock sync anomalies in autonomous navigation datasets without exhausting LLM context windows.[^ref-2]

## Academia

- **LoMa models v1.0.0** (Nov 21). COLMAP released pre-packaged ONNX models and vocabulary trees for LoMa feature detection, extraction, matching, and visual retrieval. It integrates deep learned keypoints and LightGlue-based matching directly into visual reconstruction and relocalization pipelines without native PyTorch runtimes.[^ref-3]
- **FlexGlue models v0.1** (Nov 21). COLMAP added ONNX runtime assets for FlexGlue, incorporating a DINOv3 ConvNeXt-B backbone descriptor and early-stopping sparse matcher. It enables visual mapping pipelines to leverage foundation model representations for robust sparse correspondence estimation across challenging viewpoints.[^ref-4]
- **Visual-inertial example data v1** (Nov 22). A standardized visual-inertial dataset recorded via Project Aria glasses and processed through Aria MPS was published for PyCOLMAP optimization workflows. It provides a reproducible, rectified reference benchmark for validating visual-inertial bundle adjustment and trajectory estimation in spatial computing.[^ref-5]

## Application Readiness

- **MOLA cloud: free online LiDAR SLAM from ROS bags, plus camera and LiDAR-camera calibration**[^ref-1]
  - **Readiness** (Deployment-ready for the stated use). The web platform is live and operational, accepting standard ROS 1/2 bags, .mcap, and cloud URLs to output LAS, PLY, and metric map formats.
  - **Pros.** Zero local installation needed; automatic topic and TF frame detection; supports loop closure and multi-modal fusion.
  - **Cons.** Relies on cloud processing and remote data transfer, making it unsuitable for offline or latency-critical on-robot execution.
- **pnc-diag-mcp: Zero-deserialization offline timing inspector &amp; MCP server for .mcap / .db3 / .bag (no ROS 2 install needed)**[^ref-2]
  - **Readiness** (Pilot-ready). Available as an Apache-2.0 package on PyPI with built-in declarative signal mappings for Nav2 and Autoware storage formats.
  - **Pros.** High-throughput zero-deserialization scans; no ROS dependency; integrates with LLM coding agents via MCP stdio.
  - **Cons.** Only performs read-only timing and metadata health diagnostics without verifying underlying spatial sensor calibration or 3D point quality.
- **LoMa models v1.0.0**[^ref-3]
  - **Readiness** (Research prototype). Official asset release mirrored directly into the COLMAP repository ecosystem for learned feature extraction.
  - **Pros.** Provides float32 and bfloat16 ONNX runtimes; includes pre-built vocabulary trees for efficient image retrieval.
  - **Cons.** Inherits dual licensing constraints across components and requires runtime evaluation to verify geometric accuracy against classical descriptors.
- **FlexGlue models v0.1**[^ref-4]
  - **Readiness** (Research prototype). Mirrored ONNX artifacts and early-stopping matchers integrated upstream for COLMAP feature matching workflows.
  - **Pros.** Transformer-based matching with early-stopping options in float32 and fp16 for reduced latency.
  - **Cons.** Restricted commercial usability due to the DINOv3 backbone license; high compute footprint compared to classical keypoints.
- **Visual-inertial example data v1**[^ref-5]
  - **Readiness** (Deployment-ready for the stated use). Byte-identical sample data release with verified checksums, sparse point clouds, feature databases, and rectified IMU streams.
  - **Pros.** Complete rectified visual-inertial data package designed specifically for testing and reproducible optimization.
  - **Cons.** Single-device trajectory limited in scope to sample verification rather than large-scale metric benchmarking.

## References

{::options footnote_backlink="" /}

[^ref-1]: [MOLA cloud: free online LiDAR SLAM from ROS bags, plus camera and LiDAR-camera calibration](<https://discourse.openrobotics.org/t/mola-cloud-free-online-lidar-slam-from-ros-bags-plus-camera-and-lidar-camera-calibration/60188>) — ROS Discourse, 2026-11-23.
[^ref-2]: [pnc-diag-mcp: Zero-deserialization offline timing inspector &amp; MCP server for .mcap / .db3 / .bag (no ROS 2 install needed)](<https://discourse.openrobotics.org/t/pnc-diag-mcp-zero-deserialization-offline-timing-inspector-mcp-server-for-mcap-db3-bag-no-ros-2-install-needed/60231>) — ROS Discourse, 2026-11-24.
[^ref-3]: [LoMa models v1.0.0](<https://github.com/colmap/colmap/releases/tag/models-loma-v1.0.0>) — COLMAP Releases, 2026-11-21.
[^ref-4]: [FlexGlue models v0.1](<https://github.com/colmap/colmap/releases/tag/models-flexglue-v0.1>) — COLMAP Releases, 2026-11-21.
[^ref-5]: [Visual-inertial example data v1](<https://github.com/colmap/colmap/releases/tag/datasets-visual-inertial-example-v1>) — COLMAP Releases, 2026-11-22.
