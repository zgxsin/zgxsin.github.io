---
title: Ego Motion Estimation
published: true
date: 2023-06-30
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

Visual odometry answers one question, frame after frame: **how did the camera move between the last image and this one?** That motion, the camera's own motion as opposed to the motion of things in the scene, is called **ego-motion**. Chain the frame-to-frame motions together and you get a trajectory. Every visual odometry, visual SLAM and visual-inertial pipeline has an ego-motion estimator at its core.

This post starts with the geometry of two views, then walks through the four classic ways to recover the motion, depending on what the two frames give you: 2D points in both images (essential matrix), 3D points in both frames (absolute orientation), 3D points in one frame and 2D points in the other (PnP), and points on a plane (homography). It ends with a table that says which one to use when.

## Setup and notation

A point $\mathbf{X}\_{1} = (X, Y, Z)$ in the coordinate frame of camera 1 shows up in frame 2 as

$$
\mathbf{X}_{2} = R\,\mathbf{X}_{1} + \mathbf{t},
\qquad
T_{2,1} = \begin{bmatrix} R & \mathbf{t} \\ 0 & 1 \end{bmatrix},
\qquad R \in SO(3),\ \mathbf{t} \in \mathbb{R}^3
$$

so $T_{2,1}$ maps coordinates from frame 1 to frame 2. A pinhole camera with intrinsic matrix $K$ projects the point to the pixel

$$
\mathbf{p} = \begin{bmatrix} u_p \\ v_p \\ 1 \end{bmatrix} = \frac{1}{Z} K \mathbf{X},
\qquad
K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}
$$

Undoing $K$ gives the **normalized image coordinates** $\mathbf{x} = K^{-1}\mathbf{p} = (X/Z,\ Y/Z,\ 1)^T = (u, v, 1)^T$: the pixel as seen by an ideal camera with focal length 1. Normalized coordinates are what you get once the camera is calibrated, and they let us talk about geometry without carrying $K$ around. Geometrically, $\mathbf{x}$ is the direction of the ray from the camera center to the point; the depth $Z$ along that ray is what a single image does not tell you.

## Indirect and direct methods

There are two broad ways to compute the motion between consecutive frames.

**Indirect (feature-based) methods** extract a sparse set of repeatable, salient points such as corners and blobs in each image. An invariant descriptor (ORB, SIFT, ...) or a sparse optical-flow tracker (KLT) matches them across frames, and the motion is recovered from those correspondences with the epipolar geometry described below. The error they minimize is geometric, measured in pixels:

$$
\min_{T_{2,1}} \sum_i \big\lVert \mathbf{p}_{2,i} - \pi\big(T_{2,1}\,\mathbf{X}_{1,i}\big) \big\rVert^2
$$

where $\pi(\cdot)$ projects a 3D point to the image.

**Direct methods** skip features. They warp one image onto the other using the current motion estimate and a depth for every pixel used, and minimize the difference in pixel intensities, the **photometric error**:

$$
\min_{T_{2,1}} \sum_{\mathbf{p} \in \Omega} \Big( I_2\big(\pi(T_{2,1}\,\pi^{-1}(\mathbf{p}, Z_\mathbf{p}))\big) - I_1(\mathbf{p}) \Big)^2
$$

Here $\pi^{-1}(\mathbf{p}, Z_\mathbf{p})$ lifts pixel $\mathbf{p}$ back to 3D using its depth. The pixel correspondence comes directly from the geometry, so there is no separate data-association step that could go wrong.

| | Indirect (feature-based) | Direct |
| --- | --- | --- |
| What is compared | Sparse keypoints and descriptors | Raw pixel intensities |
| Error minimized | Geometric (reprojection, in pixels) | Photometric (intensity difference) |
| Data association | Explicit matching, needs outlier rejection (RANSAC) | Implicit, given by the warp |
| Main assumption | Features are repeatable across views | **Brightness constancy**: a point keeps its intensity across frames |
| Breaks under | Textureless areas, repetitive patterns | Illumination changes, auto-exposure, non-Lambertian (shiny) surfaces, camera noise, large motions |
| Strengths | Fast, accurate, tolerates large baselines | Uses edges and weak texture, extends naturally to dense or semi-dense mapping |
| Examples | ORB-SLAM, VINS-Mono | LSD-SLAM, DSO |

In practice direct methods tend to be less accurate and more expensive than indirect ones, and the brightness-constancy assumption is fragile on a real robot with auto-exposure. That is why most visual odometry systems are feature-based, and why the rest of this post is about recovering motion from point correspondences.

## Epipolar Geometry

Take two cameras with centers $C_1$ and $C_2$ that both see a 3D point $\mathbf{X}$, at $\mathbf{x}\_1$ in image 1 and $\mathbf{x}\_2$ in image 2. The line $C_1C_2$ is the **baseline**. The three points $C_1$, $C_2$ and $\mathbf{X}$ span a plane, the **epipolar plane**, and everything interesting follows from that plane:

- The ray from $C_1$ through $\mathbf{x}\_1$ lies in the epipolar plane, and so does the ray from $C_2$ through $\mathbf{x}\_2$.
- The epipolar plane cuts each image plane in a line, the **epipolar line**. $\mathbf{x}\_2$ must lie on the epipolar line $\mathbf{l}\_2$ in image 2, and $\mathbf{x}\_1$ on $\mathbf{l}\_1$ in image 1.
- The baseline pierces each image plane at the **epipole**: $\mathbf{e}\_2$ is where camera 2 sees the center of camera 1, and $\mathbf{e}\_1$ is where camera 1 sees the center of camera 2. Every epipolar line in an image passes through its epipole, because every epipolar plane contains the baseline.

The useful consequence: from image 1 alone, the depth of $\mathbf{X}$ is unknown, so $\mathbf{X}$ could be anywhere on the ray of $\mathbf{x}\_1$. Seen from camera 2, that ray is a line, the epipolar line. So **the match of $\mathbf{x}\_1$ must lie on a known line in image 2**, which turns a 2D search for correspondences into a 1D search. Slide the point along the ray below: $\mathbf{X}$ and $\mathbf{x}\_2$ move, but $\mathbf{x}\_2$ never leaves the red line, and the epipolar constraint $\mathbf{x}\_2^T E\,\mathbf{x}\_1$ (derived in the next section) stays at zero.

{% include figures/epipolar-geometry.html %}

Switch to **rectified** cameras: the two cameras now point the same way and are displaced only sideways. The image planes are parallel to the baseline, so the baseline never pierces them and the epipoles move off to infinity. All epipolar lines become horizontal, and the match of a pixel lies on the **same row** of the other image. This is what stereo rectification does to the images of a stereo pair: it warps both images so this holds, and dense stereo matching then only has to search along rows.

## Ego-motion Estimation

### 2D to 2D

With only matched pixels in two images, there are two models for the motion: the essential (or fundamental) matrix for a general scene, and the homography for a planar scene or a purely rotating camera.

#### Essential matrix

**Deriving the constraint.** Start from $\mathbf{X}\_{2} = R\,\mathbf{X}\_{1} + \mathbf{t}$. Take the cross product with $\mathbf{t}$ on both sides, which removes $\mathbf{t}$ because $\mathbf{t} \times \mathbf{t} = \mathbf{0}$:

$$
\mathbf{t} \times \mathbf{X}_{2} = \mathbf{t} \times R\,\mathbf{X}_{1}
$$

The left side is perpendicular to $\mathbf{X}\_{2}$, so the dot product with $\mathbf{X}\_{2}$ is zero:

$$
\mathbf{X}_{2}^T \big(\mathbf{t} \times R\,\mathbf{X}_{1}\big) = 0
$$

Geometrically, this says that $\mathbf{X}\_{2}$, $\mathbf{t}$ and $R\,\mathbf{X}\_{1}$, three vectors expressed in frame 2, lie in one plane: the epipolar plane. Write the cross product as a matrix product, $\mathbf{t} \times \mathbf{a} = [\mathbf{t}]\_\times \mathbf{a}$, with the skew-symmetric matrix

$$
\mathbf{t} = \begin{bmatrix} t_x \\ t_y \\ t_z \end{bmatrix},
\qquad
[\mathbf{t}]_\times = \begin{bmatrix} 0 & -t_z & t_y \\ t_z & 0 & -t_x \\ -t_y & t_x & 0 \end{bmatrix}
$$

and divide by the two depths $Z_1 Z_2$ to turn 3D points into normalized image coordinates. The result is the **epipolar constraint**:

$$
\boxed{\ \mathbf{x}_2^T E\,\mathbf{x}_1 = 0, \qquad E = [\mathbf{t}]_\times R\ }
$$

$E$ is the **essential matrix**. The depths are gone: the constraint links the two images directly, through the motion alone. Some texts write $\mathbf{x}\_1^T E\,\mathbf{x}\_2 = 0$; that is the same constraint with the roles of the two frames swapped, and $E$ transposed.

**$E\,\mathbf{x}\_1$ is the epipolar line in image 2.** A line in the image plane, $a u + b v + c = 0$, can be stored as the 3-vector $\mathbf{l} = (a, b, c)^T$. A point $\mathbf{x} = (u, v, 1)^T$ then lies on the line exactly when

$$
\mathbf{x}^T \mathbf{l} = a u + b v + c = 0
$$

Now fix a point $\mathbf{x}\_1$ in image 1. Multiplying it by $E$ gives a plain 3-vector, call it

$$
\mathbf{l}_2 = E\,\mathbf{x}_1 = \begin{bmatrix} a \\ b \\ c \end{bmatrix}
$$

and the epipolar constraint $\mathbf{x}\_2^T E\,\mathbf{x}\_1 = \mathbf{x}\_2^T \mathbf{l}\_2 = 0$ reads

$$
a\, u_2 + b\, v_2 + c = 0
$$

This is one linear equation in the two unknown coordinates $(u\_2, v\_2)$ of the match, so the possible matches form a line in image 2: $\mathbf{l}\_2$. It is the epipolar line for two reasons:

- **It is the epipolar plane seen by camera 2.** $\mathbf{l}\_2 = [\mathbf{t}]\_\times R\,\mathbf{x}\_1 = \mathbf{t} \times (R\,\mathbf{x}\_1)$ is perpendicular to both $\mathbf{t}$ (the baseline) and $R\,\mathbf{x}\_1$ (the ray of $\mathbf{x}\_1$), with both expressed in frame 2. So $\mathbf{l}\_2$ is the normal of the epipolar plane. The points of image 2 lying in that plane are those with $\mathbf{x}\_2^T \mathbf{l}\_2 = 0$: the line where the epipolar plane cuts the image plane.
- **It passes through the epipole.** The epipole $\mathbf{e}\_2$ is where camera 2 sees the center of camera 1, which is at $\mathbf{t}$ in frame 2, so $\mathbf{e}\_2 \propto \mathbf{t}$. Then $\mathbf{e}\_2^T \mathbf{l}\_2 \propto \mathbf{t}^T \big(\mathbf{t} \times R\,\mathbf{x}\_1\big) = 0$ for every $\mathbf{x}\_1$: all epipolar lines meet at $\mathbf{e}\_2$.

To draw it, solve for $v\_2$: $v\_2 = -(a\, u\_2 + c)/b$. Going the other way, $\mathbf{l}\_1 = E^T \mathbf{x}\_2$ is the epipolar line of $\mathbf{x}\_2$ in image 1. That is how the figure above draws its red lines.

**Toy example: a sideways step.** Let the camera translate 1 m to the right without rotating, $R = I$. A point then sits 1 m further left in the new camera frame, so $\mathbf{t} = (-1, 0, 0)^T$ and

$$
E = [\mathbf{t}]_\times = \begin{bmatrix} 0 & 0 & 0 \\ 0 & 0 & 1 \\ 0 & -1 & 0 \end{bmatrix},
\qquad
\mathbf{x}_2^T E\,\mathbf{x}_1 = \begin{bmatrix} u_2 & v_2 & 1 \end{bmatrix} \begin{bmatrix} 0 \\ 1 \\ -v_1 \end{bmatrix} = v_2 - v_1 = 0
$$

So $v_2 = v_1$: matches lie on the same row, which is the rectified case from the figure.

**Properties of $E$.**

- **Scale.** The constraint is $= 0$, so $E$ and $\alpha E$ express the same thing for any $\alpha \neq 0$. In particular the length of $\mathbf{t}$ cannot be recovered from the images (more on this below).
- **Rank 2.** $[\mathbf{t}]\_\times$ has rank 2 ($[\mathbf{t}]\_\times \mathbf{t} = \mathbf{0}$), and multiplying by a rotation does not change the rank. More precisely, the singular values of $[\mathbf{t}]\_\times$ are $(\lVert\mathbf{t}\rVert, \lVert\mathbf{t}\rVert, 0)$, so every essential matrix has two equal singular values and one zero: $E = U \operatorname{diag}(\sigma, \sigma, 0) V^T$.
- **5 degrees of freedom.** 3 for the rotation and 2 for the direction of the translation; its length is the lost scale.

**The fundamental matrix.** If the camera is not calibrated, we only have pixels $\mathbf{p} = K\mathbf{x}$. Substituting $\mathbf{x} = K^{-1}\mathbf{p}$ gives the same constraint in pixel coordinates:

$$
\mathbf{p}_2^T F\,\mathbf{p}_1 = 0, \qquad F = K_2^{-T} E\, K_1^{-1}
$$

$F$ is the **fundamental matrix**. It has 7 degrees of freedom:

1. A $3 \times 3$ matrix has **9** entries.
2. It is only defined up to scale, like $E$: multiplying $F$ by any non-zero scalar gives an equivalent matrix. That leaves **8**.
3. It has rank 2, so $\det F = 0$: in $F = K\_2^{-T} [\mathbf{t}]\_\times R\, K\_1^{-1}$, every factor is invertible except $[\mathbf{t}]\_\times$, which has rank 2 since $[\mathbf{t}]\_\times \mathbf{t} = \mathbf{0}$. This one polynomial constraint removes one more, leaving **7**.

$E$ has fewer degrees of freedom than $F$ because it also satisfies the equal-singular-value constraint, which only makes sense once $K$ has been divided out.

| Aspect | Fundamental matrix $F$ | Essential matrix $E$ |
| --- | --- | --- |
| Cameras | Uncalibrated | Calibrated |
| Works on | Pixel coordinates $\mathbf{p}$ | Normalized coordinates $\mathbf{x} = K^{-1}\mathbf{p}$ |
| Encodes | Intrinsics and relative pose | Relative pose only ($R$ and direction of $\mathbf{t}$) |
| Degrees of freedom | 7 | 5 |
| Minimal points | 7 (seven-point algorithm) | 5 (five-point algorithm) |
| Relation | $F = K_2^{-T} E\, K_1^{-1}$ | $E = K_2^T F\, K_1$ |

**Estimating $E$: the eight-point algorithm.** Written out entry by entry, the epipolar constraint is

$$
\mathbf{x}_2^T E\,\mathbf{x}_1 = \sum_{i,j} x_{2,i}\, E_{ij}\, x_{1,j} = 0
$$

which is linear in the nine entries of $E$. Stacking them row by row in a vector $\mathbf{e} = (E_{11}, E_{12}, E_{13}, E_{21}, \dots, E_{33})^T$, each correspondence contributes one row:

$$
\begin{bmatrix} u_2 u_1 & u_2 v_1 & u_2 & v_2 u_1 & v_2 v_1 & v_2 & u_1 & v_1 & 1 \end{bmatrix} \mathbf{e} = 0
$$

Eight correspondences give a system $A\,\mathbf{e} = \mathbf{0}$ with $A \in \mathbb{R}^{8 \times 9}$, which pins down $\mathbf{e}$ up to scale. With more points and noise, take the least-squares solution: the right singular vector of $A$ with the smallest singular value (see the [SVD and PCA post]({% post_url 2026-03-06-svd-and-pca %})). The result is generally not a valid essential matrix, so project it onto the closest one by fixing its singular values:

$$
E \approx U \operatorname{diag}(\sigma_1, \sigma_2, \sigma_3) V^T \quad\longrightarrow\quad E = U \operatorname{diag}(1, 1, 0) V^T
$$

The same algorithm estimates $F$ from pixels, where the last step sets only $\sigma_3 = 0$. For $F$, first shift and scale the pixels so they are centered with average distance $\sqrt{2}$ (Hartley's normalization); raw pixel values in the hundreds make $A$ badly conditioned.

**The five-point algorithm.** Since $E$ has only 5 degrees of freedom, 5 correspondences are enough. Nistér's **five-point algorithm** solves the resulting polynomial system and returns up to 10 candidate solutions. It has become the standard for 2D-to-2D motion estimation in the presence of outliers, because it is used inside RANSAC, and RANSAC's cost depends steeply on the number of points per sample. To draw at least one all-inlier sample of $s$ points with probability $p$, when a fraction $\varepsilon$ of the matches are outliers, RANSAC needs

$$
N = \frac{\log(1 - p)}{\log\big(1 - (1 - \varepsilon)^s\big)}
$$

iterations. With $p = 0.99$ and half of the matches wrong ($\varepsilon = 0.5$):

| Points per sample $s$ | 3 (P3P) | 4 (homography) | 5 (essential) | 7 (fundamental) | 8 (eight-point) |
| --- | --- | --- | --- | --- | --- |
| RANSAC iterations $N$ | 35 | 72 | 146 | 588 | 1177 |

Going from 8 points to 5 cuts the work by a factor of 8.

**Recovering $R$ and $\mathbf{t}$ from $E$.** Take the SVD $E = U \operatorname{diag}(1, 1, 0) V^T$, with signs chosen so that $\det U = \det V = 1$ (flipping the sign of $E$ is allowed, since it is only defined up to scale). With

$$
W = \begin{bmatrix} 0 & -1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix}
$$

there are two possible rotations and two possible translation directions:

$$
R \in \{\, U W V^T,\ U W^T V^T \,\}, \qquad \mathbf{t} \in \{\, +\mathbf{u}_3,\ -\mathbf{u}_3 \,\}
$$

where $\mathbf{u}\_3$ is the last column of $U$, the direction that $E^T$ sends to zero. All four combinations satisfy the epipolar constraint equally well. $-\mathbf{t}$ puts camera 2 on the other side of camera 1. The second rotation $R'$ differs from the first by a 180° turn about the baseline, which flips camera 2 to look backwards (the "twisted pair"). Only one combination is physically possible, and the test is **cheirality**: triangulate a point and keep the solution that puts it in front of both cameras, i.e. with positive depth in both. In practice, triangulate all inliers and keep the solution with the most points in front.

Here is the top-down view of one correspondence under all four solutions. The rays are the same measurements every time; only the assumed pose of camera 2 changes.

{% include figures/essential-four-solutions.html %}

**The missing scale.** If $(R, \mathbf{t})$ explains the images, so does $(R, \alpha\mathbf{t})$ together with a scene scaled by $\alpha$: a twice larger world seen from a twice longer step produces exactly the same pixels. **A monocular camera cannot observe the absolute scale of the translation.** Monocular visual odometry fixes $\lVert\mathbf{t}\rVert = 1$ for the first pair of frames, triangulates points at that arbitrary scale, and from then on tracks against those points (with PnP, below), which propagates the scale but lets it drift slowly. The cure is a second source of metric information: a stereo baseline, a known object size, wheel odometry, or an IMU. Observing metric scale, together with roll and pitch from gravity, is the main reason visual-inertial odometry such as VINS-Mono adds an IMU to a single camera.

**When 2D-to-2D fails.**

- **Pure rotation** ($\mathbf{t} = \mathbf{0}$). Then $E = [\mathbf{0}]\_\times R = 0$ and there is nothing to estimate: without a baseline there is no epipolar plane. The images are instead related by a homography (below).
- **Planar scenes.** If all points lie on one plane, the eight-point algorithm breaks down and the five-point algorithm becomes ambiguous. A homography is again the right model.
- **Small baselines.** Even when $\mathbf{t}$ is not exactly zero, a short step makes triangulation poorly conditioned, so most systems wait for enough parallax before initializing.

#### Homography

Besides the essential and fundamental matrices, there is a third two-view relation: the **homography** $H$, a $3 \times 3$ matrix that maps points on one plane to another plane in projective space. If all observed points lie on one plane (a wall, the floor, a table top), the motion can be estimated through a homography.

**Derivation.** Consider matched points $\mathbf{p}\_1$ and $\mathbf{p}\_2$ in images $I_1$ and $I_2$ that are projections of a point $\mathbf{P}$ on a plane. In the coordinates of camera 1, the plane is

$$
\mathbf{n}^T \mathbf{P} + d = 0
\qquad\Longleftrightarrow\qquad
-\frac{\mathbf{n}^T \mathbf{P}}{d} = 1
$$

with unit normal $\mathbf{n}$ and distance $d$ from the camera. The trick is to multiply $\mathbf{t}$ by this expression, which equals 1 on the plane, so that both terms become linear in $\mathbf{P}$. Writing $\simeq$ for equality up to a scale (the depths):

$$
\begin{aligned}
\mathbf{p}_2 &\simeq K\big(R\,\mathbf{P} + \mathbf{t}\big) \\
&= K\left(R\,\mathbf{P} + \mathbf{t} \cdot \Big(-\frac{\mathbf{n}^T \mathbf{P}}{d}\Big)\right) \\
&= K\left(R - \frac{\mathbf{t}\,\mathbf{n}^T}{d}\right) \mathbf{P} \\
&\simeq K\left(R - \frac{\mathbf{t}\,\mathbf{n}^T}{d}\right) K^{-1} \mathbf{p}_1
\end{aligned}
$$

where the last step uses $\mathbf{P} = Z_1 K^{-1} \mathbf{p}\_1$. The middle part is the homography, which maps pixels of image 1 directly to pixels of image 2:

$$
\mathbf{p}_2 \simeq H\, \mathbf{p}_1,
\qquad
H = K\left(R - \frac{\mathbf{t}\,\mathbf{n}^T}{d}\right) K^{-1}
$$

Note that this is a point-to-point map, not a point-to-line constraint like $E$: for a planar scene, knowing the plane removes the depth ambiguity.

The figure below shows what that means. A checkerboard lies on a plane that leans back, and a pole sticks out of it. Image 2 shows the true view from the second camera, and the orange circles are image-1 pixels sent through $H$ alone, with no depth. They land exactly on the checkerboard corners for every camera motion. The pole tip is not on the plane, so $H$ puts it in the wrong place, and the dashed red line is the error: this is **parallax**. Switch to a camera that only rotates and the error vanishes, because with $\mathbf{t} = \mathbf{0}$ the depth of a point no longer matters (see pure rotation below). The four colored corners are four matches, which is all it takes to pin down $H$.

{% include figures/homography-plane.html %}

**Estimation.** Written out with the scale factor $s$,

$$
s \begin{bmatrix} u' \\ v' \\ 1 \end{bmatrix} = H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix},
\qquad
H = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & h_{33} \end{bmatrix}
$$

$H$ is defined up to scale, so it has **8 degrees of freedom**. Dividing out $s$ leaves two equations per correspondence that are linear in the entries of $H$:

$$
u' \,(h_{31} u + h_{32} v + h_{33}) = h_{11} u + h_{12} v + h_{13},
\qquad
v' \,(h_{31} u + h_{32} v + h_{33}) = h_{21} u + h_{22} v + h_{23}
$$

so **4 points** (no three of them collinear) determine $H$. With more points, stack the equations and take the smallest right singular vector, exactly like the eight-point algorithm (this is the direct linear transform, DLT).

**Decomposition.** $H$ can be decomposed into the **rotation** $R$, the **translation** $\mathbf{t}/d$ (again only up to the scale of the scene, here the distance to the plane) and the **plane normal** $\mathbf{n}$. The decomposition yields up to four solutions; requiring the points to be in front of the camera rules out two, and the remaining two need extra information, such as a rough idea of the plane normal, to be told apart. OpenCV provides it as `cv::decomposeHomographyMat`.

**Pure rotation.** When the camera only rotates, $\mathbf{t} = \mathbf{0}$ and the plane drops out:

$$
H = K R K^{-1}
$$

This holds for every point, planar or not, at any depth. It is the degenerate case of the essential matrix, and the case the homography handles best. Applications:

- **Panorama stitching.** Rotate the camera about its center, and homographies align the images into a seamless panorama.
- **Image stabilization.** Hand shake is mostly rotation, so a homography per frame compensates it.
- **Augmented reality.** Placing virtual objects on a table, a floor, or a marker is a planar homography problem, and the decomposition gives the camera pose relative to the plane.

**Essential matrix or homography?** A monocular system does not know in advance whether the first frames see a general 3D scene or a plane, or whether the camera mostly rotated. ORB-SLAM, for example, estimates both a homography and a fundamental matrix in parallel during initialization, scores each by how well it explains the matches, and picks the homography when its share of the total score is above 0.45.

### 3D to 3D

If the feature correspondences are available in three dimensions in both frames, the motion can be estimated directly in 3D. This happens with a stereo camera, which can triangulate each feature from its left and right images to get a 3D point in every frame, or with an RGB-D camera or a LiDAR. The rigid transformation between the frames minimizes the 3D Euclidean distance between corresponding points:

$$
T_{2,1} = \arg\min_{T_{2,1}} \sum_i \big\lVert \mathbf{X}_{2,i} - T_{2,1} \mathbf{X}_{1,i} \big\rVert^2
$$

where $\mathbf{X}\_{1,i}$ and $\mathbf{X}\_{2,i}$ are the same map point expressed in frame 1 and frame 2. This is the **absolute orientation** problem, and unlike the 2D-to-2D case it has a closed-form solution (Arun et al., 1987; Umeyama, 1991):

1. **Remove the centroids.** Compute $\boldsymbol{\mu}\_1 = \frac{1}{N}\sum_i \mathbf{X}\_{1,i}$ and $\boldsymbol{\mu}\_2 = \frac{1}{N}\sum_i \mathbf{X}\_{2,i}$, and center the points: $\mathbf{q}\_i = \mathbf{X}\_{1,i} - \boldsymbol{\mu}\_1$, $\mathbf{q}\_i' = \mathbf{X}\_{2,i} - \boldsymbol{\mu}\_2$. Setting the derivative of the cost with respect to $\mathbf{t}$ to zero shows that the optimal translation maps one centroid onto the other, so the rotation can be solved on its own.
2. **Build the cross-covariance** $H = \sum_i \mathbf{q}\_i\, \mathbf{q}\_i'^T$ (a $3 \times 3$ matrix). Expanding the cost, the only term that depends on $R$ is $-2\sum_i \mathbf{q}\_i'^T R\, \mathbf{q}\_i = -2 \operatorname{tr}(R H)$, so we want the rotation that maximizes $\operatorname{tr}(R H)$.
3. **Take the SVD** $H = U \Sigma V^T$. The maximizer is

$$
R = V \begin{bmatrix} 1 & 0 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & \det(V U^T) \end{bmatrix} U^T,
\qquad
\mathbf{t} = \boldsymbol{\mu}_2 - R\, \boldsymbol{\mu}_1
$$

The middle matrix guards against a reflection ($\det R = -1$), which can happen with noisy or nearly planar data.

Three non-collinear points are the minimum: two points leave the rotation about the line through them free. The new camera pose follows by chaining the estimated $T_{2,1}$ with the previous pose. Centering in step 1 matters beyond the derivation: it is the same trick as centering data before PCA, and it keeps the problem well conditioned when the points are far from the origin. ICP solves exactly this problem in every iteration, after guessing the correspondences with nearest-neighbor search (see the [KD tree post]({% post_url 2024-10-01-kd-tree %}) and the [Gauss-Newton and ICP post]({% post_url 2025-11-03-hessian-gaussian-newton %})).

### 3D to 2D (perspective from n points, PnP)

The transformation $T_{2,1}$ can also be computed from **3D-to-2D** correspondences: a 3D map point $\mathbf{X}\_{1,i}$, known in frame 1, and the pixel $\mathbf{p}\_{2,i}$ where it is observed in the current frame 2. The motion minimizes the **reprojection error**:

$$
T_{2,1} = \arg\min_{T_{2,1}} \sum_i \big\lVert \mathbf{p}_{2,i} - \pi\big(T_{2,1} \mathbf{X}_{1,i}\big) \big\rVert^2,
\qquad
\pi(\mathbf{X}) = \frac{1}{Z} K \mathbf{X}
$$

This is the **perspective-n-point** problem (PnP). The difference from 3D-to-3D is what gets measured: 3D-to-3D compares triangulated 3D positions, while 3D-to-2D compares the raw image measurement with a prediction. As a result, **3D-to-2D is more accurate than 3D-to-3D when the 3D points come from images.**

The reason is how badly a stereo pair measures depth. Take a rectified pair with focal length $f$ (pixels) and baseline $b$. A point at depth $Z$ lands at $u_L = fX/Z$ in the left image and at $u_R = f(X - b)/Z$ in the right one. Their difference, the **disparity** $d$, gives the depth:

$$
d = u_L - u_R = \frac{f\, b}{Z}
\qquad\Longleftrightarrow\qquad
Z = \frac{f\, b}{d}
$$

Matching measures $d$ with a small error $\delta d$. To first order, the depth error is the slope of $Z(d)$ times that error, and substituting $d = fb/Z$ writes it in terms of depth:

$$
\delta Z \approx \left| \frac{\partial Z}{\partial d} \right| \delta d = \frac{f\, b}{d^2}\, \delta d = \frac{Z^2}{f\, b}\, \delta d
$$

Since disparity shrinks as $1/Z$, a fixed pixel error is a growing fraction of it: the relative error $\delta Z / Z = \delta d / d$ grows linearly with depth, so the absolute error grows with the square of the distance. The error across the line of sight, $\delta X \approx Z\, \delta u / f$, only grows linearly. With $f = 500$ px, $b = 0.1$ m and half a pixel of matching noise, a point at 1 m is off by about 1 cm in depth, but a point at 10 m is off by about 1 m. A triangulated point is therefore not a point but a long, thin region stretched along the viewing ray. Move the point away from the stereo pair and watch the region stretch:

{% include figures/stereo-depth-uncertainty.html %}

3D-to-3D alignment treats these points as if all three coordinates were equally reliable, so the noisy depths pull the solution around. The reprojection error is measured in the image, where the measurement noise actually lives, and it barely cares where along the ray the point sits: errors in depth change the projection only a little. This is why stereo visual odometry systems usually prefer 3D-to-2D over 3D-to-3D, and it is also how monocular visual odometry keeps going after the 2D-to-2D initialization: triangulate map points once, then localize every new frame against them with PnP.

**Solvers.** There are many solutions in the literature:

- **P3P.** The minimal case: 3 points determine the pose but give up to **four** solutions. A fourth point picks the right one. Being minimal, P3P is the usual choice inside RANSAC (35 iterations in the table above).
- **DLT.** Treat the $3 \times 4$ matrix $[R \mid \mathbf{t}]$ as 12 unknowns. Each correspondence gives 2 linear equations, so 6 points suffice. Simple, but it ignores that $R$ is a rotation and is less accurate.
- **EPnP.** Expresses all points as weighted sums of 4 virtual control points and solves for those, in time linear in the number of points. A good non-minimal solver for many points.
- **Iterative refinement.** Whatever produces the initial guess, the final answer comes from minimizing the reprojection error above with Gauss-Newton or Levenberg-Marquardt over all inliers. Extending the same cost to also move the 3D points, over many frames, is **bundle adjustment**.

### Summary

- **Essential matrix:** encapsulates the relative rotation and translation direction between two calibrated cameras, through $\mathbf{x}\_2^T E\,\mathbf{x}\_1 = 0$. Crucial in stereo vision and structure from motion.
- **Fundamental matrix:** the same constraint for uncalibrated cameras, in pixels. It gives the epipolar lines and is the foundation of stereo matching.
- **Homography:** a point-to-point map between two images when the scene is planar or the camera only rotates.
- **PnP:** the pose of a calibrated camera from 3D points in the world and their 2D projections in the image. P3P gives up to four solutions, and additional points select the correct one.
- **3D-3D pose estimation:** also known as the absolute orientation problem. It computes the rigid transformation that aligns two sets of 3D points, in closed form with an SVD.

| Problem | Input | Minimal points | Typical solver | Metric scale |
| --- | --- | --- | --- | --- |
| Essential matrix | 2D-2D, calibrated | 5 | Nistér five-point in RANSAC, eight-point | No, translation direction only |
| Fundamental matrix | 2D-2D, uncalibrated | 7 | Seven-point, normalized eight-point (more robust and widely used) | No |
| Homography | 2D-2D, planar scene or pure rotation | 4 | DLT | No, $\mathbf{t}/d$ only |
| PnP | 3D-2D | 3 | P3P in RANSAC, EPnP, then Gauss-Newton or LM | Yes, from the 3D points |
| Absolute orientation | 3D-3D | 3, not collinear | Closed-form SVD (Arun, Umeyama), ICP when matches are unknown | Yes |

A typical monocular visual odometry pipeline uses all of these in turn. It initializes from two frames with the essential matrix or a homography, triangulates the first map points at an arbitrary scale, localizes each new frame against the map with PnP in RANSAC, triangulates new points as they appear, and polishes poses and points with bundle adjustment. A stereo or RGB-D pipeline can skip the initialization and start directly with 3D-to-2D or 3D-to-3D.
