import clappy
import unittest
import argparse
import sys
import functools
import inspect


bounds: list[inspect.BoundArguments] = []


def temp_argv(*outer_args):
    def get_decorated_func(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            global bounds
            sys.argv[1::] = outer_args
            result = test_func(*args, **kwargs)
            del sys.argv[1::]
            clappy._parser = None
            clappy._subparsers = None
            bounds = []
            return result
        return wrapper
    return get_decorated_func


signature = inspect.signature(argparse.ArgumentParser().add_argument)


def append_bound(*args, **kwargs):
    argument_bound = signature.bind(*args, **kwargs)
    bounds.append(argument_bound)


class TestClappy(unittest.TestCase):
    """Checks the result of parsing."""

    @temp_argv("a", "b", "c")
    def test_positional_arg(self):
        self.assertEqual(clappy.parse("positionals", nargs="*"), ["a", "b", "c"])

    @temp_argv("--kw", "hoge")
    def test_kwarg(self):
        self.assertEqual(clappy.parse("--kw"), "hoge")

    @temp_argv("sub1", "--subkw", "foo")
    def test_subcommand(self):
        subparser = clappy.get_subcommand_parser("sub1")
        self.assertEqual(subparser.parse("--subkw"), "foo")

    @temp_argv("-a", "3", "--b1", "4", "5", "6")
    def test_parse(self):
        append_bound("-a", default=2)
        append_bound("--b1", default=7)
        append_bound("--flag", action="store_true")
        append_bound("positionals", nargs="*")

        parser = argparse.ArgumentParser()
        for bound in bounds:
            parser.add_argument(*bound.args, **bound.kwargs)
        namespace = parser.parse_args()

        for bound in bounds:
            try:
                arg = bound.args[0]
            except IndexError:
                arg = bound.kwargs["dest"]
            finally:
                # noinspection PyUnboundLocalVariable
                arg = arg.lstrip(parser.prefix_chars)
            with self.subTest(arg=arg):
                self.assertEqual(clappy.parse(*bound.args, **bound.kwargs), getattr(namespace, arg))


if __name__ == '__main__':
    unittest.main()
