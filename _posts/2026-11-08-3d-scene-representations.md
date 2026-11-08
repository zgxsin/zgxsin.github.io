---
title: "3D Scene Representations for Robotics: From Occupancy Grids to NeRF and Gaussian Splatting"
published: false
date: 2026-11-08
author: zgxsin
---

* TOC
{:toc}

## What a map is for

A 3D map is a data structure that stores what a robot has learned about its environment so that it can answer questions later. Which representation is "best" depends almost entirely on **which questions** need answering, and how fast:

- **Where am I?** Localization needs distinctive, stable geometry to register new scans against.
- **Where can I go?** Planning needs to know which space is **free**, which is **occupied**, and, just as important, which is still **unknown**.
- **How far is the nearest obstacle?** Trajectory optimization needs a distance, ideally with a gradient.
- **What does it look like?** Visualization, inspection and digital twins need surfaces and appearance.
- **What is it?** Task planning and language interaction need objects, rooms and their relations.

No single representation is good at all five, which is why real systems usually run several in parallel. A typical robot localizes against a point cloud map, plans on a voxel or elevation map, and shows the operator a mesh or a photorealistic reconstruction, all built from the same sensor data and the same poses from SLAM.

The post has three parts:

1. **Geometric maps** built from range sensors (LiDAR, depth cameras): point clouds, elevation maps, occupancy grids, signed distance fields and meshes. These answer the first three questions.
2. **Representations fitted to images** by differentiable rendering: neural fields, **NeRF** (2020) and **3D Gaussian Splatting** (2023). These answer "what does it look like?" with photorealism, and turn out to share one rendering equation.
3. **Semantic layers, a comparison, and how to choose** for a real robot.

### Axes for comparing representations

These are the properties that distinguish the representations:

- **Explicit vs. implicit.** An explicit map stores geometry directly (points, triangles, Gaussians). An implicit map stores a function whose level set or density defines the geometry (a signed distance field, a neural network).
- **Discrete vs. continuous.** A voxel grid is only defined at grid cells, a neural field or a Gaussian mixture can be queried at any point.
- **Sparse vs. dense.** A sparse map stores only surfaces or features, a dense map also stores free and unknown space.
- **Geometry, appearance, semantics.** What is stored per element: position only, also color or radiance, also a class label or a language embedding.
- **Metric vs. topological.** Coordinates in a common frame vs. a graph of places and their connectivity.
- **Updatable and deformable.** Can new measurements be fused incrementally, and can the map be corrected when a loop closure changes the past poses?
- **Differentiable.** Can the representation be fitted to images by gradient descent? This decides whether it can be learned from cameras alone.

The second-to-last point is easy to overlook and matters a lot in practice: SLAM poses keep changing after the fact, and a map that cannot follow them drifts away from the truth.

## Part 1: Geometric maps

This part covers maps built from range measurements (LiDAR, depth cameras) with known poses. They store geometry, and some of them also free and unknown space.

## Point clouds

The simplest map is the union of all measured points, transformed into a common frame with the SLAM poses. Every LiDAR and depth camera produces points, so this representation needs no conversion and loses nothing. Formally it is an unordered set $\lbrace \mathbf{p}\_1, \dots, \mathbf{p}\_N \rbrace$, stored as an $N \times 3$ array. The order of the rows does not matter, unlike the pixels of an image, so a network that processes point clouds must be permutation invariant (a plain fully connected layer is not, PointNet is).

Points are what scan registration works on: ICP and its variants align a new scan to the map by nearest-neighbor search, which is why point cloud maps are usually stored in a [k-d tree](/2024/10/01/kd-tree/) or a voxel hash for fast lookup. In practice, the map is **downsampled** with a voxel filter (keep one point, or the centroid, per voxel) to bound its size and even out the density.

Their weakness is what they do **not** encode:

- No connectivity: there is no surface, only samples of one, so "is this point inside an object?" or "is this ray blocked?" has no answer without extra assumptions.
- No free space: a missing point can mean free space, an unobserved region, or a surface the sensor could not see (glass, black material). A planner cannot tell these apart.
- No noise model: every point counts the same, and dynamic objects leave permanent ghost trails unless they are removed explicitly.

That makes point clouds the standard for **localization** maps and a poor choice for planning.

### Normal distributions transform (NDT)

NDT (Biber and Straßer, 2003; Magnusson's 3D-NDT) replaces the points in each voxel by a Gaussian: the mean and covariance of the points that fall in it. The map becomes a piecewise smooth probability density, which makes scan registration a smooth optimization problem with analytic derivatives instead of a nearest-neighbor search. It is also far more compact than raw points. A voxel with a flat covariance is a small planar patch, a voxel with an elongated one is an edge: NDT is an early, non-rendered relative of [Gaussian splatting](#gaussian-splatting).

### Surfels

A surfel ("surface element") is a point with a normal, a radius and a confidence: a small oriented disk. Surfel maps (ElasticFusion, SuMa) keep the flexibility of points but represent the surface: surfels can be rendered into a virtual depth image for registration, averaged when the same surface is seen again, and their confidence lets unstable (dynamic) surfels fade away. Because each surfel is independent, a loop closure can simply move them, which is how ElasticFusion deforms its map instead of rebuilding it.

## Elevation maps (2.5D)

For ground robots, the full 3D structure is often more than needed. An **elevation map** is a 2D grid where each cell stores the terrain height, usually with its variance. It is compact (memory grows with area, not volume) and directly answers the question a legged or wheeled robot asks: what is the ground under my feet, and how steep or rough is it?

Fankhauser's robot-centric elevation mapping, used on ANYmal, fuses a new height measurement $h_m$ with variance $\sigma_m^2$ into a cell with height $h$ and variance $\sigma^2$ with a one-dimensional [Kalman filter](/2026/11/04/kalman-filter/) update:

$$
h^{+} = \frac{\sigma_m^2\, h + \sigma^2\, h_m}{\sigma^2 + \sigma_m^2}, \qquad
\sigma^{2,+} = \frac{\sigma^2\, \sigma_m^2}{\sigma^2 + \sigma_m^2}
$$

The map is kept in the robot frame and the variances grow as the robot moves, which models the uncertainty of its own drifting pose estimate. Layers such as slope, roughness and traversability are computed on top of the height, which the [grid_map](https://github.com/ANYbotics/grid_map) library is designed for. Modern versions (elevation_mapping_cupy) run on the GPU and add learned traversability and semantic layers.

The fundamental limitation is one height per cell: overhangs, tables, bridges and multi-floor buildings cannot be represented. Multi-level surface maps store several height intervals per cell to relax this, and when that is not enough, a full 3D representation is needed.

## Fields: describing space instead of surfaces

Points, surfels and meshes describe the surface. A **field** instead assigns a value to every point in space, $\Phi: \mathbb{R}^3 \to \mathbb{R}^n$, and the surface is a level set of the field. This is why fields are also called volumetric or implicit representations.

| Field | Value at a point $\mathbf{x}$ | Surface |
| --- | --- | --- |
| Occupancy | Probability that $\mathbf{x}$ is inside an object, in $[0, 1]$ | Level set at 0.5 |
| Signed distance (SDF) | Distance to the nearest surface, negative inside | Zero level set |
| Truncated SDF (TSDF) | SDF clipped to a band around the surface | Zero crossing |
| Radiance field | Volume density $\sigma \geq 0$ and color $\mathbf{c}$ | No hard surface; high density |

The field says *what* is stored. A separate choice is *how* the field is stored: in a discrete grid (this part), in a neural network, in a mix of both, or as a sum of Gaussians ([Part 2](#part-2-representations-fitted-to-images)).

## Voxel grids

A **voxel** ("volumetric pixel") is the 3D analog of a pixel: a small cube of space. A voxel grid divides space into equally sized voxels with resolution $r$ and stores one field value per voxel. The position of a voxel is not stored; it is implied by its index,

$$
\mathbf{i} = \left\lfloor \frac{\mathbf{x} - \mathbf{o}}{r} \right\rfloor,
$$

where $\mathbf{o}$ is the origin of the grid. This makes lookups $O(1)$ and makes voxel grids the natural representation for dense properties of space: occupancy, signed distance, color, semantic labels. To query the field between voxel centers, use **trilinear interpolation**, the 3D version of bilinear interpolation: a weighted average of the 8 surrounding voxels, where each weight is the volume of the box opposite that corner.

The price is memory, which grows with the cube of the resolution. A building of $100 \times 100 \times 10$ m at $r = 5$ cm has $2000 \times 2000 \times 200 = 8 \times 10^8$ voxels. With one float per voxel that is 3.2 GB, with the two floats of a TSDF (distance and weight) 6.4 GB, and halving the resolution multiplies it by eight. Most of those voxels are empty air or solid material that was never observed. A dense array is only practical for small, bounded volumes (KinectFusion's original desk-sized cube), and every large-scale system uses one of the sparse structures [below](#sparse-voxel-data-structures).

### Occupancy mapping

The oldest dense representation (Moravec and Elfes, 1985) stores in each voxel $m$ the probability $p(m \mid z_{1:t})$ that it is occupied, given all measurements so far. Updating probabilities directly is awkward, so the map stores the **log-odds**

$$
l(m) = \log \frac{p(m)}{1 - p(m)},
$$

which turns the recursive Bayes update (under the usual assumption that voxels are independent and the world is static) into an addition:

$$
l_t(m) = l_{t-1}(m) + \log \frac{p(m \mid z_t)}{1 - p(m \mid z_t)} - l_0 .
$$

The middle term is the **inverse sensor model**: how likely the voxel is occupied given only the current measurement. For a range sensor, every voxel the ray passes through gets a "miss" update and the voxel containing the endpoint gets a "hit" update. Rays are traversed with a 3D DDA (Amanatides and Woo), which visits exactly the voxels the ray crosses. $l_0$ is the prior, usually $0$ for $p = 0.5$.

Two practical details matter more than the math:

- **Clamping.** The log-odds are clamped to $[l_{\min}, l_{\max}]$. Without it, a voxel observed occupied a thousand times would need a thousand misses before it is free again, and the map could never react to a door opening or a person walking away. OctoMap's defaults are a hit probability of 0.7, a miss probability of 0.4, and clamping at 0.12 and 0.97.
- **Unknown is a first-class state.** A voxel with $l = l_0$ has never been observed. A planner must treat it differently from free space, and an exploration planner is attracted to the boundary between known free and unknown space (the frontier).

Occupancy is robust to noise and dynamic objects, and it is exactly what a collision checker needs. But it cannot represent a surface more precisely than one voxel, and thin structures such as cables, branches and fences are erased by misses from rays passing next to them. Wavemap addresses the latter by modeling each beam with its angular width instead of an infinitely thin ray.

### Sparse voxel data structures

Since surfaces are 2D, the number of voxels that matter grows with surface area, not volume. Three data structures exploit this.

**Octree.** An octree recursively splits a cube into eight children, so each node covers $1/8$ of its parent. Unobserved regions are never allocated, and a large region with the same value (all free, all occupied) can be **pruned** into a single coarse node. OctoMap (Hornung et al., 2013) is the classic octree occupancy map, and its multi-resolution queries are useful for coarse planning. The downside is that reaching a leaf takes as many pointer hops as the tree has levels (16 for OctoMap), which makes random access slow, and the pruning has to be maintained as values change.

**Voxel hashing.** Nießner et al. (2013) group voxels into small dense **blocks** (typically $8^3$) and store only the blocks near observed surfaces in a hash table keyed by the block's integer coordinates. A common hash function is

$$
h(x, y, z) = (x \cdot p_1 \oplus y \cdot p_2 \oplus z \cdot p_3) \bmod n
$$

with large primes $p_1 = 73856093$, $p_2 = 19349663$, $p_3 = 83492791$. A lookup is one hash plus an array index, independent of the size of the scene, and blocks can be allocated, freed or streamed to disk independently. The structure is flat, not hierarchical: there is no octree and no adaptive resolution. Voxblox and nvblox use voxel hashing, and the same idea reappears in [Instant-NGP](#hybrid-representations).

**OpenVDB.** VDB (Museth, 2013), developed for film visual effects, is a shallow tree with very wide nodes. The default configuration has a hash map at the root, two levels of internal nodes with $32^3$ and $16^3$ children, and leaf nodes of $8^3$ voxels. Only four levels cover a practically unbounded index space, each internal node uses bit masks to mark which children exist, and sequential or locally coherent access is fast thanks to caching of the last visited path. It combines the adaptivity of an octree with fast random access. VDBFusion builds a TSDF on OpenVDB, and the format comes with mature tools for meshing, filtering and level set operations.

Wavemap (Reijgwart et al., 2023) takes a different route to multi-resolution: it stores occupancy in an octree of **Haar wavelet** coefficients. Since the wavelet transform is linear, measurements can be integrated directly into the compressed representation, all resolution levels are always consistent without maintenance passes, and the integrator can work coarse-to-fine and skip regions that are already uniform.

| Structure | Random access | Hierarchy | Typical users |
| --- | --- | --- | --- |
| Dense array | Fastest, one index | No | KinectFusion, small volumes |
| Octree | Slow, one pointer hop per level | Yes, deep | OctoMap, supereight |
| Voxel hashing | Fast, one hash plus one index | No | Voxblox, nvblox |
| OpenVDB | Fast, four levels with caching | Yes, shallow and wide | VDBFusion, film VFX |
| Wavelet octree | Fast for coarse-to-fine queries | Yes, always consistent | Wavemap |

## Signed distance fields

Occupancy says whether a voxel is free. A **signed distance field (SDF)** stores more: the distance from a point to the nearest surface $\mathcal{S}$, positive outside objects and negative inside,

$$
\phi(\mathbf{x}) = \pm \min_{\mathbf{s} \in \mathcal{S}} \lVert \mathbf{x} - \mathbf{s} \rVert .
$$

The surface is the zero level set $\phi(\mathbf{x}) = 0$. Its gradient points away from the nearest surface, so the surface normal is $\nabla \phi / \lVert \nabla \phi \rVert$, and a true SDF satisfies the **eikonal equation** $\lVert \nabla \phi \rVert = 1$ almost everywhere, which neural SDF methods use as a regularizer. Two flavors are used in robotics, built for two different purposes.

{% include figures/map-fields.html %}

### TSDF: for reconstructing surfaces

Computing the true nearest-surface distance from a single depth image is not possible, because the surface is only partly observed. The **truncated signed distance function (TSDF)** (Curless and Levoy, 1996) instead uses the **projective** distance along the sensor ray. For a voxel at distance $z_v$ from the sensor, on a ray that measured the surface at depth $z_m$:

$$
d = z_m - z_v ,
$$

positive in front of the surface and negative behind it. The value is **truncated** to $[-\tau, \tau]$, and voxels with $d < -\tau$ are not updated at all, since they are hidden behind the surface and the sensor says nothing about them. Truncation keeps the update local to a band around the surface, which is what makes sparse storage effective; far from the surface the exact value does not matter for reconstruction.

Each voxel stores the distance $D$ and a weight $W$, and a new measurement with weight $w$ is fused with a **weighted running average**:

$$
D_t = \frac{W_{t-1} D_{t-1} + w\, d}{W_{t-1} + w}, \qquad W_t = \min(W_{t-1} + w,\; W_{\max}) .
$$

Averaging many noisy measurements of the same surface is what gives TSDF reconstructions their smoothness. The zero crossing can be interpolated between voxels, so the surface is recovered with **sub-voxel** accuracy. The weight $w$ can model sensor noise (smaller for far or grazing measurements), and the cap $W_{\max}$ keeps the map able to change, just like clamping in occupancy maps.

The integration loop, per depth image with known sensor pose, looks like this:

```python
for block in blocks_in_view_frustum(depth_image, pose):
    for voxel in block:
        x_sensor = pose.inverse() * voxel.center      # voxel center in the sensor frame
        u, v = project(x_sensor)                      # pixel the voxel projects to
        if not inside_image(u, v) or depth_image[v, u] is invalid:
            continue
        d = depth_image[v, u] - x_sensor.z            # projective signed distance
        if d < -tau:
            continue                                  # occluded, no information
        d = min(d, tau)
        w = measurement_weight(depth_image[v, u])
        voxel.D = (voxel.W * voxel.D + w * d) / (voxel.W + w)
        voxel.W = min(voxel.W + w, W_max)
```

This voxel-centric (projective) loop is natural for depth cameras and parallelizes perfectly on a GPU. For LiDAR, whose points are not on a regular image, Voxblox instead casts a ray from the sensor to each point and updates the voxels within $\tau$ of the endpoint, grouping points that fall in the same voxel to save work.

To turn a TSDF into a mesh, use **marching cubes**. For each cube of 8 neighboring voxels, the signs at the corners (inside or outside) give one of $2^8 = 256$ configurations, 15 after symmetry. A lookup table gives the triangles for each configuration, and each triangle vertex is placed on a cube edge by linearly interpolating where the field crosses zero.

KinectFusion (2011) made TSDF fusion real-time on a GPU. Voxblox (2017) brought it to robots at building scale on a CPU with voxel hashing, nvblox (2023) moved it back to the GPU for real-time planning, and VDBFusion builds it on OpenVDB.

### ESDF: for planning

The TSDF has two problems as a planning map: far from surfaces it only says "at least $\tau$", and the projective distance overestimates the true distance whenever the ray hits the surface at a grazing angle. A planner wants the true Euclidean distance everywhere in free space. That is the **Euclidean signed distance field (ESDF)**.

With an ESDF, a collision check for a robot approximated by a sphere of radius $\rho$ is a single lookup, $\phi(\mathbf{x}) > \rho$, and gradient-based trajectory optimizers (CHOMP, TrajOpt and the many drone planners derived from them) push the trajectory along $\nabla \phi$, away from obstacles.

An ESDF is not fused from measurements directly; it is **computed** from an occupancy map or a TSDF. Voxblox propagates distances outward from the surface voxels of the TSDF with a wavefront (brushfire) algorithm, and only re-propagates where the TSDF changed. FIESTA builds it directly from an occupancy map with a breadth-first search, nvblox computes it on the GPU, and when an ESDF is only needed in a 2D slice (for a ground robot), it can be computed much faster on that slice alone.

## Meshes

A **triangle mesh** stores vertices (3D positions) and faces (lists of vertex indices, usually triangles). The order of indices in a face matters, since it defines the polygon and its normal direction. It is the standard representation of surfaces in graphics and simulation: compact (only the surface is stored), rendered efficiently by every GPU, and supported by every 3D tool and physics engine. For a human looking at a map, a colored mesh is far easier to understand than a cloud of points.

In robotics, meshes are rarely mapped directly. They are **extracted** from something easier to fuse:

- **Marching cubes** on a TSDF, the most common route. Voxblox and nvblox extract a mesh incrementally, only for blocks that changed.
- **Poisson surface reconstruction** from an oriented point cloud, offline. It produces watertight surfaces but can hallucinate surfaces in unobserved regions.
- **Multi-view stereo** in photogrammetry pipelines (COLMAP, RealityCapture), from images with poses from structure from motion.

Meshes are hard to update incrementally (changing the topology is messy) and have no notion of free or unknown space. They are also hard to *optimize* from images: the topology is fixed by the connectivity, which gradient descent cannot change, and visibility at the silhouettes is discontinuous. So meshes are an output format for visualization, simulation and inspection rather than a working map. An exception is Kimera, which uses a mesh as the base layer of its metric-semantic map and deforms it during loop closure.

## Part 2: Representations fitted to images

This part covers representations that are optimized so that their rendered images match captured photos. They store appearance as well as geometry.

## Inverse graphics

Computer graphics goes from a 3D scene to images: given geometry, materials, lights and a camera, it renders what the camera sees. **Inverse graphics** goes the other way: given images of a scene, it recovers a 3D representation of the scene. The standard test is **novel view synthesis**: from photos with known camera poses, render the scene from a viewpoint that nobody photographed. A method can only do this well if it has captured both the geometry and the appearance of the scene.

Every method in this part answers three questions:

1. **How is the scene represented?** As a voxel grid, a neural network, or a cloud of Gaussians.
2. **How is the representation turned into an image?** This is the renderer, also called the forward map.
3. **How is the representation fitted to the photos?** Classically by triangulating matched features, today mostly by gradient descent through a differentiable renderer.

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

- **Instant-NGP** (2022) uses a multiresolution hash grid: feature tables at many resolutions, indexed by hashing the vertex coordinates, the same idea as voxel hashing. It brought NeRF training from days to minutes.
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

Each sample contributes its color with weight $w_i = T_i \alpha_i$: it must be opaque itself ($\alpha_i$), and not hidden by what is in front of it ($T_i$). This is exactly **front-to-back alpha compositing**, the "over" operator graphics has used since the 1980s, which is why the same formula shows up again in Gaussian splatting. The same weights give the **expected depth** of the pixel, $D = \sum_i w_i t_i$, and their sum $\sum_i w_i = 1 - T_{n+1}$ is how opaque the pixel is.

In the figure below, the blue cloud is semi-transparent and the red object behind it is nearly solid. Raise the density of the cloud: the transmittance drops earlier, the cloud's samples take more weight, and the red object fades from the pixel. With few samples, the pixel color is a coarse approximation; with more it converges.

{% include figures/volume-rendering-ray.html %}

Why volume rendering is so good for optimization: every sample along the ray receives a gradient, in proportion to its weight. There is no hard visibility decision. If the color is wrong, the optimizer can add density in front, remove density behind, or change the colors, all smoothly.

Note the link to occupancy mapping: a range sensor's ray also passes through free space and ends at a hit, and the occupancy update is the discrete, probabilistic version of the same ray model. Depth supervision from LiDAR or a depth camera plugs directly into the expected depth $D$ above.

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

## 3D Gaussian Splatting
{: #gaussian-splatting}

3D Gaussian Splatting (3DGS, Kerbl et al., SIGGRAPH 2023) renders in real time at a quality equal to or better than the best NeRFs, and it trains in tens of minutes. It keeps the volume rendering equation, but replaces the dense neural field with an explicit, sparse one.

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

**This is the same formula as NeRF's volume rendering.** The only difference is where $\alpha_i$ comes from: in NeRF it is the density of a sampled point integrated over a ray segment, in Gaussian splatting it is read off a closed-form 2D Gaussian. The volume rendering integral is computed without ever sampling a single 3D point in space.

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

### NeRF versus Gaussian splatting

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

## Part 3: Semantics, comparison and choice

This part adds the semantic layer on top, compares all representations side by side, and gives guidelines for a real robot.

## Semantic and topological representations

All the representations above describe geometry and appearance. A robot that is told "bring the cup from the kitchen" also needs to know what things are and how places connect.

- **Metric-semantic maps** attach a class label (or a probability distribution over classes) to each voxel, surfel, mesh vertex or Gaussian, fused over time just like occupancy. Kimera and Voxblox++ are examples.
- **Object-level maps** represent each object instance as an entity with a pose, a shape and a class, which is compact and easy to reason about, and the objects can also serve as landmarks for localization.
- **3D scene graphs** (Armeni et al., 2019; Rosinol et al., 2020; Hydra, 2022) organize the map into layers: a metric mesh at the bottom, then objects and agents, places (a topological graph of free space), rooms, and buildings at the top, with edges for containment, adjacency and traversability. A planner can then reason at the room level and refine down to metric paths only where needed.
- **Open-vocabulary maps** (ConceptFusion, ConceptGraphs, LERF) store vision-language features (for example CLIP embeddings) instead of fixed class labels, so the map can be queried with arbitrary text.

## Comparison

| Representation | Kind | Free space | Distance query | Appearance | Fits to images | Updates | Typical use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Point cloud | Explicit, sparse | No | Nearest neighbor | Color | Positions only | Easy | Localization, SfM output |
| Surfels | Explicit, sparse | No | Nearest neighbor | Color | Partly | Easy, deformable | Dense SLAM |
| Elevation map | Explicit, 2.5D grid | Above ground | Height only | Optional | No | Easy | Locomotion |
| Occupancy grid | Explicit, dense | Yes, with unknown | No | No | No | Easy | Collision checking, exploration |
| TSDF | Explicit, dense near surface | Near surfaces | Truncated | Color | Not directly | Easy | Surface reconstruction |
| ESDF | Explicit, dense | Yes | Euclidean | No | No | Derived | Trajectory optimization |
| Mesh | Explicit surface | No | Nearest triangle | Texture | Poorly, fixed topology | Hard | Visualization, simulation |
| Neural field (NeRF, neural SDF) | Implicit, continuous | No | Neural SDF only | Photorealistic | Yes, slow | Slow, global | View synthesis |
| Hybrid grid + MLP | Mixed | No | No | Photorealistic | Yes, fast | Local | Instant-NGP, nerfstudio |
| 3D Gaussians | Explicit, sparse | No | No | Photorealistic | Yes, very fast | Easy, local | Visualization, digital twins |
| Scene graph | Explicit graph | Places layer | No | No | No | Moderate | Task planning, language |

## Choosing a representation

### Maps for the robot and maps for people

A robot needs two different kinds of maps:

- **Maps for the robot** to localize, plan and avoid collisions need metric, reliable geometry and fast queries ("is this voxel free?"). Point clouds, occupancy grids, TSDF or ESDF voxel maps (voxblox, nvblox) and elevation maps remain the right tools. Their appearance does not matter.
- **Maps for people**, such as an operator who inspects a site, places waypoints and inspection points, or reviews a change over time, benefit from photorealism. Here Gaussian splatting is very attractive: it renders in real time, even in a browser, and shows gauges, labels and thin structures that a coarse mesh loses. A practical setup runs a high-fidelity mapping process in parallel with SLAM: SLAM provides localization, and its poses feed the photorealistic reconstruction.

### Guidelines

**Start from the query.** If the map is for localization, keep a downsampled point cloud or an NDT map. If it is for collision checking, use occupancy. If the planner optimizes trajectories, compute an ESDF. If a human looks at it, extract a mesh or train Gaussians. It is normal to maintain several of these side by side.

**Respect unknown space.** Point clouds, meshes and radiance fields do not separate free from unobserved space. For safety-relevant decisions, use a representation that does: occupancy, TSDF with weights, or ESDF.

**Plan for pose corrections.** Dense voxel maps are fused in a fixed frame, so a loop closure that moves past poses leaves them inconsistent. The common remedies are **submaps** (Voxgraph, many LiDAR SLAM systems): build small local maps that are internally consistent, attach each to a pose in the SLAM graph, and move them as rigid wholes when the graph is optimized. Representations made of independent elements (points, surfels, Gaussians) can instead be deformed directly. Re-integrating all data from the corrected poses is the fallback when neither works.

**Plan for scale.** A building-scale map at centimeter resolution does not fit in GPU memory, and often not in RAM. Sparse data structures help, but at some point the map has to be divided into blocks or tiles and streamed in and out of memory around the robot (out-of-core streaming), the same technique used for large terrains in games and GIS.

### Gaussian splatting in SLAM, and open problems

Gaussian splatting is moving into SLAM itself. **SplaTAM**, **Photo-SLAM** and **Gaussian Splatting SLAM (MonoGS)** track the camera against the Gaussian map while building it, and **LIV-GaussMap** fuses LiDAR, IMU and camera so the LiDAR provides accurate geometry and initialization and the camera the appearance. Open problems for real deployments include:

- **Large scenes:** gigabytes per scene call for compression, level of detail and streaming parts of the map in and out of memory. Hierarchical 3DGS and city-scale methods address this.
- **Multi-session maps:** lighting, weather and objects change between visits, and the baked-in lighting makes merging sessions hard.
- **Unobserved regions:** a robot never sees every surface. Generative priors such as diffusion models (ReconFusion) fill in plausible content, and feed-forward models (pixelSplat, MVSplat) predict Gaussians from a few images in one network pass instead of per-scene optimization.
- **Geometry accuracy**, for which surface-aligned variants such as 2DGS and PGSR are the current answer.

The trend is toward **hybrid** maps: a sparse geometric backbone for localization, a dense volumetric layer for safe planning, a radiance field for appearance, and a semantic or scene graph layer for reasoning, all tied to the same pose graph.

### Tools

- Geometric mapping: [OctoMap](https://octomap.github.io/), [Voxblox](https://github.com/ethz-asl/voxblox), [nvblox](https://github.com/nvidia-isaac/nvblox), [wavemap](https://github.com/ethz-asl/wavemap), [OpenVDB](https://www.openvdb.org/), [grid_map](https://github.com/ANYbotics/grid_map).
- Radiance fields: COLMAP for poses, the [reference 3DGS implementation](https://github.com/graphdeco-inria/gaussian-splatting), [nerfstudio](https://docs.nerf.studio/) (both `nerfacto` and `splatfacto`), the [gsplat](https://github.com/nerfstudio-project/gsplat) CUDA library, and phone apps such as Polycam and Scaniverse that capture and train splats end to end.

## References

Geometric mapping:

1. [OctoMap: An efficient probabilistic 3D mapping framework based on octrees](https://octomap.github.io/), Hornung et al., 2013
2. [Real-time 3D Reconstruction at Scale using Voxel Hashing](https://niessnerlab.org/projects/niessner2013hashing.html), Nießner et al., 2013
3. [OpenVDB documentation](https://www.openvdb.org/documentation/)
4. [A Volumetric Method for Building Complex Models from Range Images](https://graphics.stanford.edu/papers/volrange/), Curless and Levoy, 1996
5. [KinectFusion: Real-time dense surface mapping and tracking](https://www.microsoft.com/en-us/research/publication/kinectfusion-real-time-dense-surface-mapping-and-tracking/), Newcombe et al., 2011
6. [Voxblox: Incremental 3D Euclidean Signed Distance Fields for On-Board MAV Planning](https://arxiv.org/abs/1611.03631), Oleynikova et al., 2017
7. [nvblox: GPU-Accelerated Incremental Signed Distance Field Mapping](https://arxiv.org/abs/2311.00626), Millane et al., 2024
8. [VDBFusion: Flexible and Efficient TSDF Integration of Range Sensor Data](https://www.mdpi.com/1424-8220/22/3/1296), Vizzo et al., 2022
9. [Efficient volumetric mapping of multi-scale environments using wavelet-based compression (wavemap)](https://roboticsproceedings.org/rss19/p065.pdf), Reijgwart et al., 2023
10. [Probabilistic Terrain Mapping for Mobile Robots with Uncertain Localization](https://ieeexplore.ieee.org/document/8392399), Fankhauser et al., 2018
11. [ElasticFusion: Dense SLAM Without A Pose Graph](https://www.roboticsproceedings.org/rss11/p01.pdf), Whelan et al., 2015
12. [Voxgraph: Globally Consistent, Volumetric Mapping using Signed Distance Function Submaps](https://arxiv.org/abs/1911.02931), Reijgwart et al., 2020
13. [Hydra: A Real-time Spatial Perception System for 3D Scene Graph Construction and Optimization](https://arxiv.org/abs/2201.13360), Hughes et al., 2022

Neural fields, NeRF and Gaussian splatting:

14. [Machine Learning for Inverse Graphics (MIT 6.S980)](https://www.scenerepresentations.org/courses/2023/fall/inverse-graphics/), Vincent Sitzmann
15. [NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis](https://arxiv.org/abs/2003.08934), Mildenhall et al., ECCV 2020
16. [Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains](https://arxiv.org/abs/2006.10739), Tancik et al., 2020
17. [Neural Tangent Kernel: Convergence and Generalization in Neural Networks](https://arxiv.org/abs/1806.07572), Jacot et al., 2018
18. [Instant Neural Graphics Primitives with a Multiresolution Hash Encoding](https://nvlabs.github.io/instant-ngp/), Müller et al., 2022
19. [Plenoxels: Radiance Fields without Neural Networks](https://alexyu.net/plenoxels/), Fridovich-Keil et al., 2022
20. [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/), Kerbl et al., SIGGRAPH 2023
21. [EWA Splatting](https://www.cs.umd.edu/~zwicker/publications/EWASplatting-TVCG02.pdf), Zwicker et al., 2002
22. [2D Gaussian Splatting for Geometrically Accurate Radiance Fields](https://surfsplatting.github.io/), Huang et al., 2024
23. [LIV-GaussMap: LiDAR-Inertial-Visual Fusion for Real-time 3D Radiance Field Map Rendering](https://arxiv.org/abs/2401.14857), Hong et al., 2024
24. [ReconFusion: 3D Reconstruction with Diffusion Priors](https://reconfusion.github.io/)
25. [Introduction to 3D Gaussian Splatting](https://huggingface.co/blog/gaussian-splatting), Hugging Face

Surveys:

26. [Scene Representations for Robotic Spatial Perception](https://www.annualreviews.org/content/journals/10.1146/annurev-control-040423-030709), Annual Review of Control, Robotics, and Autonomous Systems, 2025
27. [What Is The Best 3D Scene Representation for Robotics? From Geometric to Foundation Models](https://arxiv.org/abs/2512.03422), 2025
