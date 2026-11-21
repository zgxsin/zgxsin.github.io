---
title: "Robotics Learning and Foundation Models Digest | November 21, 2026 at 03:30 CET"
published: true
date: 2026-11-21
author: "OpenAI Codex"
slug: robotics-learning-and-foundation-models-digest
categories: [robotics-learning, ai-generated]
---

## Learned Navigation

- **Bridging vision-language reasoning and learned control for legged navigation in the wild** (Nov 20). The author version of a Science Robotics paper describes ROAM, which uses a vision-language model to turn scene cues into risks that guide reinforcement-learned navigation and locomotion policies. The method lets a quadruped account for information such as warnings on signs when choosing where to walk.[^ref-1]
  - **Readiness** (Research prototype). The authors tested ANYmal D on two Swiss Alps hikes of 10.1 km and 2.38 km with operator interventions.
  - **Pros.** The system demonstrated sign interpretation and terrain assessment outside the lab.
  - **Cons.** Each long route was run once, and the tested system relied on a remote vision model.

## Planning and Training

- **GEMS: Generation and Experience Memory for Subgoal-Guided Long-Horizon World Model Planning** (Nov 20). The GEMS preprint pairs predicted intermediate goals with observations from past episodes to guide a frozen visual world model in closed-loop planning. Stored observations can keep a generated subgoal from skipping the grasp required to move an object.[^ref-2]
  - **Readiness** (Research prototype). The authors evaluated long-horizon planning across six benchmark tasks or suites.
  - **Pros.** GEMS reached 92.8% episode success within 150 steps on the OGBench Cube task.
  - **Cons.** It reached 17.7% on Cube-double, and physical workcell performance remains open.
- **Improving Imitation Policies for Multi-Phase Tasks through Residual Learning Allocation** (Nov 20). This preprint estimates which phase of a multi-step task benefits most from a residual reinforcement learning correction on top of an imitation policy. An assembly team can use the approach to decide where to spend a limited training budget.[^ref-3]
  - **Readiness** (Research prototype). The authors evaluated simulated docking and simulated bimanual assembly.
  - **Pros.** In the docking test, correcting the preceding channel phase improved task completion even though most failures occurred in the final phase.
  - **Cons.** Estimating completion gains requires paired episodes, and results have not been established for production assembly.

## References

{::options footnote_backlink="" /}

[^ref-1]: [Bridging vision-language reasoning and learned control for legged navigation in the wild](<https://arxiv.org/abs/2611.25215>) — arXiv Robotics, 2026-11-20.
[^ref-2]: [GEMS: Generation and Experience Memory for Subgoal-Guided Long-Horizon World Model Planning](<https://arxiv.org/abs/2611.25134>) — arXiv Robotics, 2026-11-20.
[^ref-3]: [Improving Imitation Policies for Multi-Phase Tasks through Residual Learning Allocation](<https://arxiv.org/abs/2611.25320>) — arXiv Machine Learning, 2026-11-20.
