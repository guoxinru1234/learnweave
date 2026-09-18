# NumPy线性代数官方文档
> 来源：https://numpy.org/doc/stable/reference/routines.linalg.html | 文档层（官方API参考）

Linear algebra &#8212; NumPy v2.5 Manual
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
Collapse Sidebar
Expand Sidebar
Linear algebra
#
The NumPy linear algebra functions rely on BLAS and LAPACK to provide efficient
low level implementations of standard linear algebra algorithms. Those
libraries may be provided by NumPy itself using C versions of a subset of their
reference implementations but, when possible, highly optimized libraries that
take advantage of specialized processor functionality are preferred. Examples
of such libraries are
OpenBLAS
, MKL (TM), and ATLAS. Because those libraries
are multithreaded and processor dependent, environmental variables and external
packages such as
threadpoolctl
may be needed to control the number of threads
or specify the processor architecture.
The SciPy library also contains a
linalg
submodule, and there is
overlap in the functionality provided by the SciPy and NumPy submodules. SciPy
contains functions not found in
numpy.linalg
, such as functions related to
LU decomposition and the Schur decomposition, multiple ways of calculating the
pseudoinverse, and matrix transcendentals such as the matrix logarithm. Some
functions that exist in both have augmented functionality in
scipy.linalg
.
For example,
scipy.linalg.eig
can take a second matrix argument for solving
generalized eigenvalue problems. Some functions in NumPy, however, have more
flexible broadcasting options. For example,
numpy.linalg.solve
can handle
“stacked” arrays, while
scipy.linalg.solve
accepts only a single square
array as its first argument.
Note
The term matrix as it is used on this page indicates a 2d
numpy.array
object, and not a
numpy.matrix
object. The latter is no longer
recommended, even for linear algebra. See
the matrix object documentation
for
more information.
The
&#64;
operator
#
Introduced in NumPy 1.10.0, the
&#64;
operator is preferable to
other methods when computing the matrix product between 2d arrays. The
numpy.matmul
function implements the
&#64;
operator.
Matrix and vector products
#
dot
(a, b[, out])
Dot product of two arrays.
linalg.multi_dot
(arrays, *[, out])
Compute the dot product of two or more arrays in a single function call, while automatically selecting the fastest evaluation order.
vdot
(a, b, /)
Return the dot product of two vectors.
vecdot
(x1, x2, /[, out, casting, order, ...])
Vector dot product of two arrays.
linalg.vecdot
(x1, x2, /, *[, axis])
Computes the vector dot product.
inner
(a, b, /)
Inner product of two arrays.
outer
(a, b[, out])
Compute the outer product of two vectors.
linalg.outer
(x1, x2, /)
Compute the outer product of two vectors.
matmul
(x1, x2, /[, out, casting, order, ...])
Matrix product of two arrays.
linalg.matmul
(x1, x2, /)
Computes the matrix product.
matvec
(x1, x2, /[, out, casting, order, ...])
Matrix-vector dot product of two arrays.
vecmat
(x1, x2, /[, out, casting, order, ...])
Vector-matrix dot product of two arrays.
tensordot
(a, b[, axes])
Compute 

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
