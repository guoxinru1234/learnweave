# 控制流官方文档
> 来源：https://docs.python.org/3/tutorial/controlflow.html | 文档层（官方API参考）

4. More Control Flow Tools &#8212; Python 3.14.6 documentation
Navigation
index
modules
|
next
|
previous
|
Python
&#187;
3.14.6 Documentation
&#187;
The Python Tutorial
&#187;
4.
More Control Flow Tools
|
Theme
Auto
Light
Dark
|
4.
More Control Flow Tools
Â¶
As well as the
while
statement just introduced, Python uses a few more
that we will encounter in this chapter.
4.1.
if
Statements
Â¶
Perhaps the most well-known statement type is the
if
statement. For
example:
&gt;&gt;&gt;
x
=
int
(
input
(
&quot;Please enter an integer: &quot;
))
Please enter an integer: 42
&gt;&gt;&gt;
if
x
&lt;
0
:
...
x
=
0
...
print
(
&#39;Negative changed to zero&#39;
)
...
elif
x
==
0
:
...
print
(
&#39;Zero&#39;
)
...
elif
x
==
1
:
...
print
(
&#39;Single&#39;
)
...
else
:
...
print
(
&#39;More&#39;
)
...
More
There can be zero or more
elif
parts, and the
else
part is
optional. The keyword â
elif
â is short for âelse ifâ, and is useful
to avoid excessive indentation. An
if
â¦
elif
â¦
elif
â¦ sequence is a substitute for the
switch
or
case
statements found in other languages.
If youâre comparing the same value to several constants, or checking for specific types or
attributes, you may also find the
match
statement useful. For more
details see
match Statements
.
4.2.
for
Statements
Â¶
The
for
statement in Python differs a bit from what you may be used
to in C or Pascal. Rather than always iterating over an arithmetic progression
of numbers (like in Pascal), or giving the user the ability to define both the
iteration step and halting condition (as C), Pythonâs
for
statement
iterates over the items of any sequence (a list or a string), in the order that
they appear in the sequence. For example (no pun intended):
&gt;&gt;&gt;
# Measure some strings:
&gt;&gt;&gt;
words
=
[
&#39;cat&#39;
,
&#39;window&#39;
,
&#39;defenestrate&#39;
]
&gt;&gt;&gt;
for
w
in
words
:
...
print
(
w
,
len
(
w
))
...
cat 3
window 6
defenestrate 12
Code that modifies a collection while iterating over that same collection can
be tricky to get right. Instead, it is usually more straight-forward to loop
over a copy of the collection or to create a new collection:
# Create a sample collection
users
=
{
&#39;Hans&#39;
:
&#39;active&#39;
,
&#39;ÃlÃ©onore&#39;
:
&#39;inactive&#39;
,
&#39;æ¯å¤ªé&#39;
:
&#39;active&#39;
}
# Strategy: Iterate over a copy
for
user
,
status
in
users
.
copy
()
.
items
():
if
status
==
&#39;inactive&#39;
:
del
users
[
user
]
# Strategy: Create a new collection
active_users
=
{}
for
user
,
status
in
users
.
items
():
if
status
==
&#39;active&#39;
:
active_users
[
user
]
=
status
4.3.
The
range()
Function
Â¶
If you do need to iterate over a sequence of numbers, the built-in function
range()
comes in handy. It generates arithmetic progressions:
&gt;&gt;&gt;
for
i
in
range
(
5
):
...
print
(
i
)
...
0
1
2
3
4
The given end point is never part of the generated sequence;
range(10)
generates
10 values, the legal indices for items of a sequence of length 10. It
is poss

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
