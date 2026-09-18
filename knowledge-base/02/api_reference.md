# 数据类型官方文档
> 来源：https://docs.python.org/3/tutorial/introduction.html | 文档层（官方API参考）

3. An Informal Introduction to Python &#8212; Python 3.14.6 documentation
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
3.
An Informal Introduction to Python
|
Theme
Auto
Light
Dark
|
3.
An Informal Introduction to Python
Â¶
In the following examples, input and output are distinguished by the presence or
absence of prompts (
&gt;&gt;&gt;
and
â¦
): to repeat the example, you must type
everything after the prompt, when the prompt appears; lines that do not begin
with a prompt are output from the interpreter. Note that a secondary prompt on a
line by itself in an example means you must type a blank line; this is used to
end a multi-line command.
You can use the âCopyâ button (it appears in the upper-right corner
when hovering over or tapping a code example), which strips prompts
and omits output, to copy and paste the input lines into your interpreter.
Many of the examples in this manual, even those entered at the interactive
prompt, include comments. Comments in Python start with the hash character,
#
, and extend to the end of the physical line. A comment may appear at the
start of a line or following whitespace or code, but not within a string
literal. A hash character within a string literal is just a hash character.
Since comments are to clarify code and are not interpreted by Python, they may
be omitted when typing in examples.
Some examples:
# this is the first comment
spam
=
1
# and this is the second comment
# ... and now a third!
text
=
&quot;# This is not a comment because it&#39;s inside quotes.&quot;
3.1.
Using Python as a Calculator
Â¶
Letâs try some simple Python commands. Start the interpreter and wait for the
primary prompt,
&gt;&gt;&gt;
. (It shouldnât take long.)
3.1.1.
Numbers
Â¶
The interpreter acts as a simple calculator: you can type an expression into it
and it will write the value. Expression syntax is straightforward: the
operators
+
,
-
,
*
and
/
can be used to perform
arithmetic; parentheses (
()
) can be used for grouping.
For example:
&gt;&gt;&gt;
2
+
2
4
&gt;&gt;&gt;
50
-
5
*
6
20
&gt;&gt;&gt;
(
50
-
5
*
6
)
/
4
5.0
&gt;&gt;&gt;
8
/
5
# division always returns a floating-point number
1.6
The integer numbers (e.g.
2
,
4
,
20
) have type
int
,
the ones with a fractional part (e.g.
5.0
,
1.6
) have type
float
. We will see more about numeric types later in the tutorial.
Division (
/
) always returns a float. To do
floor division
and
get an integer result you can use the
//
operator; to calculate
the remainder you can use
%
:
&gt;&gt;&gt;
17
/
3
# classic division returns a float
5.666666666666667
&gt;&gt;&gt;
&gt;&gt;&gt;
17
//
3
# floor division discards the fractional part
5
&gt;&gt;&gt;
17
%
3
# the % operator returns the remainder of the division
2
&gt;&gt;&gt;
5
*
3
+
2
# floored quotient * divisor + remainder
17
With Python, it is possible to use the
**
operator to calculate powers
[
1
]
:
&gt;&gt;&gt;
5
**
2
# 5 squared
25
&gt;&gt;&gt;
2
*

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
