# clappy

Command Line Argument Parser for Pythonic code.
Simple, readable, and writable wrapper of argparse.

with clappy:

    import clappy as cl

    foo = cl.parse("--foo")
    bar = cl.parse("--bar", is_flag=True)

without clappy:

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--foo")
    parser.add_argument("--bar", action="store_true")
    args = parser.parse_args()
    foo = args.foo
    bar = args.bar
    
Clappy is strong especially with subcommands.

with clappy:

    import clappy as cl

    if cl.subcommand("foo").invoked:
        opt = cl.parse("--foo_opt")
    elif cl.subcommand("bar").invoked:
        opt = cl.parse("--bar_opt")

without clappy:

    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparser1 = subparsers.add_parser("foo")
    subparser1.add_argument("--foo_opt")
    subparser2 = subparsers.add_parser("bar")
    subparser2.add_argument("--bar_opt")
    args = parser.parse_args()

    if hasattr(args, "foo_opt"):
        opt = args.foo_opt
    elif hasattr(args, "bar_opt"):
        opt = args.bar_opt


Clappy becomes really helpful when you have multiple modules requiring command line arguments.
Without clappy you must manage same parser and the result of parse across multiple modules.

Clappy frees you from such tiresome process by parsing independently.


## Install

`pip install clappy`

## How to use

It's a wrapper of argparse and same arguments are available.

Just call clappy.parse(*args, **kwargs) as if argparse.ArgumentParser().add_argument(*args, **kwargs). 
[Reference is here.](https://docs.python.org/3/library/argparse.html#the-add-argument-method)

Additionally, clappy.parse accepts one keyword argument named "is_flag".
It's just an alias of action="store_true" in argparse.

An option with "is_flag" doesn't require argument, and it returns bool if the option is given in command line or not.

### Subcommand

To use subcommand, call clappy.subcommand().

The subcommand function accepts same arguments as subparsers.add_parser().
[Available arguments are here.](https://docs.python.org/3/library/argparse.html#argumentparser-objects)

It accepts only one positional argument like add_parser() method.

    subcommand = clappy.subcommand(name, **kwargs)  # 1

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="foo")
    subparser = subparsers.add_parser(name, **kwargs)  # 2
    
    # 1 and 2 accept same arguments.

You can detect if the subcommand is invoked in both implicit or explicit ways.
Following 2 examples are equivalent.

    sc = clappy.subcommand("foo")
    if sc.invoked:
        # do smth

    if clappy.subcommand("foo"):
        # do smth

### Auto help generation

Call clappy.create_help() for auto help generation. 
It must be done after all arguments got parsed.

### Construct parser with args

Initialize parser with clappy.initialize_parser(*args, **kwargs).
These args are common with argparse.ArgumentParser(*args, **kwargs).
[Available arguments are here.](https://docs.python.org/3/library/argparse.html#argumentparser-objects)

