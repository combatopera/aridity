# aridity
DRY config and template system, easily extensible with Python

## The Arid Manifesto
* Keys are paths to avoid concatenation
* It's never necessary to repeat a value
* Minimal syntax for surprise-free authoring
* Evaluation lazy and influenced by context
* Strongly (dynamically) typed values
* Central defaulting rather than at call sites
* Templating using same syntax as expressions
* Easy to correctly quote/escape values in templates
* Extensibility via user-defined functions
* Easy tasks are easy, hard tasks are possible
* Many applications can share one user config
* Principle of least astonishment driven design
* Don't make users jump through hoops

## Install
These are generic installation instructions.

### To use, permanently
The quickest way to get started is to install the current release from PyPI:
```
pip3 install --user aridity
```

### To use, temporarily
If you prefer to keep .local clean, install to a virtualenv:
```
python3 -m venv venvname
venvname/bin/pip install aridity
. venvname/bin/activate
```

### To develop
First clone the repo using HTTP or SSH:
```
git clone https://github.com/combatopera/aridity.git
git clone git@github.com:combatopera/aridity.git
```
Now use pyven's pipify to create a setup.py, which pip can then use to install the project editably:
```
python3 -m venv pyvenvenv
pyvenvenv/bin/pip install pyven
pyvenvenv/bin/pipify aridity

python3 -m venv venvname
venvname/bin/pip install -e aridity
. venvname/bin/activate
```

## Config file syntax
```
: Until aridity gets support for comments, you can use the colon directive to ignore data.
: Directives MUST be separated from data by whitespace, and are typically punctuation.

: Here's the equals directive:
foo = bar
: This does what you'd expect - assign the string value bar to foo.
: Observe that bar isn't quoted, values in aridity are normally barewords.
: foo is actually a path of length 1, path components are whitespace-separated:
this is a path = this is a value
: Any existing assignment can be overridden:
foo = baz
this is a path = this is different

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
: A few paths are predefined in every new context, such as:
home directory = $(~)

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

: Evaluation is lazy, the expression is what is actually (and eagerly) assigned to the path:
no problem = $(this path will get a value later)
: If your use-case demands it, you can force eager evaluation:
bar even if foo changes later := $(foo)

: When evaluating a path the local scope is examined first, then its parents if path not found:
host
    short path = nope
    guest short path = yep
    should be nope = $(short path)
    guest should be yep = $(short path)
does not work = $(short path)

: Use the dot directive to include config from another file:
. /path/to/other/config.arid
: Thus you can factor out any config that's common to multiple deployments, and override as needed.
: It's possible (but maybe not so useful) to include under a non-trivial path:
other stuff . /path/to/other/config.arid
: There is no default context for relative paths, you must set cwd up-front as inclusion is not lazy:
cwd = /path/to
. other/config.arid

: Text between dollar and open bracket (that isn't a special form) is a function name.
: A useful function predefined in every new context is the platform slash:
path = $/($(~) Desktop report.txt)
: Unlike most functions, / can also be used (less legibly) as a value:
path = $(~)$(/)Desktop$(/)report.txt
: All functions are first class objects that can be assigned and overridden in the usual ways:
slash := $(/)
/ = something else
path = $slash($(~) Desktop report.txt)

: Simple lists can be created using the plus equals convenience directive.
: Indentation means you don't have to repeat the directive for every list element:
years +=
    2018
    2019
years += 2020
: A predefined join function takes a list and a separator and does what you'd expect:
copyright = $join($(years) $.(, ))
: Observe that functions typically take values not identifiers, so you have to 'get' explicitly.
: Lists are just a special case of nested scopes, which are much more powerful:
person
    $.(The Guardians) year = 2018
    Greta year = 2019
summary = Person of the Year was $join($map($(person) $.($label() in $(year))) $.(, )).
: Here the predefined label function gives you access to the last path component of a list element.
```

## Templates
* A template is simply an expression in a file, that may be quite large
* These are typically used to create config files for other languages e.g. YAML, HCL
    * Note that literal dollar signs must be quoted as above, everything else is safe
* A processtemplate script is provided for basic processing
```
processtemplate app.json.aridt <config.arid >app.json
```
* Conventionally the `"` path is set to the most useful escape function for the target format
    * Brackets can be elided in function composition e.g. `$"$(key)` is the same as `$"($(key))`

## Commands

### arid-config
Print given config (with optional path in config) as shell snippet.

### aridity
Interactive REPL.

### processtemplate
Process the given template to stdout using config from stdin.
