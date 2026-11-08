---
title: "NeRF and 3D Gaussian Splatting: Radiance Fields from Photos"
published: true
date: 2026-09-21
author: "Guoxiang (Shawn) Zhou"
---

* TOC
{:toc}

Two methods made photorealistic 3D reconstruction from ordinary photos practical: **NeRF** (Neural Radiance Fields, 2020) and **3D Gaussian Splatting** (3DGS, 2023). Both take photos with known camera poses, fit a **radiance field** to them, and render the scene from viewpoints nobody photographed. They render with the same equation and differ in one choice: NeRF parameterizes the radiance field **densely** with a neural network, Gaussian splatting **sparsely** with millions of explicit Gaussians. That one choice decides speed, memory, editability and how well each fits on a robot.

Both build on two ideas covered in my post on [differentiable rendering](/2026/08/02/differentiable-rendering/): fit a scene representation to images by gradient descent through a differentiable renderer, and render a **radiance field** (density and view-dependent color at every point) with **volume rendering**. The one equation to keep in mind is the discrete volume rendering formula, which composites the samples along a camera ray front to back:

$$
C = \sum_{i} T_i\, \alpha_i\, \mathbf{c}_i, \qquad T_i = \prod_{j=1}^{i-1} (1 - \alpha_j)
$$

where $\alpha_i$ is the opacity of sample $i$, $\mathbf{c}_i$ its color and $T_i$ the transmittance, the fraction of light that reaches it. NeRF evaluates a neural network at hundreds of samples per ray to get $\alpha_i$ and $\mathbf{c}_i$. Gaussian splatting reads them off a set of explicit Gaussians, which is what makes it fast.

## NeRF: neural radiance fields

NeRF (Mildenhall et al., ECCV 2020) parameterizes the radiance field **densely**, at every point in space, with an MLP, and renders it with volume rendering.

### Model

The network maps a position and a viewing direction to a density and a color:

$$
F_\theta: (\mathbf{x}, \mathbf{d}) \mapsto (\sigma, \mathbf{c})
$$

The architecture enforces the [halfway fix](/2026/08/02/differentiable-rendering/#what-volume-rendering-leaves-out) for view-dependent color. The position goes through 8 fully connected layers of 256 channels (with a skip connection that re-injects the input at the fifth layer), which output the density $\sigma$ and a feature vector. Only then is the viewing direction concatenated, and one more layer of 128 channels outputs the color. So the density, which is the geometry, cannot depend on the viewing direction, which forces the geometry to be consistent across views, while the color can.

### Positional encoding

Fed raw coordinates, an MLP produces blurry results. Neural networks have a **spectral bias** towards smooth, low-frequency functions, which is the [neural tangent kernel view](/2026/08/02/differentiable-rendering/#why-a-neural-field-is-just-an-interpolator) of an MLP. NeRF fixes this by mapping each coordinate to sines and cosines of increasing frequency before the network:

$$
\gamma(p) = \big(\sin(2^0 \pi p), \cos(2^0 \pi p), \dots, \sin(2^{L-1} \pi p), \cos(2^{L-1} \pi p)\big)
$$

with $L = 10$ frequencies for the position and $L = 4$ for the direction. Nearby points that were almost identical as inputs now differ strongly in the high-frequency components, so the network can represent sharp edges and fine texture. Tancik et al. (2020) later explained this as changing the NTK from a low-pass kernel into one with a tunable bandwidth.

### Training

NeRF is fitted to **one scene at a time**; there is no pretraining and no generalization to other scenes. Each training step:

1. Sample a batch of pixels (4096 rays) at random from all training images, and build each pixel's ray from the camera pose.
2. Render each ray with the [volume rendering quadrature](/2026/08/02/differentiable-rendering/#volume-rendering).
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
- **Instant-NGP** and **Plenoxels** (see [hybrid representations](/2026/08/02/differentiable-rendering/#hybrid-representations)) make training take minutes.
- **NeRF in the Wild** handles photo collections with varying lighting and transient objects by giving each image a learned appearance embedding.
- **BARF** refines inaccurate camera poses jointly with the scene.
- **NeuS** and **VolSDF** volume-render an SDF instead of a free density, which gives clean surfaces.
- **Light field networks** skip volume rendering altogether and map a ray directly to its color, one network evaluation per pixel, at the cost of no built-in 3D consistency.

## 3D Gaussian splatting
{: #gaussian-splatting}

3D Gaussian Splatting (Kerbl et al., SIGGRAPH 2023) renders in real time at a quality equal to or better than the best NeRFs, and trains in tens of minutes. It keeps the volume rendering equation, but replaces NeRF's dense neural field with an explicit, sparse one.

### Key idea: a sparse radiance field

NeRF parameterizes the radiance field everywhere, yet most of space is empty. Gaussian splatting parameterizes it **only where the density is nonzero**: the scene is a set of millions of 3D Gaussian blobs floating in space, each with its own position, shape, opacity and color. Space between the blobs has zero density and costs nothing to render. And because each Gaussian has a closed-form shape, we know directly which Gaussians a pixel's ray passes through, instead of blindly sampling points along the ray and asking a network what is there.

{% include figures/nerf-vs-splat-ray.html %}

### The parameters of a Gaussian

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

### View-dependent color with spherical harmonics

The color must depend on the viewing direction $\mathbf{d}$ to show highlights and reflections. Instead of a network, each Gaussian stores coefficients of **spherical harmonics** $Y_l^m$, the Fourier basis for functions on a sphere:

$$
\mathbf{c}_i(\mathbf{d}) = \sum_{l=0}^{3} \sum_{m=-l}^{l} \mathbf{k}_{i,l}^m\, Y_l^m(\mathbf{d})
$$

Degree 0 is a single constant, the diffuse color. Each higher degree adds finer angular detail. Degree 3 has $1 + 3 + 5 + 7 = 16$ basis functions per color channel, so $3 \times 16 = 48$ numbers. Training starts with degree 0 only and unlocks one more degree every 1000 iterations, so the optimizer gets the base color right before it explains the remaining error with view dependence.

### Rendering: project, then alpha-blend

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

**This is the same formula as [NeRF's volume rendering](/2026/08/02/differentiable-rendering/#volume-rendering).** The only difference is where $\alpha_i$ comes from: in NeRF it is the density of a sampled point integrated over a ray segment, in Gaussian splatting it is read off a closed-form 2D Gaussian. The volume rendering integral is computed without ever sampling a single 3D point in space.

One approximation is hidden in the sort: each Gaussian gets a single depth, that of its center. When two Gaussians overlap in depth, their order can flip as the camera moves, which can cause "popping". Later work (StopThePop, 3D Gaussian ray tracing) sorts per pixel or traces rays to remove it.

### The tile-based rasterizer

The renderer is what makes Gaussian splatting fast. It is a custom CUDA rasterizer, not a ray tracer:

1. **Cull.** Discard Gaussians outside the view frustum or too close to the camera.
2. **Project** every remaining Gaussian to 2D as above, and compute a square bounding box of three standard deviations around it.
3. **Assign to tiles.** The image is split into 16 × 16 pixel tiles. Each Gaussian is duplicated once for every tile its bounding box overlaps, with a 64-bit key: tile ID in the high bits, depth in the low bits.
4. **Sort once.** A single GPU radix sort of all keys orders the Gaussians by tile, and by depth within each tile. There is no per-pixel sorting.
5. **Blend per tile.** One thread block handles one tile and loads its list into shared memory. Each thread handles one pixel and walks the list front to back, accumulating color and transmittance, and stops as soon as the pixel is nearly opaque ($T < 10^{-4}$).

{% include figures/splat-tile-rasterizer.html %}

The backward pass for training walks the same lists back to front. Because each pixel only stored its final transmittance and the number of Gaussians it used, the intermediate transmittances can be recovered by dividing out each $(1 - \alpha_j)$, so memory stays small.

### Optimization

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

### Adaptive density control

A fixed set of Gaussians cannot fit both large uniform areas and fine detail. So every 100 iterations (from iteration 500 to 15,000), the optimizer looks at Gaussians whose view-space position gradient is large on average (above 0.0002), a sign that the region is not well reconstructed:

- **Clone** a small Gaussian in an under-reconstructed region: copy it and move the copy along the gradient to cover the missing geometry.
- **Split** a large Gaussian in an over-reconstructed region, one that covers detail it cannot express: replace it with two Gaussians sampled from it, with their scales divided by 1.6.
- **Prune** Gaussians whose opacity has fallen below a threshold, or that have become very large in world space.

Every 3000 iterations, all opacities are also reset close to zero. The optimizer then raises the opacity again only for the Gaussians that are needed, and the rest get pruned. This removes floaters near the cameras that would otherwise keep growing.

{% include figures/density-control.html %}

A typical scene ends up with one to several million Gaussians.

### Strengths and weaknesses

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

## Radiance fields in robotics

A robot needs two different kinds of maps:

- **Maps for the robot** to localize, plan and avoid collisions need metric, reliable geometry and fast queries ("is this voxel free?"). Point clouds, occupancy grids, TSDF or ESDF voxel maps (voxblox, nvblox) and elevation maps remain the right tools, see [3D map representations](/2026/06/13/3d-map-representations/). Their appearance does not matter.
- **Maps for people**, such as an operator who inspects a site, places waypoints and inspection points, or reviews a change over time, benefit from photorealism. Here Gaussian splatting is very attractive: it renders in real time, even in a browser, and shows gauges, labels and thin structures that a coarse mesh loses. A practical setup runs a high-fidelity mapping process in parallel with SLAM: SLAM provides localization, and its poses feed the photorealistic reconstruction.

### Radiance fields in SLAM, and open problems

NeRF-based SLAM came first: **iMAP** and **NICE-SLAM** track the camera against a neural field while training it, but slow rendering and global updates limit them to small scenes. Gaussian splatting has largely taken over, because its map is explicit and local. **SplaTAM**, **Photo-SLAM** and **Gaussian Splatting SLAM (MonoGS)** track the camera against the Gaussian map while building it, and **LIV-GaussMap** fuses LiDAR, IMU and camera so the LiDAR provides accurate geometry and initialization and the camera the appearance. Open problems for real deployments include:

- **Large scenes:** gigabytes per scene call for compression, level of detail and streaming parts of the map in and out of memory. Hierarchical 3DGS and city-scale methods address this.
- **Multi-session maps:** lighting, weather and objects change between visits, and the baked-in lighting makes merging sessions hard.
- **Unobserved regions:** a robot never sees every surface. Generative priors such as diffusion models (ReconFusion) fill in plausible content, and feed-forward models (pixelSplat, MVSplat) predict Gaussians from a few images in one network pass instead of per-scene optimization.
- **Geometry accuracy**, for which surface-aligned variants such as 2DGS and PGSR are the current answer.

### Tools

COLMAP for poses, the [reference 3DGS implementation](https://github.com/graphdeco-inria/gaussian-splatting), [nerfstudio](https://docs.nerf.studio/) (both `nerfacto` and `splatfacto`), the [gsplat](https://github.com/nerfstudio-project/gsplat) CUDA library, and phone apps such as Polycam and Scaniverse that capture and train splats end to end.

## References

1. [Machine Learning for Inverse Graphics (MIT 6.S980)](https://www.scenerepresentations.org/courses/2023/fall/inverse-graphics/), Vincent Sitzmann
2. [NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis](https://arxiv.org/abs/2003.08934), Mildenhall et al., ECCV 2020
3. [Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains](https://arxiv.org/abs/2006.10739), Tancik et al., 2020
4. [Instant Neural Graphics Primitives with a Multiresolution Hash Encoding](https://nvlabs.github.io/instant-ngp/), Müller et al., 2022
5. [Plenoxels: Radiance Fields without Neural Networks](https://alexyu.net/plenoxels/), Fridovich-Keil et al., 2022
6. [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/), Kerbl et al., SIGGRAPH 2023
7. [EWA Splatting](https://www.cs.umd.edu/~zwicker/publications/EWASplatting-TVCG02.pdf), Zwicker et al., 2002
8. [2D Gaussian Splatting for Geometrically Accurate Radiance Fields](https://surfsplatting.github.io/), Huang et al., 2024
9. [LIV-GaussMap: LiDAR-Inertial-Visual Fusion for Real-time 3D Radiance Field Map Rendering](https://arxiv.org/abs/2401.14857), Hong et al., 2024
10. [ReconFusion: 3D Reconstruction with Diffusion Priors](https://reconfusion.github.io/)
11. [Introduction to 3D Gaussian Splatting](https://huggingface.co/blog/gaussian-splatting), Hugging Face
