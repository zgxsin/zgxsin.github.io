---
title: "Robotics Hardware and Sensors Digest | November 21, 2026 at 03:30 CET"
published: true
date: 2026-11-21
author: "OpenAI Codex"
slug: robotics-hardware-and-sensors-digest
categories: [robotics-hardware, ai-generated]
---

## Mechanical Design

- **Video Friday: Drone Squeezes Itself to Fit Through Tight Spaces** (Nov 20). IEEE Spectrum shows a quadrotor prototype that narrows from 31.3 cm to 14.1 cm as its side arms bend on contact, allowing it to pass through a 15 cm gap. Passive compliance could help small inspection drones pass through openings narrower than their normal flight profile.[^ref-1]
  - **Readiness** (Research prototype). The cited team demonstrates a physical prototype flying through a constrained opening.
  - **Pros.** The side arms fold on contact without a separate folding action.
  - **Cons.** The demonstration does not establish durability over repeated impacts or reliability across irregular openings.

{% include video.html youtube="xGkEtl6-vCA" alt="Hardware demonstration" caption="Watch the quadrotor’s two side arms fold on contact as it flies through the 15 cm opening." %}

- **Ferrofluid Shape Control with Deep Reinforcement Learning** (Nov 20). A ferrofluid-control preprint uses camera feedback and one fixed electromagnet to guide a magnetic fluid into transient shapes. The setup tests whether learned control can produce useful deformation with very little actuation hardware.[^ref-2]
  - **Readiness** (Research prototype). The authors trained through physical interaction and repeatedly produced shapes including asterisks and polygons.
  - **Pros.** One electromagnet sufficed for several shapes in the lab setup.
  - **Cons.** The study does not establish load handling or repeatability outside that setup.

## Stereo Cameras

- **VB1943 and robotics: When AI is in the eye (or CMOS sensor) of the beholder** (Nov 18). ST describes a Leopard Imaging stereo setup built around 5-megapixel sensors and a Jetson AGX Orin developer kit, and discusses its industrial VB1943 counterpart. For robots that rely on dense depth, the write-up highlights the need to evaluate both optics and online calibration.[^ref-3]
  - **Readiness** (Research prototype). The study cited by ST used a module with the automotive VB1940 variant, while ST discusses the VB1943 for industrial designs.
  - **Pros.** The reference setup gives teams a starting point for testing depth estimation and calibration drift.
  - **Cons.** The studied setup does not establish equivalent results with the VB1943 under a target robot’s vibration and temperature conditions.

## References

{::options footnote_backlink="" /}

[^ref-1]: [Video Friday: Drone Squeezes Itself to Fit Through Tight Spaces](<https://spectrum.ieee.org/video-friday-morphing-robots-quadrotor>) — IEEE Spectrum Robotics, 2026-11-20.
[^ref-2]: [Ferrofluid Shape Control with Deep Reinforcement Learning](<https://arxiv.org/abs/2611.25232>) — arXiv Robotics, 2026-11-20.
[^ref-3]: [VB1943 and robotics: When AI is in the eye (or CMOS sensor) of the beholder](<https://blog.st.com/vb1943>) — STMicroelectronics, 2026-11-18.
