# FreeCL
FreeCL is a simple friendly command line parser.
```
given_kwarg = parse("--kwarg")
```

FreeCL allows you to parse command line arguments extremely easily.
There’s no need to manually add arguments to a parser beforehand, or reuse the parser or result in multiple scopes.

e.g. Script with freeCL:
```
from freeCL import parse

kwarg = parse("--kwarg")
parg = parse("fuga")

def set_logger():
    logger_level = parse("--log_level")
    logger.setLevel(logger_level)

set_logger()
```
Equivalent script without freeCL:
```
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--kwarg")
parser.add_argument("fuga")

def set_log_level_arg(parser):
    parser.add_argument("--log_level")

set_log_level_arg(parser)

args = parser.parse_args()
kwarg, parg, logger_level = args.kwarg1, args.fuga, args.log_level

def set_level_on_logger(level):
    logger.setLevel(level)

set_level_on_logger(logger_level)
```

## Install
```git clone https://github.com/yoko72/freeCL```
Put the dir on path.

## How to use
FreeCL is a wrapper of argparse. You can give arguments for freeCL same as argparse.
The reference of argparse is https://docs.python.org/ja/3/howto/argparse.html.

Just call freeCL.parse(*args, **kwargs) as if argparse.ArgumentParser().add_argument(*args, **kwargs).
To give some args for ArgumentParser constructor: freeCL.Parser.set_args_for_parser_getter(*args, **kwargs)
If you want to generate help automatically, call freeCL.create_help(). It must be done after all arguments got parsed. 