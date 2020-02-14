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
```
