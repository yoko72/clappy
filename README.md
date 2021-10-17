# clappy

Command Line Argument Parser for pythonic code.


Simple example with clappy:

    import clappy as cl

    foo = cl.parse("--foo")
    bar = cl.parse("--bar", is_flag=True)

Equivalent script without clappy:

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--foo")
    parser.add_argument("--bar", action="store_true")
    args = parser.parse_args()
    foo = args.foo
    bar = args.bar
    

Script with clappy is more readable and writable.

Clappy will be big help especially when you use subcommands.

Subcommand with clappy:

    import clappy as cl

    if cl.subcommand("foo").invoked:
        opt = cl.parse("--foo_opt")
    elif cl.subcommand("bar").invoked:
        opt = cl.parse("--bar_opt")

Equivalent script without clappy:

    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparser1 = subparsers.add_parser("foo")
    subparser1.add_argument("--foo_opt")
    subparser2 = subparsers.add_parser("bar")
    subparser2.add_argument("--bar_opt")
    args = parser.parse_args()
    try:
        opt = args.foo_opt
    except AttributeError:
        try:
            opt = args.bar_opt
        except AttributeError:
            pass

Clappy becomes really helpful when you have multiple modules requiring command line arguments.
Without clappy you must manage same parser and the result of parse across multiple modules.

Clappy frees you from such tiresome process by independent parsing.


## Install

`pip install clappy`

## How to use

It's a wrapper of argparse. You can give arguments for functions of clappy as if you use argparse. [Reference of argparse is here.](https://docs.python.org/ja/3/howto/argparse.html)

Just call clappy.parse(*args, **kwargs) as if argparse.ArgumentParser().add_argument(*args, **kwargs). 
Same args are available. Additionally, clappy accepts one keyword argument, "is_flag".
It's just an alias of action="store_true" in argparse. 
An option with "is_flag" doesn't require argument, and it returns bool if the option is given in command line or not.

### Subcommand

To use subcommand, call clappy.subcommand().

The subcommand function accepts same arguments as subparsers.add_parser().

    subcommand = clappy.subcommand(*args, **kwargs)  # 1

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="foo")
    subparser = subparsers.add_parser(*args, **kwargs)  # 2
    
    # 1 and 2 accept same arguments.

You can detect if the subcommand is invoked in both implicit or explicit ways.
Following 2 examples are equivalent.

    sc = clappy.subcommand("foo")
    if sc.invoked:
        # do smth

    if clappy.subcommand("foo"):
        # do smth

### Auto help generation

If you want to generate help automatically, call clappy.create_help(). 
It must be done after all arguments got parsed.

### Construct parser with args

Initialize parser with clappy.initialize_parser(*args, **kwargs).
These args are common with argparse.ArgumentParser(*args, **kwargs).

