---
title: IMU Preintegration
published: true
date: 2023-10-30
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

An IMU produces hundreds of measurements per second, a camera a few dozen frames, and an optimizer only wants to keep a state every few frames. **IMU preintegration** is the trick that bridges these rates: it summarizes all IMU measurements between two keyframes into one relative-motion measurement that does not need to be recomputed every time the optimizer moves the keyframe states.

This post follows the paper *On-Manifold Preintegration for Real-Time Visual-Inertial Odometry* (Forster et al.). It sets up visual-inertial odometry (VIO) as a factor graph, derives the IMU kinematics, builds the preintegrated measurements and their noise, shows how to handle bias changes cheaply, and ends with how to use all of it in GTSAM.

## IMU Preintegration

### What problems does it solve

Visual-inertial odometry attains highly accurate state estimates with nonlinear optimization: keep a window (or the whole history) of states and minimize the visual and inertial errors jointly. The problem is the IMU rate, typically 100 Hz to 1 kHz. A naive implementation adds a new state for every IMU measurement, and the number of variables grows so fast that real-time optimization quickly becomes infeasible.

The usual fix is to keep states only at selected **keyframes** and to integrate the IMU measurements between two keyframes into a single relative-motion constraint. Plain integration, however, needs an initial condition: the pose and velocity at the first keyframe. Every iteration of the optimizer changes that estimate, so the integration over all keyframe intervals would have to be repeated at every iteration.

Lupton and Sukkarieh showed that this repeated integration can be avoided by **reparametrizing the relative motion constraint** so that it no longer depends on the state at the first keyframe. That reparametrization is called IMU preintegration. Forster et al. carried it out properly on the rotation manifold SO(3), derived its noise covariance, and gave a first-order correction for bias changes, which is what makes it practical. It solves three problems at once:

1. **Size of the problem.** Hundreds of IMU samples between two keyframes become one factor between two states.
2. **Repeated integration.** The preintegrated measurement is computed once from the raw IMU data, independent of the keyframe states.
3. **Bias changes.** When the optimizer updates the bias estimate, the measurement is corrected with precomputed Jacobians instead of being re-integrated.

## Visual-inertial state estimation as MAP

### The state

The state of the system at time $i$ is the IMU orientation, position, velocity and biases:

$$
\mathbf{x}_i = [R_i,\ \mathbf{p}_i,\ \mathbf{v}_i,\ \mathbf{b}_i]
$$

The pose $(R_i, \mathbf{p}\_i)$ belongs to SE(3), the velocity lives in a vector space, $\mathbf{v}\_i \in \mathbb{R}^3$, and the biases are $\mathbf{b}\_i = [\mathbf{b}^g_i, \mathbf{b}^a_i] \in \mathbb{R}^6$, where $\mathbf{b}^g_i, \mathbf{b}^a_i \in \mathbb{R}^3$ are the gyroscope and accelerometer bias.

Let $\mathcal{K}\_k$ denote the set of all keyframes up to time $k$. We estimate the state of all keyframes:

$$
\mathcal{X}_k = \{\mathbf{x}_i\}_{i \in \mathcal{K}_k}
$$

The paper uses a structure-less approach, so the 3D landmarks are not variables of the optimization. The same formulation extends directly to estimating landmarks and the camera intrinsic and extrinsic calibration.

### The measurements

The inputs are the camera and IMU measurements. $\mathcal{C}\_i$ denotes the image measurements at keyframe $i$. The camera can observe several landmarks $l$ at time $i$, so $\mathcal{C}\_i$ contains several image measurements $\mathbf{z}\_{il}$; with slight abuse of notation we write $l \in \mathcal{C}\_i$ when landmark $l$ is seen at time $i$.

$\mathcal{I}\_{ij}$ denotes the set of IMU measurements acquired between two consecutive keyframes $i$ and $j$. Depending on the IMU rate and on how often keyframes are selected, it contains anything from a few to hundreds of measurements. The set of measurements collected up to time $k$ is

$$
\mathcal{Z}_k = \{\mathcal{C}_i, \mathcal{I}_{ij}\}_{(i,j) \in \mathcal{K}_k}
$$

### Factor graph and MAP estimation

The posterior of the variables $\mathcal{X}\_k$ given the measurements $\mathcal{Z}\_k$ and the prior $p(\mathcal{X}\_0)$ is

$$
\begin{aligned}
p(\mathcal{X}_k \mid \mathcal{Z}_k)
&\propto p(\mathcal{X}_0)\, p(\mathcal{Z}_k \mid \mathcal{X}_k) \\
&\stackrel{(a)}{=} p(\mathcal{X}_0) \prod_{(i,j) \in \mathcal{K}_k} p(\mathcal{C}_i, \mathcal{I}_{ij} \mid \mathcal{X}_k) \\
&\stackrel{(b)}{=} p(\mathcal{X}_0) \prod_{(i,j) \in \mathcal{K}_k} p(\mathcal{I}_{ij} \mid \mathbf{x}_i, \mathbf{x}_j) \\
&\qquad \cdot \prod_{i \in \mathcal{K}_k} \prod_{l \in \mathcal{C}_i} p(\mathbf{z}_{il} \mid \mathbf{x}_i)
\end{aligned}
$$

Step (a) assumes the measurements are independent of each other. Step (b) applies the Markov property: an image measurement at time $i$ depends only on the state at time $i$, and the IMU measurements between $i$ and $j$ depend only on the states at $i$ and $j$.

The measurements are known, so they become parameters of the factors, and the unknowns are the only variables. This is a **factor graph**: a bipartite graph with one node per unknown state and one node per probability factor, with an edge whenever a factor involves a state. For VIO, every keyframe state carries vision factors, and consecutive keyframe states are connected by one IMU factor and one bias factor.

The MAP estimate $\mathcal{X}\_k^\star$ maximizes the posterior, which is the same as minimizing the negative log-posterior. **Under zero-mean Gaussian noise**, the negative log-posterior is a sum of squared residuals:

$$
\mathcal{X}_k^\star = \arg\min_{\mathcal{X}_k} \; \lVert \mathbf{r}_0 \rVert^2_{\Sigma_0} +
\sum_{(i,j) \in \mathcal{K}_k} \lVert \mathbf{r}_{\mathcal{I}_{ij}} \rVert^2_{\Sigma_{ij}} +
\sum_{i \in \mathcal{K}_k} \sum_{l \in \mathcal{C}_i} \lVert \mathbf{r}_{\mathcal{C}_{il}} \rVert^2_{\Sigma_{\mathcal{C}}}
$$

where $\lVert \mathbf{r} \rVert^2\_\Sigma = \mathbf{r}^T \Sigma^{-1} \mathbf{r}$. $\mathbf{r}\_0$, $\mathbf{r}\_{\mathcal{I}\_{ij}}$ and $\mathbf{r}\_{\mathcal{C}\_{il}}$ are the residuals of the prior, the IMU and the camera measurements, and $\Sigma_0$, $\Sigma\_{ij}$, $\Sigma\_{\mathcal{C}}$ their covariances. A residual measures the mismatch between a measured quantity and the value predicted from the state. The rest of this post derives $\mathbf{r}\_{\mathcal{I}\_{ij}}$ and $\Sigma\_{ij}$.

## IMU model and motion integration

### What an IMU measures

In one sentence each:

- The **gyroscope** measures the angular velocity of the IMU frame relative to an inertial frame, expressed in the IMU frame.
- The **accelerometer** measures the acceleration of the IMU relative to an inertial frame, **minus gravity**, expressed in the IMU frame.

Both are corrupted by additive white noise $\boldsymbol{\eta}$ and a slowly varying bias $\mathbf{b}$:

$$
\begin{aligned}
{}_B\tilde{\boldsymbol{\omega}}_{WB}(t) &= {}_B\boldsymbol{\omega}_{WB}(t) + \mathbf{b}^g(t) + \boldsymbol{\eta}^g(t) \\
{}_B\tilde{\mathbf{a}}(t) &= R_{WB}^T(t)\big({}_W\mathbf{a}(t) - {}_W\mathbf{g}\big) + \mathbf{b}^a(t) + \boldsymbol{\eta}^a(t)
\end{aligned}
$$

The pose of the IMU is $\lbrace R\_{WB}, {}\_W\mathbf{p}\rbrace$, which maps a point from the body (IMU) frame $B$ to the world frame $W$. The body frame is assumed to coincide with the IMU frame, and the camera pose in the body frame, $T\_{BC}$, is known from calibration. ${}\_B\boldsymbol{\omega}\_{WB}(t) \in \mathbb{R}^3$ is the angular velocity of $B$ relative to $W$, expressed in $B$; ${}\_W\mathbf{a}(t) \in \mathbb{R}^3$ is the acceleration of the sensor and ${}\_W\mathbf{g}$ the gravity vector, both in world coordinates. **We neglect the rotation of the earth**, which amounts to treating $W$ as an inertial frame.

### Why the minus gravity

An accelerometer does not measure total acceleration. It measures **non-gravitational acceleration**, also called **proper acceleration** or **specific force**:

$$
\mathbf{f} = \mathbf{a} - \mathbf{g}
$$

That is where the minus sign comes from. A stationary IMU has $\mathbf{a} = \mathbf{0}$, so it measures $\mathbf{f} = -\mathbf{g}$. With a z-up world frame,

$$
\mathbf{g} = \begin{bmatrix} 0 \\ 0 \\ -9.81 \end{bmatrix}
\quad\Rightarrow\quad
-\mathbf{g} = \begin{bmatrix} 0 \\ 0 \\ 9.81 \end{bmatrix}
$$

which is what an IMU reports when it is stationary with its z-axis pointing straight up (for example, a board lying level, component side up): $[0,\ 0,\ 9.81]^T\ \mathrm{m/s^2}$, plus bias. Intuitively, the table pushes the IMU up with a force that cancels gravity, and that push is what the accelerometer feels. An IMU in free fall has $\mathbf{a} = \mathbf{g}$ and measures zero.

The reading depends on how the **sensor's own axes** are oriented, not on the world-frame convention. A tilted IMU spreads the same 9.81 across its axes, $\tilde{\mathbf{a}} = R\_{WB}^T [0,\ 0,\ 9.81]^T$, which is how a static IMU estimates roll and pitch. An IMU whose z-axis points down, such as the forward-right-down body frame used with NED world frames in aerospace, reads $[0,\ 0,\ -9.81]^T$ at rest. In both cases the specific force points physically up, away from the Earth.

### Kinematic model and integration

To infer motion from the IMU, use the kinematic model

$$
\dot{R}_{WB} = R_{WB}\, {}_B\boldsymbol{\omega}_{WB}^\wedge, \qquad
{}_W\dot{\mathbf{v}} = {}_W\mathbf{a}, \qquad
{}_W\dot{\mathbf{p}} = {}_W\mathbf{v}
$$

where $(\cdot)^\wedge$ turns a vector into its skew-symmetric matrix. The first equation is the time derivative of a rotation whose angular velocity is expressed in the body frame (see the section *Rotation as a continuous-time trajectory in SO(3)* in Solà's *Quaternion kinematics for the error-state Kalman filter*). The state at time $t + \Delta t$ follows by integration:

$$
\begin{aligned}
R_{WB}(t+\Delta t) &= R_{WB}(t)\, \operatorname{Exp}\Big(\int_t^{t+\Delta t} {}_B\boldsymbol{\omega}_{WB}(\tau)\, d\tau\Big) \\
{}_W\mathbf{v}(t+\Delta t) &= {}_W\mathbf{v}(t) + \int_t^{t+\Delta t} {}_W\mathbf{a}(\tau)\, d\tau \\
{}_W\mathbf{p}(t+\Delta t) &= {}_W\mathbf{p}(t) + \int_t^{t+\Delta t} {}_W\mathbf{v}(\tau)\, d\tau \\
&= {}_W\mathbf{p}(t) + \int_t^{t+\Delta t} \Big({}_W\mathbf{v}(t) + \int_t^{\tau} {}_W\mathbf{a}(\tau_1)\, d\tau_1\Big) d\tau \\
&= {}_W\mathbf{p}(t) + {}_W\mathbf{v}(t)\, \Delta t + \int_t^{t+\Delta t} \int_t^{\tau} {}_W\mathbf{a}(\tau_1)\, d\tau_1\, d\tau
\end{aligned}
$$

$\operatorname{Exp}(\boldsymbol{\phi})$ maps a rotation vector to a rotation matrix, and $\operatorname{Log}$ is its inverse. The rotation formula is exact only when the direction of $\boldsymbol{\omega}$ is constant over the interval, which is fine for the short intervals used next. Assuming ${}\_W\mathbf{a}$ and ${}\_B\boldsymbol{\omega}\_{WB}$ are constant in $[t, t+\Delta t]$:

$$
\begin{aligned}
R_{WB}(t+\Delta t) &= R_{WB}(t)\, \operatorname{Exp}\big({}_B\boldsymbol{\omega}_{WB}(t)\, \Delta t\big) \\
{}_W\mathbf{v}(t+\Delta t) &= {}_W\mathbf{v}(t) + {}_W\mathbf{a}(t)\, \Delta t \\
{}_W\mathbf{p}(t+\Delta t) &= {}_W\mathbf{p}(t) + {}_W\mathbf{v}(t)\, \Delta t + \tfrac{1}{2}\, {}_W\mathbf{a}(t)\, \Delta t^2
\end{aligned}
$$

Now replace ${}\_W\mathbf{a}$ and ${}\_B\boldsymbol{\omega}\_{WB}$ with the IMU model solved for the true quantities. Dropping the frame subscripts from here on, since the notation is unambiguous:

$$
\begin{aligned}
R(t+\Delta t) &= R(t)\, \operatorname{Exp}\big((\tilde{\boldsymbol{\omega}}(t) - \mathbf{b}^g(t) - \boldsymbol{\eta}^{gd}(t))\, \Delta t\big) \\
\mathbf{v}(t+\Delta t) &= \mathbf{v}(t) + \mathbf{g}\, \Delta t + R(t)\big(\tilde{\mathbf{a}}(t) - \mathbf{b}^a(t) - \boldsymbol{\eta}^{ad}(t)\big)\, \Delta t \\
\mathbf{p}(t+\Delta t) &= \mathbf{p}(t) + \mathbf{v}(t)\, \Delta t + \tfrac{1}{2}\mathbf{g}\, \Delta t^2 + \tfrac{1}{2} R(t)\big(\tilde{\mathbf{a}}(t) - \mathbf{b}^a(t) - \boldsymbol{\eta}^{ad}(t)\big)\, \Delta t^2
\end{aligned}
$$

This is equation (31) of the paper. The velocity and position updates assume the orientation $R(t)$ is constant between two measurements, which is not an exact solution of $\dot{R} = R\,\boldsymbol{\omega}^\wedge$ when the rotation rate is non-zero. A **high-rate IMU** keeps this error small. The scheme is simple and easy to propagate uncertainty through; for slower IMUs, a higher-order integration method may be worth it.

$\boldsymbol{\eta}^{gd}$ and $\boldsymbol{\eta}^{ad}$ are the **discrete-time** noises. Their covariance depends on the sampling period and relates to the continuous-time noise spectral density by

$$
\operatorname{Cov}(\boldsymbol{\eta}^{gd}(t)) = \frac{1}{\Delta t} \operatorname{Cov}(\boldsymbol{\eta}^{g}(t)), \qquad
\operatorname{Cov}(\boldsymbol{\eta}^{ad}(t)) = \frac{1}{\Delta t} \operatorname{Cov}(\boldsymbol{\eta}^{a}(t))
$$

The faster the IMU samples, the noisier each individual sample, but averaging over more samples per second keeps the integrated noise the same.

## IMU preintegration on manifold

### Integrating from one keyframe to the next

Assume the IMU is synchronized with the camera and provides measurements at discrete times $k$. Iterating equation (31) over all intervals between keyframes $k = i$ and $k = j$, with $\Delta t\_{ij} = \sum\_{k=i}^{j-1} \Delta t$ and the shorthand $(\cdot)\_k = (\cdot)(t_k)$:

$$
\begin{aligned}
R_j &= R_i \prod_{k=i}^{j-1} \operatorname{Exp}\big((\tilde{\boldsymbol{\omega}}_k - \mathbf{b}^g_k - \boldsymbol{\eta}^{gd}_k)\, \Delta t\big) \\
\mathbf{v}_j &= \mathbf{v}_i + \mathbf{g}\, \Delta t_{ij} + \sum_{k=i}^{j-1} R_k\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_k - \boldsymbol{\eta}^{ad}_k\big)\, \Delta t \\
\mathbf{p}_j &= \mathbf{p}_i + \sum_{k=i}^{j-1} \Big[\mathbf{v}_k\, \Delta t + \tfrac{1}{2}\mathbf{g}\, \Delta t^2 + \tfrac{1}{2} R_k\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_k - \boldsymbol{\eta}^{ad}_k\big)\, \Delta t^2\Big]
\end{aligned}
$$

This already predicts the motion from $t_i$ to $t_j$, but it has the drawback from the introduction: **it has to be recomputed whenever the linearization point at $t_i$ changes**. A change in $R_i$ changes every $R_k$ for $k = i, \dots, j-1$, and with them every term of the sums.

### Relative motion increments

To avoid that, move everything that depends on the state at $t_i$ to the left-hand side, and rotate into the frame of keyframe $i$. This defines **relative motion increments** whose right-hand sides are independent of the pose and velocity at $t_i$:

$$
\begin{aligned}
\Delta R_{ij} &\doteq R_i^T R_j = \prod_{k=i}^{j-1} \operatorname{Exp}\big((\tilde{\boldsymbol{\omega}}_k - \mathbf{b}^g_k - \boldsymbol{\eta}^{gd}_k)\, \Delta t\big) \\
\Delta \mathbf{v}_{ij} &\doteq R_i^T\big(\mathbf{v}_j - \mathbf{v}_i - \mathbf{g}\, \Delta t_{ij}\big) = \sum_{k=i}^{j-1} \Delta R_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_k - \boldsymbol{\eta}^{ad}_k\big)\, \Delta t \\
\Delta \mathbf{p}_{ij} &\doteq R_i^T\big(\mathbf{p}_j - \mathbf{p}_i - \mathbf{v}_i\, \Delta t_{ij} - \tfrac{1}{2}\mathbf{g}\, \Delta t_{ij}^2\big) = \sum_{k=i}^{j-1} \Big[\Delta \mathbf{v}_{ik}\, \Delta t + \tfrac{1}{2} \Delta R_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_k - \boldsymbol{\eta}^{ad}_k\big)\, \Delta t^2\Big]
\end{aligned}
$$

with $\Delta R\_{ik} = R_i^T R_k$ and $\Delta \mathbf{v}\_{ik} = R_i^T(\mathbf{v}\_k - \mathbf{v}\_i - \mathbf{g}\, \Delta t\_{ik})$. This is equation (33) of the paper.

The rotation and velocity lines follow by multiplying the first two lines of the previous block by $R_i^T$. The position line takes a little more work. Write $\mathbf{a}^{\prime}\_k = \tilde{\mathbf{a}}\_k - \mathbf{b}^a_k - \boldsymbol{\eta}^{ad}\_k$ and use the definition of $\Delta \mathbf{v}\_{ik}$ to replace each velocity, $\mathbf{v}\_k = \mathbf{v}\_i + \mathbf{g}\, \Delta t\_{ik} + R_i \Delta \mathbf{v}\_{ik}$:

$$
\begin{aligned}
\mathbf{p}_j - \mathbf{p}_i
&= \sum_{k=i}^{j-1} \Big[\mathbf{v}_k\, \Delta t + \tfrac{1}{2}\mathbf{g}\, \Delta t^2 + \tfrac{1}{2} R_k \mathbf{a}'_k\, \Delta t^2\Big] \\
&= \mathbf{v}_i\, \Delta t_{ij} + \mathbf{g} \sum_{k=i}^{j-1} \Big[\Delta t_{ik}\, \Delta t + \tfrac{1}{2}\Delta t^2\Big] + \sum_{k=i}^{j-1} \Big[R_i \Delta \mathbf{v}_{ik}\, \Delta t + \tfrac{1}{2} R_k \mathbf{a}'_k\, \Delta t^2\Big]
\end{aligned}
$$

With $n = j - i$ samples, $\Delta t\_{ik} = (k - i)\Delta t$ and the gravity sum is $\Delta t^2 \big(\tfrac{n(n-1)}{2} + \tfrac{n}{2}\big) = \tfrac{1}{2} n^2 \Delta t^2 = \tfrac{1}{2}\Delta t\_{ij}^2$. Moving the $\mathbf{v}\_i$ and $\mathbf{g}$ terms to the left and multiplying by $R_i^T$ gives the position line, since $R_i^T R_k = \Delta R\_{ik}$.

Unlike $\Delta R\_{ij}$, **neither $\Delta \mathbf{v}\_{ij}$ nor $\Delta \mathbf{p}\_{ij}$ is the true physical change in velocity or position.** They are defined so that the right-hand side is **independent of the state at time $i$ and of gravity**, which means it can be computed directly from the IMU measurements between the two keyframes.

Two issues remain with equation (33):

1. The sums and products still **depend on the bias estimate**.
2. The right-hand side has a **fairly intricate dependence on the measurement noise**, which makes it awkward to write down a likelihood.

The rest of the derivation fixes both: assume the bias stays constant between two keyframes and correct it to first order later, and rewrite equation (33) so that the noise appears as a separate additive term.

For the first point, assume

$$
\mathbf{b}^g_k = \mathbf{b}^g_i, \qquad \mathbf{b}^a_k = \mathbf{b}^a_i, \qquad k = i, \dots, j-1
$$

### Preintegrated IMU measurements

Equation (33) relates the states at keyframes $i$ and $j$ (left-hand side) to the measurements (right-hand side), so it is already a measurement model. To make the likelihood easy to write, isolate the noise.

**Rotation.** For a small $\delta\boldsymbol{\phi}$, $\operatorname{Exp}(\boldsymbol{\phi} + \delta\boldsymbol{\phi}) \approx \operatorname{Exp}(\boldsymbol{\phi})\operatorname{Exp}(J_r(\boldsymbol{\phi})\, \delta\boldsymbol{\phi})$, where $J_r$ is the right Jacobian of SO(3). Applying this to each factor of the product splits off the noise:

$$
\Delta R_{ij} \approx \prod_{k=i}^{j-1} \Big[\operatorname{Exp}\big((\tilde{\boldsymbol{\omega}}_k - \mathbf{b}^g_i)\, \Delta t\big) \operatorname{Exp}\big(-J_r^k\, \boldsymbol{\eta}^{gd}_k\, \Delta t\big)\Big],
\qquad J_r^k \doteq J_r\big((\tilde{\boldsymbol{\omega}}_k - \mathbf{b}^g_i)\, \Delta t\big)
$$

The identity $\operatorname{Exp}(\boldsymbol{\phi})\, R = R \operatorname{Exp}(R^T\boldsymbol{\phi})$ moves all the noise terms to the end of the product:

$$
\Delta R_{ij} \approx \Delta \tilde{R}_{ij} \prod_{k=i}^{j-1} \operatorname{Exp}\big(-\Delta \tilde{R}_{k+1,j}^T\, J_r^k\, \boldsymbol{\eta}^{gd}_k\, \Delta t\big) \doteq \Delta \tilde{R}_{ij} \operatorname{Exp}(-\delta\boldsymbol{\phi}_{ij})
$$

where the **preintegrated rotation measurement** is

$$
\Delta \tilde{R}_{ij} \doteq \prod_{k=i}^{j-1} \operatorname{Exp}\big((\tilde{\boldsymbol{\omega}}_k - \mathbf{b}^g_i)\, \Delta t\big)
$$

**Velocity and position.** Substitute $\Delta R\_{ik} \approx \Delta \tilde{R}\_{ik} \operatorname{Exp}(-\delta\boldsymbol{\phi}\_{ik}) \approx \Delta \tilde{R}\_{ik}(I - \delta\boldsymbol{\phi}\_{ik}^\wedge)$ into the velocity and position lines of equation (33), use $-\delta\boldsymbol{\phi}^\wedge \mathbf{a} = \mathbf{a}^\wedge \delta\boldsymbol{\phi}$, and drop the products of noise terms. Everything noise-free collects into the **preintegrated velocity and position measurements**

$$
\Delta \tilde{\mathbf{v}}_{ij} \doteq \sum_{k=i}^{j-1} \Delta \tilde{R}_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_i\big)\, \Delta t,
\qquad
\Delta \tilde{\mathbf{p}}_{ij} \doteq \sum_{k=i}^{j-1} \Big[\Delta \tilde{\mathbf{v}}_{ik}\, \Delta t + \tfrac{1}{2} \Delta \tilde{R}_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_i\big)\, \Delta t^2\Big]
$$

and the rest into the noise terms $\delta\mathbf{v}\_{ij}$ and $\delta\mathbf{p}\_{ij}$, given in the noise propagation section below.

**The measurement model.** Plugging the three expressions back into equation (33) gives

$$
\begin{aligned}
\Delta \tilde{R}_{ij} &= R_i^T R_j \operatorname{Exp}(\delta\boldsymbol{\phi}_{ij}) \\
\Delta \tilde{\mathbf{v}}_{ij} &= R_i^T\big(\mathbf{v}_j - \mathbf{v}_i - \mathbf{g}\, \Delta t_{ij}\big) + \delta\mathbf{v}_{ij} \\
\Delta \tilde{\mathbf{p}}_{ij} &= R_i^T\big(\mathbf{p}_j - \mathbf{p}_i - \mathbf{v}_i\, \Delta t_{ij} - \tfrac{1}{2}\mathbf{g}\, \Delta t_{ij}^2\big) + \delta\mathbf{p}_{ij}
\end{aligned}
$$

This is equation (38) of the paper, and it has exactly the form we want: **measurement = function of the state "plus" noise**.

- The left-hand side, $\Delta \tilde{R}\_{ij}$, $\Delta \tilde{\mathbf{v}}\_{ij}$ and $\Delta \tilde{\mathbf{p}}\_{ij}$, is computed **directly from the raw IMU measurements** and the bias estimate.
- The first term on the right depends only on the **state variables** at $i$ and $j$.
- $\delta\boldsymbol{\phi}\_{ij}$, $\delta\mathbf{v}\_{ij}$ and $\delta\mathbf{p}\_{ij}$ are the **noise**.

With this form the log-likelihood is straightforward. If $\delta\mathbf{v}\_{ij}$ and $\delta\mathbf{p}\_{ij}$ are zero-mean Gaussian, the negative log-likelihood of the last two lines is a quadratic function. The same holds for the rotation if $\delta\boldsymbol{\phi}\_{ij}$ is zero-mean Gaussian, with the error measured in the tangent space through $\operatorname{Log}$.

### Noise propagation

Stack the preintegration noise into

$$
\boldsymbol{\eta}^\Delta_{ij} \doteq [\delta\boldsymbol{\phi}_{ij}^T,\ \delta\mathbf{v}_{ij}^T,\ \delta\mathbf{p}_{ij}^T]^T \sim \mathcal{N}(\mathbf{0}_{9 \times 1}, \Sigma_{ij})
$$

To first order, the three components are

$$
\begin{aligned}
\delta\boldsymbol{\phi}_{ij} &\simeq \sum_{k=i}^{j-1} \Delta \tilde{R}_{k+1,j}^T\, J_r^k\, \boldsymbol{\eta}^{gd}_k\, \Delta t \\
\delta\mathbf{v}_{ij} &\simeq \sum_{k=i}^{j-1} \Big[-\Delta \tilde{R}_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_i\big)^\wedge \delta\boldsymbol{\phi}_{ik}\, \Delta t + \Delta \tilde{R}_{ik}\, \boldsymbol{\eta}^{ad}_k\, \Delta t\Big] \\
\delta\mathbf{p}_{ij} &\simeq \sum_{k=i}^{j-1} \Big[\delta\mathbf{v}_{ik}\, \Delta t - \tfrac{1}{2}\Delta \tilde{R}_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_i\big)^\wedge \delta\boldsymbol{\phi}_{ik}\, \Delta t^2 + \tfrac{1}{2}\Delta \tilde{R}_{ik}\, \boldsymbol{\eta}^{ad}_k\, \Delta t^2\Big]
\end{aligned}
$$

These express $\boldsymbol{\eta}^\Delta\_{ij}$ as a **linear function of the IMU noise** $\boldsymbol{\eta}^d_k \doteq [\boldsymbol{\eta}^{gd}\_k, \boldsymbol{\eta}^{ad}\_k]$. So once the covariance $\Sigma\_\eta$ of $\boldsymbol{\eta}^d_k$ is known from the IMU datasheet, $\Sigma\_{ij}$ follows by linear propagation.

In practice the propagation is done **incrementally**, one IMU sample at a time, so the covariance is ready the moment the next keyframe arrives. Each new sample updates the noise as $\boldsymbol{\eta}^\Delta\_{i,k+1} = A_k\, \boldsymbol{\eta}^\Delta\_{ik} + B_k\, \boldsymbol{\eta}^d_k$, starting from $\Sigma\_{ii} = \mathbf{0}\_{9 \times 9}$:

$$
\Sigma_{i,k+1} = A_k\, \Sigma_{ik}\, A_k^T + B_k\, \Sigma_\eta\, B_k^T
$$

$$
A_k = \begin{bmatrix}
\Delta \tilde{R}_{k,k+1}^T & \mathbf{0} & \mathbf{0} \\
-\Delta \tilde{R}_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_i\big)^\wedge \Delta t & I & \mathbf{0} \\
-\tfrac{1}{2}\Delta \tilde{R}_{ik}\big(\tilde{\mathbf{a}}_k - \mathbf{b}^a_i\big)^\wedge \Delta t^2 & I\, \Delta t & I
\end{bmatrix},
\qquad
B_k = \begin{bmatrix}
J_r^k\, \Delta t & \mathbf{0} \\
\mathbf{0} & \Delta \tilde{R}_{ik}\, \Delta t \\
\mathbf{0} & \tfrac{1}{2}\Delta \tilde{R}_{ik}\, \Delta t^2
\end{bmatrix}
$$

This is an EKF-style covariance prediction, but on the relative increments instead of on the absolute state.

### Incorporating bias updates

So far the bias $\lbrace \bar{\mathbf{b}}^a_i, \bar{\mathbf{b}}^g_i\rbrace$ used during preintegration between $k = i$ and $k = j$ was assumed correct and fixed. During optimization, though, the bias estimate changes by a small $\delta\mathbf{b}$. Recomputing the preintegrated measurements at every change would bring back the repeated integration we wanted to avoid, so instead, for a bias update $\mathbf{b} \leftarrow \bar{\mathbf{b}} + \delta\mathbf{b}$, use a **first-order expansion**:

$$
\begin{aligned}
\Delta \tilde{R}_{ij}(\mathbf{b}^g_i) &\simeq \Delta \tilde{R}_{ij}(\bar{\mathbf{b}}^g_i) \operatorname{Exp}\Big(\frac{\partial \Delta \bar{R}_{ij}}{\partial \mathbf{b}^g}\, \delta\mathbf{b}^g_i\Big) \\
\Delta \tilde{\mathbf{v}}_{ij}(\mathbf{b}^g_i, \mathbf{b}^a_i) &\simeq \Delta \tilde{\mathbf{v}}_{ij}(\bar{\mathbf{b}}^g_i, \bar{\mathbf{b}}^a_i) + \frac{\partial \Delta \bar{\mathbf{v}}_{ij}}{\partial \mathbf{b}^g}\, \delta\mathbf{b}^g_i + \frac{\partial \Delta \bar{\mathbf{v}}_{ij}}{\partial \mathbf{b}^a}\, \delta\mathbf{b}^a_i \\
\Delta \tilde{\mathbf{p}}_{ij}(\mathbf{b}^g_i, \mathbf{b}^a_i) &\simeq \Delta \tilde{\mathbf{p}}_{ij}(\bar{\mathbf{b}}^g_i, \bar{\mathbf{b}}^a_i) + \frac{\partial \Delta \bar{\mathbf{p}}_{ij}}{\partial \mathbf{b}^g}\, \delta\mathbf{b}^g_i + \frac{\partial \Delta \bar{\mathbf{p}}_{ij}}{\partial \mathbf{b}^a}\, \delta\mathbf{b}^a_i
\end{aligned}
$$

The Jacobians are evaluated at $\bar{\mathbf{b}}\_i$, **remain constant**, and can be **precomputed during preintegration**, accumulating one term per IMU sample:

$$
\begin{aligned}
\frac{\partial \Delta \bar{R}_{ij}}{\partial \mathbf{b}^g} &= -\sum_{k=i}^{j-1} \Delta \tilde{R}_{k+1,j}^T\, J_r^k\, \Delta t \\
\frac{\partial \Delta \bar{\mathbf{v}}_{ij}}{\partial \mathbf{b}^a} &= -\sum_{k=i}^{j-1} \Delta \bar{R}_{ik}\, \Delta t,
\qquad
\frac{\partial \Delta \bar{\mathbf{v}}_{ij}}{\partial \mathbf{b}^g} = -\sum_{k=i}^{j-1} \Delta \bar{R}_{ik}\big(\tilde{\mathbf{a}}_k - \bar{\mathbf{b}}^a_i\big)^\wedge \frac{\partial \Delta \bar{R}_{ik}}{\partial \mathbf{b}^g}\, \Delta t \\
\frac{\partial \Delta \bar{\mathbf{p}}_{ij}}{\partial \mathbf{b}^a} &= \sum_{k=i}^{j-1} \Big[\frac{\partial \Delta \bar{\mathbf{v}}_{ik}}{\partial \mathbf{b}^a}\, \Delta t - \tfrac{1}{2}\Delta \bar{R}_{ik}\, \Delta t^2\Big] \\
\frac{\partial \Delta \bar{\mathbf{p}}_{ij}}{\partial \mathbf{b}^g} &= \sum_{k=i}^{j-1} \Big[\frac{\partial \Delta \bar{\mathbf{v}}_{ik}}{\partial \mathbf{b}^g}\, \Delta t - \tfrac{1}{2}\Delta \bar{R}_{ik}\big(\tilde{\mathbf{a}}_k - \bar{\mathbf{b}}^a_i\big)^\wedge \frac{\partial \Delta \bar{R}_{ik}}{\partial \mathbf{b}^g}\, \Delta t^2\Big]
\end{aligned}
$$

The rotation does not depend on the accelerometer bias, which is why it has only a gyroscope Jacobian. If the bias drifts far from $\bar{\mathbf{b}}\_i$, the linearization degrades; implementations then re-integrate with the new bias as the linearization point.

### Preintegrated IMU factors

With the measurement model of equation (38), Gaussian noise with covariance $\Sigma\_{ij}$ (to first order), and the bias correction above, the IMU residual $\mathbf{r}\_{\mathcal{I}\_{ij}} \doteq [\mathbf{r}\_{\Delta R\_{ij}}^T,\ \mathbf{r}\_{\Delta \mathbf{v}\_{ij}}^T,\ \mathbf{r}\_{\Delta \mathbf{p}\_{ij}}^T]^T \in \mathbb{R}^9$ is

$$
\begin{aligned}
\mathbf{r}_{\Delta R_{ij}} &\doteq \operatorname{Log}\Big(\Big(\Delta \tilde{R}_{ij}(\bar{\mathbf{b}}^g_i) \operatorname{Exp}\Big(\frac{\partial \Delta \bar{R}_{ij}}{\partial \mathbf{b}^g}\, \delta\mathbf{b}^g\Big)\Big)^T R_i^T R_j\Big) \\
\mathbf{r}_{\Delta \mathbf{v}_{ij}} &\doteq R_i^T\big(\mathbf{v}_j - \mathbf{v}_i - \mathbf{g}\, \Delta t_{ij}\big) - \Big[\Delta \tilde{\mathbf{v}}_{ij}(\bar{\mathbf{b}}^g_i, \bar{\mathbf{b}}^a_i) + \frac{\partial \Delta \bar{\mathbf{v}}_{ij}}{\partial \mathbf{b}^g}\, \delta\mathbf{b}^g + \frac{\partial \Delta \bar{\mathbf{v}}_{ij}}{\partial \mathbf{b}^a}\, \delta\mathbf{b}^a\Big] \\
\mathbf{r}_{\Delta \mathbf{p}_{ij}} &\doteq R_i^T\big(\mathbf{p}_j - \mathbf{p}_i - \mathbf{v}_i\, \Delta t_{ij} - \tfrac{1}{2}\mathbf{g}\, \Delta t_{ij}^2\big) - \Big[\Delta \tilde{\mathbf{p}}_{ij}(\bar{\mathbf{b}}^g_i, \bar{\mathbf{b}}^a_i) + \frac{\partial \Delta \bar{\mathbf{p}}_{ij}}{\partial \mathbf{b}^g}\, \delta\mathbf{b}^g + \frac{\partial \Delta \bar{\mathbf{p}}_{ij}}{\partial \mathbf{b}^a}\, \delta\mathbf{b}^a\Big]
\end{aligned}
$$

Every quantity with a tilde or a bar is computed once from the IMU data. When the optimizer evaluates the factor, it only plugs in the current states $\mathbf{x}\_i$, $\mathbf{x}\_j$ and the bias change: **no re-integration, whatever the linearization point**. The paper also gives the analytic Jacobians of these residuals with respect to the states, which a Gauss-Newton or Levenberg-Marquardt solver needs.

### Bias model

Biases are slowly time-varying, so they are modeled as a **Brownian motion**, that is, integrated white noise:

$$
\dot{\mathbf{b}}^g(t) = \boldsymbol{\eta}^{bg}, \qquad \dot{\mathbf{b}}^a(t) = \boldsymbol{\eta}^{ba}
$$

Integrating over the interval $[t_i, t_j]$ between two consecutive keyframes gives

$$
\mathbf{b}^g_j = \mathbf{b}^g_i + \boldsymbol{\eta}^{bgd}, \qquad \mathbf{b}^a_j = \mathbf{b}^a_i + \boldsymbol{\eta}^{bad}
$$

where the discrete noises have zero mean and covariance $\Sigma^{bgd} \doteq \Delta t\_{ij} \operatorname{Cov}(\boldsymbol{\eta}^{bg})$ and $\Sigma^{bad} \doteq \Delta t\_{ij} \operatorname{Cov}(\boldsymbol{\eta}^{ba})$. Note that the variance grows **linearly with the time between keyframes**: the longer the gap, the more the bias is allowed to drift. This adds one more term per pair of consecutive keyframes to the MAP cost:

$$
\lVert \mathbf{r}_{\mathbf{b}_{ij}} \rVert^2 \doteq \lVert \mathbf{b}^g_j - \mathbf{b}^g_i \rVert^2_{\Sigma^{bgd}} + \lVert \mathbf{b}^a_j - \mathbf{b}^a_i \rVert^2_{\Sigma^{bad}}
$$

## Usage in GTSAM

GTSAM implements all of the above in `gtsam/navigation`. The pieces map one to one onto the sections of this post:

| Paper | GTSAM |
| --- | --- |
| IMU noise densities, gravity | `PreintegrationParams` / `PreintegrationCombinedParams` |
| $\Delta \tilde{R}\_{ij}$, $\Delta \tilde{\mathbf{v}}\_{ij}$, $\Delta \tilde{\mathbf{p}}\_{ij}$, $\Sigma\_{ij}$, bias Jacobians | `PreintegratedImuMeasurements` / `PreintegratedCombinedMeasurements` |
| State $\mathbf{x}\_i$ | `Pose3` + `Vector3` velocity (together a `NavState`) + `imuBias::ConstantBias` |
| IMU factor $\mathbf{r}\_{\mathcal{I}\_{ij}}$ | `ImuFactor` (5 keys) |
| IMU factor plus bias random walk $\mathbf{r}\_{\mathbf{b}\_{ij}}$ | `CombinedImuFactor` (6 keys) |

`ImuFactor` connects pose and velocity at $i$ and $j$ and the bias at $i$; the bias evolution is then added separately, typically with a `BetweenFactor<imuBias::ConstantBias>`. `CombinedImuFactor` connects the biases at both $i$ and $j$ and propagates the bias random walk inside the same covariance, which is the usual choice.

A minimal loop between two keyframes looks like this:

```cpp
#include <gtsam/inference/Symbol.h>
#include <gtsam/navigation/CombinedImuFactor.h>
#include <gtsam/nonlinear/NonlinearFactorGraph.h>

using gtsam::symbol_shorthand::B;  // bias
using gtsam::symbol_shorthand::V;  // velocity
using gtsam::symbol_shorthand::X;  // pose

// Z-up navigation frame: gravity points along -z.
auto params = gtsam::PreintegrationCombinedParams::MakeSharedU(9.81);
params->accelerometerCovariance = gtsam::I_3x3 * std::pow(accel_noise_density, 2);
params->gyroscopeCovariance     = gtsam::I_3x3 * std::pow(gyro_noise_density, 2);
params->biasAccCovariance       = gtsam::I_3x3 * std::pow(accel_bias_random_walk, 2);
params->biasOmegaCovariance     = gtsam::I_3x3 * std::pow(gyro_bias_random_walk, 2);
params->integrationCovariance   = gtsam::I_3x3 * 1e-8;
params->body_P_sensor = body_T_imu;  // optional, if the IMU is not the body frame

gtsam::imuBias::ConstantBias bias_i;  // current estimate, the linearization point b_bar
gtsam::PreintegratedCombinedMeasurements pim(params, bias_i);

// Between keyframe i and keyframe j, feed every IMU sample.
for (const auto& m : imu_samples_between_i_and_j) {
  pim.integrateMeasurement(m.acc, m.gyro, m.dt);
}

// Optional: predict state j from state i, e.g. as the initial guess.
gtsam::NavState state_j_guess = pim.predict(gtsam::NavState(pose_i, vel_i), bias_i);

gtsam::NonlinearFactorGraph graph;
graph.add(gtsam::CombinedImuFactor(X(i), V(i), X(j), V(j), B(i), B(j), pim));

// After optimizing, restart preintegration from the new bias estimate.
pim.resetIntegrationAndSetBias(optimized_bias_j);
```

A few practical notes:

- **Noise parameters** are the continuous-time densities from the IMU datasheet or an Allan-variance calibration (for example with Kalibr): accelerometer noise density in $\mathrm{m/s^2/\sqrt{Hz}}$, gyroscope noise density in $\mathrm{rad/s/\sqrt{Hz}}$, and the bias random walks. GTSAM divides by $\Delta t$ internally, as in the discrete-noise relation above. Datasheet values are usually inflated by a factor of a few in practice to absorb unmodeled effects.
- **Gravity direction.** `MakeSharedU` is for a z-up navigation frame (gravity along $-z$), `MakeSharedD` for z-down frames such as NED. Getting this wrong is the classic IMU-factor bug: a stationary IMU then looks like it is accelerating at $2g$.
- **Measurement order.** `integrateMeasurement` expects the specific force from the accelerometer and the angular rate from the gyroscope, in the IMU frame, exactly as the sensor reports them.
- **Bias linearization point.** The factor stores the Jacobians from the bias-update section and applies the first-order correction while the optimizer runs. Calling `resetIntegrationAndSetBias` with the latest estimate before integrating the next interval keeps $\delta\mathbf{b}$ small, so the linearization stays accurate.
- **Tangent versus manifold preintegration.** GTSAM builds with `GTSAM_TANGENT_PREINTEGRATION` on by default, which preintegrates in the tangent space of `NavState` rather than with the product of rotations used in the paper (`ManifoldPreintegration`). The factor interface is identical, and both are accurate for typical keyframe intervals.
- **Fixed-lag smoothing.** For real-time use, these factors are usually combined with vision factors in an `IncrementalFixedLagSmoother` or `ISAM2`, which only relinearizes the parts of the graph that changed.

## Reference

1. C. Forster, L. Carlone, F. Dellaert, D. Scaramuzza. *On-Manifold Preintegration for Real-Time Visual-Inertial Odometry*. IEEE Transactions on Robotics, 2017.
2. T. Lupton, S. Sukkarieh. *Visual-Inertial-Aided Navigation for High-Dynamic Motion in Built Environments Without Initial Conditions*. IEEE Transactions on Robotics, 2012.
3. J. Solà. *Quaternion kinematics for the error-state Kalman filter*. arXiv:1711.02508, 2017.
4. [GTSAM `ImuFactor` and `CombinedImuFactor`](https://github.com/borglab/gtsam/tree/develop/gtsam/navigation).
