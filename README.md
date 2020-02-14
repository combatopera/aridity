# aridity
[![Build Status](https://travis-ci.org/combatopera/aridity.svg?branch=master)](https://travis-ci.org/combatopera/aridity)

## The Arid Manifesto
* Paths as keys to avoid key concatenation
* It's never necessary to repeat a value
* Minimal syntax for surprise-free authoring
* Lazy context-sensitive evaluation
* Strongly (dynamically) typed values
* Central defaulting rather than at call sites
* Templating using same syntax as expressions
* Easy to correctly quote/escape values in templates
* Extensibility via user-defined functions
* Easy tasks are easy, hard tasks are possible
* Many applications can share one user config
* Principle of least astonishment driven design

## Config file syntax
```
: Until aridity gets support for comments, you can use the colon directive to ignore data.
: Directives MUST be separated from data by whitespace, and are typically punctuation.

: Here's the equals directive:
foo = bar
: This does what you'd expect - assign the string value bar to foo.
: foo is actually a path of length 1, path components are whitespace-separated:
this is a path = this is a value

: Internal whitespace in values is preserved (leading and trailing whitespace is not):
two sentences = Some like 2 spaces.  After a full stop.

: You can use indentation to avoid typing a common path prefix multiple times:
app1 feature1
    data1 = value1
    data2 = value2
app2
    feature1 data = value3
    feature2
        data1 = value4
        data2 = value5
: Exactly the same effect without using indentation:
app1 feature1 data1 = value1
app1 feature1 data2 = value2
app2 feature1 data = value3
app2 feature2 data1 = value4
app2 feature2 data2 = value5

: The right hand side of an equals is actually an expression.
: In an expression, a dollar sign with brackets can be used to refer to another path:
has value
    bar = $(foo)
    value3 = $(app2 feature1 data)
: Round brackets and square brackets have exactly the same effect:
also has value bar = $[foo]
: Values can be concatenated:
two bars
    without spacing = $(foo)$(foo)
    with one space  = $(foo) $(foo)
    with 2 spaces   = $(foo)  $(foo)

: To get a literal dollar there is a special form for quoting:
financial report = $'(We lost $100 on Friday.)
: Be careful with nested brackets, the first matching bracket ends the special form:
behaviour
    expected   = $'[Lunch cost $20 (worth it though).]
    unexpected = $'(Lunch cost $20 (worth it though).)

: Another special form can be used to preserve leading/trailing whitespace:
padded bars = $.( $(foo) $(foo) )
: Brackets can span multiple lines:
bar per line
    without final newline = $.($(foo)
$(foo))
    with final newline = $.($(foo)
$(foo)
)

: Evaluation is lazy, the expression is what is actually assigned to the path:
no problem = $(this path will get a value later)
: If your use-case demands it, you can force eager evaluation:
bar even if foo changes later := $(foo)

: When evaluating a path the local context is examined first, then its parents if path not found:
host
    short path = nope
    guest short path = yep
    should be nope = $(short path)
    guest should be yep = $(short path)
does not work = $(short path)
```
