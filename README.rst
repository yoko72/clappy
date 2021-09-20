clappy
======

Command Line Argument Parser for PYthonic code.

::

   given_kwarg1 = clappy.parse("--kwarg1")

You can get each given command line argument easily. You don't have to bother about using parser anymore.

e.g. Script with clappy:

::

   import clappy as cl

   kwarg = cl.parse("--kwarg")
   posi_args = cl.parse("fuga")

   def set_logger():
       logger.setLevel(cl.parse("--log_level"))

   set_logger()

Equivalent script without clappy:

::

   from argparse import ArgumentParser

   parser = ArgumentParser()
   parser.add_argument("--kwarg")
   parser.add_argument("fuga")

   def set_log_level_arg(parser):
       parser.add_argument("--log_level")

   set_log_level_arg(parser)

   args = parser.parse_args()
   kwarg, posi_args, logger_level = args.kwarg1, args.fuga, args.log_level

   def set_level_on_logger(level):
       logger.setLevel(level)

   set_level_on_logger(logger_level)

When you accept arguments from command-line in multiple scopes, you must
give the parser and result to another scope. Clappy will solve it!

Install
-------

``pip install clappy``

How to use
----------

clappy is a wrapper of argparse. You can give arguments for clappy same
as argparse. `Reference of argparse is
here. <https://docs.python.org/ja/3/howto/argparse.html>`__

Just call clappy.parse(\*args, \*\*kwargs) as if argparse.ArgumentParser().add_argument(\*args, \*\*kwargs).
Both methods accept same args.

If you want to generate help automatically, call clappy.create_help().
It must be done after all arguments got parsed.

To give some args for ArgumentParser constructor: initialize parser with
clappy.initialize_parser(\*args, \*\*kwargs).
