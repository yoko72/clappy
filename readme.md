# EasyCL

## why EasyCL?

Easy to write and read.
You can get command line arguments in multiple places directly and separately.

e.g. Script with EasyCL:
```
kwarg = EasyCL.get_arg("--kwarg")
parg = EasyCL.get_arg("fuga")

def set_logger():
    logger_level = EasyCL.get_arg("--log_level")
    logger.setLevel(logger_level)

set_logger()
```


Equivalent script without EasyCL:
```
parser = argparse.ArgumentParser()
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

Without EasyCL, you must give parser instance to add arguments in other scope.
Moreover, you must parse after all arguments set.
Then you must give the result of parse to other scope again to process the result.

EasyCL frees you from such tiresome steps.

## How to use
It's just a wrapper of argparse. You can give same arguments for EasyCL.

To give some args for ArgumentParser constructor: 
```EasyCL.set_args_for_parser_getter(*args, **kwargs)```

To give arguments for parser.add_argument(*args, **kwargs):
```EasyCL.get_arg(*args, **kwargs)```

If you want help auto generation, add following code after all arguments received.
```EasyCL.create_help()```
