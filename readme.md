# EasyCL

##why EasyCL?

Easy to write and read.
You can directly and independently get command line arguments in multiple places.

e.g. with Easy CL:
```
kwarg1 = EasyCL.get_arg("--kwarg1")
parg1 = EasyCL.get_arg("fuga")

def set_logger():
    logger_level = EasyCL.get_arg("--log_level")
    logger.setLevel(logger_level)

set_logger()
```


Equivalent script without EasyCL:
```
parser = argparse.ArgumentParser()
parser.add_argument("--kwarg1")
parser.add_argument("fuga")

def set_log_level_arg(parser):
    parser.add_argument("--log_level")

set_log_level_arg(parser)

args = parser.parse_args()
kwarg1, parg1, logger_level = args.kwarg1, args.fuga, args.log_level

def set_level_on_logger(level):
    logger.setLevel(level)

set_level_on_logger(logger_level)
```

You must give parser to add arguments in other scope.
Moreover, you must parse after all arguments set.
Then you must give the result of parse to other scope again to process the result.

It's really tiresome.


##How to install
```git clone```

##How to use
It's just a wrapper of argparse. Same arguments should be given for EasyCL.
Few cost to learn.

To give some args for ArgumentParser constructor: 
```EasyCL.set_args_for_parser_getter(*args, **kwargs)```

To give arguments for parser.add_argument(*args, **kwargs):
```EasyCL.get_arg(*args, **kwargs)```

If you want help auto generation, add following code after all arguments received.
```EasyCL.create_help()```
