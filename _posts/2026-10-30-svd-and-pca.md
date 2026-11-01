---
title: Singular Value Decomposition and PCA analysis
published: true
date: 2026-10-30
author: zgxsin
---

In the Linear Algebra Essentials post, eigen decomposition $A = PDP^{-1}$ lets us look at a transformation in a coordinate system where it only scales. But it has two limits:

1. It only works for square matrices.
2. Not every square matrix has an eigenbasis (e.g. a shear), and even when it does, the eigenvectors are generally not orthogonal, so $P$ can skew space.

The Singular Value Decomposition (SVD) removes both limits. **Every** matrix, of any shape, can be written as rotate $\rightarrow$ stretch $\rightarrow$ rotate. PCA is then just SVD applied to mean-centered data.

Notation: all vectors are column vectors. A row vector is always written as a transpose, e.g. $\vec{v}^T$, and $\vec{a} \cdot \vec{b} = \vec{a}^T\vec{b}$.

## Singular Value Decomposition

### Why we care: data is a matrix, and it is usually low rank

In data-driven science, measurements are naturally stacked into a matrix. Following the book's convention, each column $\vec{x}_k$ is one "snapshot":

$$
X = \begin{bmatrix} \vert & \vert & & \vert \\ \vec{x}_1 & \vec{x}_2 & \cdots & \vec{x}_m \\ \vert & \vert & & \vert \end{bmatrix} \in \mathbb{R}^{n \times m}
$$

For example, each column can be a face image flattened into a vector ($n$ = number of pixels), or the state of a fluid simulation at time $k\Delta t$. Usually $n \gg m$: millions of numbers per snapshot, a few hundred or thousand snapshots. The matrix is tall and skinny.

The remarkable observation is that such data is typically **low rank**: a few dominant patterns explain most of it. Faces share cheeks, foreheads and mouths; a flow behind a car is dominated by periodic vortex shedding. The SVD is the tool that extracts these patterns, purely from data.

This is also what "tailored to a specific problem" means. The Fourier transform expresses any signal in a fixed, generic basis of sines and cosines. The SVD instead **learns the basis from the data itself**: it gives the best orthonormal basis for this particular matrix. A basis learned from faces is very efficient for faces, and much worse for anything else.

### The idea: rotate, stretch, rotate

For any $n \times m$ matrix $X$:

$$
X = U \Sigma V^T
$$

- $U$ ($n \times n$): orthonormal. Its columns $\vec{u}_i$ are the **left singular vectors**, a nice orthonormal basis of the output space.
- $\Sigma$ ($n \times m$): diagonal, with non-negative entries $\sigma_1 \ge \sigma_2 \ge \dots \ge 0$, the **singular values**, sorted from largest to smallest.
- $V$ ($m \times m$): orthonormal. Its columns $\vec{v}_i$ are the **right singular vectors**, a nice orthonormal basis of the input space.

Read $U\Sigma V^T\vec{x}$ from right to left, the same way as $PDP^{-1}\vec{x}$:

1. $V^T$: change coordinates of $\vec{x}$ into the $\vec{v}$-basis. Since $V$ is orthonormal, $V^{-1} = V^T$, so this is a pure rotation (possibly with a reflection). Lengths and angles are preserved, and the $i$-th new coordinate is just the dot product $\vec{v}_i \cdot \vec{x}$.
2. $\Sigma$: stretch each coordinate by $\sigma_i$. If $X$ changes dimensions, $\Sigma$ also adds zero coordinates or drops coordinates.
3. $U$: rotate the result into place in the output space.

Geometrically: **$X$ maps the unit sphere to an ellipsoid**. The $\vec{v}_i$ are the directions on the sphere that land on the axes of the ellipsoid, the $\vec{u}_i$ are the directions of those axes, and the $\sigma_i$ are the lengths of the semi-axes. If a singular value is zero, the ellipsoid gets flattened into a lower dimension.

The book builds such a matrix by hand: first stretch the axes by $\Sigma = \text{diag}(3, 1, 0.5)$, then rotate with $R_zR_yR_x$. So $X = (R_zR_yR_x)\,\Sigma\, I$, which is already an SVD with $U = R_zR_yR_x$ and $V = I$. Any matrix can be read this way, the SVD just finds the rotations for you.

Column by column, $XV = U\Sigma$ means:

$$
X\vec{v}_i = \sigma_i \vec{u}_i
$$

Compare with eigenvectors, $A\vec{v} = \lambda\vec{v}$. An eigenvector must land on its own span. A singular vector is allowed to land somewhere else ($\vec{u}_i$), with the guarantee that orthogonal inputs $\vec{v}_i$ land on orthogonal outputs $\vec{u}_i$. That weaker requirement is why the SVD always exists.

### Economy SVD

When $X$ is tall ($n \ge m$), $\Sigma$ has at most $m$ non-zero rows, and the bottom $n - m$ rows are all zeros:

$$
X = U\Sigma V^T = \begin{bmatrix} \hat{U} & \hat{U}^\perp \end{bmatrix} \begin{bmatrix} \hat{\Sigma} \\ 0 \end{bmatrix} V^T = \hat{U}\hat{\Sigma}V^T
$$

The columns $\hat{U}^\perp$ only ever get multiplied by zeros, so the **economy SVD** drops them: $\hat{U}$ is $n \times m$ and $\hat{\Sigma}$ is $m \times m$. Same matrix, much less memory. In numpy this is `np.linalg.svd(X, full_matrices=False)`.

### Where do $U$, $\Sigma$, $V$ come from? Correlations

Make square, symmetric matrices out of $X$:

$$
X^TX = (U\Sigma V^T)^T(U\Sigma V^T) = V\Sigma^T U^T U \Sigma V^T = V (\Sigma^T\Sigma) V^T
$$

$$
XX^T = U (\Sigma\Sigma^T) U^T
$$

These are exactly eigen decompositions $PDP^{-1}$. So:

- $V$ = eigenvectors of $X^TX$.
- $U$ = eigenvectors of $XX^T$.
- $\sigma_i = \sqrt{\lambda_i}$, where $\lambda_i$ are the eigenvalues of $X^TX$ (or $XX^T$, they share the non-zero ones).

These two matrices have a concrete meaning. Entry $(j, k)$ of $X^TX$ is the dot product of columns $j$ and $k$ of $X$: how similar snapshot $j$ is to snapshot $k$. Likewise, $XX^T$ holds the dot products of the rows. That's why they are called **correlation matrices**. So the SVD finds the directions that capture the most correlation in the data, ordered from most to least.

Why does this always work? $X^TX$ is symmetric, and symmetric matrices always have real eigenvalues and an **orthonormal** eigenbasis (spectral theorem). Its eigenvalues are also never negative, so the square roots are real.

To see why, take any eigenvector $\vec{v}$ of $X^TX$ with eigenvalue $\lambda$, scaled to unit length ($\lVert\vec{v}\rVert = 1$), and compute the number $\vec{v}^TX^TX\vec{v}$ in two ways:

1. Using the eigenvector equation $X^TX\vec{v} = \lambda\vec{v}$:

   $$
   \vec{v}^T(X^TX\vec{v}) = \vec{v}^T(\lambda\vec{v}) = \lambda\lVert\vec{v}\rVert^2 = \lambda
   $$

2. Grouping differently, since $(X\vec{v})^T = \vec{v}^TX^T$:

   $$
   \vec{v}^TX^TX\vec{v} = (X\vec{v})^T(X\vec{v}) = \lVert X\vec{v}\rVert^2
   $$

Both are the same number, so $\lambda = \lVert X\vec{v}\rVert^2 \ge 0$. The eigenvalue is the squared length of $X\vec{v}$, and a squared length can't be negative. It is zero exactly when $X\vec{v} = \vec{0}$, i.e. when $\vec{v}$ is in the null space of $X$.

### A worked example

$$
A = \begin{bmatrix} 3 & 0 \\ 4 & 5 \end{bmatrix}, \quad
A^TA = \begin{bmatrix} 25 & 20 \\ 20 & 25 \end{bmatrix}
$$

$\det(A^TA - \lambda I) = (25-\lambda)^2 - 400 = 0$ gives $\lambda_1 = 45$, $\lambda_2 = 5$, so $\sigma_1 = 3\sqrt{5}$ and $\sigma_2 = \sqrt{5}$. The eigenvectors are:

$$
\vec{v}_1 = \frac{1}{\sqrt{2}}\begin{bmatrix} 1 \\ 1 \end{bmatrix}, \quad
\vec{v}_2 = \frac{1}{\sqrt{2}}\begin{bmatrix} 1 \\ -1 \end{bmatrix}
$$

Then $\vec{u}_i = A\vec{v}_i / \sigma_i$:

$$
\vec{u}_1 = \frac{1}{3\sqrt{5}} \cdot \frac{1}{\sqrt{2}}\begin{bmatrix} 3 \\ 9 \end{bmatrix} = \frac{1}{\sqrt{10}}\begin{bmatrix} 1 \\ 3 \end{bmatrix}, \quad
\vec{u}_2 = \frac{1}{\sqrt{5}} \cdot \frac{1}{\sqrt{2}}\begin{bmatrix} 3 \\ -1 \end{bmatrix} = \frac{1}{\sqrt{10}}\begin{bmatrix} 3 \\ -1 \end{bmatrix}
$$

Check: $\vec{u}_1 \cdot \vec{u}_2 = 0$, as promised. Also $\det(A) = 15 = \sigma_1\sigma_2$: the rotations $U$ and $V^T$ don't change area, so all the area scaling comes from $\Sigma$.

Note that the eigenvectors of $A$ itself are $[0, 1]^T$ and $[1, -2]^T$, which are not orthogonal. The SVD picks a different, orthogonal pair of directions.

### Method of snapshots

The trick $\vec{u}_i = X\vec{v}_i / \sigma_i$ used above matters a lot in practice. If each snapshot has a million pixels, $XX^T$ has $10^{12}$ entries, impossible to even store. But $X^TX$ is only $m \times m$. Sirovich's **method of snapshots**: eigen-decompose the small $X^TX$ to get $V$ and $\Sigma$, then recover the large $U$:

$$
\tilde{U} = X\tilde{V}\tilde{\Sigma}^{-1}
$$

(keeping only the non-zero singular values so $\tilde{\Sigma}$ is invertible).

### SVD as a sum of simple pieces

Multiplying out $U\Sigma V^T$ gives a sum of rank-1 matrices (the "dyadic summation"):

$$
X = \sigma_1 \vec{u}_1\vec{v}_1^T + \sigma_2 \vec{u}_2\vec{v}_2^T + \dots + \sigma_r \vec{u}_r\vec{v}_r^T
$$

where $r$ is the rank of $X$ (the number of non-zero singular values). Each term $\vec{u}_i\vec{v}_i^T$ is the simplest possible transformation: measure how much of $\vec{x}$ points along $\vec{v}_i$ (a dot product), and output that amount along $\vec{u}_i$. The $\sigma_i$ says how important that piece is, and the pieces come **sorted by importance**.

Step by step:

1. Absorb $\Sigma$ into $U$. Multiplying by a diagonal matrix on the right scales each column by its diagonal entry (the same fact behind $AP = PD$ in the previous post):

   $$
   U\Sigma =
   \begin{bmatrix} \vert & \vert & \\ \vec{u}_1 & \vec{u}_2 & \cdots \\ \vert & \vert & \end{bmatrix}
   \begin{bmatrix} \sigma_1 & & \\ & \sigma_2 & \\ & & \ddots \end{bmatrix}
   =
   \begin{bmatrix} \vert & \vert & \\ \sigma_1\vec{u}_1 & \sigma_2\vec{u}_2 & \cdots \\ \vert & \vert & \end{bmatrix}
   $$

2. Write $V^T$ as rows. The columns of $V$ are $\vec{v}_i$, so the rows of $V^T$ are $\vec{v}_i^T$:

   $$
   X = (U\Sigma)V^T =
   \begin{bmatrix} \vert & \vert & \\ \sigma_1\vec{u}_1 & \sigma_2\vec{u}_2 & \cdots \\ \vert & \vert & \end{bmatrix}
   \begin{bmatrix} \text{---}\ \vec{v}_1^T\ \text{---} \\ \text{---}\ \vec{v}_2^T\ \text{---} \\ \vdots \end{bmatrix}
   $$

3. Multiply column times row. Any matrix product is the sum of (column $k$ of $A$) times (row $k$ of $B$). Writing $\vec{a}_k$ for column $k$ of $A$ and $\vec{b}_k^T$ for row $k$ of $B$:

   $$
   AB = \sum_k \vec{a}_k \vec{b}_k^T
   $$

   Entry $(i, j)$ of $AB$ is $\sum_k A_{ik}B_{kj}$, and entry $(i, j)$ of the outer product $\vec{a}_k\vec{b}_k^T$ is $A _{ik}B _{kj}$. Summing the outer products over $k$ gives the same entries.

4. Apply it with column $k$ of $U\Sigma$ being $\sigma_k\vec{u}_k$ and row $k$ of $V^T$ being $\vec{v}_k^T$:

   $$
   X = \sum_k (\sigma_k\vec{u}_k)\,\vec{v}_k^T = \sigma_1\vec{u}_1\vec{v}_1^T + \sigma_2\vec{u}_2\vec{v}_2^T + \cdots
   $$

5. Terms with $\sigma_k = 0$ (and the all-zero rows of $\Sigma$ that pair with $\hat{U}^\perp$) contribute nothing, which leaves exactly $r$ terms. Each $\vec{u}_k\vec{v}_k^T$ is rank 1, since every column of it is a multiple of $\vec{u}_k$.

Check with the worked example above:

$$
\sigma_1\vec{u}_1\vec{v}_1^T = \frac{3\sqrt{5}}{\sqrt{20}}\begin{bmatrix} 1 \\ 3 \end{bmatrix}\begin{bmatrix} 1 & 1 \end{bmatrix}
= \begin{bmatrix} 1.5 & 1.5 \\ 4.5 & 4.5 \end{bmatrix}, \quad
\sigma_2\vec{u}_2\vec{v}_2^T = \frac{\sqrt{5}}{\sqrt{20}}\begin{bmatrix} 3 \\ -1 \end{bmatrix}\begin{bmatrix} 1 & -1 \end{bmatrix}
= \begin{bmatrix} 1.5 & -1.5 \\ -0.5 & 0.5 \end{bmatrix}
$$

They add up to $\begin{bmatrix} 3 & 0 \\ 4 & 5 \end{bmatrix} = A$.

The first piece alone, $A _1 = \sigma _1\vec{u} _1\vec{v} _1^T$, is the best rank-1 approximation of $A$. What it misses is the error matrix, which here is exactly the second piece:

$$
E = A - A _1 = \sigma _2\vec{u} _2\vec{v} _2^T = \begin{bmatrix} 1.5 & -1.5 \\ -0.5 & 0.5 \end{bmatrix}
$$

To say how big this error is, we need a size for a matrix. The **Frobenius norm** treats a matrix as one long vector of its entries, and takes the usual vector length: square every entry, add them up, take the square root.

$$
\lVert M \rVert _F = \sqrt{\sum _{i,j} M _{ij}^2}
$$

For the error matrix:

$$
\lVert E \rVert _F^2 = 1.5^2 + (-1.5)^2 + (-0.5)^2 + 0.5^2 = 5 = \sigma _2^2
$$

That's no coincidence. For any rank-1 piece, entry $(i, j)$ of $\sigma\vec{u}\vec{v}^T$ is $\sigma u _i v _j$, so

$$
\lVert \sigma\vec{u}\vec{v}^T \rVert _F^2 = \sum _{i,j} \sigma^2 u _i^2 v _j^2 = \sigma^2 \Big(\sum _i u _i^2\Big)\Big(\sum _j v _j^2\Big) = \sigma^2 \lVert\vec{u}\rVert^2\lVert\vec{v}\rVert^2 = \sigma^2
$$

since $\vec{u}$ and $\vec{v}$ are unit vectors. **The singular value is exactly the size of its piece.**

Moreover, seen as long vectors, the pieces are orthogonal to each other (because the $\vec{u} _i$ are orthogonal and the $\vec{v} _i$ are orthogonal). So their squared sizes add up like in Pythagoras' theorem:

$$
\lVert A \rVert _F^2 = \sigma _1^2 + \sigma _2^2 + \cdots, \qquad
\lVert A - A _k \rVert _F^2 = \sigma _{k+1}^2 + \sigma _{k+2}^2 + \cdots
$$

Check: $\lVert A \rVert _F^2 = 3^2 + 0^2 + 4^2 + 5^2 = 50 = 45 + 5 = \sigma _1^2 + \sigma _2^2$. The rank-1 approximation captures 45 of the 50 (90% of the "energy"), and the error is the remaining 5.

For a data matrix, read it this way: $\vec{u}_i$ is a pattern (e.g. a spatial shape), and $\sigma_i\vec{v}_i^T$ says how much of that pattern is present in each snapshot (e.g. over time). If the columns are spatial measurements over time, $U$ holds spatial patterns and $V$ holds temporal patterns.

This also gives orthonormal bases for the four fundamental subspaces of the previous post:

- $\vec{u}_1, \dots, \vec{u}_r$ span the column space of $X$.
- $\vec{v}_1, \dots, \vec{v}_r$ span the row space of $X$.
- $\vec{v}_{r+1}, \dots, \vec{v}_m$ (the ones with $\sigma = 0$) span the null space: those directions get squished to $\vec{0}$.
- $\vec{u}_{r+1}, \dots, \vec{u}_n$ span the rest of the output space that $X$ can never reach.

### Truncation: keep only what matters

Keep only the first $k$ terms, with $k < r$ (keeping all $r$ non-zero terms would give back $X$ exactly):

$$
X \approx \tilde{X} = \sum _{i=1}^{k} \sigma _i \vec{u} _i\vec{v} _i^T = \tilde{U} \tilde{\Sigma} \tilde{V}^T
$$

The tilde means "keep only the first $k$":

- $\tilde{U} = [\vec{u} _1, \dots, \vec{u} _k]$, the first $k$ columns of $U$ ($n \times k$).
- $\tilde{\Sigma} = \text{diag}(\sigma _1, \dots, \sigma _k)$, the top-left $k \times k$ block of $\Sigma$.
- $\tilde{V} = [\vec{v} _1, \dots, \vec{v} _k]$, the first $k$ columns of $V$ ($m \times k$).

Multiplying them out column times row, exactly as in the dyadic summation steps, gives the sum. So the sum and $\tilde{U}\tilde{\Sigma}\tilde{V}^T$ are two ways to write the same matrix.

**Eckart–Young theorem**: $\tilde{X}$ is the best rank-$k$ approximation of $X$ in the least-squares sense:

$$
\underset{\tilde{X},\ \text{rank}(\tilde{X}) = k}{\arg\min} \lVert X - \tilde{X} \rVert _F = \tilde{U}\tilde{\Sigma}\tilde{V}^T
$$

No other rank-$k$ matrix gets closer. The error is exactly what you threw away, $\lVert X - \tilde{X} \rVert _F^2 = \sigma _{k+1}^2 + \sigma _{k+2}^2 + \dots + \sigma _r^2$.

**Example: image compression.** A grayscale image is just a matrix. The book's $2000 \times 1500$ photo of a dog stores $3 \times 10^6$ numbers. Keeping $k = 100$ terms means storing the first 100 columns of $U$ and $V$ plus 100 singular values: $100 \times (2000 + 1500 + 1)$ numbers, about 11.7% of the original, and the image already looks quite accurate. With $k = 5$ (0.57% storage) you only see blurry blobs; with $k = 20$ (2.33%) the dog is recognizable.

### How many terms to keep?

This is one of the most important (and contentious) choices when using the SVD. Common options:

1. **Energy threshold.** Keep enough terms to capture, e.g., 90% or 99% of the "energy". The book plots the cumulative sum of the singular values, $\sum _{i=1}^{k}\sigma _i / \sum _i\sigma _i$. Another common definition uses squares, $\sum _{i=1}^{k}\sigma _i^2 / \sum _i\sigma _i^2$, which matches the Frobenius error above. Crude, but widely used.
2. **Elbow.** Plot $\sigma_k$ on a log scale and look for the "knee" where the curve flattens: the big values are signal, the flat tail is noise.
3. **Optimal hard threshold (Gavish & Donoho).** If the data is a low-rank signal plus Gaussian white noise of magnitude $\gamma$, there is a provably optimal cutoff $\tau$: keep only the $\sigma_k > \tau$. For a square $n \times n$ matrix with known noise, $\tau = \frac{4}{\sqrt{3}}\sqrt{n}\,\gamma$. When the noise level is unknown (the usual case), $\tau = \omega(\beta)\,\sigma_{\text{med}}$, where $\sigma_{\text{med}}$ is the median singular value and $\omega(\beta)$ depends only on the aspect ratio $\beta = m/n$. In the book's toy example, this cleans up noise much better than a 90% energy cutoff.

One caveat: the SVD assumes the data "separates" into column patterns times row patterns. Data that is shifted or misaligned (e.g. a traveling wave) looks artificially high rank, even if it is simple.

### Pseudo-inverse and least squares

The SVD also solves $A\vec{x} = \vec{b}$ when $A$ is not square or not invertible. Write $A = \tilde{U}\tilde{\Sigma}\tilde{V}^T$, keeping all $r$ non-zero singular values (so this is exact, not an approximation). Then undo each step in turn: rotate back with $\tilde{U}^T$, un-stretch with $\tilde{\Sigma}^{-1}$, rotate back with $\tilde{V}$. That gives the Moore–Penrose **pseudo-inverse**:

$$
A^\dagger = \tilde{V}\tilde{\Sigma}^{-1}\tilde{U}^T, \quad \tilde{\vec{x}} = A^\dagger\vec{b}
$$

- If there are too many equations (tall $A$, usually no exact solution), $\tilde{\vec{x}}$ is the **least-squares** solution minimizing $\lVert A\vec{x} - \vec{b}\rVert_2$.
- If there are too few equations (wide $A$, infinitely many solutions), $\tilde{\vec{x}}$ is the **minimum-norm** solution.

Plugging back in, $A\tilde{\vec{x}} = \tilde{U}\tilde{U}^T\vec{b}$. This is not $\vec{b}$ in general: $\tilde{U}\tilde{U}^T$ projects $\vec{b}$ onto the column space of $A$, which is the closest point that $A$ can actually reach. A common mistake is to assume $\tilde{U}\tilde{U}^T = I$. Only $\tilde{U}^T\tilde{U} = I$ holds for a truncated $\tilde{U}$.

It's cheap, too: inverting orthonormal matrices is just a transpose, and inverting a diagonal matrix is just taking reciprocals.

The 1D case gives a nice intuition. Fit $\vec{b} \approx \vec{a}x$ (a line through the origin with slope $x$). The SVD of the single column $\vec{a}$ is $\tilde{U} = \vec{a}/\lVert\vec{a}\rVert$, $\tilde{\Sigma} = \lVert\vec{a}\rVert$, $\tilde{V} = 1$, so:

$$
x = \frac{\vec{a} \cdot \vec{b}}{\lVert\vec{a}\rVert^2}
$$

The best slope is the dot product of $\vec{b}$ with the unit direction of $\vec{a}$ (a projection, as in the dot-product section of the previous post), divided once more by $\lVert\vec{a}\rVert$ because $\vec{a}$ was not normalized.

## PCA

### The question PCA answers

Suppose we have $n$ samples (experiments, patients, people), each with $m$ measured features. PCA literature puts each sample as a **row** of the data matrix $X$ ($n \times m$), the opposite of the snapshot-as-column convention above. As everywhere in this post, vectors are columns, so if sample $j$ is the vector $\vec{x}_j \in \mathbb{R}^m$, it appears in $X$ transposed:

$$
X = \begin{bmatrix} \text{---}\ \vec{x}_1^T\ \text{---} \\ \vdots \\ \text{---}\ \vec{x}_n^T\ \text{---} \end{bmatrix}
$$

Plot the samples and you get a cloud of points in $m$ dimensions.

PCA asks: **which direction does the cloud spread out the most?** Then: which direction, orthogonal to the first, spreads out the most next? And so on. These directions are the **principal components**. If the cloud is long and thin, the first direction captures most of the information and the others are mostly noise. 

### Step 1: center the data

Spread is measured around the center, so subtract the mean of each column (feature). First compute the mean of every feature, and collect them into the **mean vector** $\bar{\vec{x}}$:

$$
\bar{x} _j = \frac{1}{n}\sum _{i=1}^{n} X _{ij}, \qquad
\bar{\vec{x}} = \begin{bmatrix} \bar{x} _1 \\ \bar{x} _2 \\ \vdots \\ \bar{x} _m \end{bmatrix} = \frac{1}{n}\sum _{j=1}^{n} \vec{x} _j
$$

$\bar{x} _j$ is the average of column $j$ (e.g. the average height of all people), so $\bar{\vec{x}} \in \mathbb{R}^m$ is the "average sample", the center of the cloud. Like every sample, it appears in $X$-shaped matrices as the row $\bar{\vec{x}}^T$.

To subtract it from every sample at once, stack $n$ copies of $\bar{\vec{x}}^T$ into an $n \times m$ matrix. A column of ones ($n \times 1$) times the row $\bar{\vec{x}}^T$ ($1 \times m$) does exactly that, since each row of the product is $1 \cdot \bar{\vec{x}}^T$:

$$
\bar{X} = \begin{bmatrix} 1 \\ \vdots \\ 1 \end{bmatrix} \bar{\vec{x}}^T
= \begin{bmatrix} \bar{x} _1 & \cdots & \bar{x} _m \\ \vdots & & \vdots \\ \bar{x} _1 & \cdots & \bar{x} _m \end{bmatrix}, \qquad
B = X - \bar{X}
$$

Each row of $B$ is a sample minus the average sample, $\vec{b} _j^T = (\vec{x} _j - \bar{\vec{x}})^T$, so the cloud is now centered at the origin, and every column of $B$ averages to zero.

Without this step, the first direction found would just point from the origin to the center of the cloud, which says nothing about its shape. The book also recommends scaling each feature to unit variance before the SVD (see practical notes).

### Step 2: find the direction of maximum variance

Why maximum variance? Because the direction with the most variance is also the line that fits the data best. Step by step:

**(a) Split each point.** Take a centered point $\vec{b} _j$ and a unit direction $\vec{w}$. The point is its projection onto the line, $(\vec{b} _j^T\vec{w})\vec{w}$, plus a perpendicular leftover $\vec{b} _j - (\vec{b} _j^T\vec{w})\vec{w}$.

**(b) Apply Pythagoras.** The two pieces are perpendicular, so

$$
\lVert\vec{b} _j\rVert^2 = \underbrace{(\vec{b} _j^T\vec{w})^2} _{\text{kept}} + \underbrace{\lVert\vec{b} _j - (\vec{b} _j^T\vec{w})\vec{w}\rVert^2} _{\text{lost}}
$$

**(c) Sum over all samples.** The left side, $\sum _j \lVert\vec{b} _j\rVert^2$, is fixed by the data and does not depend on $\vec{w}$. So whatever is kept is not lost, and vice versa.

**(d) Conclude.** Maximizing the kept part, $\sum _j (\vec{b} _j^T\vec{w})^2$ (which is $n-1$ times the variance along $\vec{w}$), is the same as minimizing the lost part, the total squared distance from the points to the line.

So the maximum-variance direction is the best-fitting line through the cloud, and dropping the low-variance directions throws away as little as possible. The same argument with $k$ directions gives the best-fitting $k$-dimensional subspace, which is Eckart–Young seen from the PCA side.

The assumption is that large variance is signal and small variance is noise or redundancy. That often holds, but two caveats apply:

- Units matter: measuring a feature in millimetres instead of metres inflates its variance, which is why features are often standardized first.
- PCA ignores labels: a direction that separates two classes can have small variance and get dropped.

Now the computation. Project every centered sample $\vec{b}_j$ (row $j$ of $B$ is $\vec{b}_j^T$) onto a unit direction $\vec{w}$. The projected value is a dot product, $\vec{b}_j \cdot \vec{w} = \vec{b}_j^T\vec{w}$, which for all samples at once is $B\vec{w}$. The variance of those projections is:

$$
\frac{1}{n-1}\lVert B\vec{w}\rVert^2 = \vec{w}^T \underbrace{\frac{B^TB}{n-1}}_{C} \vec{w}
$$

where $C$ is the **covariance matrix** of the data, defined as

$$
C = \frac{1}{n-1} B^TB \qquad (m \times m)
$$

Where this comes from:

1. The projections are just numbers, $p_j = \vec{b}_j \cdot \vec{w}$. Stacking them gives $B\vec{w}$, since each row $\vec{b}_j^T$ of $B$ times $\vec{w}$ is one entry:

   $$
   B\vec{w} = \begin{bmatrix} \vec{b}_1^T\vec{w} \\ \vdots \\ \vec{b}_n^T\vec{w} \end{bmatrix} = \begin{bmatrix} p_1 \\ \vdots \\ p_n \end{bmatrix}
   $$

2. Their sample variance is the usual formula:

   $$
   \text{Var}(p) = \frac{1}{n-1}\sum_{j=1}^{n}(p_j - \bar{p})^2
   $$

3. The mean is zero because the data is centered. Dot products are linear, so the mean of the projections is the projection of the mean:

   $$
   \bar{p} = \frac{1}{n}\sum_j \vec{b}_j \cdot \vec{w} = \Big(\frac{1}{n}\sum_j \vec{b}_j\Big) \cdot \vec{w} = \vec{0} \cdot \vec{w} = 0
   $$

   So $\text{Var}(p) = \frac{1}{n-1}\sum_j p_j^2$. This is the payoff of Step 1.

4. A sum of squares is a squared length: $\sum_j p_j^2 = \lVert B\vec{w}\rVert^2$.

5. Using $\lVert\vec{y}\rVert^2 = \vec{y}^T\vec{y}$ and $(B\vec{w})^T = \vec{w}^TB^T$:

   $$
   \frac{1}{n-1}(B\vec{w})^T(B\vec{w}) = \vec{w}^T\Big(\frac{B^TB}{n-1}\Big)\vec{w}
   $$

   Pulling $\vec{w}$ out to the sides separates the direction we choose ($\vec{w}$) from a matrix that depends only on the data ($C$). That turns "find the best direction" into an eigenvector problem.

Why $n-1$ and not $n$? This is Bessel's correction: the mean was estimated from the same data, which makes the deviations slightly smaller than around the true mean, and dividing by $n-1$ compensates. For PCA it is just a constant factor that scales every variance equally, so it doesn't change which direction wins.

Why is $C$ called the covariance matrix? Entry $(i, k)$ of $B^TB$ is the dot product of columns $i$ and $k$ of $B$, and $B _{ji} = X _{ji} - \bar{x} _i$ is how far sample $j$'s feature $i$ is from its mean. Written out entry by entry:

$$
C _{ik} = \frac{1}{n-1}\sum _{j=1}^{n} (X _{ji} - \bar{x} _i)(X _{jk} - \bar{x} _k)
$$

That is the textbook definition of the covariance of features $i$ and $k$: the average of (feature $i$'s deviation) times (feature $k$'s deviation). It is positive if the two features tend to be above or below their means together, negative if one tends to be high when the other is low, and near zero if they are unrelated. On the diagonal ($i = k$) it becomes the average squared deviation, i.e. the variance of feature $i$.

For example, with two features, height and weight:

$$
C = \begin{bmatrix} \text{Var}(\text{height}) & \text{Cov}(\text{height}, \text{weight}) \\ \text{Cov}(\text{weight}, \text{height}) & \text{Var}(\text{weight}) \end{bmatrix}
$$

The off-diagonal entries are equal ($C _{ik} = C _{ki}$), so $C$ is always symmetric. So the first principal direction is:

$$
\vec{w}_1 = \underset{\lVert\vec{w}\rVert = 1}{\arg\max}\ \vec{w}^T B^TB \vec{w}
$$

Which unit $\vec{w}$ maximizes $\vec{w}^TC\vec{w}$? The answer is the top eigenvector of $C$, because $\vec{w}^TC\vec{w}$ turns out to be a weighted average of the eigenvalues:

1. Rewrite in the eigenbasis. $C$ is symmetric, so it has an orthonormal eigenbasis: $C = Q\Lambda Q^T$, where the columns of $Q$ are the eigenvectors $\vec{q} _1, \dots, \vec{q} _m$ and $\Lambda = \text{diag}(\lambda _1, \dots, \lambda _m)$ with $\lambda _1 \ge \lambda _2 \ge \dots \ge 0$. Write $\vec{w}$ in eigenbasis coordinates, $\vec{w} = Q\vec{c} = c _1\vec{q} _1 + \dots + c _m\vec{q} _m$. Then

   $$
   \vec{w}^TC\vec{w} = \vec{c}^TQ^T(Q\Lambda Q^T)Q\vec{c} = \vec{c}^T\Lambda\vec{c} = \lambda _1 c _1^2 + \lambda _2 c _2^2 + \dots + \lambda _m c _m^2
   $$

   This is the same change-of-basis idea as $A = PDP^{-1}$: in its own eigenbasis, $C$ only scales.

2. The weights add up to 1. $Q$ is a rotation, so it doesn't change lengths, and a unit $\vec{w}$ has unit coordinates:

   $$
   c _1^2 + c _2^2 + \dots + c _m^2 = \lVert\vec{c}\rVert^2 = \lVert\vec{w}\rVert^2 = 1
   $$

   So the weights $c _i^2$ are non-negative and sum to 1: $\vec{w}^TC\vec{w}$ is a **weighted average** of the eigenvalues.

3. An average can't beat the maximum. Replacing every $\lambda _i$ by the largest one, $\lambda _1$, can only make the sum bigger:

   $$
   \lambda _1 c _1^2 + \lambda _2 c _2^2 + \dots + \lambda _m c _m^2 \;\le\; \lambda _1 (c _1^2 + c _2^2 + \dots + c _m^2) = \lambda _1
   $$

   The bound is reached by putting all the weight on the largest eigenvalue: $c _1 = 1$ and all other $c _i = 0$, i.e. $\vec{w} = \vec{q} _1$. Any weight moved to a smaller eigenvalue pulls the average down. It's like averaging grades: however you weight your courses, your average can't exceed your best grade.

- The first principal direction is the eigenvector of $C$ with the largest eigenvalue.
- The variance along it is that eigenvalue $\lambda _1$.
- The next directions are the next eigenvectors, automatically orthogonal.

In eigenbasis coordinates, $C$ becomes diagonal: the new coordinates are **uncorrelated**. PCA is a change of basis (as in the previous post) to the coordinate system where the features no longer vary together.

What does that mean? Take centered height and weight with covariance matrix

$$
C = \begin{bmatrix} 25 & 20 \\ 20 & 25 \end{bmatrix}
$$

The off-diagonal 20 says the features are correlated: taller people tend to be heavier, and the cloud is a tilted ellipse. Knowing someone is above average in height lets you guess they are probably above average in weight too, so the two coordinates share information.

This $C$ has eigenvectors $\vec{q} _1 = \frac{1}{\sqrt{2}}[1, 1]^T$ and $\vec{q} _2 = \frac{1}{\sqrt{2}}[1, -1]^T$, with eigenvalues 45 and 5. For one person, let $\vec{b}$ be their centered sample (a row of $B$, as in Step 1):

$$
\vec{b} = \begin{bmatrix} \text{height} - \overline{\text{height}} \\ \text{weight} - \overline{\text{weight}} \end{bmatrix}
$$

Describe each person by the projections of $\vec{b}$ onto the eigenvectors instead of by height and weight (below, "height" and "weight" are short for the centered values, the two entries of $\vec{b}$):

$$
z _1 = \vec{q} _1^T\vec{b} = \tfrac{1}{\sqrt{2}}(\text{height} + \text{weight}) \ \ \text{("overall size")}, \qquad
z _2 = \vec{q} _2^T\vec{b} = \tfrac{1}{\sqrt{2}}(\text{height} - \text{weight}) \ \ \text{("tall for one's weight")}
$$

The data points don't move; we only describe them in new axes that point along the long and short axes of the ellipse. To get the variances and covariance of the new coordinates, use the variance formula from above: the variance along a unit direction $\vec{q}$ is $\vec{q}^TC\vec{q}$, and likewise the covariance of the projections onto two directions is $\vec{q} _1^TC\vec{q} _2$. For example,

$$
\text{Var}(z _1) = \vec{q} _1^TC\vec{q} _1 = \tfrac{1}{2}\begin{bmatrix} 1 & 1 \end{bmatrix}\begin{bmatrix} 25 & 20 \\ 20 & 25 \end{bmatrix}\begin{bmatrix} 1 \\ 1 \end{bmatrix} = \tfrac{1}{2}(25 + 25 + 2 \cdot 20)
$$

This is the familiar rule $\text{Var}(aX + bY) = a^2\text{Var}(X) + b^2\text{Var}(Y) + 2ab\,\text{Cov}(X, Y)$ with $a = b = \frac{1}{\sqrt{2}}$. For $z _2$ the minus sign flips the covariance term, and in $\text{Cov}(z _1, z _2)$ the two covariance contributions cancel:

$$
\text{Var}(z _1) = \tfrac{1}{2}(25 + 25 + 2 \cdot 20) = 45, \quad
\text{Var}(z _2) = \tfrac{1}{2}(25 + 25 - 2 \cdot 20) = 5, \quad
\text{Cov}(z _1, z _2) = \tfrac{1}{2}(25 - 25) = 0
$$

So in the new coordinates the covariance matrix is $\begin{bmatrix} 45 & 0 \\ 0 & 5 \end{bmatrix}$. The zero off-diagonal means $z _1$ and $z _2$ are uncorrelated: knowing someone's "size" tells you nothing (linearly) about whether they are tall for their weight. The diagonal holds the variances along the new axes, which are exactly the eigenvalues. Seen from these axes, the ellipse is no longer tilted.

In general, with all eigenvectors as the columns of $Q$, the new coordinates of all samples are $Z = BQ$, and their covariance matrix is

$$
\frac{1}{n-1}Z^TZ = Q^T\Big(\frac{B^TB}{n-1}\Big)Q = Q^TCQ = \Lambda
$$

This is the same move as $D = P^{-1}AP$ in the previous post: the same object, seen from its eigenbasis, becomes diagonal.

Why this matters: correlated features are partly redundant (height and weight largely tell you the same thing, "size"). After the rotation, each coordinate carries its own information, and its variance (45 vs. 5) says how much it matters, so the small ones can be dropped with little loss. That is Step 4. One caveat: uncorrelated is weaker than independent. PCA removes linear relationships between coordinates, but a curved relationship can remain.

### Step 3: PCA is just the SVD of $B$

Take the SVD of the centered data, $B = U\Sigma V^T$. Then:

$$
C = \frac{B^TB}{n-1} = V \frac{\Sigma^T\Sigma}{n-1} V^T
$$

That is the eigen decomposition of $C$. So:

| PCA | SVD of $B$ |
| --- | --- |
| Principal directions | Columns of $V$ |
| Variance along direction $i$ | $\lambda_i = \sigma_i^2 / (n-1)$ |
| Coordinates of samples in the new basis ("scores") | $T = BV = U\Sigma$ |

A handy trick from the book: take the SVD of $B / \sqrt{n}$ instead. Then the singular values are directly the standard deviations along each principal direction.

In practice, compute PCA with the SVD rather than forming $C$ explicitly. Forming $B^TB$ squares the condition number and loses numerical precision.

### Example: a noisy Gaussian cloud

The book's example makes the geometry very concrete. Generate 10,000 2D points from a standard normal distribution, then:

1. stretch them by 2 along $x$ and by 0.5 along $y$,
2. rotate by $\pi/3$,
3. shift the center to $[2, 1]^T$.

That is, the data is literally built as rotate $\cdot$ stretch $\cdot$ (random points) + shift. Now forget how it was built and run PCA: subtract the mean, take the SVD of $B/\sqrt{n}$. The singular values come out as $1.974$ and $0.503$ (vs. the true 2 and 0.5), and the singular vectors match the rotation by $\pi/3$ up to sign:

$$
R_{\pi/3} = \begin{bmatrix} 0.5 & -0.8660 \\ 0.8660 & 0.5 \end{bmatrix}, \quad
U = \begin{bmatrix} -0.4998 & -0.8662 \\ -0.8662 & 0.4998 \end{bmatrix}
$$

PCA recovered the stretch and the rotation purely from the data. Drawing $\sigma_1\vec{u}_1$ and $\sigma_2\vec{u}_2$ from the mean gives the axes of the cloud, and scaling the unit circle by $U\Sigma$ gives the 1, 2 and 3 standard-deviation ellipses. (In this example the points are stored as columns, so the directions are in $U$ rather than $V$.)

### Step 4: reduce the dimension

Keep only the first $k$ principal directions, $V_k$, and each sample goes from $m$ numbers to $k$ numbers:

$$
T_k = BV_k
$$

By Eckart–Young, this is the best possible $k$-dimensional linear summary of the data. The fraction of variance kept is:

$$
\frac{\sum_{i=1}^{k}\lambda_i}{\sum_{i=1}^{m}\lambda_i} = \frac{\sum_{i=1}^{k}\sigma_i^2}{\sum_{i=1}^{m}\sigma_i^2}
$$

**Example: ovarian cancer.** 216 patients (121 with ovarian cancer, 95 without), each with expression levels of 4000 genes. The singular values drop quickly, because gene expressions are highly correlated. Projecting each patient onto just the first three principal components (three dot products, $\vec{v}_1 \cdot \vec{x}$, $\vec{v}_2 \cdot \vec{x}$, $\vec{v}_3 \cdot \vec{x}$) turns 4000 numbers into a 3D point, and patients with and without cancer form visibly separate clusters. Clustering in PCA space is a foundation of machine learning and pattern recognition.

### Example: eigenfaces

The most famous demonstration of SVD/PCA. Take the Extended Yale Face Database: $192 \times 168$ pixel face images under 64 lighting conditions. Use 36 people for training and hold back 2 for testing.

1. Flatten each image into a column of $32{,}256$ pixels.
2. Compute the average face and subtract it from each column (the centering step of PCA).
3. Take the economy SVD of the resulting matrix $X$. The columns of $U$, reshaped back into $192 \times 168$ images, are the **eigenfaces**.

To represent a new face $\vec{x}$ that was never in the training data, project it onto the first $k$ eigenfaces and add the average back:

$$
\tilde{\vec{x}} = \bar{\vec{x}} + \tilde{U}\tilde{U}^T(\vec{x} - \bar{\vec{x}})
$$

$\tilde{U}^T(\vec{x} - \bar{\vec{x}})$ gives the $k$ coordinates of the face in "eigenface space", and $\tilde{U}$ turns them back into an image. With $k \le 200$ the result is poor; past $k = 400$ it becomes a passable likeness. Fun fact: the eigenfaces can even roughly approximate a dog or a cappuccino, since they capture broad, smooth features rather than anything specific to faces.

The coordinates themselves are useful: images of two different people, projected onto just the 5th and 6th eigenfaces, already fall into two separate clusters. Some principal components capture what all faces share, some capture lighting, and some distinguish individuals. This is the basis of classic face recognition.

### Putting it together

```python
import numpy as np

# X: n samples (rows) x m features (columns)
X_mean = X.mean(axis=0)
B = X - X_mean

U, S, Vt = np.linalg.svd(B, full_matrices=False)

variance = S**2 / (X.shape[0] - 1)       # variance along each principal direction
explained = variance / variance.sum()     # fraction of variance explained

k = 2
T_k = B @ Vt[:k].T                        # n x k: data in the top-k principal coordinates
X_approx = T_k @ Vt[:k] + X_mean          # back to the original space (rank-k reconstruction)
```

### Practical notes

1. **Centering is essential.** Forgetting to subtract the mean is the most common PCA bug.
2. **Scaling matters.** Variance depends on units: height in millimeters would dominate weight in kilograms. If features have different units, also divide each column by its standard deviation (equivalently, do PCA on the correlation matrix).
3. **Signs are arbitrary.** If $\vec{v}_i$ is a principal direction, so is $-\vec{v}_i$ (with $\vec{u}_i$ flipped too). Different libraries return different signs, as in the noisy Gaussian example.
4. **Rows vs columns.** With samples as rows, the principal directions are the columns of $V$. With samples as columns (snapshots, eigenfaces), the roles swap and the principal directions are the columns of $U$.
5. **PCA is linear.** It finds the best flat subspace. If the data lies on a curved surface, PCA can't unroll it.

## References

1. [Steve Brunton](https://www.youtube.com/watch?v=gXbThCXjZFM&list=PLMrJAkhIeNNSVjnsviglFoY2nXildDCcv&index=1)
2. Book: [Data Driven Science & Engineering](https://databookuw.com/databook.pdf), Chapter 1
3. [3Blue1Brown](https://youtu.be/PFDu9oVAE-g?si=pMQHEo7CZ41-ls_i)
