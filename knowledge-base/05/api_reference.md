# NumPy数组官方文档
> 来源：https://numpy.org/doc/stable/user/absolute_beginners.html | 文档层（官方API参考）

NumPy: the absolute basics for beginners &#8212; NumPy v2.5 Manual
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
Collapse Sidebar
Expand Sidebar
NumPy: the absolute basics for beginners
#
Welcome to the absolute beginner’s guide to NumPy!
NumPy (Numerical Python) is an open source Python library that’s
widely used in science and engineering. The NumPy library contains
multidimensional array data structures, such as the homogeneous, N-dimensional
ndarray
, and a large library of functions that operate efficiently on these
data structures. Learn more about NumPy at
What is NumPy
,
and if you have comments or suggestions, please
reach out
!
How to import NumPy
#
After
installing NumPy
, it may be imported
into Python code like:
import
numpy
as
np
This widespread convention allows access to NumPy features with a short,
recognizable prefix (
np.
) while distinguishing NumPy features from others
that have the same name.
Reading the example code
#
Throughout the NumPy documentation, you will find blocks that look like:
&gt;&gt;&gt;
a
=
np
.
array
([[
1
,
2
,
3
],
...
[
4
,
5
,
6
]])
&gt;&gt;&gt;
a
.
shape
(2, 3)
Text preceded by
&gt;&gt;&gt;
or
...
is input, the code that you would
enter in a script or at a Python prompt. Everything else is output, the
results of running your code. Note that
&gt;&gt;&gt;
and
...
are not part of the
code and may cause an error if entered at a Python prompt.
To run the code in the examples, you can copy and paste it into a Python script or
REPL, or use the experimental interactive examples in the browser provided in various
locations in the documentation.
Why use NumPy?
#
Python lists are excellent, general-purpose containers. They can be
“heterogeneous”, meaning that they can contain elements of a variety of types,
and they are quite fast when used to perform individual operations on a handful
of elements.
Depending on the characteristics of the data and the types of operations that
need to be performed, other containers may be more appropriate; by exploiting
these characteristics, we can improve speed, reduce memory consumption, and
offer a high-level syntax for performing a variety of common processing tasks.
NumPy shines when there are large quantities of “homogeneous” (same-type) data
to be processed on the CPU.
What is an “array”?
#
In computer programming, an array is a structure for storing and retrieving
data. We often talk about an array as if it were a grid in space, with each
cell storing one element of the data. For instance, if each element of the
data were a number, we might visualize a “one-dimensional” array like a
list:
\[\begin{split}\begin{array}{|c||c|c|c|}
\hline
1 &amp; 5 &amp; 2 &amp; 0 \\
\hline
\end{array}\end{split}\]
A two-dimensional array would be like a table:
\[\begin{split}\begin{array}{|c||c|c|c|}
\hline
1 &amp; 5 &amp; 2 &amp; 0 \\
\hline
8 &amp; 3 &amp; 6 &amp; 1 \\
\hline
1 &amp; 7 &amp; 2 &amp; 9 \\
\hline
\end{array}\end{split}\]
A three-dimensional array would be lik

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
