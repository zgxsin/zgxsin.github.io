---
title: "Differentiable Rendering: From Volume Rendering to NeRF"
published: false
date: 2026-08-02
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

## Inverse graphics

Computer graphics goes from a 3D scene to images: given geometry, materials, lights and a camera, it renders what the camera sees. **Inverse graphics** goes the other way: given images of a scene, it recovers a 3D representation of the scene. The standard test is **novel view synthesis**: from photos with known camera poses, render the scene from a viewpoint that nobody photographed. A method can only do this well if it has captured both the geometry and the appearance of the scene.

Every method in this post answers three questions:

1. **How is the scene represented?** As a voxel grid, a neural network, or a mix of both.
2. **How is the representation turned into an image?** This is the renderer, also called the forward map.
3. **How is the representation fitted to the photos?** Classically by triangulating matched features, today mostly by gradient descent through a differentiable renderer.

This post builds up the answer that made the field take off: represent the scene as a **radiance field**, render it with **volume rendering**, and fit it by gradient descent. That is **NeRF** (2020). Its successor, [3D Gaussian splatting](/2026/09/21/gaussian-splatting/), keeps the same rendering equation with a different representation. For geometric maps built from range sensors (occupancy, TSDF, ESDF), see [3D map representations](/2026/06/13/3d-map-representations/).

### The classical pipeline: SfM and MVS

The classical way to build a 3D model from photos is **photogrammetry**, which chains two steps:

- **Structure from motion (SfM)** matches features across images, estimates the camera poses, triangulates the matched features and refines everything with bundle adjustment. [COLMAP](https://colmap.github.io/) is the standard tool. The geometry behind it (epipolar constraint, triangulation) is covered in my post on [ego-motion estimation](/2023/06/30/ego-motion-estimation/), and bundle adjustment is a nonlinear least squares problem, see [Gauss-Newton and Levenberg-Marquardt](/2025/11/03/hessian-gaussian-newton/).
- **Multi-view stereo (MVS)** takes the poses as given and matches every pixel to densify the model, then a surface is meshed and textured.

| | Structure from motion (SfM) | Multi-view stereo (MVS) |
| --- | --- | --- |
| Estimates | Camera poses and 3D points together | Dense 3D geometry, poses given |
| Output | Sparse point cloud and camera poses | Dense point cloud or mesh |
| Uses | Pose estimation for robotics, AR, and as the first step of NeRF and 3DGS | Detailed 3D models, VR, visual effects |

Photogrammetry works, but it relies on matching, and matching breaks on textureless walls, shiny and transparent surfaces, thin structures and the sky. A textured mesh also cannot express view-dependent effects: a reflection is baked into the texture and looks wrong from every other angle. SfM points are **sparse** and **not very accurate**, so on its own SfM does not solve inverse graphics. It is still the starting point of both NeRF and Gaussian splatting, which take the SfM camera poses as given, and in the case of Gaussian splatting also the SfM points as initialization. On a robot, the SLAM poses can play the same role.

### Differentiable rendering

The modern approach is **analysis by synthesis**. Pick a scene representation with parameters $\theta$, and a renderer $\mathcal{R}$ that produces the image the scene would give from camera pose $\pi_k$. Then adjust $\theta$ until the rendered images match the captured ones:

$$
\theta^\ast = \arg\min_\theta \sum_k \big\lVert \mathcal{R}(\theta, \pi_k) - I_k \big\rVert^2
$$

This works with gradient descent only if the renderer is **differentiable** with respect to $\theta$. That requirement shapes everything else: rasterizing a triangle mesh is not differentiable in a useful way, because whether a pixel sees a triangle or the one behind it is a hard, discrete decision. Volumetric representations, where every point along a ray contributes a little, are smooth and differentiable, which is why they dominate.

{% include figures/differentiable-rendering-loop.html %}

## Fields: describing space instead of surfaces

Point clouds and meshes describe the surface. A **field** instead assigns a value to every point in space, $\Phi: \mathbb{R}^3 \to \mathbb{R}^n$, and the surface is a level set of the field. This is why fields are also called volumetric or implicit representations.

| Field | Value at a point $\mathbf{x}$ | Surface |
| --- | --- | --- |
| Occupancy | Probability that $\mathbf{x}$ is inside an object, in $[0, 1]$ | Level set at 0.5 |
| Signed distance (SDF) | Distance to the nearest surface, negative inside | Zero level set |
| Truncated SDF (TSDF) | SDF clipped to a band around the surface | Zero crossing |
| Radiance field | Volume density $\sigma \geq 0$ and color $\mathbf{c}$ | No hard surface; high density |

The field says *what* is stored. A separate choice is *how* the field is stored: in a discrete grid (voxels, see [3D map representations](/2026/06/13/3d-map-representations/#voxel-grids)), in a neural network, or in a mix of both. The next section covers the last two.

## Neural fields

A **neural field** stores a field in the weights of a neural network, usually a small multilayer perceptron (MLP) $\Phi\_\theta: \mathbb{R}^3 \to \mathbb{R}^n$ that is queried with a coordinate. Depending on what it outputs:

- **Occupancy networks and DeepSDF** (2019) learn occupancy or signed distance, and learned priors fill in unobserved parts of objects.
- **iSDF** and **NICE-SLAM / Co-SLAM** learn an SDF online from depth images, so a neural map can replace the TSDF in a SLAM system.
- **NeRF** learns density and view-dependent color, for photorealistic view synthesis ([below](#nerf-neural-radiance-fields)).

Its properties are the opposite of a voxel grid's:

- **Memory does not grow with resolution.** The field is continuous, and a few megabytes of weights can describe a whole scene.
- **Queries are slow.** Every query is a full forward pass through the network, which is expensive in compute and GPU memory when millions of points are needed per image.
- **No locality.** No subset of the weights corresponds to a region of space, so you cannot edit or delete one part of the scene, and you cannot run convolutions over it. For a robot map this also means updates are global: a new observation changes shared weights, and old parts of the map can be forgotten.
- **Adaptive resolution for free.** During optimization the network spends its capacity where the signal has high frequencies.

### Why a neural field is just an interpolator

Despite the name, a neural field has little to do with "intelligence". Jacot et al. (2018) showed that an infinitely wide MLP trained by gradient descent behaves like **kernel regression** with the **neural tangent kernel (NTK)**:

$$
f(\mathbf{x}) = \sum_{i=1}^{n} \left(\mathbf{K}^{-1}\mathbf{y}\right)_i\, k(\mathbf{x}_i, \mathbf{x}),
\qquad
k_{\text{NTK}}(\mathbf{x}_1, \mathbf{x}_2) = \big\langle \nabla_\theta f_{\theta_0}(\mathbf{x}_1),\, \nabla_\theta f_{\theta_0}(\mathbf{x}_2) \big\rangle
$$

where $\mathbf{K}\_{ij} = k(\mathbf{x}\_i, \mathbf{x}\_j)$ over the training points and $\mathbf{y}$ holds their target values. In other words, a neural field interpolates its training samples according to a fixed, fairly simple rule. It is about as "smart" as a voxel grid with a clever interpolation kernel. This view also explains a known weakness: the NTK of a plain MLP on raw coordinates is a smooth, low-pass kernel, so the network struggles to fit high-frequency detail. NeRF's positional encoding, covered below, fixes exactly that.

### Hybrid representations

**Hybrid representations** store features in a grid and use a small network to decode them. To query $\mathbf{x}$, interpolate the feature vectors at the surrounding grid vertices, then pass the result through a tiny MLP. The grid gives locality and fast lookups, the network "super-resolves" the grid and acts as a learned interpolation kernel. It trades memory against compute, and gets the best of both: fast and continuous.

- **Instant-NGP** (2022) uses a multiresolution hash grid: feature tables at many resolutions, indexed by hashing the vertex coordinates, the same idea as [voxel hashing](/2026/06/13/3d-map-representations/#sparse-voxel-data-structures). It brought NeRF training from days to minutes.
- **Plenoxels** (2022) drops the network entirely: a sparse voxel grid stores density and spherical-harmonic color coefficients directly, and still matches NeRF quality. The network was never the essential part; the differentiable volume rendering was.
- **TensoRF** (2022) factorizes the feature grid into products of low-rank vectors and matrices to save memory.

## Rendering a field

There are two ways to render a field, depending on what the field stores.

### Sphere tracing for signed distance fields

If the field is an SDF, the value $\phi(\mathbf{x})$ is the distance to the nearest surface in *any* direction. So a sphere of radius $\phi(\mathbf{x})$ around $\mathbf{x}$ contains no surface, and the ray can safely jump forward by exactly that distance:

$$
\mathbf{x}_{k+1} = \mathbf{x}_k + \phi(\mathbf{x}_k)\, \mathbf{d}
$$

stopping when $\phi(\mathbf{x}\_k) < \epsilon$. This is **sphere tracing**. It never steps through a surface, it converges to the first hit, and the total distance traveled is the depth of that pixel. A second network then gives the color at the hit point. Methods such as Scene Representation Networks (SRN) and IDR render this way, and the whole chain is differentiable. Its weakness is that gradients only reach the field at the single hit point, which makes it hard for the optimization to create a surface where none exists yet, or to change the topology.

### Volume rendering

If the field is a radiance field, the scene is treated like a cloud of tiny particles with **volume density** $\sigma(\mathbf{x}) \geq 0$ and color $\mathbf{c}(\mathbf{x})$, so the field has the signature $\Phi: \mathbb{R}^3 \to \mathbb{R}^+ \times \mathbb{R}^3$. Cast a ray from the camera center $\mathbf{o}$ in direction $\mathbf{d}$:

$$
\mathbf{r}(t) = \mathbf{o} + t\,\mathbf{d}
$$

The density is defined so that the probability that the ray hits a particle in a short interval around $t$ is $\sigma(t)\,dt$, writing $\sigma(t)$ for $\sigma(\mathbf{r}(t))$. If the ray hits a particle at $t$, the pixel gets the color $\mathbf{c}(t)$ of that particle. But that only counts if $t$ is the *first* hit, so we also need the **transmittance** $T(t)$: the probability that the ray traveled from the camera to $t$ without hitting anything.

**Transmittance.** To survive to $t + dt$, the ray must survive to $t$ and then not hit anything in $[t, t + dt]$:

$$
T(t + dt) = T(t)\,\big(1 - \sigma(t)\,dt\big)
$$

Rearranging gives a differential equation, which integrates to an exponential:

$$
\frac{T(t + dt) - T(t)}{dt} = -T(t)\,\sigma(t)
\;\;\Rightarrow\;\;
\frac{T'(t)}{T(t)} = -\sigma(t)
\;\;\Rightarrow\;\;
T(t) = \exp\left(-\int_0^t \sigma(s)\, ds\right)
$$

This is the Beer-Lambert law: light decays exponentially with the accumulated density along the path.

**Where the ray stops.** $1 - T(t)$ is the probability that the ray has hit something before $t$, which is a cumulative distribution function. Its derivative is the probability density of the first hit:

$$
p(t) = \frac{d}{dt}\big(1 - T(t)\big) = T(t)\,\sigma(t)
$$

The pixel color is the expected color at the first hit:

$$
\boxed{\ C(\mathbf{r}) = \int_{t_n}^{t_f} T(t)\,\sigma(t)\,\mathbf{c}(t)\, dt\ }
$$

integrated between a near plane $t_n$ and a far plane $t_f$. If the ray reaches the far plane without hitting anything, the background shows through with weight $T(t_f)$.

**Quadrature.** The integral has no closed form for a general field, so split $[t_n, t_f]$ into $n$ segments with endpoints $t_1, \dots, t_{n+1}$ and lengths $\delta_i = t_{i+1} - t_i$, and assume the density and color are constant within each segment, $\sigma_i$ and $\mathbf{c}\_i$. Careful: constant density does **not** mean constant transmittance within a segment. When $\sigma_i$ is large, the front of the segment blocks the back of it. Within segment $i$, the transmittance is what survived all previous segments times what survived the part of segment $i$ before $t$:

$$
T(t) = T_i\, e^{-\sigma_i (t - t_i)}, \qquad T_i = \exp\left(-\sum_{j=1}^{i-1} \sigma_j \delta_j\right)
$$

$T_i$ answers "how much light is blocked by all previous segments". Now the integral over each segment can be done exactly:

$$
\begin{aligned}
C &\approx \sum_{i=1}^{n} \int_{t_i}^{t_{i+1}} T(t)\,\sigma_i\,\mathbf{c}_i\, dt
= \sum_{i=1}^{n} T_i\,\sigma_i\,\mathbf{c}_i \int_{t_i}^{t_{i+1}} e^{-\sigma_i (t - t_i)}\, dt \\
&= \sum_{i=1}^{n} T_i\,\sigma_i\,\mathbf{c}_i\, \frac{1 - e^{-\sigma_i \delta_i}}{\sigma_i}
= \sum_{i=1}^{n} T_i\, \big(1 - e^{-\sigma_i \delta_i}\big)\, \mathbf{c}_i
\end{aligned}
$$

The $\sigma_i$ cancels. Define the **opacity** of segment $i$ as $\alpha_i = 1 - e^{-\sigma_i \delta_i}$, the probability that the ray stops inside it. Then $e^{-\sigma_j \delta_j} = 1 - \alpha_j$, and the result is the volume rendering equation in its discrete form:

$$
\boxed{\ C \approx \sum_{i=1}^{n} T_i\, \alpha_i\, \mathbf{c}_i, \qquad T_i = \prod_{j=1}^{i-1} (1 - \alpha_j), \qquad \alpha_i = 1 - e^{-\sigma_i \delta_i}\ }
$$

Each sample contributes its color with weight $w_i = T_i \alpha_i$: it must be opaque itself ($\alpha_i$), and not hidden by what is in front of it ($T_i$). This is exactly **front-to-back alpha compositing**, the "over" operator graphics has used since the 1980s, which is why the same formula shows up again in [Gaussian splatting](/2026/09/21/gaussian-splatting/). The same weights give the **expected depth** of the pixel, $D = \sum_i w_i t_i$, and their sum $\sum_i w_i = 1 - T_{n+1}$ is how opaque the pixel is.

In the figure below, the blue cloud is semi-transparent and the red object behind it is nearly solid. Raise the density of the cloud: the transmittance drops earlier, the cloud's samples take more weight, and the red object fades from the pixel. With few samples, the pixel color is a coarse approximation; with more it converges.

{% include figures/volume-rendering-ray.html %}

Why volume rendering is so good for optimization: every sample along the ray receives a gradient, in proportion to its weight. There is no hard visibility decision. If the color is wrong, the optimizer can add density in front, remove density behind, or change the colors, all smoothly.

Note the link to [occupancy mapping](/2026/06/13/3d-map-representations/#occupancy-mapping): a range sensor's ray also passes through free space and ends at a hit, and the occupancy update is the discrete, probabilistic version of the same ray model. Depth supervision from LiDAR or a depth camera plugs directly into the expected depth $D$ above.

### What volume rendering leaves out

Volume rendering is a simplified model of light transport. The full physical **rendering equation** says the radiance leaving point $\mathbf{x}$ in direction $\boldsymbol{\omega}\_o$ is what the point emits plus what it reflects from all incoming directions $\boldsymbol{\omega}\_i$ over the hemisphere $\Omega$:

$$
L_o(\mathbf{x}, \boldsymbol{\omega}_o) = L_e(\mathbf{x}, \boldsymbol{\omega}_o) + \int_\Omega f_r(\mathbf{x}, \boldsymbol{\omega}_i, \boldsymbol{\omega}_o)\, L_i(\mathbf{x}, \boldsymbol{\omega}_i)\, (\boldsymbol{\omega}_i \cdot \mathbf{n})\, d\boldsymbol{\omega}_i
$$

where $f_r$ is the material's reflectance function (the BRDF) and $\mathbf{n}$ the surface normal. A radiance field with color $\mathbf{c}(\mathbf{x})$ throws away the integral and keeps only emission, $L_o = L_e(\mathbf{x})$: every particle glows with its own fixed color. So there are no true reflections, no inter-reflections, no materials, and no relighting. The usual halfway fix, used by NeRF and Gaussian splatting, is to let the color depend on the viewing direction, $\mathbf{c}(\mathbf{x}, \mathbf{d})$, while keeping the density $\sigma(\mathbf{x})$ independent of it. That reproduces specular highlights and reflections as seen from the training views, but they are baked in: you cannot move the light.

## NeRF: neural radiance fields

NeRF (Mildenhall et al., ECCV 2020) parameterizes the radiance field **densely**, at every point in space, with an MLP, and renders it with volume rendering.

### Model

The network maps a position and a viewing direction to a density and a color:

$$
F_\theta: (\mathbf{x}, \mathbf{d}) \mapsto (\sigma, \mathbf{c})
$$

The architecture enforces the halfway fix above. The position goes through 8 fully connected layers of 256 channels (with a skip connection that re-injects the input at the fifth layer), which output the density $\sigma$ and a feature vector. Only then is the viewing direction concatenated, and one more layer of 128 channels outputs the color. So the density, which is the geometry, cannot depend on the viewing direction, which forces the geometry to be consistent across views, while the color can.

### Positional encoding

Fed raw coordinates, an MLP produces blurry results. Neural networks have a **spectral bias** towards smooth, low-frequency functions, which is the NTK observation from above. NeRF fixes this by mapping each coordinate to sines and cosines of increasing frequency before the network:

$$
\gamma(p) = \big(\sin(2^0 \pi p), \cos(2^0 \pi p), \dots, \sin(2^{L-1} \pi p), \cos(2^{L-1} \pi p)\big)
$$

with $L = 10$ frequencies for the position and $L = 4$ for the direction. Nearby points that were almost identical as inputs now differ strongly in the high-frequency components, so the network can represent sharp edges and fine texture. Tancik et al. (2020) later explained this as changing the NTK from a low-pass kernel into one with a tunable bandwidth.

### Training

NeRF is fitted to **one scene at a time**; there is no pretraining and no generalization to other scenes. Each training step:

1. Sample a batch of pixels (4096 rays) at random from all training images, and build each pixel's ray from the camera pose.
2. Render each ray with the volume rendering quadrature.
3. Compare with the true pixel colors and backpropagate the squared error into the network weights:

$$
\mathcal{L} = \sum_{\mathbf{r}} \big\lVert \hat{C}(\mathbf{r}) - C(\mathbf{r}) \big\rVert^2
$$

The original NeRF uses no depth at all; depth supervision from LiDAR or depth cameras is an optional extra that speeds up training and improves geometry. The samples along each ray are **stratified**: the range $[t_n, t_f]$ is split into $N$ equal bins and one point is drawn uniformly inside each bin. Since the sample positions change every iteration, the network sees the whole continuous ray over training rather than a fixed set of points.

```python
import torch

def render_rays(field, rays_o, rays_d, near, far, n_samples=64):
    """Volume-render a batch of rays. rays_o, rays_d: (B, 3), rays_d of unit length."""
    bins = torch.linspace(near, far, n_samples + 1)
    lower, upper = bins[:-1], bins[1:]
    t = lower + (upper - lower) * torch.rand(rays_o.shape[0], n_samples)  # stratified, (B, N)

    pts = rays_o[:, None, :] + t[..., None] * rays_d[:, None, :]          # (B, N, 3)
    sigma, rgb = field(pts, rays_d[:, None, :].expand_as(pts))            # (B, N), (B, N, 3)

    delta = torch.diff(t, dim=-1)
    delta = torch.cat([delta, torch.full_like(delta[:, :1], 1e10)], dim=-1)
    alpha = 1.0 - torch.exp(-sigma * delta)
    # T_i = prod_{j<i} (1 - alpha_j), an exclusive cumulative product.
    ones = torch.ones_like(alpha[:, :1])
    trans = torch.cumprod(torch.cat([ones, 1.0 - alpha + 1e-10], dim=-1), dim=-1)[:, :-1]
    weights = trans * alpha

    color = (weights[..., None] * rgb).sum(dim=1)
    depth = (weights * t).sum(dim=1)
    return color, depth, weights

for step in range(n_steps):
    rays_o, rays_d, target = sample_random_rays(images, poses, batch_size=4096)
    color, _, _ = render_rays(nerf, rays_o, rays_d, near, far)
    loss = ((color - target) ** 2).mean()
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

### Hierarchical sampling

Most samples along a ray land in empty space or behind the first surface, where they contribute nothing. NeRF trains two networks at once to spend samples where they matter:

1. A **coarse** network is evaluated at $N_c = 64$ stratified samples.
2. Its weights $w_i = T_i \alpha_i$, normalized to sum to one, form a piecewise-constant probability density along the ray that peaks where the surface is.
3. $N_f = 128$ more samples are drawn from that density by inverse transform sampling, and the **fine** network is evaluated at all $64 + 128$ points to produce the final color.

Both networks are trained with the photometric loss. This is importance sampling: the integral is estimated with samples concentrated where the integrand is large.

### Limitations and follow-ups

The original NeRF produced a breakthrough in quality, with only about 5 MB of weights per scene, but it has clear limitations:

- **Slow.** Training takes one to two days on a single GPU, and rendering one image takes tens of seconds, because every pixel needs about 200 network evaluations.
- **One static scene per model.** Nothing moving, no generalization.
- **Needs accurate poses**, usually from COLMAP.
- **Artifacts:** "floaters" of spurious density in poorly observed space, aliasing when the rendering resolution differs from training, and trouble with unbounded outdoor scenes.
- **Implicit:** you cannot select or edit part of the scene, and extracting a surface (threshold the density, then marching cubes) gives noisy meshes. Geometry is often worse than the images suggest, and there is no explicit free space.

A large body of follow-up work addresses these:

- **Mip-NeRF** and **Mip-NeRF 360** render cones instead of rays to fix aliasing, and handle unbounded scenes by contracting far-away space. **Zip-NeRF** combines this with hash grids.
- **Instant-NGP** and **Plenoxels** (see [hybrid representations](#hybrid-representations)) make training take minutes.
- **NeRF in the Wild** handles photo collections with varying lighting and transient objects by giving each image a learned appearance embedding.
- **BARF** refines inaccurate camera poses jointly with the scene.
- **NeuS** and **VolSDF** volume-render an SDF instead of a free density, which gives clean surfaces.
- **Light field networks** skip volume rendering altogether and map a ray directly to its color, one network evaluation per pixel, at the cost of no built-in 3D consistency.

## What comes next

NeRF showed that differentiable volume rendering of a radiance field reconstructs scenes with remarkable quality. Its weakness is the dense parameterization: every pixel needs hundreds of network evaluations, and the network has no locality. [3D Gaussian splatting](/2026/09/21/gaussian-splatting/) keeps the volume rendering equation but parameterizes the radiance field sparsely with explicit Gaussians, which brings rendering to real time.

## References

1. [Machine Learning for Inverse Graphics (MIT 6.S980)](https://www.scenerepresentations.org/courses/2023/fall/inverse-graphics/), Vincent Sitzmann
2. [NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis](https://arxiv.org/abs/2003.08934), Mildenhall et al., ECCV 2020
3. [Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains](https://arxiv.org/abs/2006.10739), Tancik et al., 2020
4. [Neural Tangent Kernel: Convergence and Generalization in Neural Networks](https://arxiv.org/abs/1806.07572), Jacot et al., 2018
5. [Instant Neural Graphics Primitives with a Multiresolution Hash Encoding](https://nvlabs.github.io/instant-ngp/), Müller et al., 2022
6. [Plenoxels: Radiance Fields without Neural Networks](https://alexyu.net/plenoxels/), Fridovich-Keil et al., 2022
