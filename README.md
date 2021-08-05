# C/C++ dependencies automation

## Motivation

This set of scripts was initially developed to enhance CI yaml configs of my project [Melon](https://github.com/kovdan01/melon/). It is also used there to provide an easy way to setup development environment for new contributors.

## How to use

**NOTE:** currently this is a super-alpha version. The interface might and **will** actually change.

At the moment, the design is super dummy and straight-forward, but at least it works. Here is everything that you might want to know.

- The main file is called `builder.py`. It contains `Builder` class definition, that implements all the useful routines. You can find the documentation in sources.
- The inner state of a `Builder` object might be loaded or stored from/to a file (by default named `builder.pkl`) with `load_builder` and `save_builder` functions.
- There is a bunch of small python scripts in tools and libs directories. Those just load builder's inner state, execute the method corresponding to the script name and store the builder state back to the file.
- `init.py` python script just calls the `Builder` constructor ans saves the object state to a file; `all.sh` shell script calls alls the scripts that were mentioned in the previous point.
