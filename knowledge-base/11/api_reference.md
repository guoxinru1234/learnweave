# Pandas合并官方文档
> 来源：https://pandas.pydata.org/docs/user_guide/merging.html | 文档层（官方API参考）

Merge, join, concatenate and compare &#8212; pandas 3.0.5 documentation
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
X
Mastodon
Merge, join, concatenate and compare
#
pandas provides various methods for combining and comparing
Series
or
DataFrame
.
concat()
: Merge multiple
Series
or
DataFrame
objects along a shared index or column
DataFrame.join()
: Merge multiple
DataFrame
objects along the columns
DataFrame.combine_first()
: Update missing values with non-missing values in the same location
merge()
: Combine two
Series
or
DataFrame
objects with SQL-style joining
merge_ordered()
: Combine two
Series
or
DataFrame
objects along an ordered axis
merge_asof()
: Combine two
Series
or
DataFrame
objects by near instead of exact matching keys
Series.compare()
and
DataFrame.compare()
: Show differences in values between two
Series
or
DataFrame
objects
concat()
#
The
concat()
function concatenates an arbitrary amount of
Series
or
DataFrame
objects along an axis while
performing optional set logic (union or intersection) of the indexes on
the other axes. Like
numpy.concatenate
,
concat()
takes a list or dict of homogeneously-typed objects and concatenates them.
In [1]:
df1
=
pd
.
DataFrame
(
...:
{
...:
&quot;A&quot;
:
[
&quot;A0&quot;
,
&quot;A1&quot;
,
&quot;A2&quot;
,
&quot;A3&quot;
],
...:
&quot;B&quot;
:
[
&quot;B0&quot;
,
&quot;B1&quot;
,
&quot;B2&quot;
,
&quot;B3&quot;
],
...:
&quot;C&quot;
:
[
&quot;C0&quot;
,
&quot;C1&quot;
,
&quot;C2&quot;
,
&quot;C3&quot;
],
...:
&quot;D&quot;
:
[
&quot;D0&quot;
,
&quot;D1&quot;
,
&quot;D2&quot;
,
&quot;D3&quot;
],
...:
},
...:
index
=
[
0
,
1
,
2
,
3
],
...:
)
...:
In [2]:
df2
=
pd
.
DataFrame
(
...:
{
...:
&quot;A&quot;
:
[
&quot;A4&quot;
,
&quot;A5&quot;
,
&quot;A6&quot;
,
&quot;A7&quot;
],
...:
&quot;B&quot;
:
[
&quot;B4&quot;
,
&quot;B5&quot;
,
&quot;B6&quot;
,
&quot;B7&quot;
],
...:
&quot;C&quot;
:
[
&quot;C4&quot;
,
&quot;C5&quot;
,
&quot;C6&quot;
,
&quot;C7&quot;
],
...:
&quot;D&quot;
:
[
&quot;D4&quot;
,
&quot;D5&quot;
,
&quot;D6&quot;
,
&quot;D7&quot;
],
...:
},
...:
index
=
[
4
,
5
,
6
,
7
],
...:
)
...:
In [3]:
df3
=
pd
.
DataFrame
(
...:
{
...:
&quot;A&quot;
:
[
&quot;A8&quot;
,
&quot;A9&quot;
,
&quot;A10&quot;
,
&quot;A11&quot;
],
...:
&quot;B&quot;
:
[
&quot;B8&quot;
,
&quot;B9&quot;
,
&quot;B10&quot;
,
&quot;B11&quot;
],
...:
&quot;C&quot;
:
[
&quot;C8&quot;
,
&quot;C9&quot;
,
&quot;C10&quot;
,
&quot;C11&quot;
],
...:
&quot;D&quot;
:
[
&quot;D8&quot;
,
&quot;D9&quot;
,
&quot;D10&quot;
,
&quot;D11&quot;
],
...:
},
...:
index
=
[
8
,
9
,
10
,
11
],
...:
)
...:
In [4]:
frames
=
[
df1
,
df2
,
df3
]
In [5]:
result
=
pd
.
concat
(
frames
)
In [6]:
result
Out[6]:
A B C D
0 A0 B0 C0 D0
1 A1 B1 C1 D1
2 A2 B2 C2 D2
3 A3 B3 C3 D3
4 A4 B4 C4 D4
5 A5 B5 C5 D5
6 A6 B6 C6 D6
7 A7 B7 C7 D7
8 A8 B8 C8 D8
9 A9 B9 C9 D9
10 A10 B10 C10 D10
11 A11 B11 C11 D11
Note
concat()
makes a full copy of the data, and iteratively
reusing
concat()
can create unnecessary copies. Collect all
DataFrame
or
Series
ob

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
