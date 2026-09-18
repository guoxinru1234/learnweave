# 模块官方文档
> 来源：https://docs.python.org/3/tutorial/modules.html | 文档层（官方API参考）

6. Modules &#8212; Python 3.14.6 documentation
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
6.
Modules
|
Theme
Auto
Light
Dark
|
6.
Modules
Â¶
If you quit from the Python interpreter and enter it again, the definitions you
have made (functions and variables) are lost. Therefore, if you want to write a
somewhat longer program, you are better off using a text editor to prepare the
input for the interpreter and running it with that file as input instead. This
is known as creating a script. As your program gets longer, you may want to
split it into several files for easier maintenance. You may also want to use a
handy function that youâve written in several programs without copying its
definition into each program.
To support this, Python has a way to put definitions in a file and use them in a
script or in an interactive instance of the interpreter. Such a file is called a
module; definitions from a module can be imported into other modules or into
the main module (the collection of variables that you have access to in a
script executed at the top level and in calculator mode).
A module is a file containing Python definitions and statements. The file name
is the module name with the suffix
.py
appended. Within a module, the
moduleâs name (as a string) is available as the value of the global variable
__name__
. For instance, use your favorite text editor to create a file
called
fibo.py
in the current directory with the following contents:
# Fibonacci numbers module
def
fib
(
n
):
&quot;&quot;&quot;Write Fibonacci series up to n.&quot;&quot;&quot;
a
,
b
=
0
,
1
while
a
&lt;
n
:
print
(
a
,
end
=
&#39; &#39;
)
a
,
b
=
b
,
a
+
b
print
()
def
fib2
(
n
):
&quot;&quot;&quot;Return Fibonacci series up to n.&quot;&quot;&quot;
result
=
[]
a
,
b
=
0
,
1
while
a
&lt;
n
:
result
.
append
(
a
)
a
,
b
=
b
,
a
+
b
return
result
Now enter the Python interpreter and import this module with the following
command:
&gt;&gt;&gt;
import
fibo
This does not add the names of the functions defined in
fibo
directly to
the current
namespace
(see
Python Scopes and Namespaces
for more details);
it only adds the module name
fibo
there. Using
the module name you can access the functions:
&gt;&gt;&gt;
fibo
.
fib
(
1000
)
0 1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987
&gt;&gt;&gt;
fibo
.
fib2
(
100
)
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
&gt;&gt;&gt;
fibo
.
__name__
&#39;fibo&#39;
If you intend to use a function often you can assign it to a local name:
&gt;&gt;&gt;
fib
=
fibo
.
fib
&gt;&gt;&gt;
fib
(
500
)
0 1 1 2 3 5 8 13 21 34 55 89 144 233 377
6.1.
More on Modules
Â¶
A module can contain executable statements as well as function definitions.
These statements are intended to initialize the module. They are executed only
the first time the module name is encountered in an import statement.
[
1
]
(They are also run if the file is executed as a script.)
Each module has its own private namespace, which is us

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
