---
title: Kalman Filter and Extended Kalman Filter
published: true
date: 2026-04-25
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

## The state estimation problem

A robot never observes its state directly. It knows a **process model** (how the state evolves given the control input) and a **measurement model** (what the sensors should read given the state), and both are corrupted by noise. The job of a state estimator is to infer the hidden state $x(k)$ from all the measurements up to now, $z(1{:}k)$.

The Kalman filter (KF) is the answer for one special case: the models are **linear** and all noise is **Gaussian**. The extended Kalman filter (EKF) stretches the same equations to nonlinear models by linearizing them. Both are special cases of the **Bayesian filter**, so that is where we start.

Notation (following the ETH Recursive Estimation lecture notes): $v$ is process noise, $w$ is sensor noise, subscript $p$ means "prior" (after prediction, before the measurement) and subscript $m$ means "posterior" (after the measurement).

## Probability density function

A state estimator does not output a single guess for the state but a **probability density function (PDF)** over all possible states. For a continuous random variable $x \in \mathbb{R}^n$, the PDF $p(x)$ says how likely each value is: the probability that $x$ lies in a region $\mathcal{A}$ is the integral of the density over that region,

$$
\Pr(x \in \mathcal{A}) = \int_{\mathcal{A}} p(x)\, dx, \qquad p(x) \geq 0, \qquad \int p(x)\, dx = 1.
$$

The density itself is not a probability (it can be larger than 1); only its integral over a region is. A narrow, tall PDF means we are certain about the state, a wide, flat one means we are not.

The notation $p(x \mid z)$ is a **conditional PDF**: the density of $x$ once we know the value of $z$. Measurements enter the estimator this way, by conditioning on them.

The PDF that matters most here is the **Gaussian** (normal) distribution $x \sim \mathcal{N}(\hat{x}, P)$, with mean $\hat{x}$ and covariance $P$:

$$
p(x) = \frac{1}{\sqrt{(2\pi)^n \det P}} \exp\left(-\frac{1}{2}(x - \hat{x})^T P^{-1} (x - \hat{x})\right)
$$

It is fully described by just these two quantities, and its negative log is a quadratic in $x$. Both facts come back below: the first is why the Kalman filter only has to track a mean and a covariance, the second is why its update is a least squares problem.

## Bayesian filter

### Goal and assumptions

We want the [PDF](#probability-density-function) of the current state given all measurements, $p(x(k) \mid z(1{:}k))$, and we want to compute it **recursively**: from the result of step $k-1$ plus the new measurement $z(k)$, without storing the whole history. Two assumptions make that possible:

1. **Markov property**: given $x(k-1)$, the state $x(k)$ does not depend on older states or measurements. This holds because $x(k)$ is built from $x(k-1)$ and the process noise $v(k-1)$, and that noise is independent of the past:

   $$
   p(x(k) \mid x(0{:}k-1), z(1{:}k-1)) = p(x(k) \mid x(k-1))
   $$

2. **Conditional independence of measurements**: given $x(k)$, the measurement $z(k)$ does not depend on anything else. This holds because $z(k)$ is built from $x(k)$ and the sensor noise $w(k)$, which is independent of everything else:

   $$
   p(z(k) \mid x(0{:}k), z(1{:}k-1)) = p(z(k) \mid x(k))
   $$

The known control input $u$ is left out of the conditioning to keep the notation short. The recursion starts from the initial PDF $p(x(0))$, which is the posterior at $k = 0$ since no measurement has arrived yet.

### Three probability rules

The whole derivation uses only these rules, for any random variables $a$, $b$, $c$:

- **Product rule**: a joint PDF splits into a conditional times a marginal,

  $$
  p(a, b \mid c) = p(a \mid b, c)\, p(b \mid c)
  $$

- **Marginalization** (law of total probability): a variable we do not care about can be integrated out of a joint PDF,

  $$
  p(a \mid c) = \int p(a, b = \lambda \mid c)\, d\lambda
  $$

- **Bayes' rule**: write the product rule in both orders, $p(a \mid b, c)\, p(b \mid c) = p(b \mid a, c)\, p(a \mid c)$, and divide by $p(b \mid c)$,

  $$
  p(a \mid b, c) = \frac{p(b \mid a, c)\, p(a \mid c)}{p(b \mid c)}
  $$

### Step 1: prior update (prediction)

We have the previous posterior $p(x(k-1) \mid z(1{:}k-1))$ and want the PDF of the new state $x(k)$ given the same measurements, before $z(k)$ arrives.

**(a) Marginalize over the previous state.** The process model links $x(k)$ to $x(k-1)$, so bring $x(k-1)$ in and integrate it out again:

$$
p(x(k) \mid z(1{:}k-1)) = \int p(x(k), x(k-1) = \lambda \mid z(1{:}k-1))\, d\lambda
$$

**(b) Apply the product rule** with $a = x(k)$, $b = x(k-1)$, $c = z(1{:}k-1)$:

$$
p(x(k) \mid z(1{:}k-1)) = \int p(x(k) \mid x(k-1) = \lambda, z(1{:}k-1))\; p(x(k-1) = \lambda \mid z(1{:}k-1))\, d\lambda
$$

**(c) Apply the Markov property.** Given $x(k-1)$, the old measurements carry no extra information about $x(k)$, so $z(1{:}k-1)$ drops out of the first factor:

$$
\underbrace{p(x(k) \mid z(1{:}k-1))}_{\text{prior}} = \int \underbrace{p(x(k) \mid x(k-1) = \lambda)}_{\text{process model}} \; \underbrace{p(x(k-1) = \lambda \mid z(1{:}k-1))}_{\text{previous posterior}} \, d\lambda
$$

Both factors are now known: the first comes from the process model, the second is the result of the previous step. Read it as: for every possible previous state $\lambda$, take how likely it was, push it through the process model, and add up all the contributions. Because of the process noise, the prior is wider than the previous posterior.

### Step 2: measurement update (correction)

Now the measurement $z(k)$ arrives, and we want the posterior $p(x(k) \mid z(1{:}k))$.

**(a) Split off the new measurement.** $z(1{:}k)$ is just $z(k)$ together with $z(1{:}k-1)$:

$$
p(x(k) \mid z(1{:}k)) = p(x(k) \mid z(k), z(1{:}k-1))
$$

**(b) Apply Bayes' rule** with $a = x(k)$, $b = z(k)$, $c = z(1{:}k-1)$:

$$
p(x(k) \mid z(1{:}k)) = \frac{p(z(k) \mid x(k), z(1{:}k-1))\; p(x(k) \mid z(1{:}k-1))}{p(z(k) \mid z(1{:}k-1))}
$$

**(c) Apply conditional independence.** Given $x(k)$, the old measurements say nothing more about $z(k)$, so $z(1{:}k-1)$ drops out of the first factor in the numerator:

$$
p(x(k) \mid z(1{:}k)) = \frac{p(z(k) \mid x(k))\; p(x(k) \mid z(1{:}k-1))}{p(z(k) \mid z(1{:}k-1))}
$$

**(d) Compute the denominator.** Marginalize over $x(k)$, apply the product rule, and drop $z(1{:}k-1)$ by conditional independence once more:

$$
p(z(k) \mid z(1{:}k-1)) = \int p(z(k), x(k) = \lambda \mid z(1{:}k-1))\, d\lambda = \int p(z(k) \mid x(k) = \lambda)\; p(x(k) = \lambda \mid z(1{:}k-1))\, d\lambda
$$

This does not depend on $x(k)$: it is only the constant that makes the posterior integrate to 1. Putting everything together:

$$
\underbrace{p(x(k) \mid z(1{:}k))}_{\text{posterior}} = \frac{\overbrace{p(z(k) \mid x(k))}^{\text{measurement model}} \; \overbrace{p(x(k) \mid z(1{:}k-1))}^{\text{prior (step 1)}}}{\underbrace{\int p(z(k) \mid x(k) = \lambda)\, p(x(k) = \lambda \mid z(1{:}k-1)) \, d\lambda}_{\text{normalization } = \; p(z(k) \mid z(1:k-1))}}
$$

The first factor in the numerator is the **likelihood**, which comes from the measurement model, and the second is the prior from step 1, which summarizes everything seen so far. In short, posterior $\propto$ likelihood $\times$ prior: states that explain the measurement well gain weight, the others lose it, so the posterior is narrower than the prior.

### The recursion

Each time step runs the two steps in turn:

$$
p(x(k-1) \mid z(1{:}k-1)) \;\xrightarrow{\text{process model}}\; p(x(k) \mid z(1{:}k-1)) \;\xrightarrow{\text{measurement } z(k)}\; p(x(k) \mid z(1{:}k))
$$

Only the latest posterior has to be stored, never the full history.

For general models these integrals have no closed form (particle filters approximate them by sampling). The Kalman filter is the case where they do.

## Kalman Filter

### Model

Consider the linear, time-varying system

$$
\begin{aligned}
x(k) &= A(k-1)\,x(k-1) + u(k-1) + v(k-1)
\\ z(k) &= H(k)\,x(k) + w(k)
\end{aligned}
\qquad k = 1, 2, \dots
$$

with state $x(k)$, known control input $u(k)$, measurement $z(k)$, and mutually independent Gaussian random variables

$$
x(0) \sim \mathcal{N}(x_0, P_0), \qquad v(k) \sim \mathcal{N}(0, Q(k)), \qquad w(k) \sim \mathcal{N}(0, R(k)).
$$

The key fact: a Gaussian stays Gaussian under a linear map, and the product of two Gaussians is again Gaussian (up to scale). So the prior and the posterior are both Gaussian at every step, and a Gaussian is fully described by its mean and covariance. The Bayesian filter therefore collapses into a recursion on two quantities:

$$
\hat{x}_p(k),\ P_p(k) \quad \text{(prior)}, \qquad \hat{x}_m(k),\ P_m(k) \quad \text{(posterior)}.
$$

### Kalman filter equations

**Initialization:** $\hat{x}_m(0) = x_0$, $P_m(0) = P_0$.

**Step 1: prior update / prediction**

$$
\begin{aligned}
\hat{x}_p(k) &= A(k-1)\,\hat{x}_m(k-1) + u(k-1)
\\ P_p(k) &= A(k-1)\,P_m(k-1)\,A^T(k-1) + Q(k-1)
\end{aligned}
$$

The mean is pushed through the model with the noise set to its mean, zero. The covariance is transformed by $A$ (since $\text{Var}[Ax] = A\,\text{Var}[x]\,A^T$) and then **grows** by $Q$: predicting without measuring always makes us less certain.

**Step 2: measurement update**

$$
\begin{aligned}
P_m(k) &= \left(P_p^{-1}(k) + H^T(k)\,R^{-1}(k)\,H(k)\right)^{-1}
\\ \hat{x}_m(k) &= \hat{x}_p(k) + P_m(k)\,H^T(k)\,R^{-1}(k)\,\big(z(k) - H(k)\,\hat{x}_p(k)\big)
\end{aligned}
$$

This is the **information form**: inverse covariances (information matrices) simply add. The prior contributes $P_p^{-1}$, the measurement contributes $H^T R^{-1} H$, so the posterior is always at least as certain as the prior. The term $z(k) - H(k)\hat{x}_p(k)$ is the **innovation**: the difference between what we measured and what we expected to measure.

### The Kalman gain form

The form found in most code avoids inverting the $n \times n$ matrix $P_p$ and instead inverts an $m \times m$ matrix, where $m$ is the measurement dimension (usually much smaller than the state dimension $n$):

$$
\begin{aligned}
S(k) &= H(k)\,P_p(k)\,H^T(k) + R(k)
\\ K(k) &= P_p(k)\,H^T(k)\,S^{-1}(k)
\\ \hat{x}_m(k) &= \hat{x}_p(k) + K(k)\,\big(z(k) - H(k)\,\hat{x}_p(k)\big)
\\ P_m(k) &= \big(I - K(k)\,H(k)\big)\,P_p(k)
\end{aligned}
$$

$S$ is the covariance of the innovation, and $K$ is the **Kalman gain**. The two forms are identical. Dropping the index $k$, the gain matches because

$$
P_m H^T R^{-1} = P_p H^T (H P_p H^T + R)^{-1}
\;\Longleftrightarrow\;
H^T R^{-1}(H P_p H^T + R) = (P_p^{-1} + H^T R^{-1} H)\, P_p H^T,
$$

and both sides of the right equation expand to $H^T R^{-1} H P_p H^T + H^T$. The covariance matches by the matrix inversion lemma: $(P_p^{-1} + H^T R^{-1} H)^{-1} = P_p - P_p H^T (H P_p H^T + R)^{-1} H P_p = (I - KH)P_p$.

The gain balances the two sources of information:

- $R \to 0$ (perfect sensor): with $H = I$, $K \to I$ and the estimate jumps to the measurement.
- $P_p \to 0$ (perfect prior) or $R \to \infty$ (useless sensor): $K \to 0$ and the measurement is ignored.

In practice $P_m = (I - KH)P_p$ can lose symmetry and positive definiteness through rounding. The **Joseph form** $P_m = (I - KH)P_p(I - KH)^T + K R K^T$ is algebraically the same but numerically safer.

### Toy example: 1D robot

A robot moves along a line with commanded displacement $u = 1$ per step, process noise $Q = 0.5$, and a position sensor with noise $R = 0.5$ ($A = H = 1$). Start at $\hat{x}_m(0) = 0$, $P_m(0) = 1$.

Prediction:

$$
\hat{x}_p(1) = 0 + 1 = 1, \qquad P_p(1) = 1 + 0.5 = 1.5
$$

The sensor reads $z(1) = 1.6$. Update:

$$
K = \frac{1.5}{1.5 + 0.5} = 0.75, \qquad \hat{x}_m(1) = 1 + 0.75 \cdot (1.6 - 1) = 1.45, \qquad P_m(1) = (1 - 0.75) \cdot 1.5 = 0.375
$$

The information form gives the same: $P_m = (1/1.5 + 1/0.5)^{-1} = (0.667 + 2)^{-1} = 0.375$. The prior was three times more uncertain than the sensor, so the estimate moved 75% of the way towards the measurement, and the posterior variance is smaller than both $P_p = 1.5$ and $R = 0.5$.

### The measurement update is a least squares problem

Since the posterior is proportional to likelihood times prior, and both are Gaussian, maximizing it (MAP estimation) is the same as minimizing the negative log:

$$
\hat{x}_m = \arg\min_x \; \underbrace{(x - \hat{x}_p)^T P_p^{-1} (x - \hat{x}_p)}_{\text{prior residual}} + \underbrace{(z - Hx)^T R^{-1} (z - Hx)}_{\text{measurement residual}}
$$

Setting the gradient to zero:

$$
\big(P_p^{-1} + H^T R^{-1} H\big)\, x = P_p^{-1}\hat{x}_p + H^T R^{-1} z
$$

The matrix on the left is exactly $P_m^{-1}$, and rearranging gives exactly the information-form update. The Hessian of this cost is the posterior information matrix. This is the bridge between filtering and the optimization methods in [Nonlinear Least Squares for Robotics](/2025/11/03/hessian-gaussian-newton/): a Kalman update is one weighted least squares solve over the **current state only**, while graph optimization solves the same kind of problem over **many states at once**.

For a linear Gaussian system, the Kalman filter is not an approximation: it is the exact Bayesian posterior, and therefore the optimal estimator in the minimum mean squared error sense.

## Extended Kalman Filter

### Nonlinear model

Real robots are nonlinear: orientation enters through rotations, cameras project through a division by depth, a range sensor measures a norm. The general model is

$$
\begin{aligned}
x(k) &= q_{k-1}\big(x(k-1), u(k-1), v(k-1)\big)
\\ z(k) &= h_k\big(x(k), w(k)\big)
\end{aligned}
$$

The problem: **a Gaussian pushed through a nonlinear function is generally no longer Gaussian**, so the mean-and-covariance recursion is no longer exact. The EKF forces it anyway: it linearizes $q$ and $h$ with a first-order Taylor expansion around the current best estimate and applies the KF equations to the linearized system.

### EKF equations

Linearize the process model around the last posterior mean (noise at zero):

$$
A(k-1) = \frac{\partial q_{k-1}}{\partial x}\bigg|_{\hat{x}_m(k-1),\, u(k-1),\, 0}, \qquad L(k-1) = \frac{\partial q_{k-1}}{\partial v}\bigg|_{\hat{x}_m(k-1),\, u(k-1),\, 0}
$$

**Prediction**

$$
\begin{aligned}
\hat{x}_p(k) &= q_{k-1}\big(\hat{x}_m(k-1), u(k-1), 0\big)
\\ P_p(k) &= A(k-1)\,P_m(k-1)\,A^T(k-1) + L(k-1)\,Q(k-1)\,L^T(k-1)
\end{aligned}
$$

Linearize the measurement model around the prior mean:

$$
H(k) = \frac{\partial h_k}{\partial x}\bigg|_{\hat{x}_p(k),\, 0}, \qquad M(k) = \frac{\partial h_k}{\partial w}\bigg|_{\hat{x}_p(k),\, 0}
$$

**Measurement update**

$$
\begin{aligned}
K(k) &= P_p(k)\,H^T(k)\,\big(H(k)\,P_p(k)\,H^T(k) + M(k)\,R(k)\,M^T(k)\big)^{-1}
\\ \hat{x}_m(k) &= \hat{x}_p(k) + K(k)\,\big(z(k) - h_k(\hat{x}_p(k), 0)\big)
\\ P_m(k) &= \big(I - K(k)\,H(k)\big)\,P_p(k)
\end{aligned}
$$

Note what is linearized and what is not: the **means** are propagated through the true nonlinear functions $q$ and $h$, only the **covariances** use the Jacobians.

### Toy example: range to a beacon

A robot at 2D position $p$ measures its distance to a beacon at the origin, $z = \lVert p \rVert + w$. With the prior mean $\hat{p}_p = (3, 4)$:

$$
h(\hat{p}_p) = 5, \qquad H = \frac{\partial \lVert p \rVert}{\partial p^T}\bigg|_{\hat{p}_p} = \frac{\hat{p}_p^T}{\lVert \hat{p}_p \rVert} = \begin{bmatrix} 0.6 & 0.8 \end{bmatrix}
$$

$H$ is the unit vector pointing from the beacon to the robot. A single range only corrects the estimate **along the line of sight**: the uncertainty perpendicular to it (moving on the circle of radius 5) is untouched. The Jacobian makes this kind of observability question explicit.

### Limitations of the EKF

1. **Linearization error.** The measurement model is linearized at the prior $\hat{x}_p$, because the posterior is not yet known. If the measurement pulls the estimate far from the prior, the linearization is evaluated at the wrong point and the update is inconsistent. An optimizer has the same first-order approximation but **re-linearizes** at every iteration. The **iterated EKF** does the same thing: it repeats the update, re-linearizing $h$ at the latest estimate, which is exactly Gauss-Newton on the MAP cost above.
2. **Markov assumption.** The filter keeps only the current state, and past states are marginalized out with their linearization frozen. If a new measurement relates to an old state (a loop closure), the filter has nothing to attach it to.
3. **Quadratic cost in the state size.** The filter stores and updates a dense covariance matrix. EKF-SLAM with landmarks in the state grows as $O(n^2)$ in memory and per-update time, which is why it is considered unsuitable for large scenes.
4. **Overconfidence.** Linearizing at changing estimates can give the filter spurious information about unobservable directions (for example global yaw in visual-inertial odometry), making the covariance too small. Observability-constrained and invariant EKFs exist to fix this.

Even so, when compute is limited or the state is small, the EKF is still a very effective choice, and it remains the backbone of many production estimators.

### Error-state EKF

Orientation lives on the rotation **manifold**, not in a vector space. A manifold is a space that looks flat when you zoom in, but is curved globally. The surface of the Earth is the classic example: around you it looks like a plane and a local map with $x$ and $y$ coordinates works fine, but globally it is a sphere, and no single flat map covers it without distortion.

Rotations form such a space. A rotation matrix $R$ has 9 entries, but they must satisfy $R^T R = I$ and $\det R = 1$, which leaves only 3 degrees of freedom. The valid rotations form a curved 3D surface inside the 9D space of matrices, called $SO(3)$. Unit quaternions are the same story: 4 numbers with unit norm, a 3D sphere inside 4D space.

The Kalman filter, however, assumes a vector space: its update $\hat{x}\_m = \hat{x}\_p + K(\dots)$ adds a correction, and its covariance is an $n \times n$ matrix over that space. Applied directly to orientation, this goes wrong in two ways:

- **Adding leaves the manifold.** The sum of two rotation matrices is not a rotation matrix, and a unit quaternion plus a correction no longer has unit norm. It is like stepping off the Earth's surface into the air.
- **The parametrization has the wrong size.** A quaternion has 4 numbers for 3 degrees of freedom, so its 4D covariance has zero uncertainty in one direction and is singular. Three Euler angles have the right size but suffer from gimbal lock, where the parametrization breaks down at some orientations.

The fix uses the "locally flat" property. Near the current estimate $\hat{R}$, a small rotation is described by an ordinary 3D vector $\delta\theta$ (roughly rotation axis times angle) in the flat **tangent space**, the local map. The filter does its linear algebra there, with a proper $3 \times 3$ covariance, and the result is mapped back onto the manifold with the exponential map, by multiplication rather than addition. Composing two rotations always gives a valid rotation, so the estimate never leaves the manifold.

This is the **error-state** (or indirect) Kalman filter: keep the nominal state (with a real quaternion or rotation matrix) and run the filter on a small error state $\delta x$, with the rotation error as the minimal 3D vector $\delta\theta$:

$$
R = \hat{R}\,\text{Exp}(\delta\theta), \qquad p = \hat{p} + \delta p, \quad \dots
$$

After each update, the estimated error is injected into the nominal state and reset to zero. The error stays small, so the linearization is accurate, and its covariance has the right dimension. This is the formulation used by most IMU-based filters, including OpenVINS. Solà's *Quaternion kinematics for the error-state Kalman filter* derives it in full.

## How is it used in robotics state estimation

In robot state estimation, the **IMU usually drives the prediction step**. Accelerometer and gyroscope readings are treated as the input $u$ of the process model, not as measurements. Integrating them propagates orientation, velocity and position at the IMU rate (hundreds of Hz), with the IMU biases also kept in the state:

$$
x = \begin{bmatrix} R_{WB} & {}_W p & {}_W v & b_g & b_a \end{bmatrix}
$$

Exteroceptive sensors (camera, LiDAR, GNSS, leg kinematics) arrive at lower rates and provide the **measurement updates** that bound the drift of pure integration. The main design choice is **what** the estimator receives from those sensors. Take a camera as the example:

- **Loosely coupled:** a separate visual odometry module first turns the images into a pose. The EKF predicts with the IMU and uses that finished pose as its measurement. The camera's raw data never reaches the filter.
- **Tightly coupled:** the estimator works with the raw measurements directly, such as the pixel positions of tracked features. Camera and IMU data are combined in one estimation problem, solved either by an EKF or by graph optimization.

In short, loose coupling fuses the **results** of each sensor, tight coupling fuses the **measurements** themselves. The VINS-Mono paper draws the same distinction. The two sections below compare them.

### Loosely coupled approach

In a loosely coupled system, the exteroceptive measurements are **not** used in the same estimation step. Each sensor pipeline first runs on its own (visual odometry produces a pose, LiDAR odometry produces a pose) and the fusion filter only sees those results as measurements.

A typical loosely coupled EKF:

- **Prediction:** integrating the IMU readings propagates the state estimate and its covariance.
- **Update:** the pose from visual or LiDAR odometry is used directly as the measurement, together with the uncertainty that the odometry module reports for it.

#### What the update does, conceptually

The update is a negotiation between the IMU prediction and the odometry pose, where each side is weighted by how much it is trusted.

1. **A drifting guess.** Since the last update, the filter has only integrated the IMU. Small errors in acceleration and rotation rate accumulate into position and orientation drift, so the covariance $P_p$ keeps growing.
2. **A second opinion.** The odometry module reports a pose together with its uncertainty $R$. It is an independent estimate, free of the IMU's drift.
3. **Compare.** The innovation is the difference between the odometry pose and the predicted pose: how surprised the filter is.
4. **Decide whom to trust.** The Kalman gain $K$ weighs $P_p$ against $R$. After a long stretch without updates the prediction is very uncertain, and the estimate moves most of the way to the odometry pose. If the odometry is noisy, the estimate barely moves. This is the [1D toy example](#toy-example-1d-robot) in 6D.
5. **Correct more than the pose.** The odometry only measures orientation and position, yet velocity and the IMU biases are corrected too. $P_p$ records how the states are correlated: if the predicted position keeps running ahead of the odometry, a too-high velocity or a wrong accelerometer bias is the likely cause. The gain passes part of the correction to those states, which is how the filter learns the biases and why later predictions drift less.
6. **Shrink the uncertainty.** Two sources of information combined give a covariance $P_m$ smaller than $P_p$. Then the IMU takes over again and the uncertainty grows until the next odometry pose.

Over time the estimate follows a sawtooth: smooth, high-rate IMU motion with growing uncertainty, then a snap towards the odometry pose and a drop in uncertainty at every update. The IMU provides smoothness and rate, the odometry bounds the long-term drift, and the gain decides at every step how much each counts. The whole negotiation relies on $R$ being honest: if the odometry claims to be more accurate than it is, the filter keeps getting pulled towards bad poses, and nothing in the update can detect it.

The idea is to reduce the dependency between sensor modalities and the computational complexity of the system. Loosely coupled systems are usually more **robust**: one odometry sub-system can benefit from another, and if one fails the system still produces output from the rest. They are also modular: swapping the visual odometry does not touch the filter.

The price is **accuracy**. Each sub-system compresses its raw data into a single pose with a covariance that is often a rough guess, and correlations between the pose and the filter state are lost. The fusion cannot go back and use the raw data. The IMU also cannot help the sub-system, for example to predict feature locations or to reject bad matches.

If a loosely coupled approach is selected, **sensor dominance** is key. You need to decide which sensor is dominant on the robot. The robust odometry architecture then aids the odometry of the dominant sensor, and the other odometry sources are only used when the dominant one fails.

### Tightly coupled approach

In a tightly coupled system, the raw (or lightly processed) measurements of all sensors are used in **one** filtering or optimization step: feature pixel coordinates instead of a visual odometry pose, point-to-plane distances instead of a LiDAR odometry pose. Since all information is combined in one step, it is usually more **accurate**, but needs more computation. And when one sensor delivers bad data, the damage can be worse than in a loosely coupled system, because it directly corrupts the joint estimate. Outlier rejection, for example a chi-square test on the innovation $(z - h(\hat{x}_p))^T S^{-1} (z - h(\hat{x}_p))$, becomes essential.

Tightly coupled methods come in two flavours:

- **Filter-based.** The prominent example is the **MSCKF** (Multi-State Constraint Kalman Filter), used in OpenVINS. Its state holds the current IMU state plus a sliding window of cloned past poses. Features are not put in the state, which avoids the quadratic growth of EKF-SLAM. A feature tracked over several frames is triangulated, and its reprojection residuals are projected onto the null space of the feature Jacobian. This yields a constraint that depends only on the poses in the window, which is then used as an EKF update.
- **Optimization-based.** VINS-Mono, OKVIS and LIO-SAM jointly optimize a sliding window of states over IMU factors and visual or LiDAR factors, using a factor graph (for example GTSAM or Ceres). Old states are marginalized out to keep the window bounded. To avoid re-integrating the IMU at every iteration when the state estimate changes, these systems use [IMU preintegration](/2023/10/30/imu-preintegration/). Because they re-linearize at every iteration, they avoid the EKF's main weakness, which is why optimization dominates modern visual SLAM when compute allows.

| | Loosely coupled | Tightly coupled |
| --- | --- | --- |
| Measurements fused | Sub-system outputs (poses) | Raw measurements (features, points) |
| Accuracy | Lower | Higher |
| Robustness to a failing sensor | Higher, sub-systems are isolated | Lower, needs careful outlier rejection |
| Computation | Lower | Higher |
| Examples | EKF fusing IMU with VO or LiDAR poses | MSCKF / OpenVINS, VINS-Mono, LIO-SAM |

Real systems often mix the two. **Super Odometry**, for example, is IMU-centric: an IMU odometry module is constrained by separate visual-inertial and LiDAR-inertial odometry estimates, which keep the IMU biases in check, while those modules in turn use the IMU prediction. Its key insight: **an IMU and its state estimation can be very accurate as long as the bias drift is well constrained by other sensors.** This keeps the robustness of loose coupling, since any one exteroceptive sensor can fail, while still exploiting the IMU tightly.

## References

1. [OpenVins](https://docs.openvins.com/)
2. [Super Odometry: A Robust LiDAR-Visual-Inertial Estimator for Challenging Environments](https://publications.ri.cmu.edu/storage/publications/2024/07/CMU_MSR_thesis_shibo.pdf)
3. [Recursive Estimation, Lecture Notes, ETH Zurich](https://idsc.ethz.ch/education/lectures/recursive-estimation.html)
4. [VINS-Mono: A Robust and Versatile Monocular Visual-Inertial State Estimator](https://arxiv.org/abs/1708.03852)
5. [Quaternion kinematics for the error-state Kalman filter, Joan Solà](https://arxiv.org/abs/1711.02508)
6. [A Multi-State Constraint Kalman Filter for Vision-aided Inertial Navigation](https://www-users.cse.umn.edu/~stergios/papers/ICRA07-MSCKF.pdf)
7. 视觉SLAM十四讲 (14 Lectures on Visual SLAM), Gao Xiang, Lecture 10: Backend
