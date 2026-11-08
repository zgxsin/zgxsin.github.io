---
title: "3D Gaussian Splatting: Real-Time Radiance Fields"
published: false
date: 2026-09-21
author: zgxsin
---

* TOC
{:toc}

3D Gaussian Splatting (3DGS, Kerbl et al., SIGGRAPH 2023) reconstructs a scene from photos with known camera poses and renders it from new viewpoints in real time, at a quality equal to or better than the best NeRFs, after tens of minutes of training.

It builds on two ideas covered in my post on [differentiable rendering and NeRF](/2026/08/02/differentiable-rendering-nerf/): fit a scene representation to images by gradient descent through a differentiable renderer, and render a **radiance field** (density and view-dependent color at every point) with **volume rendering**. The one equation to keep in mind is the discrete volume rendering formula, which composites the samples along a camera ray front to back:

$$
C = \sum_{i} T_i\, \alpha_i\, \mathbf{c}_i, \qquad T_i = \prod_{j=1}^{i-1} (1 - \alpha_j)
$$

where $\alpha_i$ is the opacity of sample $i$, $\mathbf{c}_i$ its color and $T_i$ the transmittance, the fraction of light that reaches it. NeRF evaluates a neural network at hundreds of samples per ray to get $\alpha_i$ and $\mathbf{c}_i$. Gaussian splatting gets them from a set of explicit Gaussians instead, which is what makes it fast.

## Key idea: a sparse radiance field

NeRF parameterizes the radiance field everywhere, yet most of space is empty. Gaussian splatting parameterizes it **only where the density is nonzero**: the scene is a set of millions of 3D Gaussian blobs floating in space, each with its own position, shape, opacity and color. Space between the blobs has zero density and costs nothing to render. And because each Gaussian has a closed-form shape, we know directly which Gaussians a pixel's ray passes through, instead of blindly sampling points along the ray and asking a network what is there.

{% include figures/nerf-vs-splat-ray.html %}

## The parameters of a Gaussian

Each Gaussian $i$ is a 3D density with mean $\boldsymbol{\mu}\_i$ and covariance $\Sigma_i$:

$$
G_i(\mathbf{x}) = \exp\left(-\tfrac{1}{2} (\mathbf{x} - \boldsymbol{\mu}_i)^T \Sigma_i^{-1} (\mathbf{x} - \boldsymbol{\mu}_i)\right)
$$

The covariance makes the Gaussian **anisotropic**: a flat disc can cover a wall with one Gaussian, and a long needle can cover a thin edge. But $\Sigma$ cannot be optimized directly, because gradient descent would quickly make it non-positive-definite, which is not a valid covariance. So the covariance is built from a rotation $R$ and a diagonal scaling matrix $S$:

$$
\Sigma = R\, S\, S^T R^T
$$

which is the eigendecomposition of $\Sigma$ in reverse: $R$ holds the principal axes and the scales $s_k$ are the standard deviations along them. Any rotation and any scales give a valid covariance. The figure shows the 2D version, where $R$ is a rotation by an angle.

{% include figures/gaussian-covariance.html %}

In 3D, the rotation is stored as a unit quaternion. In total, each Gaussian has 59 parameters:

| Parameter | Numbers | Activation |
| --- | --- | --- |
| Position $\boldsymbol{\mu}$ | 3 | none |
| Rotation (quaternion $\mathbf{q}$) | 4 | normalized to unit length |
| Scale $\mathbf{s}$ | 3 | exponential, so scales stay positive |
| Opacity $o$ | 1 | sigmoid, so it stays in $(0, 1)$ |
| Color (spherical harmonics, degree 3) | 48 | none |

## View-dependent color with spherical harmonics

The color must depend on the viewing direction $\mathbf{d}$ to show highlights and reflections. Instead of a network, each Gaussian stores coefficients of **spherical harmonics** $Y_l^m$, the Fourier basis for functions on a sphere:

$$
\mathbf{c}_i(\mathbf{d}) = \sum_{l=0}^{3} \sum_{m=-l}^{l} \mathbf{k}_{i,l}^m\, Y_l^m(\mathbf{d})
$$

Degree 0 is a single constant, the diffuse color. Each higher degree adds finer angular detail. Degree 3 has $1 + 3 + 5 + 7 = 16$ basis functions per color channel, so $3 \times 16 = 48$ numbers. Training starts with degree 0 only and unlocks one more degree every 1000 iterations, so the optimizer gets the base color right before it explains the remaining error with view dependence.

## Rendering: project, then alpha-blend

**Projection.** A 3D Gaussian seen through a perspective camera is approximately a 2D Gaussian on the image, a technique called EWA splatting (Zwicker et al., 2001). The mean projects like any point. The covariance is transformed with the camera rotation $W$ and with $J$, the Jacobian of the perspective projection linearized at the Gaussian's center:

$$
\Sigma' = J\, W\, \Sigma\, W^T J^T
$$

The top-left $2 \times 2$ block of $\Sigma'$ is the covariance of the 2D Gaussian on the image. The linearization is the approximation: it is exact for the center and good as long as the Gaussian is small compared with its distance from the camera.

**Blending.** For a pixel $\mathbf{p}$, the opacity of Gaussian $i$ is its learned opacity times its 2D Gaussian evaluated at the pixel:

$$
\alpha_i = o_i \exp\left(-\tfrac{1}{2} (\mathbf{p} - \boldsymbol{\mu}'_i)^T \Sigma_i'^{-1} (\mathbf{p} - \boldsymbol{\mu}'_i)\right)
$$

and with the Gaussians that overlap the pixel sorted by depth, front to back, the pixel color is

$$
C = \sum_{i} \mathbf{c}_i\, \alpha_i \prod_{j=1}^{i-1} (1 - \alpha_j)
$$

**This is the same formula as [NeRF's volume rendering](/2026/08/02/differentiable-rendering-nerf/#volume-rendering).** The only difference is where $\alpha_i$ comes from: in NeRF it is the density of a sampled point integrated over a ray segment, in Gaussian splatting it is read off a closed-form 2D Gaussian. The volume rendering integral is computed without ever sampling a single 3D point in space.

One approximation is hidden in the sort: each Gaussian gets a single depth, that of its center. When two Gaussians overlap in depth, their order can flip as the camera moves, which can cause "popping". Later work (StopThePop, 3D Gaussian ray tracing) sorts per pixel or traces rays to remove it.

## The tile-based rasterizer

The renderer is what makes Gaussian splatting fast. It is a custom CUDA rasterizer, not a ray tracer:

1. **Cull.** Discard Gaussians outside the view frustum or too close to the camera.
2. **Project** every remaining Gaussian to 2D as above, and compute a square bounding box of three standard deviations around it.
3. **Assign to tiles.** The image is split into 16 × 16 pixel tiles. Each Gaussian is duplicated once for every tile its bounding box overlaps, with a 64-bit key: tile ID in the high bits, depth in the low bits.
4. **Sort once.** A single GPU radix sort of all keys orders the Gaussians by tile, and by depth within each tile. There is no per-pixel sorting.
5. **Blend per tile.** One thread block handles one tile and loads its list into shared memory. Each thread handles one pixel and walks the list front to back, accumulating color and transmittance, and stops as soon as the pixel is nearly opaque ($T < 10^{-4}$).

{% include figures/splat-tile-rasterizer.html %}

The backward pass for training walks the same lists back to front. Because each pixel only stored its final transmittance and the number of Gaussians it used, the intermediate transmittances can be recovered by dividing out each $(1 - \alpha_j)$, so memory stays small.

## Optimization

Training follows the differentiable rendering loop:

1. **Initialize** one Gaussian per SfM point (or LiDAR point), with the point's color and an isotropic scale set from the distance to its nearest neighbors. Random initialization also works, but worse.
2. **Render** a training view with the rasterizer.
3. **Compute the loss** against the photo, a mix of L1 error and a structural similarity term:

   $$
   \mathcal{L} = (1 - \lambda)\, \mathcal{L}_1 + \lambda\, \mathcal{L}_{\text{D-SSIM}}, \qquad \lambda = 0.2
   $$

4. **Update** all Gaussian parameters with Adam.
5. **Adapt the density**: periodically add and remove Gaussians, see below.

The default schedule runs 30,000 iterations. The main difficulty is that this optimization is badly non-convex: a Gaussian cannot "jump" to where it is needed, it can only slide along its gradient, so the optimization easily gets stuck in local minima. The two fixes are the point cloud initialization, which starts the Gaussians near the right places, and the adaptive density control.

## Adaptive density control

A fixed set of Gaussians cannot fit both large uniform areas and fine detail. So every 100 iterations (from iteration 500 to 15,000), the optimizer looks at Gaussians whose view-space position gradient is large on average (above 0.0002), a sign that the region is not well reconstructed:

- **Clone** a small Gaussian in an under-reconstructed region: copy it and move the copy along the gradient to cover the missing geometry.
- **Split** a large Gaussian in an over-reconstructed region, one that covers detail it cannot express: replace it with two Gaussians sampled from it, with their scales divided by 1.6.
- **Prune** Gaussians whose opacity has fallen below a threshold, or that have become very large in world space.

Every 3000 iterations, all opacities are also reset close to zero. The optimizer then raises the opacity again only for the Gaussians that are needed, and the rest get pruned. This removes floaters near the cameras that would otherwise keep growing.

{% include figures/density-control.html %}

A typical scene ends up with one to several million Gaussians.

## Strengths and weaknesses

Strengths:

- **Real-time rendering** of photorealistic scenes, typically above 100 fps at 1080p, also in a web browser.
- **Fast training**, roughly 30 to 45 minutes per scene on one GPU.
- **Explicit and local:** individual Gaussians can be selected, moved, deleted or merged with another scene, which is impossible with a neural field. Like points and surfels, they can be added where new parts of the scene are observed and moved after a loop closure.
- **Initialized from geometry:** a LiDAR or SfM point cloud is a natural starting point, so Gaussian maps fit well on top of an existing SLAM system.
- **Extensible:** semantic or language features can be attached to each Gaussian and rendered the same way as color.
- **Handles view-dependent effects** and semi-transparency that a textured mesh cannot.

Weaknesses:

- **Memory and storage.** Millions of Gaussians of 59 floats each come to hundreds of megabytes up to over 1 GB per scene, roughly 4 GB of GPU memory to view and more than 12 GB to train a large scene. NeRF stores a scene in a few megabytes.
- **Artifacts** in views far from the training trajectory: floaters, blurry or needle-shaped Gaussians.
- **Geometry is not a surface.** The Gaussians reproduce the appearance, but they do not lie exactly on the surface, so depth and normals extracted from them are noisy. **2D Gaussian Splatting** (2DGS) flattens them into oriented discs, very much like surfels, which gives much better surfaces and meshes.
- **No free space**, like NeRF and meshes: the absence of Gaussians does not distinguish free from unobserved.
- **Depends on good poses** and initialization, and on fairly dense coverage of the scene.
- **Not compatible with standard graphics pipelines** built around meshes, though support is growing.
- **Static** and **baked lighting**, the same as NeRF.

## NeRF versus Gaussian splatting

The course I followed (MIT 6.S980, Machine Learning for Inverse Graphics) describes any 3D inverse graphics method by four parts: how the field is parameterized, what it models, how it is rendered (the forward map), and how it is fitted (the inference method). In those terms, the two methods differ in the parameterization and share almost everything else:

| | NeRF | 3D Gaussian splatting |
| --- | --- | --- |
| Field parameterization | Dense: an MLP queried anywhere in space | Sparse: millions of explicit 3D Gaussians |
| Geometry and appearance | Density $\sigma(\mathbf{x})$, view-dependent color $\mathbf{c}(\mathbf{x}, \mathbf{d})$ | Per Gaussian: opacity, covariance, spherical-harmonic color |
| Forward map | Ray marching with volume rendering quadrature | Projection to 2D, tile rasterization, alpha blending |
| Inference | Per-scene gradient descent | Per-scene gradient descent plus density control |
| Rendering speed | Tens of seconds per frame (original) | Real time, often above 100 fps |
| Storage | About 5 MB of weights | Hundreds of MB to over 1 GB |
| Editing and map updates | Hard, no locality | Easy, Gaussians are explicit |
| Surface extraction | Threshold density and run marching cubes, noisy | Not direct; use variants such as 2DGS |

The 3DGS paper compared the main methods on the Mip-NeRF 360 dataset of large indoor and outdoor scenes, on one A6000 GPU:

| Method | Training time | Rendering speed | Storage | Quality (PSNR) |
| --- | --- | --- | --- | --- |
| Plenoxels | 25 min | 6.8 fps | 2.1 GB | 23.1 dB |
| Instant-NGP (large) | 7.5 min | 9.4 fps | 48 MB | 25.6 dB |
| Mip-NeRF 360 | 48 h | 0.06 fps | 8.6 MB | 27.7 dB |
| 3D Gaussian splatting | 41 min | 134 fps | 734 MB | 27.2 dB |

Gaussian splatting matches the best NeRF in quality, renders more than 2000 times faster, and trains about 70 times faster, at the price of about 100 times more storage.

## Gaussian splatting in robotics

A robot needs two different kinds of maps:

- **Maps for the robot** to localize, plan and avoid collisions need metric, reliable geometry and fast queries ("is this voxel free?"). Point clouds, occupancy grids, TSDF or ESDF voxel maps (voxblox, nvblox) and elevation maps remain the right tools, see [3D map representations](/2026/06/13/3d-map-representations/). Their appearance does not matter.
- **Maps for people**, such as an operator who inspects a site, places waypoints and inspection points, or reviews a change over time, benefit from photorealism. Here Gaussian splatting is very attractive: it renders in real time, even in a browser, and shows gauges, labels and thin structures that a coarse mesh loses. A practical setup runs a high-fidelity mapping process in parallel with SLAM: SLAM provides localization, and its poses feed the photorealistic reconstruction.

### Gaussian splatting in SLAM, and open problems

Gaussian splatting is moving into SLAM itself. **SplaTAM**, **Photo-SLAM** and **Gaussian Splatting SLAM (MonoGS)** track the camera against the Gaussian map while building it, and **LIV-GaussMap** fuses LiDAR, IMU and camera so the LiDAR provides accurate geometry and initialization and the camera the appearance. Open problems for real deployments include:

- **Large scenes:** gigabytes per scene call for compression, level of detail and streaming parts of the map in and out of memory. Hierarchical 3DGS and city-scale methods address this.
- **Multi-session maps:** lighting, weather and objects change between visits, and the baked-in lighting makes merging sessions hard.
- **Unobserved regions:** a robot never sees every surface. Generative priors such as diffusion models (ReconFusion) fill in plausible content, and feed-forward models (pixelSplat, MVSplat) predict Gaussians from a few images in one network pass instead of per-scene optimization.
- **Geometry accuracy**, for which surface-aligned variants such as 2DGS and PGSR are the current answer.

### Tools

COLMAP for poses, the [reference 3DGS implementation](https://github.com/graphdeco-inria/gaussian-splatting), [nerfstudio](https://docs.nerf.studio/) (both `nerfacto` and `splatfacto`), the [gsplat](https://github.com/nerfstudio-project/gsplat) CUDA library, and phone apps such as Polycam and Scaniverse that capture and train splats end to end.

## References

1. [Machine Learning for Inverse Graphics (MIT 6.S980)](https://www.scenerepresentations.org/courses/2023/fall/inverse-graphics/), Vincent Sitzmann
2. [NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis](https://arxiv.org/abs/2003.08934), Mildenhall et al., ECCV 2020
3. [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/), Kerbl et al., SIGGRAPH 2023
4. [EWA Splatting](https://www.cs.umd.edu/~zwicker/publications/EWASplatting-TVCG02.pdf), Zwicker et al., 2002
5. [2D Gaussian Splatting for Geometrically Accurate Radiance Fields](https://surfsplatting.github.io/), Huang et al., 2024
6. [LIV-GaussMap: LiDAR-Inertial-Visual Fusion for Real-time 3D Radiance Field Map Rendering](https://arxiv.org/abs/2401.14857), Hong et al., 2024
7. [ReconFusion: 3D Reconstruction with Diffusion Priors](https://reconfusion.github.io/)
8. [Introduction to 3D Gaussian Splatting](https://huggingface.co/blog/gaussian-splatting), Hugging Face
