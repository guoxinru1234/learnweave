# NumPy广播官方文档
> 来源：https://numpy.org/doc/stable/user/basics.broadcasting.html | 文档层（官方API参考）

Broadcasting &#8212; NumPy v2.5 Manual
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
Collapse Sidebar
Expand Sidebar
Broadcasting
#
See also
numpy.broadcast
The term broadcasting describes how NumPy treats arrays with different
shapes during arithmetic operations. Subject to certain constraints,
the smaller array is “broadcast” across the larger array so that they
have compatible shapes. Broadcasting provides a means of vectorizing
array operations so that looping occurs in C instead of Python. It does
this without making needless copies of data and usually leads to
efficient algorithm implementations. There are, however, cases where
broadcasting is a bad idea because it leads to inefficient use of memory
that slows computation.
NumPy operations are usually done on pairs of arrays on an
element-by-element basis. In the simplest case, the two arrays must
have exactly the same shape, as in the following example:
&gt;&gt;&gt;
import
numpy
as
np
&gt;&gt;&gt;
a
=
np
.
array
([
1.0
,
2.0
,
3.0
])
&gt;&gt;&gt;
b
=
np
.
array
([
2.0
,
2.0
,
2.0
])
&gt;&gt;&gt;
a
*
b
array([2., 4., 6.])
NumPy’s broadcasting rule relaxes this constraint when the arrays’
shapes meet certain constraints. The simplest broadcasting example occurs
when an array and a scalar value are combined in an operation:
&gt;&gt;&gt;
import
numpy
as
np
&gt;&gt;&gt;
a
=
np
.
array
([
1.0
,
2.0
,
3.0
])
&gt;&gt;&gt;
b
=
2.0
&gt;&gt;&gt;
a
*
b
array([2., 4., 6.])
The result is equivalent to the previous example where
b
was an array.
We can think of the scalar
b
being stretched during the arithmetic
operation into an array with the same shape as
a
. The new elements in
b
, as shown in
Figure 1
, are simply copies of the
original scalar. The stretching analogy is
only conceptual. NumPy is smart enough to use the original scalar value
without actually making copies so that broadcasting operations are as
memory and computationally efficient as possible.
Figure 1
#
In the simplest example of broadcasting, the scalar
b
is
stretched to become an array of same shape as
a
so the shapes
are compatible for element-by-element multiplication.
The code in the second example is more efficient than that in the first
because broadcasting moves less memory around during the multiplication
(
b
is a scalar rather than an array).
General broadcasting rules
#
When operating on two arrays, NumPy compares their shapes element-wise.
It starts with the trailing (i.e. rightmost) dimension and works its
way left. Two dimensions are compatible when
they are equal, or
one of them is 1.
If these conditions are not met, a
ValueError:
operands
could
not
be
broadcast
together
exception is
thrown, indicating that the arrays have incompatible shapes.
Input arrays do not need to have the same number of dimensions. The
resulting array will have the same number of dimensions as the input array
with the greatest number of dimensions, where the size of each dimension is
the largest size of the corresponding dimension

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
