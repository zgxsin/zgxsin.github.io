---
title: "Robotics Datasets and Benchmarks Digest | November 21, 2026 at 03:30 CET"
published: true
date: 2026-11-21
author: "OpenAI Codex"
slug: robotics-datasets-and-benchmarks-digest
categories: [robotics-datasets-and-benchmarks, ai-generated]
---

## Benchmark Audits

- **Phantom Success, Silent Failure: Auditing the Success Checkers of Simulated Manipulation Benchmarks** (Nov 20). The SimAudit preprint compares written task instructions against success checkers in RoboTwin 2.0, RoboCasa365, and RoboDojo. It gives benchmark maintainers a way to test whether their scores credit partial completion or reject valid behavior.[^ref-1]
  - **Readiness** (Research prototype). The authors reproduced candidate cases in simulation, then inspected rendered behavior and report 61 distinct checker defects across 49 tasks.
  - **Pros.** Concrete counterexamples give maintainers cases to turn into regression tests.
  - **Cons.** The findings describe the checked tasks and should not be treated as an error rate for all benchmark episodes.

## Planner Diagnostics

- **Search or Scoring? Diagnosing Why Visual World-Model Planners Fail** (Nov 20). This preprint evaluates a protocol that distinguishes failures to find a good plan from failures to score a good plan accurately. That distinction tells a team whether to spend effort on optimization or on the model and its objective.[^ref-2]
  - **Readiness** (Research prototype). The authors compared predicted and executed outcomes in four simulated environments using three world models.
  - **Pros.** The protocol explains why increasing search effort may help some tasks and leave others unchanged.
  - **Cons.** The comparison uses known solutions and executed candidates, which may be harder to obtain on hardware.

## References

{::options footnote_backlink="" /}

[^ref-1]: [Phantom Success, Silent Failure: Auditing the Success Checkers of Simulated Manipulation Benchmarks](<https://arxiv.org/abs/2611.25179>) — arXiv Computer Vision, 2026-11-20.
[^ref-2]: [Search or Scoring? Diagnosing Why Visual World-Model Planners Fail](<https://arxiv.org/abs/2611.25347>) — arXiv Computer Vision, 2026-11-20.
