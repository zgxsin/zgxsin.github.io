---
title: Linear Algebra Essentials
published: true
date: 2026-01-15
author: "Guoxiang (Shawn) Zhou"
---

## Linear Transformations

Visually, a transformation is linear if it has two properties:

1. The origin stays fixed.
2. Grid lines remain parallel and evenly spaced.

## Matrices

Think of matrices as linear transformations. The columns of a matrix are where the basis vectors land.

The determinant is the factor by which the transformation scales areas (volumes in 3D). A negative determinant means the orientation is flipped (in 3D, a right-handed coordinate system becomes left-handed). A determinant of zero means space is squished into a lower dimension.

## Inverse matrices, column space and null space

- Inverse Matrix $A^{-1}$

  This is the reverse transformation of the original matrix $A$. The inverse matrix $A^{-1}$ exists if and only if $\det(A) \neq 0$.

- Column Space

  The set of all possible outputs $A\vec{x}$ is the column space of $A$. The span of the columns is the column space.

- Null Space or kernel of the matrix $A$

  The set of all $\vec{x}$ with $A\vec{x} = \vec{0}$ is the null space or kernel of the matrix $A$.

- Matrix Rank

  The rank is the number of dimensions in the column space. A matrix has full rank when its rank is as large as possible, i.e. the smaller of its number of rows and columns. A full-rank square matrix squishes no dimension, so it is invertible.

## Nonsquare matrices as transformations between dimensions

Take the following $3 \times 2$ matrix for example:

$$
\underbrace{\begin{bmatrix} \color{#3a9a5b}2 & \color{#d9534f}0 \\ \color{#3a9a5b}-1 & \color{#d9534f}1 \\ \color{#3a9a5b}-2 & \color{#d9534f}1 \end{bmatrix}}_{3 \text{ rows} \,\times\, 2 \text{ columns}}
$$

Its two columns are where the two 2D basis vectors land, and each is a 3D vector. So it transforms a vector in 2D space to a vector in 3D space. The outputs lie on a plane through the origin of the 3D space (the column space). The number of dimensions in the column space (2) is the same as the number of dimensions in the input space, so the matrix is still full rank.

## Dot products and duality

A dot product with a fixed vector can be thought of as a linear transformation from 2D space to the 1D number line. Its matrix is the $1 \times 2$ matrix obtained by tipping that vector on its side.

From

$$
\begin{bmatrix} x_1 \\ y_1 \end{bmatrix} \cdot \begin{bmatrix} x_2 \\ y_2 \end{bmatrix}
$$

to

$$
\underbrace{\begin{bmatrix} x_1 & y_1 \end{bmatrix}}_{\text{transform}} \begin{bmatrix} x_2 \\ y_2 \end{bmatrix} = x_1 x_2 + y_1 y_2
$$

## Cramer's rule

Cramer's rule solves $A\vec{x} = \vec{v}$ for $\vec{x}$. Start with a special case.

An orthonormal transformation (a rotation, possibly with a reflection) preserves dot products:

$$
T(\vec{v}) \cdot T(\vec{w}) = \vec{v} \cdot \vec{w} \quad \text{for all } \vec{v}, \vec{w}
$$

In other words, $T$ preserves lengths and angles.

Think about the following example.

$$
\begin{bmatrix}
\cos(30^\circ) & -\sin(30^\circ)
\\ \sin(30^\circ) & \cos(30^\circ)
\end{bmatrix}
\begin{bmatrix} x \\ y \end{bmatrix}
=
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
$$

where

$$
A = \begin{bmatrix}
\cos(30^\circ) & -\sin(30^\circ)
\\ \sin(30^\circ) & \cos(30^\circ)
\end{bmatrix}
$$

The transformation $A$ takes $[x, y]^T$ to $[1, 2]^T$. Since $A$ is orthonormal, the dot product of $[x, y]^T$ with the first basis vector is unchanged by the transformation:

$$
x = \begin{bmatrix} x \\ y \end{bmatrix} \cdot \begin{bmatrix} 1 \\ 0 \end{bmatrix} =
\left(A\begin{bmatrix} x \\ y \end{bmatrix}\right) \cdot \left(A\begin{bmatrix} 1 \\ 0 \end{bmatrix}\right) =
\begin{bmatrix} 1 \\ 2 \end{bmatrix} \cdot \begin{bmatrix}
\cos(30^\circ) \\ \sin(30^\circ)
\end{bmatrix}
$$

Similarly, with the second basis vector:

$$
y = \begin{bmatrix} 1 \\ 2 \end{bmatrix} \cdot \begin{bmatrix}
-\sin(30^\circ) \\ \cos(30^\circ)
\end{bmatrix}
$$

But an orthonormal matrix is a special case. A general matrix does not preserve dot products, so this trick fails. Take the following for example:

$$
\begin{bmatrix}
2 & -1
\\ 0 & 1
\end{bmatrix}
\begin{bmatrix} x \\ y \end{bmatrix}
=
\begin{bmatrix} 4 \\ 2 \end{bmatrix},
\quad
A = \begin{bmatrix}
2 & -1
\\ 0 & 1
\end{bmatrix}
$$

Use areas instead of dot products. The parallelogram spanned by $\hat{i}$ and $[x, y]^T$ has signed area $y$. After the transformation, every area is scaled by $\det(A)$, and that parallelogram is spanned by $A\hat{i}$ (the first column of $A$) and the output $\vec{v}$. So

$$
y = \frac{\det\begin{bmatrix} 2 & 4 \\ 0 & 2 \end{bmatrix}}{\det(A)} = \frac{4}{2} = 2
$$

The same argument with $\hat{j}$ gives $x$: the parallelogram spanned by $[x, y]^T$ and $\hat{j}$ has signed area $x$, so replace the first column of $A$ with $\vec{v}$:

$$
x = \frac{\det\begin{bmatrix} 4 & -1 \\ 2 & 1 \end{bmatrix}}{\det(A)} = \frac{6}{2} = 3
$$

Check: $2 \cdot 3 - 2 = 4$ and $2 = 2$. In general, Cramer's rule says each coordinate is $\det(A_i) / \det(A)$, where $A_i$ is $A$ with its $i$-th column replaced by $\vec{v}$.

## Change of Basis

Suppose Jennifer uses a different basis. Write her basis vectors in our coordinates and put them in the columns of $A$:

$$
A = \begin{bmatrix} \color{#3a9a5b}2 & \color{#d9534f}-1 \\ \color{#3a9a5b}1 & \color{#d9534f}1 \end{bmatrix}
$$

$A$ translates a vector from her coordinates into ours:

$$
A \underbrace{\begin{bmatrix} x_j \\ y_j \end{bmatrix}}_{\text{her coordinates}} = \underbrace{\begin{bmatrix} x_o \\ y_o \end{bmatrix}}_{\text{our coordinates}}
$$

and $A^{-1}$ translates from our coordinates into hers.

## Eigenvectors and Eigenvalues

Most vectors get knocked off their span during a linear transformation. Eigenvectors are the special vectors that remain on their own span, they only get stretched or squished. The eigenvalue is the factor by which an eigenvector is stretched or squished (it can be negative or fractional).

For example, the matrix below stretches all vectors on the x-axis by a factor of 3, and all vectors on the line spanned by $[-1, 1]^T$ by a factor of 2.

$$
A = \begin{bmatrix}
3 & 1
\\ 0 & 2
\end{bmatrix}
$$

For a 3D rotation, the eigenvector is the axis of rotation, and its eigenvalue is 1 since rotations do not change lengths.

- Computing eigenvalues and eigenvectors

  Symbolically, an eigenvector $\vec{v}$ with eigenvalue $\lambda$ satisfies:

  $$
  A\vec{v} = \lambda\vec{v} \;\Rightarrow\; (A - \lambda I)\vec{v} = \vec{0}
  $$

  For a non-zero $\vec{v}$ to be sent to $\vec{0}$, $A - \lambda I$ must squish space into a lower dimension, which means:

  $$
  \det(A - \lambda I) = 0
  $$

  For the example above, $(3-\lambda)(2-\lambda) = 0$, so $\lambda = 2$ or $\lambda = 3$. Plug each $\lambda$ back in and solve $(A - \lambda I)\vec{v} = \vec{0}$ to get the eigenvectors.

- Special cases

  1. 90° rotation $$\begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix}$$: $\lambda^2 + 1 = 0$ has only imaginary roots $\pm i$, so there are no real eigenvectors.
  2. Shear $$\begin{bmatrix} 1 & 1 \\ 0 & 1 \end{bmatrix}$$: the only eigenvalue is 1, and only the vectors on the x-axis are eigenvectors.
  3. Scaling by 2: the only eigenvalue is 2, but every vector is an eigenvector.

- Eigenbasis

  An eigenbasis is a set of basis vectors which are also eigenvectors.

  1. Standard basis vectors are eigenvectors $\Rightarrow$ diagonal matrix

     The columns of a matrix are where the basis vectors land. If $\hat{i}$ and $\hat{j}$ (standard basis) are eigenvectors, they are only scaled: $A\hat{i} = \lambda_1\hat{i} = [\lambda_1, 0]^T$ and $A\hat{j} = \lambda_2\hat{j} = [0, \lambda_2]^T$. So the matrix is diagonal with the eigenvalues on the diagonal:

     $$
     D = \begin{bmatrix} \lambda_1 & 0 \\ 0 & \lambda_2 \end{bmatrix}
     $$

     Diagonal matrices are easy to work with, e.g. $D^{100}$ is just each diagonal entry raised to the 100th power.

  2. Eigenvectors are not the standard basis $\Rightarrow$ change basis

     If there are enough eigenvectors to span the space, put them as the columns of the change of basis matrix $P$, and the corresponding eigenvalues (in the same order) on the diagonal of $D$. For the example $A$ above, with eigenvectors $[1, 0]^T$ ($\lambda = 3$) and $[-1, 1]^T$ ($\lambda = 2$):

     $$
     P = \begin{bmatrix} 1 & -1 \\ 0 & 1 \end{bmatrix}, \quad
     P^{-1} = \begin{bmatrix} 1 & 1 \\ 0 & 1 \end{bmatrix}, \quad
     D = \begin{bmatrix} 3 & 0 \\ 0 & 2 \end{bmatrix}
     $$

     Then:

     $$
     A = PDP^{-1} \quad \Leftrightarrow \quad D = P^{-1}AP
     $$

     Why it holds: $A$ applied to each column of $P$ gives $\lambda_i\vec{v}_i$, and $D$ applied on the right of $P$ scales each column of $P$ by $\lambda_i$. So $AP = PD$, and multiplying both sides by $P^{-1}$ on the right gives $A = PDP^{-1}$.

  3. Geometric view of $A = PDP^{-1}$

     Read $PDP^{-1}\vec{x}$ from right to left:

     1. $P^{-1}$: translate $\vec{x}$ from standard coordinates into eigenbasis coordinates. $\vec{x} = P\vec{x}'$ translates eigenbasis coordinates $\vec{x}'$ to standard coordinates $\vec{x}$, so $P^{-1}\vec{x}$ goes the other way.
     2. $D$: in the eigenbasis, the transformation only scales each coordinate by its eigenvalue.
     3. $P$: translate the result back into standard coordinates.

     Taking this detour gives the same result as applying $A$ directly. $A$ and $D$ describe the same transformation, just seen from two different coordinate systems.

  4. Why it eases computation

     The $P^{-1}P$ pairs in the middle cancel out:

     $$
     A^n = (PDP^{-1})(PDP^{-1})\cdots(PDP^{-1}) = PD^nP^{-1}
     $$

     For the example above:

     $$
     A^n = \begin{bmatrix} 1 & -1 \\ 0 & 1 \end{bmatrix}
     \begin{bmatrix} 3^n & 0 \\ 0 & 2^n \end{bmatrix}
     \begin{bmatrix} 1 & 1 \\ 0 & 1 \end{bmatrix}
     = \begin{bmatrix} 3^n & 3^n - 2^n \\ 0 & 2^n \end{bmatrix}
     $$

  Not every transformation has an eigenbasis, e.g. a shear does not have enough eigenvectors to span the full space, so no invertible $P$ can be built.

## References

1. [3Blue1Brown, Essence of Linear Algebra](https://youtu.be/PFDu9oVAE-g?si=pMQHEo7CZ41-ls_i)

## Todo

- Cross products
- Finish the last two videos
