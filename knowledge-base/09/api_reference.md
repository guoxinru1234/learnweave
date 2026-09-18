# Pandas数据结构官方文档
> 来源：https://pandas.pydata.org/docs/user_guide/dsintro.html | 文档层（官方API参考）

Intro to data structures &#8212; pandas 3.0.5 documentation
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
X
Mastodon
Intro to data structures
#
We’ll start with a quick, non-comprehensive overview of the fundamental data
structures in pandas to get you started. The fundamental behavior about data
types, indexing, axis labeling, and alignment apply across all of the
objects. To get started, import NumPy and load pandas into your namespace:
In [1]:
import
numpy
as
np
In [2]:
import
pandas
as
pd
Fundamentally, data alignment is intrinsic. The link
between labels and data will not be broken unless done so explicitly by you.
We’ll give a brief intro to the data structures, then consider all of the broad
categories of functionality and methods in separate sections.
Series
#
Series
is a one-dimensional labeled array capable of holding any data
type (integers, strings, floating point numbers, Python objects, etc.). The axis
labels are collectively referred to as the index. The basic method to create a
Series
is to call:
s
=
pd
.
Series
(
data
,
index
=
index
)
Here,
data
can be many different things:
a Python dict
an ndarray
a scalar value (like 5)
The passed index is a list of axis labels. The constructor’s behavior
depends on data’s type:
From ndarray
If
data
is an ndarray, index must be the same length as data. If no
index is passed, one will be created having values
[0,
...,
len(data)
-
1]
.
In [3]:
s
=
pd
.
Series
(
np
.
random
.
randn
(
5
),
index
=
[
&quot;a&quot;
,
&quot;b&quot;
,
&quot;c&quot;
,
&quot;d&quot;
,
&quot;e&quot;
])
In [4]:
s
Out[4]:
a 0.469112
b -0.282863
c -1.509059
d -1.135632
e 1.212112
dtype: float64
In [5]:
s
.
index
Out[5]:
Index([&#39;a&#39;, &#39;b&#39;, &#39;c&#39;, &#39;d&#39;, &#39;e&#39;], dtype=&#39;str&#39;)
In [6]:
pd
.
Series
(
np
.
random
.
randn
(
5
))
Out[6]:
0 -0.173215
1 0.119209
2 -1.044236
3 -0.861849
4 -2.104569
dtype: float64
Note
pandas supports non-unique index values. If an operation
that does not support duplicate index values is attempted, an exception
will be raised at that time.
From dict
Series
can be instantiated from dicts:
In [7]:
d
=
{
&quot;b&quot;
:
1
,
&quot;a&quot;
:
0
,
&quot;c&quot;
:
2
}
In [8]:
pd
.
Series
(
d
)
Out[8]:
b 1
a 0
c 2
dtype: int64
If an index is passed, the values in data corresponding to the labels in the
index will be pulled out.
In [9]:
d
=
{
&quot;a&quot;
:
0.0
,
&quot;b&quot;
:
1.0
,
&quot;c&quot;
:
2.0
}
In [10]:
pd
.
Series
(
d
)
Out[10]:
a 0.0
b 1.0
c 2.0
dtype: float64
In [11]:
pd
.
Series
(
d
,
index
=
[
&quot;b&quot;
,
&quot;c&quot;
,
&quot;d&quot;
,
&quot;a&quot;
])
Out[11]:
b 1.0
c 2.0
d NaN
a 0.0
dtype: float64
Note
NaN (not a number) is the standard missing data marker used in pandas.
From scalar value
If
data
is a scalar value, the value will be repeated to match
the length of index. If the index is not provided, it defaults
to
RangeIndex(1)
.
In [12]:
pd
.
Series
(
5.0
,
index
=
[
&quot;a&quot;
,
&quot;b&quot;
,
&quot;c&quot;
,
&quot;d&quot;


---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
