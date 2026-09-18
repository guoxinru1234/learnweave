# Pandas索引官方文档
> 来源：https://pandas.pydata.org/docs/user_guide/indexing.html | 文档层（官方API参考）

Indexing and selecting data &#8212; pandas 3.0.5 documentation
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
X
Mastodon
Indexing and selecting data
#
The axis labeling information in pandas objects serves many purposes:
Identifies data (i.e. provides metadata) using known indicators,
important for analysis, visualization, and interactive console display.
Enables automatic and explicit data alignment.
Allows intuitive getting and setting of subsets of the data set.
In this section, we will focus on the final point: namely, how to slice, dice,
and generally get and set subsets of pandas objects. The primary focus will be
on Series and DataFrame as they have received more development attention in
this area.
Note
The Python and NumPy indexing operators
[]
and attribute operator
.
provide quick and easy access to pandas data structures across a wide range
of use cases. This makes interactive work intuitive, as there’s little new
to learn if you already know how to deal with Python dictionaries and NumPy
arrays. However, since the type of the data to be accessed isn’t known in
advance, directly using standard operators has some optimization limits. For
production code, we recommended that you take advantage of the optimized
pandas data access methods exposed in this chapter.
See the
MultiIndex / Advanced Indexing
for
MultiIndex
and more advanced indexing documentation.
See the
cookbook
for some advanced strategies.
Different choices for indexing
#
Object selection has had a number of user-requested additions in order to
support more explicit location based indexing. pandas now supports three types
of multi-axis indexing.
.loc
is primarily label based, but may also be used with a boolean array.
.loc
will raise
KeyError
when the items are not found. Allowed inputs are:
A single label, e.g.
5
or
'a'
(Note that
5
is interpreted as a
label of the index. This use is not an integer position along the
index.).
A list or array of labels
['a',
'b',
'c']
.
A slice object with labels
'a':'f'
(Note that contrary to usual Python
slices, both the start and the stop are included, when present in the
index! See
Slicing with labels
and
Endpoints are inclusive
.)
A boolean array (any
NA
values will be treated as
False
).
A
callable
function with one argument (the calling Series or DataFrame) and
that returns valid output for indexing (one of the above).
A tuple of row (and column) indices whose elements are one of the
above inputs.
See more at
Selection by Label
.
.iloc
is primarily integer position based (from
0
to
length-1
of the axis), but may also be used with a boolean
array.
.iloc
will raise
IndexError
if a requested
indexer is out-of-bounds, except slice indexers which allow
out-of-bounds indexing. (this conforms with Python/NumPy slice
semantics). Allowed inputs are:
An integer e.g.
5
.
A list or array of integers
[4,
3,
0]
.
A slice object with ints
1:7
.
A boolean array (any
NA
values will be treated as
False
).
A
callable
function with one argu

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
