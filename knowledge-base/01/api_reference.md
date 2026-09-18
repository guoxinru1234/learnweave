# Python解释器官方文档
> 来源：https://docs.python.org/3/tutorial/interpreter.html | 文档层（官方API参考）

2. Using the Python Interpreter &#8212; Python 3.14.6 documentation
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
2.
Using the Python Interpreter
|
Theme
Auto
Light
Dark
|
2.
Using the Python Interpreter
Â¶
2.1.
Invoking the Interpreter
Â¶
The Python interpreter is usually installed as
/usr/local/bin/python3.14
on those machines where it is available; putting
/usr/local/bin
in your
Unix shellâs search path makes it possible to start it by typing the command:
python3.14
to the shell.
[
1
]
Since the choice of the directory where the interpreter lives
is an installation option, other places are possible; check with your local
Python guru or system administrator. (E.g.,
/usr/local/python
is a
popular alternative location.)
On Windows machines where you have installed Python from the
Microsoft Store
, the
python3.14
command will be available. If you have
the
py.exe launcher
installed, you can use the
py
command. See
Python install manager
for other ways to launch Python.
Typing an end-of-file character (Control-D on Unix, Control-Z on
Windows) at the primary prompt causes the interpreter to exit with a zero exit
status. If that doesnât work, you can exit the interpreter by typing the
following command:
quit()
.
The interpreterâs line-editing features include interactive editing, history
substitution and code completion on most systems.
Perhaps the quickest check to see whether command line editing is supported is
typing a word in on the Python prompt, then pressing Left arrow (or Control-b).
If the cursor moves, you have command line editing; see Appendix
Interactive Input Editing and History Substitution
for an introduction to the keys.
If nothing appears to happen, or if a sequence like
^[[D
or
^B
appears,
command line editing isnât available; youâll only be able to use
backspace to remove characters from the current line.
The interpreter operates somewhat like the Unix shell: when called with standard
input connected to a tty device, it reads and executes commands interactively;
when called with a file name argument or with a file as standard input, it reads
and executes a script from that file.
A second way of starting the interpreter is
python
-c
command
[arg]
...
,
which executes the statement(s) in command, analogous to the shellâs
-c
option. Since Python statements often contain spaces or other
characters that are special to the shell, it is usually advised to quote
command in its entirety.
Some Python modules are also useful as scripts. These can be invoked using
python
-m
module
[arg]
...
, which executes the source file for module as
if you had spelled out its full name on the command line.
When a script file is used, it is sometimes useful to be able to run the script
and enter interactive mode afterwards. This can be done by passing
-i
before the script.
All command line options are described in
Command line and environment
.
2.1.1.
Argument Passing
Â¶
When k

---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
