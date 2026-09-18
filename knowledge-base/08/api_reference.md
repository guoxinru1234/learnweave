# NumPy随机数官方文档
> 来源：https://numpy.org/doc/stable/reference/random/index.html | 文档层（官方API参考）

Random sampling &#8212; NumPy v2.5 Manual
Skip to main content
Back to top
Ctrl+K
Choose version
GitHub
Collapse Sidebar
Expand Sidebar
Random sampling
#
Quick start
#
The
numpy.random
module implements pseudo-random number generators
(PRNGs or RNGs, for short) with the ability to draw samples from a variety of
probability distributions. In general, users will create a
Generator
instance
with
default_rng
and call the various methods on it to obtain samples from
different distributions.
Try it in your browser!
&gt;&gt;&gt;
import
numpy
as
np
&gt;&gt;&gt;
rng
=
np
.
random
.
default_rng
()
Generate one random float uniformly distributed over the range
\([0, 1)\)
:
&gt;&gt;&gt;
rng
.
random
()
0.06369197489564249 # may vary
Generate an array of 10 numbers according to a unit Gaussian distribution:
&gt;&gt;&gt;
rng
.
standard_normal
(
10
)
array([-0.31018314, -1.8922078 , -0.3628523 , -0.63526532, 0.43181166, # may vary
0.51640373, 1.25693945, 0.07779185, 0.84090247, -2.13406828])
Generate an array of 5 integers uniformly over the range
\([0, 10)\)
:
&gt;&gt;&gt;
rng
.
integers
(
low
=
0
,
high
=
10
,
size
=
5
)
array([8, 7, 6, 2, 0]) # may vary
Go BackOpen In Tab
Our RNGs are deterministic sequences and can be reproduced by specifying a seed integer to
derive its initial state. By default, with no seed provided,
default_rng
will
seed the RNG from nondeterministic data from the operating system and therefore
generate different numbers each time. The pseudo-random sequences will be
independent for all practical purposes, at least those purposes for which our
pseudo-randomness was good for in the first place.
Try it in your browser!
&gt;&gt;&gt;
import
numpy
as
np
&gt;&gt;&gt;
rng1
=
np
.
random
.
default_rng
()
&gt;&gt;&gt;
rng1
.
random
()
0.6596288841243357 # may vary
&gt;&gt;&gt;
rng2
=
np
.
random
.
default_rng
()
&gt;&gt;&gt;
rng2
.
random
()
0.11885628817151628 # may vary
Go BackOpen In Tab
Warning
The pseudo-random number generators implemented in this module are designed
for statistical modeling and simulation. They are not suitable for security
or cryptographic purposes. See the
secrets
module from the
standard library for such use cases.
Seeds should be large positive integers.
default_rng
can take positive
integers of any size. We recommend using very large, unique numbers to ensure
that your seed is different from anyone else’s. This is good practice to ensure
that your results are statistically independent from theirs unless you are
intentionally trying to reproduce their result. A convenient way to get
such a seed number is to use
secrets.randbits
to get an
arbitrary 128-bit integer.
Try it in your browser!
&gt;&gt;&gt;
import
numpy
as
np
&gt;&gt;&gt;
import
secrets
&gt;&gt;&gt;
secrets
.
randbits
(
128
)
122807528840384100672342137672332424406 # may vary
&gt;&gt;&gt;
rng1
=
np
.
random
.
default_rng
(
122807528840384100672342137672332424406
)
&gt;&gt;&gt;
rng1
.
random
()
0.5363922081269535
&gt;&gt;&gt;
rng2
=
np
.
random
.
default_rng


---
*本知识库内容来自 Python Data Science Handbook (CC-BY) 及 Python/NumPy/Pandas 官方文档。*
