# FreeCL

## why FreeCL?

FreeCL halves codes to treat command line arguments.  
Your code will get more readability.  
You can get command line arguments in multiple places directly, separately, and freely!

It will take very shot time since it's a wrapper of argparse.


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


Equivalent script without EasyCL:
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

Without freeCL, you must  
･Give parser instance to function in order to add arguments.  
･Parse after all arguments set.  
･Give the result of parse to other scope again to process the result.  

freeCL frees you from such tiresome steps.

## How to use
It's a wrapper of argparse. You can give same arguments for freeCL as argparse.  
Just call freeCL.parse(*args, **kwargs) with same arguments as argparse.ArgumentParser().add_argument(*args, **kwargs).

To give some args for ArgumentParser constructor:
```freeCL.Parser.set_args_for_parser_getter(*args, **kwargs)```

If you want help auto generation, add following code after all arguments received.
```EasyCL.create_help()```
