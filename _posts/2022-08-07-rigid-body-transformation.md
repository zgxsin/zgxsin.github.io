---
title: About Shifted Rigid Body Transformation
published: true
date: 2022-08-07
author: "Guoxiang (Shawn) Zhou"
---

## Introduction

Assume we have two coordinate frames: world frame _W_ and robot frame _R_. Let $T_{WR}$ denote the transformation from world frame to robot frame. Assume $P^W$ and $P^R$ are the corresponding points in world frame and robot frame respectively. They satisfy:

$$P^W = T_{WR} * P^R$$

If $P^R$ is the origin of the robot frame, that is $P^R=[0,0,0,1]^T$, then $P^W=[\vec{t}, 1]^T$ where $\vec{t}$ is the translation part of $T_{WR}$. Obviously, $\vec{t}$ in $T_{WR}$ is a vector starting from the origin of frame _W_ and ending at the origin of frame _R_ expressed in frame _W_.

## The effect of shifting frames on rigid body transformation.

Assume there is a point cloud, which is described in robot frame _R_ with resect to the world frame _R_. The point cloud pose is denoted as $T_{WR}$. Now we want to shift the robot frame _R_ using a transformation, for example, shift robot frame _R_ in +y axis by 2 meters w.r.t the original robot frame _R_. **Notice only the coordinate frame instead of the points is shifted**. Assume the shifted robot frame is _R'_. Since points are not shifted, any point in the point cloud still has the same cooridnate as before in the world frame _W_ after this shifting process. For example, point A has a
coordinate [0, 2, 0] in _R_, now its coordinate is [0, 0, 0] in _R'_, but its world frame coordinate is the same.

We can then construct the transformation matrix among frame _R_ and _R'_ : $T_{RR'} = \\\{I, \vec{t}\\\}$ where $\vec{t} = [0, 2, 0]^T$. Afterwards, the point cloud in frame _R'_ can be obtained by: $T_{R'R}* P^R$. The point cloud pose (the pose of frame _R'_) is: $T_{WR}*T_{RR'}$.

## The effect of shifting points on rigid body transformation.

Assume there is a point cloud, which is described in robot frame _R_ with resect to the world frame _R_. The point cloud pose is denoted as $T_{WR}$. Now we want to shift the point cloud in robot frame _R_ using a transformation, for example, shift point cloud in -y axis by 2 meters in the robot frame _R_. For example, point A has a coordinate $[0, 2, 0]^T$ in _R_, after shifting, its corridnate becames $[0, 0, 0]^T$. We can construct a transformation for this process:

$$Cloud^{Transformed} = T * Cloud^R$$

where $T=\\\{ I, [0,-2,0]^T \\\}$.

So the transformed point cloud is $Cloud^{Transformed}$ and its pose is $T_{WR}$.
