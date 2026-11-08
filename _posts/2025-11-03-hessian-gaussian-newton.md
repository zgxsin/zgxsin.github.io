---
title: "Nonlinear Least Squares for Robotics: Gauss-Newton, Levenberg-Marquardt and ICP"
published: true
date: 2025-11-03
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

## Hessian Matrix

Notation: all vectors are column vectors, $\vec{x} = [x_1, \dots, x_n]^T \in \mathbb{R}^n$. A row vector is always written as a transpose.

### Derivative with respect to a vector: the gradient

For a scalar function of one variable, $f^{\prime}(x)$ tells us how much $f$ changes when $x$ moves a little: $f(x + \delta) \approx f(x) + f^{\prime}(x)\,\delta$.

For a scalar function of a vector, $f: \mathbb{R}^n \rightarrow \mathbb{R}$, $\vec{x}$ can move in $n$ independent directions. So "the derivative w.r.t. $\vec{x}$" is just all $n$ partial derivatives, stacked into a vector. This is the **gradient**:

$$
\nabla f(\vec{x}) = \frac{\partial f}{\partial \vec{x}} = \begin{bmatrix} \frac{\partial f}{\partial x_1} \\ \vdots \\ \frac{\partial f}{\partial x_n} \end{bmatrix} \in \mathbb{R}^n
$$

It plays exactly the same role as $f^{\prime}(x)$:

$$
f(\vec{x} + \vec{\delta}) \approx f(\vec{x}) + \nabla f(\vec{x})^T \vec{\delta}
$$

The dot product $\nabla f^T \vec{\delta}$ adds up the change caused by each coordinate of the step. It is largest when $\vec{\delta}$ points along $\nabla f$, which is why the gradient is the direction of steepest ascent.

> Layout convention: some books write $\frac{\partial f}{\partial \vec{x}}$ as a row vector (numerator layout). Here it is a column vector (denominator layout), so that it has the same shape as $\vec{x}$. The math is the same, only transposes move around.

### The Jacobian: derivative of a vector-valued function

The gradient handles functions with a single output. For a vector function $\vec{r}: \mathbb{R}^n \rightarrow \mathbb{R}^m$, every output has its own gradient. Stacking the transposed gradients as rows gives the **Jacobian**, the $m \times n$ matrix of all first partial derivatives, $$J_{ij} = \frac{\partial r_i}{\partial x_j}$$:

$$
J = \frac{\partial \vec{r}}{\partial \vec{x}^T} = \begin{bmatrix} \nabla r_1^T \\ \vdots \\ \nabla r_m^T \end{bmatrix} = \begin{bmatrix} \frac{\partial r_1}{\partial x_1} & \cdots & \frac{\partial r_1}{\partial x_n} \\ \vdots & \ddots & \vdots \\ \frac{\partial r_m}{\partial x_1} & \cdots & \frac{\partial r_m}{\partial x_n} \end{bmatrix}, \qquad \vec{r}(\vec{x} + \vec{\delta}) \approx \vec{r}(\vec{x}) + J\vec{\delta}
$$

The Jacobian is the best linear approximation of $\vec{r}$ near $\vec{x}$: for small steps, the nonlinear function behaves like multiplication by the matrix $J$. Row $i$ says how output $r_i$ reacts to the step, column $j$ says how all outputs react to moving $x_j$. The transpose in $\frac{\partial \vec{r}}{\partial \vec{x}^T}$ records exactly that shape: the outputs run down the rows like the column $\vec{r}$, the inputs run along the columns like the row $\vec{x}^T$.

The gradient is the special case $m = 1$, where the Jacobian is the single row $\nabla f^T$. The Hessian, introduced below, is the Jacobian of the gradient. And Gauss-Newton is built entirely on Jacobians: it never needs second derivatives.

**Toy example: polar to Cartesian.** $\vec{r}(\rho, \theta) = (\rho\cos\theta,\ \rho\sin\theta)$ has

$$
J = \begin{bmatrix} \frac{\partial x}{\partial \rho} & \frac{\partial x}{\partial \theta} \\ \frac{\partial y}{\partial \rho} & \frac{\partial y}{\partial \theta} \end{bmatrix} = \begin{bmatrix} \cos\theta & -\rho\sin\theta \\ \sin\theta & \rho\cos\theta \end{bmatrix}
$$

The first column is the outward unit vector: increasing $\rho$ moves the point radially. The second column is tangent to the circle with length $\rho$: increasing $\theta$ moves the point sideways, faster the farther it is from the origin. The determinant, $\det J = \rho$, is how much a small area grows under the map, which is where the $\rho$ in $dx\,dy = \rho\,d\rho\,d\theta$ comes from.

### Toy example: gradient by hand

Take $f(x_1, x_2) = x_1^3 + x_1 x_2^2$. Differentiate w.r.t. each coordinate, treating the other one as a constant:

$$
\nabla f = \begin{bmatrix} 3x_1^2 + x_2^2 \\ 2x_1 x_2 \end{bmatrix}, \qquad \nabla f(1, 2) = \begin{bmatrix} 7 \\ 4 \end{bmatrix}
$$

Sanity check with a small step $\vec{\delta} = [0.01, 0]^T$: $f(1.01, 2) = 1.030301 + 4.04 = 5.070301$, and the linear prediction is $f(1,2) + 7 \cdot 0.01 = 5 + 0.07 = 5.07$. Close.

### Gradient rules: linear, quadratic and chain rule

Most derivatives in least squares are built from these. Each one can be checked by writing the sums out.

**1. Linear: $f = \vec{a}^T\vec{x}$.** $f = \sum_i a_i x_i$, so $\frac{\partial f}{\partial x_k} = a_k$:

$$
\nabla(\vec{a}^T\vec{x}) = \vec{a}
$$

This is the vector version of $\frac{d}{dx}(ax) = a$.

**2. Quadratic form: $f = \vec{x}^T A \vec{x}$.** $$f = \sum_i \sum_j x_i A_{ij} x_j$$. The variable $x_k$ shows up once as $x_i$ (when $i = k$) and once as $x_j$ (when $j = k$):

$$
\frac{\partial f}{\partial x_k} = \sum_j A_{kj} x_j + \sum_i x_i A_{ik} = (A\vec{x})_k + (A^T\vec{x})_k
\quad\Rightarrow\quad
\nabla(\vec{x}^TA\vec{x}) = (A + A^T)\vec{x}
$$

If $A$ is symmetric this is $2A\vec{x}$, the vector version of $\frac{d}{dx}(ax^2) = 2ax$.

Toy check with $$A = \begin{bmatrix} 1 & 2 \\ 0 & 3 \end{bmatrix}$$: $\vec{x}^TA\vec{x} = x_1^2 + 2x_1x_2 + 3x_2^2$. By hand the gradient is $[2x_1 + 2x_2,\ 2x_1 + 6x_2]^T$, and indeed $$A + A^T = \begin{bmatrix} 2 & 2 \\ 2 & 6 \end{bmatrix}$$.

**3. Chain rule: $f = g(\vec{r}(\vec{x}))$.** A step $\vec{\delta}$ changes $\vec{r}$ by $J\vec{\delta}$, which changes $g$ by $\nabla g^T (J\vec{\delta}) = (J^T \nabla g)^T \vec{\delta}$. So

$$
\nabla f = J^T \nabla g
$$

The most important case is the squared norm $$f = \|\vec{r}(\vec{x})\|^2 = \vec{r}^T\vec{r}$$, where $\nabla g = 2\vec{r}$:

$$
\nabla \|\vec{r}(\vec{x})\|^2 = 2J^T\vec{r}
$$

For linear least squares, $\vec{r} = A\vec{x} - \vec{b}$ and $J = A$, so $$\nabla\|A\vec{x} - \vec{b}\|^2 = 2A^T(A\vec{x} - \vec{b})$$. Setting it to zero gives the normal equations $A^TA\vec{x} = A^T\vec{b}$.

### Aside: the normal equations

When $A$ is tall (more equations than unknowns), $A\vec{x} = \vec{b}$ usually has no exact solution, so we settle for the $\vec{x}$ that minimizes $$\|A\vec{x} - \vec{b}\|^2$$. The normal equations $A^TA\vec{x} = A^T\vec{b}$ turn that into a square $n \times n$ system, with a unique solution when $A$ has full column rank.

The name is geometric. Rewrite them as

$$
A^T(\vec{b} - A\vec{x}) = \vec{0}
$$

The leftover error $\vec{b} - A\vec{x}$ is **normal** (perpendicular) to every column of $A$. So $A\vec{x}$ is the orthogonal projection of $\vec{b}$ onto the column space of $A$, the closest point that $A$ can reach.

**Toy example: fit a line $y = a + bt$ through $(0, 1), (1, 2), (2, 2)$.**

$$
A = \begin{bmatrix} 1 & 0 \\ 1 & 1 \\ 1 & 2 \end{bmatrix},\quad
\vec{b} = \begin{bmatrix} 1 \\ 2 \\ 2 \end{bmatrix},\quad
A^TA = \begin{bmatrix} 3 & 3 \\ 3 & 5 \end{bmatrix},\quad
A^T\vec{b} = \begin{bmatrix} 5 \\ 6 \end{bmatrix}
$$

Solving the $2 \times 2$ system gives $a = 7/6$, $b = 1/2$. The leftover error is $\vec{b} - A\vec{x} = (-1/6,\ 1/3,\ -1/6)$. Its dot product with both columns, $(1, 1, 1)$ and $(0, 1, 2)$, is zero, as promised.

Here is the same example drawn to scale in 3D. Every $A\vec{x}$ is a mix of the two columns, so all of them together form a plane through the origin, and each point on the plane is the set of predictions of some line. The data $\vec{b}$ sits slightly above the plane, because no line passes through all three points. Dropping straight down from $\vec{b}$ lands on $A\vec{\hat{x}}$. Move the slider to try other points on the plane: the dashed line to $\vec{b}$ is the slanted side of a right triangle, so it is always longer than the perpendicular drop of $0.41$.

{% include figures/projection-column-space.html %}

This is why least squares and orthogonal projection give the same answer, in any dimension. "Perpendicular to the plane" means perpendicular to every column that spans it, and that is exactly what $A^T(\vec{b} - A\vec{\hat{x}}) = \vec{0}$ says, one column per row of $A^T$.

Gauss-Newton (below) solves exactly this kind of system in every iteration, with the Jacobian $J$ in place of $A$ and $-\vec{r}$ in place of $\vec{b}$.

### The Hessian: the second derivative

The gradient is itself a function $\mathbb{R}^n \rightarrow \mathbb{R}^n$. Its Jacobian is the **Hessian**, the $n \times n$ matrix of all second partial derivatives:

$$
H(\vec{x}) = \nabla^2 f(\vec{x}) = \frac{\partial}{\partial \vec{x}^T}\left(\frac{\partial f}{\partial \vec{x}}\right) = \frac{\partial^2 f}{\partial \vec{x}\,\partial \vec{x}^T} = \begin{bmatrix}
\frac{\partial^2 f}{\partial x_1^2} & \frac{\partial^2 f}{\partial x_1 \partial x_2} & \cdots & \frac{\partial^2 f}{\partial x_1 \partial x_n}
\\ \frac{\partial^2 f}{\partial x_2 \partial x_1} & \frac{\partial^2 f}{\partial x_2^2} & \cdots & \frac{\partial^2 f}{\partial x_2 \partial x_n}
\\ \vdots & \vdots & \ddots & \vdots
\\ \frac{\partial^2 f}{\partial x_n \partial x_1} & \frac{\partial^2 f}{\partial x_n \partial x_2} & \cdots & \frac{\partial^2 f}{\partial x_n^2}
\end{bmatrix}, \qquad H_{ij} = \frac{\partial^2 f}{\partial x_i \partial x_j}
$$

- The diagonal $$H_{ii}$$ is the ordinary curvature along axis $x_i$.
- The off-diagonal $$H_{ij}$$ says how the slope in $x_i$ changes when you move in $x_j$ (the "twist" of the surface).
- If the second derivatives are continuous, the order of differentiation does not matter (Schwarz's theorem), so **$H$ is symmetric**.

Just like $f^{\prime}(x)$ gave the linear approximation, the Hessian gives the quadratic one, the vector version of $f(x + \delta) \approx f + f^{\prime}\delta + \frac{1}{2}f^{\prime\prime}\delta^2$:

$$
f(\vec{x} + \vec{\delta}) \approx f(\vec{x}) + \nabla f(\vec{x})^T\vec{\delta} + \frac{1}{2}\vec{\delta}^T H(\vec{x})\,\vec{\delta}
$$

### Toy example: Hessian by hand

Continue with $f(x_1, x_2) = x_1^3 + x_1x_2^2$ and $\nabla f = [3x_1^2 + x_2^2,\ 2x_1x_2]^T$. Differentiate each gradient entry again w.r.t. $x_1$ and $x_2$:

$$
H = \begin{bmatrix} \frac{\partial}{\partial x_1}(3x_1^2 + x_2^2) & \frac{\partial}{\partial x_2}(3x_1^2 + x_2^2) \\ \frac{\partial}{\partial x_1}(2x_1x_2) & \frac{\partial}{\partial x_2}(2x_1x_2) \end{bmatrix} = \begin{bmatrix} 6x_1 & 2x_2 \\ 2x_2 & 2x_1 \end{bmatrix}, \qquad H(1, 2) = \begin{bmatrix} 6 & 4 \\ 4 & 2 \end{bmatrix}
$$

Note that it is symmetric, and that for a non-quadratic function it **depends on the point**.

For the quadratic form, differentiating $\nabla(\vec{x}^TA\vec{x}) = (A + A^T)\vec{x}$ once more gives a constant Hessian $H = A + A^T$ ($= 2A$ for symmetric $A$). A quadratic has the same curvature everywhere, so its second-order Taylor expansion is exact.

### What the Hessian tells you: curvature

To measure curvature in a direction, reduce $f$ to one variable. Fix a point $\vec{x}$ and a unit direction $\vec{v}$, walk along the line $\vec{x} + t\vec{v}$, and look at the 1D slice $g(t) = f(\vec{x} + t\vec{v})$. Its ordinary second derivative $g^{\prime\prime}(0)$ says how $f$ bends along that line: positive curves up, negative curves down, zero is flat. Applying the chain rule twice gives it directly from the Hessian:

$$
g^{\prime\prime}(0) = \frac{d^2}{dt^2} f(\vec{x} + t\vec{v}) \Big|_{t=0} = \vec{v}^T H \vec{v}
$$

The direction $\vec{v}$ must have unit length so that $t$ is real distance. Doubling $\vec{v}$ would make you walk twice as fast and multiply the result by 4, so directions would not be comparable. For the bowl below ($$H = \begin{bmatrix}2 & 1 \\ 1 & 2\end{bmatrix}$$), the curvature is $2$ along $x_1$, $3$ along the diagonal $(1,1)/\sqrt{2}$, and $1$ along the anti-diagonal $(1,-1)/\sqrt{2}$.

Since $H$ is symmetric, it has an orthonormal eigenbasis, $H = Q\Lambda Q^T$. Along eigenvector $\vec{q}_i$ the curvature is exactly $\lambda_i$, and the largest and smallest eigenvalues are the strongest and weakest curvatures over all directions. At a critical point ($\nabla f = 0$), this classifies the point:

| Eigenvalues of $H$ | Shape | Critical point |
| --- | --- | --- |
| all $> 0$ (positive definite) | bowl | local minimum |
| all $< 0$ (negative definite) | dome | local maximum |
| mixed signs (indefinite) | saddle | neither |
| some $= 0$ (singular) | flat in some direction | test is inconclusive |

**Toy example: a bowl.** $f = x_1^2 + x_1x_2 + x_2^2$ has $\nabla f = [2x_1 + x_2,\ x_1 + 2x_2]^T$, zero only at the origin, and $$H = \begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}$$ with eigenvalues $3$ (along $[1, 1]^T/\sqrt{2}$) and $1$ (along $[1, -1]^T/\sqrt{2}$). Both positive, so the origin is a minimum. The level sets are ellipses, steepest along the diagonal and flattest along the anti-diagonal.

**Toy example: a saddle.** $f = x_1^2 + 3x_1x_2 + 2x_2^2$ has $$H = \begin{bmatrix} 2 & 3 \\ 3 & 4 \end{bmatrix}$$. Both diagonal entries are positive, so along each axis $f$ curves up, yet $\det H = 8 - 9 = -1 < 0$, so the eigenvalues ($3 \pm \sqrt{10} \approx 6.16, -0.16$) have opposite signs. Along $\vec{v} = [3, -2]^T$: $f(3t, -2t) = 9t^2 - 18t^2 + 8t^2 = -t^2$, which goes down. The origin is a saddle. The strong coupling term $3x_1x_2$ is what creates the downhill direction, and only the off-diagonal entries of the Hessian can show that.

The figure below shows both examples, plus a flat valley $f = \frac{1}{2}(x_1 + x_2)^2$ with eigenvalues $2$ and $0$. On the left, the level sets of $f$ are seen from above, with the two eigenvector directions dashed. On the right is the slice $f(t\vec{v}) = \frac{1}{2}(\vec{v}^TH\vec{v})\,t^2$ through the origin: a parabola whose curvature is $\vec{v}^TH\vec{v}$. Rotate $\vec{v}$ and watch the parabola: it is steepest along one eigenvector ($$\lambda_{\max}$$), flattest along the other ($$\lambda_{\min}$$), and never leaves the band between them. For the saddle, the band crosses zero, so some directions curve down. For the valley, one direction has zero curvature: the level sets are parallel lines, and moving along them does not change $f$ at all.

{% include figures/hessian-curvature.html %}

### Why we care: Newton's method

Minimize the quadratic approximation over $\vec{\delta}$ by setting its gradient (the linear and quadratic rules) to zero:

$$
\nabla f + H\vec{\delta} = 0 \quad\Rightarrow\quad H\vec{\delta} = -\nabla f
$$

This is **Newton's method**: jump to the bottom of the local bowl, then repeat. Gradient descent only knows the slope and must guess a step size. Newton also knows the curvature, so it takes big steps in flat directions and small steps in steep ones. For a quadratic $f = \frac{1}{2}\vec{x}^TA\vec{x} - \vec{b}^T\vec{x}$ with symmetric positive definite $A$, we have $\nabla f = A\vec{x} - \vec{b}$ and $H = A$, so a single Newton step from any $\vec{x}$ lands at $\vec{x} - A^{-1}(A\vec{x} - \vec{b}) = A^{-1}\vec{b}$, the exact minimum.

The catch: computing all $n^2$ second derivatives is expensive, and away from a minimum $H$ may not be positive definite, so $\vec{\delta}$ can even point uphill. For least squares, $$f = \|\vec{r}(\vec{x})\|^2$$, differentiating $\nabla f = 2J^T\vec{r}$ once more gives

$$
H = 2J^TJ + 2\sum_{i=1}^m r_i \nabla^2 r_i
$$

The first term only needs first derivatives and is always positive semi-definite. The second term needs the Hessian of every residual. Dropping it is exactly the idea of Gauss-Newton.

### Checking derivatives numerically

When deriving gradients and Hessians by hand, always check them against finite differences:

```python
import numpy as np

f = lambda x: x[0]**3 + x[0] * x[1]**2
grad = lambda x: np.array([3 * x[0]**2 + x[1]**2, 2 * x[0] * x[1]])
hess = lambda x: np.array([[6 * x[0], 2 * x[1]], [2 * x[1], 2 * x[0]]])

x, eps = np.array([1.0, 2.0]), 1e-6
I = np.eye(2)
num_grad = np.array([(f(x + eps * e) - f(x - eps * e)) / (2 * eps) for e in I])
num_hess = np.array([(grad(x + eps * e) - grad(x - eps * e)) / (2 * eps) for e in I]).T

print(num_grad, grad(x))  # [7. 4.] [7. 4.]
print(num_hess, hess(x))  # [[6. 4.] [4. 2.]] for both
```

## Gauss-Newton

### The problem: nonlinear least squares

A huge number of estimation problems in robotics and vision look like this: we have a parameter vector $\vec{x} \in \mathbb{R}^n$ (a pose, a calibration, a curve) and $m$ measurements. For each measurement, a **residual** $r_i(\vec{x})$ says how far the prediction is from what we measured. We want the $\vec{x}$ that makes all residuals small:

$$
\min_{\vec{x}} F(\vec{x}) = \frac{1}{2}\sum_{i=1}^m r_i(\vec{x})^2 = \frac{1}{2}\|\vec{r}(\vec{x})\|^2
$$

The $\frac{1}{2}$ is only there to cancel the factor 2 from differentiating. With it, the results from the Hessian section become:

$$
\nabla F = J^T\vec{r}, \qquad H = J^TJ + \sum_{i=1}^m r_i \nabla^2 r_i
$$

If $\vec{r}$ is linear, $\vec{r} = A\vec{x} - \vec{b}$, this is ordinary linear least squares, and the normal equations solve it in one shot. If $\vec{r}$ is nonlinear (distances, rotations, exponentials), there is no closed form and we iterate.

### Two ways to arrive at the same step

**View 1: approximate Newton.** Newton's step solves $H\vec{\delta} = -\nabla F$. Drop the expensive second term of the Hessian, $H \approx J^TJ$:

$$
\boxed{J^TJ\,\vec{\delta} = -J^T\vec{r}}
$$

**View 2: linearize the residuals, not the cost.** Replace each residual by its first-order Taylor expansion, $\vec{r}(\vec{x} + \vec{\delta}) \approx \vec{r} + J\vec{\delta}$. The cost becomes a *linear* least-squares problem in $\vec{\delta}$:

$$
\min_{\vec{\delta}} \frac{1}{2}\|\vec{r} + J\vec{\delta}\|^2
$$

Setting its gradient $J^T(\vec{r} + J\vec{\delta})$ to zero gives exactly the same boxed equation. This second view is the one to keep in mind: **Gauss-Newton repeatedly solves the linear least-squares problem you get by linearizing the residuals**. It never needs a second derivative.

The algorithm:

1. Start from an initial guess $\vec{x}_0$.
2. Evaluate the residuals $\vec{r}$ and the Jacobian $J$ at the current $\vec{x}$.
3. Solve $J^TJ\,\vec{\delta} = -J^T\vec{r}$ for the step.
4. Update $\vec{x} \leftarrow \vec{x} + \vec{\delta}$, and repeat until $\vec{\delta}$ or the change in $F$ is tiny.

The $n \times n$ matrix $J^TJ$ is always symmetric positive semi-definite. If $J$ has full column rank, it is positive definite. So the Gauss-Newton step is always a **descent direction**: $\nabla F^T\vec{\delta} = -\vec{\delta}^TJ^TJ\vec{\delta} < 0$. The true Newton step does not have that guarantee.

### When is dropping the second term OK?

The dropped term is $\sum_i r_i \nabla^2 r_i$. It is small when:

- **the residuals are small**, i.e. the model fits the data well near the solution (in the noise-free case $r_i = 0$ at the solution and the term vanishes exactly), or
- **the residuals are nearly linear**, so $\nabla^2 r_i \approx 0$.

In those cases Gauss-Newton behaves like Newton near the solution, and the number of correct digits roughly doubles every iteration (quadratic convergence). With large residuals and strongly curved residual functions, it slows down to linear convergence, and it can even fail to converge.

### Toy example: one residual

Find $\sqrt{2}$ by minimizing $F = \frac{1}{2}r(x)^2$ with $r(x) = x^2 - 2$. Here $J = r^{\prime}(x) = 2x$, and with a single residual the Gauss-Newton step is just $\delta = -r/J$, which is Newton's method for finding the *root* of $r$:

$$
x_{k+1} = x_k - \frac{x_k^2 - 2}{2x_k}
$$

| iteration | Gauss-Newton | Newton on $F$ |
| --- | --- | --- |
| 0 | 1.0 | 1.0 |
| 1 | 1.5 | 2.0 |
| 2 | 1.416667 | 1.6 |
| 3 | 1.414216 | 1.442254 |
| 4 |  | 1.415011 |

Interesting: here Gauss-Newton beats full Newton. At $x_0 = 1$ the full Hessian is $J^2 + r\,r^{\prime\prime} = 4 + (-1)(2) = 2$, half the Gauss-Newton approximation $J^2 = 4$, so Newton takes a step twice as large and overshoots to $2$. Far from the solution, the "exact" second-order model of $F$ is not necessarily the better one. Both methods agree near $\sqrt{2}$, where $r \rightarrow 0$ and the dropped term disappears.

### Toy example: locating a robot from range measurements

A robot at unknown position $\vec{x} \in \mathbb{R}^2$ measures its distance $d_i$ to three beacons $\vec{p}_i$:

$$
\vec{p}_1 = (0, 0),\quad \vec{p}_2 = (6, 0),\quad \vec{p}_3 = (0, 8), \qquad d_1 = d_2 = d_3 = 5
$$

The true position is $(3, 4)$, but suppose we don't know that. The residuals are "predicted distance minus measured distance":

$$
r_i(\vec{x}) = \|\vec{x} - \vec{p}_i\| - d_i
$$

The gradient of a distance is the unit vector pointing away from the beacon, so row $i$ of the Jacobian is

$$
\nabla r_i^T = \frac{(\vec{x} - \vec{p}_i)^T}{\|\vec{x} - \vec{p}_i\|}
$$

Starting from $\vec{x}_0 = (1, 1)$:

$$
\vec{r} = \begin{bmatrix} -3.586 \\ 0.099 \\ 2.071 \end{bmatrix},\quad
J = \begin{bmatrix} 0.707 & 0.707 \\ -0.981 & 0.196 \\ 0.141 & -0.990 \end{bmatrix},\quad
J^TJ = \begin{bmatrix} 1.482 & 0.168 \\ 0.168 & 1.519 \end{bmatrix},\quad
J^T\vec{r} = \begin{bmatrix} -2.340 \\ -4.566 \end{bmatrix}
$$

Solving $J^TJ\vec{\delta} = -J^T\vec{r}$ gives $\vec{\delta} = (1.255, 2.869)$, so $\vec{x}_1 = (2.255, 3.869)$. Repeating:

| iteration | $\vec{x}$ | $F(\vec{x})$ |
| --- | --- | --- |
| 0 | (1, 1) | 8.58 |
| 1 | (2.2546, 3.8687) | 0.253 |
| 2 | (3.0200, 4.0106) | 2.2e-4 |
| 3 | (3.000008, 4.000006) | 4.7e-11 |
| 4 | (3, 4) | 3.2e-25 |

The error goes $0.02 \rightarrow 10^{-5} \rightarrow 10^{-11}$, squaring every time. That is the quadratic convergence of the zero-residual case.

Geometrically, $J^TJ$ is built from the unit directions to the beacons. If all beacons were on one line through the robot, all rows of $J$ would be parallel, $J^TJ$ would be singular, and the position perpendicular to the line could not be determined. **The conditioning of $J^TJ$ tells you how well the geometry constrains the unknowns.** We will see the same thing in ICP.

In code, the whole method is a few lines:

```python
import numpy as np

def gauss_newton(residual, jacobian, x, iters=10):
    for _ in range(iters):
        r, J = residual(x), jacobian(x)
        x = x + np.linalg.solve(J.T @ J, -J.T @ r)
    return x

P = np.array([[0.0, 0.0], [6.0, 0.0], [0.0, 8.0]])
d = np.array([5.0, 5.0, 5.0])
residual = lambda x: np.linalg.norm(x - P, axis=1) - d
jacobian = lambda x: (x - P) / np.linalg.norm(x - P, axis=1)[:, None]

print(gauss_newton(residual, jacobian, np.array([1.0, 1.0])))  # [3. 4.]
```

A practical note: forming $J^TJ$ squares the condition number of $J$. For badly conditioned problems, solve the linear least-squares problem $$\min\|\vec{r} + J\vec{\delta}\|$$ directly with QR (`np.linalg.lstsq`) instead. For small, well-conditioned problems like ICP, the normal equations with a Cholesky solve are standard and fast.

### Weighted least squares

Measurements are rarely equally reliable. With a weight $w_i$ per residual (typically $1/\sigma_i^2$, or in general an information matrix $W = \Sigma^{-1}$), the cost $\frac{1}{2}\vec{r}^TW\vec{r}$ leads to

$$
J^TWJ\,\vec{\delta} = -J^TW\vec{r}
$$

Here $\Sigma$ is the $m \times m$ covariance of the measurement noise: $$\Sigma_{ii} = \sigma_i^2$$ is the variance of measurement $i$, and the off-diagonal entries say whether the noise on two measurements is correlated. Its inverse turns uncertainty into confidence. For independent measurements, $\Sigma$ is diagonal and $\Sigma^{-1} = \text{diag}(1/\sigma_1^2, \dots, 1/\sigma_m^2)$, so the cost becomes $\frac{1}{2}\sum_i r_i^2/\sigma_i^2$. Each residual is measured in units of its own standard deviation: a 1 cm miss on a sensor with $\sigma = 1$ cm costs as much as a 1 m miss on a sensor with $\sigma = 1$ m. With correlations, $\vec{r}^T\Sigma^{-1}\vec{r}$ is the squared Mahalanobis distance, which automatically counts correlated (partly redundant) measurements less than independent ones.

$J^TWJ$ is the **information matrix** of the estimate: near the solution, its inverse is the covariance of $\vec{x}$ (derived in the next section). Robust kernels (Huber, Cauchy) are implemented as weights that are recomputed every iteration from the current residuals, giving large residuals (outliers) a small weight. This is called iteratively reweighted least squares.

### Why the information matrix gives the covariance

The measurements are noisy, so the estimate $\hat{\vec{x}}$ is random too. Repeat the experiment with fresh noise and Gauss-Newton converges somewhere slightly different. The covariance $\text{Cov}(\hat{\vec{x}})$ describes that scatter, and it can be read off the matrix we already built for the step.

**Setup.** Model the measurements as $\vec{z} = \vec{h}(\vec{x}^\circ) + \vec{\varepsilon}$, where $\vec{x}^\circ$ is the true value and the noise $\vec{\varepsilon}$ has zero mean and covariance $\Sigma$. The residuals are $\vec{r}(\vec{x}) = \vec{h}(\vec{x}) - \vec{z}$, so at the true value they are pure noise: $\vec{r}(\vec{x}^\circ) = -\vec{\varepsilon}$.

**Step 1: the error is a linear function of the noise.** If the noise is small, $\hat{\vec{x}}$ is close to $\vec{x}^\circ$, and one Gauss-Newton step from $\vec{x}^\circ$ lands on $\hat{\vec{x}}$ to first order:

$$
\hat{\vec{x}} - \vec{x}^\circ \approx -(J^TWJ)^{-1}J^TW\,\vec{r}(\vec{x}^\circ) = \underbrace{(J^TWJ)^{-1}J^TW} _{A}\,\vec{\varepsilon}
$$

**Step 2: propagate the covariance.** For any linear map, $\text{Cov}(A\vec{\varepsilon}) = A\Sigma A^T$. With $W = \Sigma^{-1}$, and using that both are symmetric:

$$
\text{Cov}(\hat{\vec{x}}) \approx (J^TWJ)^{-1}J^TW\,\Sigma\,WJ\,(J^TWJ)^{-1}
$$

Since $W\Sigma W = W$, the middle part $J^TW\Sigma WJ$ is just $J^TWJ$, which cancels one of the inverses:

$$
\boxed{\text{Cov}(\hat{\vec{x}}) \approx (J^TWJ)^{-1}}
$$

This is also why the weights should be the inverse noise covariance: with any other $W$ the sandwich does not collapse, and the estimate ends up with a larger covariance (the Gauss-Markov theorem).

**Another view: the cost is a log-likelihood.** For Gaussian noise, $p(\vec{z} \mid \vec{x}) \propto \exp(-\frac{1}{2}\vec{r}^TW\vec{r})$, so minimizing the cost is maximum likelihood estimation. Near the minimum, the cost is the quadratic bowl $F(\hat{\vec{x}} + \vec{\delta}) \approx F(\hat{\vec{x}}) + \frac{1}{2}\vec{\delta}^T(J^TWJ)\vec{\delta}$, so the likelihood around $\hat{\vec{x}}$ is $\propto \exp(-\frac{1}{2}\vec{\delta}^T(J^TWJ)\vec{\delta})$, a Gaussian with covariance $(J^TWJ)^{-1}$. **The curvature of the cost is the precision of the estimate.** A sharp bowl means $\vec{x}$ is pinned down; a flat bowl means many values fit almost equally well. Along each eigenvector of $J^TWJ$, the variance is $1/\lambda$.

**Why "near the solution".** $J$ has to be evaluated at the converged $\hat{\vec{x}}$, and the derivation assumes the residuals are close to linear over the size of the noise. For strongly nonlinear problems or large noise, it is an approximation. It also assumes $\Sigma$ is the true noise covariance: if the weights are guesses, $(J^TWJ)^{-1}$ is only as good as the guess.

**Toy example: averaging.** Estimate a scalar $x$ from $n$ measurements $z_i$, each with noise $\sigma$. The residuals are $r_i = x - z_i$, so $J$ is a column of ones and $W = I/\sigma^2$. Then $J^TWJ = n/\sigma^2$, and the variance is $\sigma^2/n$: the familiar standard error of the mean. Information adds up over measurements, so variance shrinks as $1/n$.

**Toy example: the beacons.** Suppose each distance in the trilateration example has noise $\sigma = 0.1$. At the solution $(3, 4)$, the rows of $J$ are $(0.6, 0.8)$, $(-0.6, 0.8)$ and $(0.6, -0.8)$:

$$
J^TWJ = \frac{1}{\sigma^2}\begin{bmatrix} 1.08 & -0.48 \\ -0.48 & 1.92 \end{bmatrix}, \qquad (J^TWJ)^{-1} = \begin{bmatrix} 0.0104 & 0.0026 \\ 0.0026 & 0.0059 \end{bmatrix}
$$

So the predicted standard deviation is $0.102$ in $x$ and $0.077$ in $y$. The position is better determined in $y$ because all three beacon directions have a large $y$ component. A Monte Carlo run confirms it:

```python
sigma = 0.1
W = np.eye(3) / sigma**2
J = jacobian(np.array([3.0, 4.0]))
print(np.linalg.inv(J.T @ W @ J))  # [[0.0104 0.0026] [0.0026 0.0059]]

rng = np.random.default_rng(0)
X = []
for _ in range(20000):
    d = 5.0 + sigma * rng.standard_normal(3)
    residual = lambda x, d=d: np.linalg.norm(x - P, axis=1) - d
    X.append(gauss_newton(residual, jacobian, np.array([1.0, 1.0])))
print(np.cov(np.array(X).T))  # [[0.0105 0.0026] [0.0026 0.0058]]
```

The same reading explains degeneracy. If $J^TWJ$ has a zero eigenvalue, the variance in that direction is $1/0 = \infty$: the data says nothing about it. We will see exactly this in the ICP floor example.

## Levenberg-Marquardt: Gauss-Newton with a safety net

Gauss-Newton trusts its linearization over the full step. When the starting point is far away, the linear model may be badly wrong, the step overshoots, and the iteration can diverge.

### Toy example: Gauss-Newton diverging

Take $r(x) = \arctan(x)$, whose root is $x = 0$. Then $J = \frac{1}{1 + x^2}$ and the Gauss-Newton step is $\delta = -\arctan(x)(1 + x^2)$. From $x_0 = 2$:

$$
2 \rightarrow -3.54 \rightarrow 13.95 \rightarrow -279.3 \rightarrow 122017 \rightarrow \dots
$$

Far from zero, $\arctan$ is nearly flat, so $J$ is tiny, and the linear model predicts that the root is far away. Each step overshoots more than the last.

### The fix: damping

Levenberg-Marquardt adds a damping term $\lambda \ge 0$:

$$
(J^TJ + \lambda I)\,\vec{\delta} = -J^T\vec{r}
$$

- $\lambda \rightarrow 0$: this is the Gauss-Newton step.
- $\lambda$ large: $\vec{\delta} \approx -\frac{1}{\lambda}J^T\vec{r} = -\frac{1}{\lambda}\nabla F$, a short gradient-descent step.

So $\lambda$ blends smoothly between "fast near the solution" and "safe far from it". It also makes the matrix positive definite even when $J^TJ$ is singular. It is equivalent to solving the linearized problem with a penalty on step length, $$\min \frac{1}{2}\|\vec{r} + J\vec{\delta}\|^2 + \frac{\lambda}{2}\|\vec{\delta}\|^2$$, i.e. a **trust region**: only trust the linearization near the current point.

$\lambda$ is adapted automatically:

1. Compute the step with the current $\lambda$.
2. If the cost $F$ decreased, accept the step and decrease $\lambda$ (e.g. $\lambda \leftarrow \lambda/10$), because the linear model is trustworthy.
3. If not, reject the step and increase $\lambda$ (e.g. $\lambda \leftarrow 10\lambda$), then try again with a shorter, more gradient-like step.

On the $\arctan$ example, starting at $x_0 = 2$ with $\lambda = 1$:

| iteration | $x$ | $\lambda$ |
| --- | --- | --- |
| 0 | 2.0 | 1 |
| 1 | 1.787 | 0.1 |
| 2 | 0.175 | 0.01 |
| 3 | -0.0017 | 0.001 |
| 4 | -0.000002 | 0.0001 |

The first step is cautious. As soon as it gets near the root, $\lambda$ shrinks, and it converges as fast as Gauss-Newton. Marquardt's variant uses $\lambda\,\text{diag}(J^TJ)$ instead of $\lambda I$, so the damping respects the different scales of the parameters. Solvers like Ceres, g2o and `scipy.optimize.least_squares` are built on this idea.

### Summary of the methods

| Method | Step | Needs | Notes |
| --- | --- | --- | --- |
| Gradient descent | $\vec{\delta} = -\alpha\nabla F$ | first derivatives | robust but slow, step size $\alpha$ must be tuned |
| Newton | $H\vec{\delta} = -\nabla F$ | second derivatives | fast near the solution, $H$ may be indefinite |
| Gauss-Newton | $J^TJ\vec{\delta} = -J^T\vec{r}$ | Jacobian of residuals | always descends, fast when residuals are small, may overshoot |
| Levenberg-Marquardt | $(J^TJ + \lambda I)\vec{\delta} = -J^T\vec{r}$ | Jacobian of residuals | robust, the default for nonlinear least squares |

## Applications in Point to Plane ICP

### The registration problem

Iterative Closest Point (ICP) aligns two point clouds, for example a new LiDAR scan (the **source**, points $\vec{p}_i$) to a map (the **target**, points $\vec{q}_i$ with surface normals $\vec{n}_i$). We look for a rotation $R$ and translation $\vec{t}$ that put the source on top of the target. The correspondences are unknown, so ICP alternates:

1. For each transformed source point $R\vec{p}_i + \vec{t}$, find the nearest target point $\vec{q}_i$ (with a k-d tree).
2. Update $R, \vec{t}$ to make the matched pairs fit better.
3. Repeat until it stops moving.

The only design choice is what "fit better" means in step 2.

### Point-to-point vs point-to-plane

**Point-to-point** minimizes $$\sum_i \|R\vec{p}_i + \vec{t} - \vec{q}_i\|^2$$. This has a closed-form solution via the SVD of the cross-covariance of the matched pairs (the Kabsch/Umeyama method, see the SVD post). But it penalizes the full 3D distance to one particular target point. A LiDAR never samples the same spot twice, so even at the perfect alignment, the nearest neighbor of $\vec{p}_i$ is some neighboring sample, not "the same" point. Point-to-point keeps pulling the source toward the sample positions, and it converges slowly.

**Point-to-plane** only penalizes the distance *along the normal*, i.e. the distance to the local tangent plane of the target surface:

$$
\min_{R, \vec{t}} \sum_i \left(\vec{n}_i^T(R\vec{p}_i + \vec{t} - \vec{q}_i)\right)^2
$$

Sliding along the surface is free. That matches reality: if a source point lies on the target surface, it is aligned, wherever exactly the nearest sample is. The price is that there is no closed-form solution any more, because $R$ is constrained to be a rotation. This is a nonlinear least-squares problem, and a perfect fit for Gauss-Newton:

- the residuals are linear in $\vec{t}$ and nearly linear in small rotations, and
- at the solution, the residuals are close to zero (just sensor noise).

### Parametrizing the update

A rotation matrix has 9 entries but only 3 degrees of freedom, so we cannot just add a $\vec{\delta}$ to $R$. Instead, at each iteration we transform the source with the current estimate (so $\vec{p}_i$ below means the already transformed point) and solve for a small **correction**: a rotation vector $\vec{\omega} \in \mathbb{R}^3$ (axis times angle) and a translation $\vec{\tau} \in \mathbb{R}^3$, stacked as $\vec{\delta} = [\vec{\omega};\ \vec{\tau}] \in \mathbb{R}^6$.

For small angles, $\exp([\vec{\omega}] _\times) \approx I + [\vec{\omega}] _\times$, where $[\vec{\omega}] _\times\vec{p} = \vec{\omega} \times \vec{p}$. So the residual after the correction is

$$
r_i(\vec{\delta}) = \vec{n}_i^T(\vec{p}_i + \vec{\omega} \times \vec{p}_i + \vec{\tau} - \vec{q}_i) = \underbrace{\vec{n}_i^T(\vec{p}_i - \vec{q}_i)} _{r_i} + \vec{n}_i^T(\vec{\omega} \times \vec{p}_i) + \vec{n}_i^T\vec{\tau}
$$

The scalar triple product can be cycled, $\vec{n} \cdot (\vec{\omega} \times \vec{p}) = \vec{\omega} \cdot (\vec{p} \times \vec{n})$, which pulls $\vec{\omega}$ out front:

$$
r_i(\vec{\delta}) \approx r_i + \underbrace{\begin{bmatrix} (\vec{p}_i \times \vec{n}_i)^T & \vec{n}_i^T \end{bmatrix}} _{J_i\ (1 \times 6)} \begin{bmatrix} \vec{\omega} \\ \vec{\tau} \end{bmatrix}
$$

Each correspondence contributes one row $J_i$, and the Jacobian has a nice physical reading. The translation part is the normal: moving along the normal changes the distance, moving within the plane does not. The rotation part, $\vec{p}_i \times \vec{n}_i$, is the "lever arm": rotating about an axis changes the distance most for points far from the axis whose normal is tangent to the rotation.

The Gauss-Newton step is the $6 \times 6$ system

$$
\left(\sum_i J_i^TJ_i\right)\vec{\delta} = -\sum_i J_i^T r_i
$$

which is cheap no matter how many points there are. Then we apply the correction on the left of the current estimate, using the exact exponential map (Rodrigues' formula) so that $R$ stays a valid rotation:

$$
\Delta R = \exp([\vec{\omega}] _\times), \qquad R \leftarrow \Delta R\,R, \qquad \vec{t} \leftarrow \Delta R\,\vec{t} + \vec{\tau}
$$

Note that we never needed the Hessian of $r_i$ with respect to the rotation. Gauss-Newton only asks for the Jacobian of the residual, which is why it is the workhorse of ICP, bundle adjustment and pose graph optimization.

### Flagging the degenerate axes

ICP flags a degenerate axis from the eigendecomposition of the same matrix that builds the Gauss-Newton step. Factor

$$
J^TJ = V\Lambda V^T, \qquad \lambda_1 \le \cdots \le \lambda_6
$$

Column $\vec{v}_k$ of $V$ is a direction in $(\vec{\omega}, \vec{\tau})$. To see what $\lambda_k$ measures, go back to the linearization: a correction $\vec{\delta}$ changes the residuals to first order as $\vec{r}(\vec{\delta}) \approx \vec{r} + J\vec{\delta}$. Entry $i$ of $J\vec{\delta}$ is how far point $i$ moves toward or away from its plane. Take a step of length $s$ along the eigenvector, $\vec{\delta} = s\,\vec{v}_k$. The residuals change by $\Delta\vec{r} = s\,J\vec{v}_k$, and the size of that change over all points is

$$
\|\Delta\vec{r}\|^2 = s^2\,\vec{v}_k^TJ^TJ\,\vec{v}_k = s^2\,\lambda_k
$$

So $\lambda_k$ is how strongly the residuals react to motion along $\vec{v}_k$. It is also the curvature $\vec{v}^T H \vec{v}$ from [What the Hessian tells you: curvature](#what-the-hessian-tells-you-curvature), with $H$ replaced by the Gauss-Newton approximation $J^TJ$.

A tiny $\lambda_k$ means a pose step along $\vec{v}_k$ leaves the residuals almost unchanged: the scan cannot see that motion, and $\vec{v}_k$ is a degenerate axis. Flag every eigenvalue that is negligible next to the strongest one,

$$
\mathcal{D} = \{ k : \lambda_k \le \epsilon\, \lambda_{\max} \}
$$

with $\epsilon$ around $10^{-3}$ after the scaling below. The flagged axes are the columns $\vec{v}_k$ for $k \in \mathcal{D}$. One symmetric eigendecomposition of a $6 \times 6$ matrix is the whole test, and it is redone every iteration because the correspondences change.

**One scale for rotation and translation.** Stacking the rows $J_i$ of all $m$ correspondences gives

$$
J = \begin{bmatrix} J_{\omega} & J_{\tau} \end{bmatrix} = \begin{bmatrix} (\vec{p}_1 \times \vec{n}_1)^T & \vec{n}_1^T \\ (\vec{p}_2 \times \vec{n}_2)^T & \vec{n}_2^T \\ \vdots & \vdots \\ (\vec{p}_m \times \vec{n}_m)^T & \vec{n}_m^T \end{bmatrix} \in \mathbb{R}^{m \times 6}, \qquad J_{\omega},\ J_{\tau} \in \mathbb{R}^{m \times 3}
$$

The first three columns $J_{\omega}$ multiply the rotation $\vec{\omega}$, and the last three $J_{\tau}$ multiply the translation $\vec{\tau}$. Each row of $J_{\tau}$ is a unit normal, so it is dimensionless. Each row of $J_{\omega}$ is a lever arm $$\vec{p}_i \times \vec{n}_i$$ in meters, so it grows with the cloud, and its eigenvalues grow with length squared.

The reason is how far a rotation moves a point. A small rotation $\vec{\omega}$ moves $$\vec{p}_i$$ by $$\vec{\omega} \times \vec{p}_i$$, which is proportional to the point's distance from the rotation axis: $1^\circ$ moves a point 1 m away by about $1.7\,\text{cm}$, and a point 10 m away by about $17\,\text{cm}$. The residual changes by $$\vec{n}_i^T(\vec{\omega} \times \vec{p}_i) = (\vec{p}_i \times \vec{n}_i)^T\vec{\omega}$$, so a row of $$J_{\omega}$$ grows with the point's distance from the origin.

The origin is the origin of the frame the points are written in, here the target (map) frame. Each iteration first moves the source with the current estimate, and the correction $\Delta R$ is applied on the left, so it rotates everything about that origin and $\vec{\omega}$ is an axis through it. Strictly, the displacement $$\|\vec{\omega} \times \vec{p}_i\|$$ depends on the distance to that axis, and the distance to the origin $$\|\vec{p}_i\|$$ is an upper bound on it. Where the origin sits therefore matters. In the sensor frame, $$\|\vec{p}_i\|$$ is the measured range. In a map frame whose origin is 1 km away, every lever arm is about 1 km, and the rotation eigenvalues are huge even for a small room. Implementations usually express the points relative to the sensor or the scan's centroid before building $J$. That does not change which motions the scan can see; it only changes how rotation and translation mix inside $J$, which keeps the numbers well conditioned.

In the figure, the same angle $\theta$ sweeps each point along its own circle, and the arc it travels has length $r\theta$. Doubling the distance doubles the displacement: the plot on the right is a straight line through the origin with slope $\theta$. A translation, the dashed line, moves every point by the same amount.

{% include figures/rotation-lever-arm.html %}

The two diagonal blocks of $J^TJ$ are sums of squares of the rows:

$$
J_{\omega}^TJ_{\omega} = \sum_{i=1}^m (\vec{p}_i \times \vec{n}_i)(\vec{p}_i \times \vec{n}_i)^T, \qquad J_{\tau}^TJ_{\tau} = \sum_{i=1}^m \vec{n}_i\vec{n}_i^T
$$

Scale the cloud by a factor $c$, $$\vec{p}_i \to c\,\vec{p}_i$$. Every row of $J_{\omega}$ is multiplied by $c$, the rotation block by $c^2$, and so are its eigenvalues. The translation block holds only unit normals and does not change.

The same follows from $$\lambda_k = \|J\vec{v}_k\|^2$$, one direction at a time:

- **A pure rotation**, $\vec{v} = [\hat{\omega};\ \vec{0}]$ with $\|\hat{\omega}\| = 1$. Point $i$'s residual changes by $$(\vec{p}_i \times \vec{n}_i)^T\hat{\omega}$$ per radian. After scaling it changes by $$(c\,\vec{p}_i \times \vec{n}_i)^T\hat{\omega}$$, which is $c$ times as much, for every point. So $J\vec{v}$ becomes $cJ\vec{v}$, and $$\|J\vec{v}\|^2$$ becomes $$c^2\|J\vec{v}\|^2$$.
- **A pure translation**, $\vec{v} = [\vec{0};\ \hat{\tau}]$. Point $i$'s residual changes by $$\vec{n}_i^T\hat{\tau}$$, which does not involve $$\vec{p}_i$$, so $$\|J\vec{v}\|^2$$ is the same for any $c$.

With $c = 10$, a $1^\circ$ rotation that moved a point at 1 m by $1.7\,\text{cm}$ now moves the same point, at 10 m, by $17\,\text{cm}$. Each residual change is 10 times larger and the sum of their squares is 100 times larger, while a $1.7\,\text{cm}$ translation still changes every residual by the same amount as before.

The cutoff $\epsilon\,\lambda_{\max}$ compares rotation eigenvalues with translation eigenvalues, so without a fix, which axes look weak would depend on the size of the scene and not on its shape.

The fix is to divide $J_{\omega}$ by a length $L$ (1 m, or the mean range) before forming $J^TJ$. The unknowns are the two halves of the Gauss-Newton step $\vec{\delta} = [\vec{\omega};\ \vec{\tau}]$: the rotation $\vec{\omega}$ in radians and the translation $\vec{\tau}$ in meters. Moving the factor $L$ from the matrix onto the rotation leaves the predicted residual change $J\vec{\delta}$ unchanged:

$$
J\vec{\delta} = J_{\omega}\vec{\omega} + J_{\tau}\vec{\tau} = \frac{J_{\omega}}{L}\,(L\vec{\omega}) + J_{\tau}\vec{\tau} = \tilde{J}\tilde{\vec{\delta}}, \qquad
\tilde{J} = \begin{bmatrix} \dfrac{J_{\omega}}{L} & J_{\tau} \end{bmatrix}, \quad
\tilde{\vec{\delta}} = \begin{bmatrix} L\vec{\omega} \\ \vec{\tau} \end{bmatrix}
$$

The new unknown $\tilde{\vec{\delta}}$ has the arc length $L\vec{\omega}$ in place of the angle, so all six of its entries are in meters, and both blocks of $\tilde{J}$ are dimensionless. Solve for $\tilde{\vec{\delta}}$ and run the eigenvalue test on $\tilde{J}^T\tilde{J}$, and the same $\epsilon$ applies to a rotation and a translation. Divide the first three entries of the solved $\tilde{\vec{\delta}}$ by $L$ to get $\vec{\omega}$ back in radians. The scenes in this post are about a meter across, so $L = 1$ and the raw matrix is already on that scale. The original LOAM mapping code skips the scaling and uses one absolute cutoff on all six raw eigenvalues, 100, chosen for that program's ranges and voxel size. Forks of the same code use 10 or 1.

**The step, with the flagged axes frozen.** The component of the update along each flagged eigenvector is set to zero, and those pose coordinates stay where the iteration was linearized: the previous pose, or the IMU or wheel prediction. Invert only the healthy eigenvalues (the pseudoinverse of $\Lambda$):

$$
\vec{\delta} = -V\Lambda^{+} V^T J^T\vec{r}, \qquad
\Lambda^{+}_{kk} = \begin{cases} 1/\lambda_k & k \notin \mathcal{D} \\ 0 & k \in \mathcal{D} \end{cases}
$$

Here $J$, $V$, $\Lambda$ and $\vec{\delta}$ are the scaled $\tilde{J}$, its eigendecomposition, and the scaled step $\tilde{\vec{\delta}}$, so the first three entries of the solution are $L\vec{\omega}$. Divide them by $L$ before the exponential map. When $J^TJ$ is singular, $J^TJ\vec{\delta} = -J^T\vec{r}$ has no unique solution; $\Lambda^{+}$ still returns one, with the flagged components equal to zero. When every $\lambda_k$ is merely small, the same map is the projection $P = VSV^T$ applied to a full solve, where $S$ is diagonal with $1$ on the healthy eigenvalues and $0$ on $\mathcal{D}$. LOAM multiplies its solved update by this $P$. It is the solution remapping of Zhang, Kaess and Singh (ICRA 2016): the part of the optimized pose in the well-constrained subspace is kept, and the degenerate subspace is put back on the prior. Assembling $\vec{\delta}$ from $\Lambda^{+}$ is the version that stays defined at $\lambda_k = 0$.

The eigenvalues you zeroed are also what you hand to the next estimator. Along $\vec{v}_k$ the variance is $1/\lambda_k$, from the covariance section: a flagged axis carries no information from this scan. Publish $V\tilde{\Lambda}V^T$ with those eigenvalues set to zero, and the IMU or wheel prior is what informs them. Levenberg-Marquardt lifts every eigenvalue, $\lambda_k \mapsto \lambda_k + \lambda$, and the step along $\vec{v}_k$ shrinks to $-(\vec{v}_k^T J^T\vec{r})/(\lambda_k + \lambda)$. The iteration survives a singular $J^TJ$. The eigenvectors are the axes you report.

### Toy example: why one plane is not enough

Suppose every point lies on a flat floor, $z = 0$, so $\vec{n}_i = (0, 0, 1)$ for all $i$. For $\vec{p}_i = (x_i, y_i, 0)$:

$$
\vec{p}_i \times \vec{n}_i = (y_i,\ -x_i,\ 0), \qquad J_i = \begin{bmatrix} y_i & -x_i & 0 & 0 & 0 & 1 \end{bmatrix}
$$

Columns 3, 4 and 5 of $J$ are zero for every point. Rotation about $z$ (yaw) and translation in $x$ and $y$ simply slide the floor within itself, and no point-to-plane residual can see that. $J^TJ$ has three zero eigenvalues: for 500 random floor points in $[-1, 1]^2$, the eigenvalues are

$$
\text{eig}(J^TJ) = (0,\ 0,\ 0,\ 158,\ 163,\ 501)
$$

Read $$\lambda_k = \|J\vec{v}_k\|^2$$ from [Flagging the degenerate axes](#flagging-the-degenerate-axes) on this floor. Two directions show the extremes:

- **A step up, along $t_z$**, $\vec{v} = (0, 0, 0, 0, 0, 1)$. $J\vec{v}$ is the last column of $J$, all ones. Every point's distance to the floor changes by $s$, and with 500 points $\lambda = 500$. The scan sees this motion clearly.
- **A step in yaw**, $\vec{v} = (0, 0, 1, 0, 0, 0)$. $J\vec{v}$ is the third column, all zeros. The floor spins within its own plane, no point moves toward or away from it, and $\lambda = 0$.

When the residuals do not change, the cost cannot change either: the data fits equally well at any yaw, so it says nothing about yaw.

Because the yaw, $t_x$ and $t_y$ columns are zero, the null space of $J^TJ$ is spanned by

$$
\vec{v}_{\text{yaw}} = \begin{bmatrix} 0 \\ 0 \\ 1 \\ 0 \\ 0 \\ 0 \end{bmatrix}, \quad
\vec{v}_{t_x} = \begin{bmatrix} 0 \\ 0 \\ 0 \\ 1 \\ 0 \\ 0 \end{bmatrix}, \quad
\vec{v}_{t_y} = \begin{bmatrix} 0 \\ 0 \\ 0 \\ 0 \\ 1 \\ 0 \end{bmatrix}
$$

and those are the axes the eigenvalue test flags. The three positive eigenvalues belong to roll, pitch and $t_z$.

This is the Hessian-eigenvalue story from [What the Hessian tells you: curvature](#what-the-hessian-tells-you-curvature), seen through the Gauss-Newton approximation $J^TJ$. Zero curvature in a direction means the cost is flat there: the problem is **degenerate**, and $J^TJ\vec{\delta} = -J^T\vec{r}$ has no unique solution. A long featureless corridor is the same situation: translation along the corridor leaves every point-to-plane residual unchanged.

Add two walls, $x = 0$ with normal $(1, 0, 0)$ and $y = 0$ with normal $(0, 1, 0)$. For a point $(0, y, z)$ on the first wall, $J_i = [0,\ z,\ -y,\ 1,\ 0,\ 0]$. For a point $(x, 0, z)$ on the second wall, $J_i = [-z,\ 0,\ x,\ 0,\ 1,\ 0]$. Together with the floor, every column now has non-zero entries, and all six degrees of freedom are constrained.

**A corridor at an angle.** Let the corridor run along $\hat{u} = (\cos\theta, \sin\theta, 0)$, with floor normal $(0, 0, 1)$ and one wall normal $\vec{w} = (-\sin\theta, \cos\theta, 0)$. Translation along the corridor is tangent to both planes, so every row of $J$ annihilates

$$
\vec{v} = \begin{bmatrix} 0 \\ 0 \\ 0 \\ \cos\theta \\ \sin\theta \\ 0 \end{bmatrix}
$$

and $\lambda = 0$ for that axis. At $\theta = 30^\circ$ the flagged direction is $(0,\ 0,\ 0,\ \sqrt{3}/2,\ 1/2,\ 0)$: a horizontal translation at $30^\circ$, which is the corridor heading itself.

The diagonal entries are a different reading of the same matrix. $$(J^TJ)_{t_x t_x} = \sum_i n_{i,x}^2$$. Floor normals have $n_x = 0$, so they add nothing to that sum. Each wall normal contributes $\sin^2\theta$, and $N$ wall points give $N\sin^2\theta$. At $\theta = 30^\circ$ and $N = 400$,

$$
(J^TJ)_{t_x t_x} = 400 \cdot \frac{1}{4} = 100, \qquad (J^TJ)_{t_y t_y} = 400 \cdot \frac{3}{4} = 300
$$

Both entries are ordinary positive numbers. The zero-eigenvalue direction is the mix $\cos\theta\, t_x + \sin\theta\, t_y$, and that mix is what the eigenvector records.

**Noise on a weak axis.** Tilt every floor normal by an independent $0.5^\circ$ and add $1\,\text{cm}$ of noise to the source, with no true motion. The three weak eigenvalues come out near $0.03$, under $10^{-4}$ of $$\lambda_{\max} \approx 504$$, and $$10^{-3}\lambda_{\max}$$ still separates them cleanly from the next eigenvalue at $149$. The eigenvectors are yaw, $t_x$ and $t_y$, each with a small extra component because the normals are tilted. Ordinary Gauss-Newton divides by those eigenvalues and answers with $2.55^\circ$ of yaw and a horizontal slide of $7.4\,\text{mm}$ in $x$ and $2.1\,\text{mm}$ in $y$. Zeroing the three flagged eigenvalues removes all three. Pitch stays at $-0.02^\circ$ and $t_z$ at $-0.2\,\text{mm}$, which is as much motion as this floor can support.

```python
import numpy as np

def gauss_newton_degenerate(points, normals, residual, length=1.0, eps_ratio=1e-3):
    # Rotation columns are lever arms in meters. Divide by `length` so one
    # eigenvalue cutoff covers rotation and translation. delta[:3] comes back in radians.
    J = np.hstack([np.cross(points, normals) / length, normals])
    evals, V = np.linalg.eigh(J.T @ J)          # columns of V, eigenvalues ascending
    healthy = evals > eps_ratio * evals[-1]
    inv = np.zeros_like(evals)
    inv[healthy] = 1.0 / evals[healthy]
    delta = -V @ (inv * (V.T @ (J.T @ residual)))
    delta[:3] /= length
    return delta, evals, V, healthy

# A floor, but the normals are tilted by 0.5 deg and the source has 1 cm of
# noise. There is no true motion: a correct update is about zero.
rng = np.random.default_rng(0)
xy = rng.uniform(-1, 1, (500, 2))
pts = np.column_stack([xy, np.zeros(500)])
nrm = np.column_stack([rng.normal(0, np.deg2rad(0.5), (500, 2)), np.ones(500)])
nrm /= np.linalg.norm(nrm, axis=1)[:, None]
src = pts + rng.normal(0, 0.01, pts.shape)
residual = np.sum((src - pts) * nrm, axis=1)

delta, evals, V, healthy = gauss_newton_degenerate(src, nrm, residual)
J = np.hstack([np.cross(src, nrm), nrm])
full = np.linalg.solve(J.T @ J, -J.T @ residual)   # ordinary Gauss-Newton, for comparison

names = ["wx", "wy", "wz", "tx", "ty", "tz"]
for i in range(6):
    v = V[:, i].copy()
    if v[np.argmax(np.abs(v))] < 0:
        v = -v
    tag = "keep" if healthy[i] else "flag"
    bits = "  ".join(f"{names[k]}={v[k]:+.2f}" for k in range(6) if abs(v[k]) >= 0.2)
    print(f"{tag}  lam={evals[i]:8.3f}  {bits}")

def show(tag, d):
    print(f"{tag:8s} yaw {np.rad2deg(d[2]):+7.2f} deg"
          f"   pitch {np.rad2deg(d[1]):+7.3f} deg"
          f"   t [mm] {1e3 * d[3]:+7.2f} {1e3 * d[4]:+7.2f} {1e3 * d[5]:+7.2f}")

show("full", full)
show("flagged", delta)
```

```
flag  lam=   0.025  wz=+0.95  ty=-0.28
flag  lam=   0.038  tx=+0.99
flag  lam=   0.043  wz=+0.30  ty=+0.95
keep  lam= 148.786  wx=+0.72  wy=-0.69
keep  lam= 172.457  wx=+0.69  wy=+0.72
keep  lam= 503.690  tz=+0.99
full     yaw   +2.55 deg   pitch  -0.025 deg   t [mm]   -7.42   +2.09   -0.17
flagged  yaw   +0.00 deg   pitch  -0.024 deg   t [mm]   +0.00   -0.00   -0.19
```

### Putting it together

Here is the complete point-to-plane ICP on that "room corner" scene. The target and the source are two *different* random samplings of the same three faces, so no source point has an exact match in the target. The source is offset by a rotation of about $14°$ and a translation of $14\,\text{cm}$.

```python
import numpy as np
from scipy.spatial import cKDTree

def skew(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])

def exp_so3(w):
    theta = np.linalg.norm(w)
    if theta < 1e-12:
        return np.eye(3) + skew(w)
    K = skew(w / theta)
    return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * K @ K

def sample_corner(n, rng):
    """Points on the three faces x=0, y=0, z=0 of the unit cube, with normals."""
    pts, nrm = [], []
    for axis in range(3):
        p = rng.uniform(0, 1, (n, 3))
        p[:, axis] = 0
        pts.append(p)
        nrm.append(np.tile(np.eye(3)[axis], (n, 1)))
    return np.vstack(pts), np.vstack(nrm)

def point_to_plane_icp(src, dst, dst_normals, iters=10):
    tree = cKDTree(dst)
    R, t = np.eye(3), np.zeros(3)
    for k in range(iters):
        p = src @ R.T + t                      # source in the current estimate
        _, idx = tree.query(p)                 # nearest-neighbor correspondences
        q, n = dst[idx], dst_normals[idx]
        r = np.sum((p - q) * n, axis=1)        # r_i = n_i^T (p_i - q_i)
        J = np.hstack([np.cross(p, n), n])     # J_i = [(p_i x n_i)^T, n_i^T]
        delta = np.linalg.solve(J.T @ J, -J.T @ r)
        dR = exp_so3(delta[:3])
        R, t = dR @ R, dR @ t + delta[3:]
        print(f"iter {k}: rms residual = {np.sqrt(np.mean(r**2)):.2e}")
    return R, t

rng = np.random.default_rng(0)
dst, dst_normals = sample_corner(500, rng)
src_true, _ = sample_corner(500, rng)
R_true, t_true = exp_so3(np.deg2rad([5, -8, 10])), np.array([0.05, -0.1, 0.08])
src = (src_true - t_true) @ R_true             # so that R_true @ src + t_true lies on dst

R, t = point_to_plane_icp(src, dst, dst_normals)
angle_err = np.arccos(np.clip((np.trace(R.T @ R_true) - 1) / 2, -1, 1))
print("rotation error [deg]:", np.rad2deg(angle_err).round(4))
print("translation error:", np.linalg.norm(t - t_true).round(6))
```

Output:

```
iter 0: rms residual = 1.43e-01
iter 1: rms residual = 2.10e-02
iter 2: rms residual = 4.23e-03
iter 3: rms residual = 2.57e-03
iter 4: rms residual = 2.46e-03
...
rotation error [deg]: 0.0518
translation error: 0.000913
```

It converges in about 4 iterations to $0.05°$ and under $1\,\text{mm}$. The residual levels off instead of reaching zero: 26 of the 1500 source points lie within $3.5\,\text{cm}$ of an edge of the corner, and their nearest neighbor lands on the wrong face. In a real system, these outliers are what the robust weights from the weighted least-squares section are for.

For comparison, point-to-point ICP (with the closed-form SVD solution in each iteration) on the same data is still $1.8°$ and $3\,\text{cm}$ off after 10 iterations, and stalls at about $0.3°$ and $6\,\text{mm}$ even after 60. It keeps trying to match sample positions that do not exist in the other scan.

