# Pandas分组官方文档
> 来源：https://pandas.pydata.org/docs/user_guide/groupby.html | 文档层（官方API参考）

Group by: split-apply-combine &#8212; pandas 3.0.5 documentation
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
X
Mastodon
Group by: split-apply-combine
#
By “group by” we are referring to a process involving one or more of the following
steps:
Splitting the data into groups based on some criteria.
Applying a function to each group independently.
Combining the results into a data structure.
Out of these, the split step is the most straightforward. In the apply step, we
might wish to do one of the following:
Aggregation: compute a summary statistic (or statistics) for each
group. Some examples:
Compute group sums or means.
Compute group sizes / counts.
Transformation: perform some group-specific computations and return a
like-indexed object. Some examples:
Standardize data (zscore) within a group.
Filling NAs within groups with a value derived from each group.
Filtration: discard some groups, according to a group-wise computation
that evaluates to True or False. Some examples:
Discard data that belong to groups with only a few members.
Filter out data based on the group sum or mean.
Many of these operations are defined on GroupBy objects. These operations are similar
to those of the
aggregating API
,
window API
, and
resample API
.
It is possible that a given operation does not fall into one of these categories or
is some combination of them. In such a case, it may be possible to compute the
operation using GroupBy’s
apply
method. This method will examine the results of the
apply step and try to sensibly combine them into a single result if it doesn’t fit into either
of the above three categories.
Note
An operation that is split into multiple steps using built-in GroupBy operations
will be more efficient than using the
apply
method with a user-defined Python
function.
The name GroupBy should be quite familiar to those who have used
a SQL-based tool (or
itertools
), in which you can write code like:
SELECT
Column1
,
Column2
,
mean
(
Column3
),
sum
(
Column4
)
FROM
SomeTable
GROUP
BY
Column1
,
Column2
We aim to make operations like this natural and easy to express using
pandas. We’ll address each area of GroupBy functionality, then provide some
non-trivial examples / use cases.
See the
cookbook
for some advanced strategies.
Splitting an object into groups
#
The abstract definition of grouping is to provide a mapping of labels to
group names. To create a GroupBy object (more on what the GroupBy object is
later), you may do the following:
In [1]:
speeds
=
pd
.
DataFrame
(
...:
[
...:
(
&quot;bird&quot;
,
&quot;Falconiformes&quot;
,
389.0
),
...:
(
&quot;bird&quot;
,
&quot;Psittaciformes&quot;
,
24.0
),
...:
(
&quot;mammal&quot;
,
&quot;Carnivora&quot;
,
80.2
),
...:
(
&quot;mammal&quot;
,
&quot;Primates&quot;
,
np
.
nan
),
...:
(
&quot;mammal&quot;
,
&quot;Carnivora&quot;
,
58
),
...:
],
...:
index
=
[
&quot;falcon&quot;
,
&quot;parrot&quot;
,
&quot;lion&quot;
,
&quot;monkey&quot;
,
&quot;leopard&quot;
],
...:
columns
=
(
&quot;class&qu

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
