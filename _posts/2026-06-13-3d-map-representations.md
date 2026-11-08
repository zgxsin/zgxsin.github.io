---
title: "3D Map Representations for Robots: Point Clouds, Voxels and Distance Fields"
published: false
date: 2026-06-13
author: "Guoxiang (Shawn) Zhou"
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

This post covers the geometric maps built from range sensors (LiDAR, depth cameras) with known poses: point clouds, elevation maps, occupancy grids, signed distance fields and meshes. These answer the first three questions. Photorealistic maps fitted to images are covered in two companion posts, on [differentiable rendering](/2026/08/02/differentiable-rendering/) and on [NeRF and 3D Gaussian splatting](/2026/09/21/nerf-and-gaussian-splatting/).

### Axes for comparing representations

These are the properties that distinguish the representations:

- **Explicit vs. implicit.** An explicit map stores geometry directly (points, triangles, Gaussians). An implicit map stores a function whose level set or density defines the geometry (a signed distance field, a neural network).
- **Discrete vs. continuous.** A voxel grid is only defined at grid cells, a neural field or a Gaussian mixture can be queried at any point.
- **Sparse vs. dense.** A sparse map stores only surfaces or features, a dense map also stores free and unknown space.
- **Geometry, appearance, semantics.** What is stored per element: position only, also color or radiance, also a class label or a language embedding.
- **Metric vs. topological.** Coordinates in a common frame vs. a graph of places and their connectivity.
- **Updatable and deformable.** Can new measurements be fused incrementally, and can the map be corrected when a loop closure changes the past poses?

The last point is easy to overlook and matters a lot in practice: SLAM poses keep changing after the fact, and a map that cannot follow them drifts away from the truth.

## Point clouds

The simplest map is the union of all measured points, transformed into a common frame with the SLAM poses. Every LiDAR and depth camera produces points, so this representation needs no conversion and loses nothing. Formally it is an unordered set $\lbrace \mathbf{p}\_1, \dots, \mathbf{p}\_N \rbrace$, stored as an $N \times 3$ array. The order of the rows does not matter, unlike the pixels of an image, so a network that processes point clouds must be permutation invariant (a plain fully connected layer is not, PointNet is).

Points are what scan registration works on: ICP and its variants align a new scan to the map by nearest-neighbor search, which is why point cloud maps are usually stored in a [k-d tree](/2024/10/01/kd-tree/) or a voxel hash for fast lookup. In practice, the map is **downsampled** with a voxel filter (keep one point, or the centroid, per voxel) to bound its size and even out the density.

Their weakness is what they do **not** encode:

- No connectivity: there is no surface, only samples of one, so "is this point inside an object?" or "is this ray blocked?" has no answer without extra assumptions.
- No free space: a missing point can mean free space, an unobserved region, or a surface the sensor could not see (glass, black material). A planner cannot tell these apart.
- No noise model: every point counts the same, and dynamic objects leave permanent ghost trails unless they are removed explicitly.

That makes point clouds the standard for **localization** maps and a poor choice for planning.

### Normal distributions transform (NDT)

NDT (Biber and Straßer, 2003; Magnusson's 3D-NDT) replaces the points in each voxel by a Gaussian: the mean and covariance of the points that fall in it. The map becomes a piecewise smooth probability density, which makes scan registration a smooth optimization problem with analytic derivatives instead of a nearest-neighbor search. It is also far more compact than raw points. A voxel with a flat covariance is a small planar patch, a voxel with an elongated one is an edge: NDT is an early, non-rendered relative of [Gaussian splatting](/2026/09/21/nerf-and-gaussian-splatting/#gaussian-splatting).

### Surfels

A surfel ("surface element") is a point with a normal, a radius and a confidence: a small oriented disk. Surfel maps (ElasticFusion, SuMa) keep the flexibility of points but represent the surface: surfels can be rendered into a virtual depth image for registration, averaged when the same surface is seen again, and their confidence lets unstable (dynamic) surfels fade away. Because each surfel is independent, a loop closure can simply move them, which is how ElasticFusion deforms its map instead of rebuilding it.

## Elevation maps (2.5D)

For ground robots, the full 3D structure is often more than needed. An **elevation map** is a 2D grid where each cell stores the terrain height, usually with its variance. It is compact (memory grows with area, not volume) and directly answers the question a legged or wheeled robot asks: what is the ground under my feet, and how steep or rough is it?

Fankhauser's robot-centric elevation mapping, used on ANYmal, fuses a new height measurement $h_m$ with variance $\sigma_m^2$ into a cell with height $h$ and variance $\sigma^2$ with a one-dimensional [Kalman filter](/2026/04/25/kalman-filter/) update:

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

The field says *what* is stored. A separate choice is *how* the field is stored: in a discrete grid (this post), in a neural network or a hybrid of both ([differentiable rendering](/2026/08/02/differentiable-rendering/#neural-fields)), or as a sum of Gaussians ([Gaussian splatting](/2026/09/21/nerf-and-gaussian-splatting/#gaussian-splatting)).

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

with large primes $p_1 = 73856093$, $p_2 = 19349663$, $p_3 = 83492791$. A lookup is one hash plus an array index, independent of the size of the scene, and blocks can be allocated, freed or streamed to disk independently. The structure is flat, not hierarchical: there is no octree and no adaptive resolution. Voxblox and nvblox use voxel hashing, and the same idea reappears in [Instant-NGP](/2026/08/02/differentiable-rendering/#hybrid-representations).

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

## Photorealistic maps

The representations above are built for the robot: they store geometry, and some of them free space. None of them looks like the scene. **Radiance fields** fill that gap: they are fitted to camera images by differentiable rendering and reproduce what the scene looks like from any viewpoint.

- **NeRF** stores the radiance field in a neural network. It is compact and continuous, but slow to render and hard to update locally. See [NeRF and 3D Gaussian splatting](/2026/09/21/nerf-and-gaussian-splatting/#nerf-neural-radiance-fields).
- **3D Gaussian splatting** stores it as millions of explicit Gaussians, renders in real time, and can be initialized from a LiDAR or SfM point cloud. See [NeRF and 3D Gaussian splatting](/2026/09/21/nerf-and-gaussian-splatting/#gaussian-splatting).

Neither stores free space, so they complement the maps above rather than replace them.

## Semantic and topological representations

All the representations above describe geometry and appearance. A robot that is told "bring the cup from the kitchen" also needs to know what things are and how places connect.

- **Metric-semantic maps** attach a class label (or a probability distribution over classes) to each voxel, surfel, mesh vertex or Gaussian, fused over time just like occupancy. Kimera and Voxblox++ are examples.
- **Object-level maps** represent each object instance as an entity with a pose, a shape and a class, which is compact and easy to reason about, and the objects can also serve as landmarks for localization.
- **3D scene graphs** (Armeni et al., 2019; Rosinol et al., 2020; Hydra, 2022) organize the map into layers: a metric mesh at the bottom, then objects and agents, places (a topological graph of free space), rooms, and buildings at the top, with edges for containment, adjacency and traversability. A planner can then reason at the room level and refine down to metric paths only where needed.
- **Open-vocabulary maps** (ConceptFusion, ConceptGraphs, LERF) store vision-language features (for example CLIP embeddings) instead of fixed class labels, so the map can be queried with arbitrary text.

## Comparison

| Representation | Kind | Free space | Distance query | Appearance | Updates | Typical use |
| --- | --- | --- | --- | --- | --- | --- |
| Point cloud | Explicit, sparse | No | Nearest neighbor | Color | Easy | Localization, SfM output |
| Surfels | Explicit, sparse | No | Nearest neighbor | Color | Easy, deformable | Dense SLAM |
| Elevation map | Explicit, 2.5D grid | Above ground | Height only | Optional | Easy | Locomotion |
| Occupancy grid | Explicit, dense | Yes, with unknown | No | No | Easy | Collision checking, exploration |
| TSDF | Explicit, dense near surface | Near surfaces | Truncated | Color | Easy | Surface reconstruction |
| ESDF | Explicit, dense | Yes | Euclidean | No | Derived | Trajectory optimization |
| Mesh | Explicit surface | No | Nearest triangle | Texture | Hard | Visualization, simulation |
| Radiance field (NeRF, 3DGS) | Implicit or explicit | No | No | Photorealistic | Slow (NeRF), easy (3DGS) | Visualization, digital twins |
| Scene graph | Explicit graph | Places layer | No | No | Moderate | Task planning, language |

## Choosing a representation

### Maps for the robot and maps for people

A robot needs two different kinds of maps:

- **Maps for the robot** to localize, plan and avoid collisions need metric, reliable geometry and fast queries ("is this voxel free?"). Point clouds, occupancy grids, TSDF or ESDF voxel maps (voxblox, nvblox) and elevation maps remain the right tools. Their appearance does not matter.
- **Maps for people**, such as an operator who inspects a site, places waypoints and inspection points, or reviews a change over time, benefit from photorealism. Here [Gaussian splatting](/2026/09/21/nerf-and-gaussian-splatting/#gaussian-splatting) is very attractive: it renders in real time, even in a browser, and shows gauges, labels and thin structures that a coarse mesh loses. A practical setup runs a high-fidelity mapping process in parallel with SLAM: SLAM provides localization, and its poses feed the photorealistic reconstruction.

### Guidelines

**Start from the query.** If the map is for localization, keep a downsampled point cloud or an NDT map. If it is for collision checking, use occupancy. If the planner optimizes trajectories, compute an ESDF. If a human looks at it, extract a mesh or train a radiance field. It is normal to maintain several of these side by side.

**Respect unknown space.** Point clouds, meshes and radiance fields do not separate free from unobserved space. For safety-relevant decisions, use a representation that does: occupancy, TSDF with weights, or ESDF.

**Plan for pose corrections.** Dense voxel maps are fused in a fixed frame, so a loop closure that moves past poses leaves them inconsistent. The common remedies are **submaps** (Voxgraph, many LiDAR SLAM systems): build small local maps that are internally consistent, attach each to a pose in the SLAM graph, and move them as rigid wholes when the graph is optimized. Representations made of independent elements (points, surfels, Gaussians) can instead be deformed directly. Re-integrating all data from the corrected poses is the fallback when neither works.

**Plan for scale.** A building-scale map at centimeter resolution does not fit in GPU memory, and often not in RAM. Sparse data structures help, but at some point the map has to be divided into blocks or tiles and streamed in and out of memory around the robot (out-of-core streaming), the same technique used for large terrains in games and GIS.

The trend is toward **hybrid** maps: a sparse geometric backbone for localization, a dense volumetric layer for safe planning, a radiance field for appearance, and a semantic or scene graph layer for reasoning, all tied to the same pose graph.

### Tools

[OctoMap](https://octomap.github.io/), [Voxblox](https://github.com/ethz-asl/voxblox), [nvblox](https://github.com/nvidia-isaac/nvblox), [wavemap](https://github.com/ethz-asl/wavemap), [OpenVDB](https://www.openvdb.org/), [grid_map](https://github.com/ANYbotics/grid_map).

## References

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
14. [Scene Representations for Robotic Spatial Perception](https://www.annualreviews.org/content/journals/10.1146/annurev-control-040423-030709), Annual Review of Control, Robotics, and Autonomous Systems, 2025
15. [What Is The Best 3D Scene Representation for Robotics? From Geometric to Foundation Models](https://arxiv.org/abs/2512.03422), 2025
