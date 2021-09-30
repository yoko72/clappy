import clappy
import unittest
import argparse
import sys
import functools
import inspect
from test.support import captured_stderr


PREFIX = "-"
bounds: list[inspect.BoundArguments] = []


def temp_argv(*outer_args):
    def get_decorated_func(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            global bounds
            sys.argv[1::] = outer_args
            result = test_func(*args, **kwargs)
            del sys.argv[1::]
            return result
        return wrapper
    return get_decorated_func


signature = inspect.signature(argparse.ArgumentParser().add_argument)


def append_bound(*args, **kwargs):
    argument_bound = signature.bind(*args, **kwargs)
    bounds.append(argument_bound)


def get_namespace_from_pure_argparse():
    parser = argparse.ArgumentParser()
    for bound in bounds:
        parser.add_argument(*bound.args, **bound.kwargs)
    return parser.parse_args()


def get_arg(bound):
    try:
        arg = bound.args[0]
    except IndexError:
        arg = bound.kwargs["dest"]
    finally:
        # noinspection PyUnboundLocalVariable
        arg = arg.lstrip(PREFIX)
    return arg


class MyTestResult(unittest.TestResult):
    def addFailure(self, test, err):
        # here you can do what you want to do when a test case fails
        print('test failed!')
        super(MyTestResult, self).addFailure(test, err)

    def addError(self, test, err):
        # here you can do what you want to do when a test case raises an error
        super(MyTestResult, self).addError(test, err)


class TestClappy(unittest.TestCase):
    """Checks the result of parsing."""

    def tearDown(self) -> None:
        global bounds
        clappy._parser = None
        clappy._subparsers = None
        bounds = []

    @temp_argv("a", "b", "c")
    def test_positional_arg(self):
        self.assertEqual(clappy.parse("positionals", nargs="*"), ["a", "b", "c"])

    @temp_argv("--kw", "hoge")
    def test_kwarg(self):
        self.assertEqual(clappy.parse("--kw"), "hoge")

    @temp_argv("-k", "foo")
    def test_abbreviated(self):
        self.assertEqual(clappy.parse("--keyword", "-k", "-kw"), "foo")

    @temp_argv("-ke", "foo")
    def test_shorter_name_than_given_arg(self):
        append_bound("-keyword")
        namespace = get_namespace_from_pure_argparse()
        self.assertEqual(clappy.parse(*bounds[0].args, **bounds[0].kwargs), namespace.keyword)

    @temp_argv("sub1", "--subkw", "foo")
    def test_subcommand(self):
        subparser = clappy.get_subcommand_parser("sub1")
        result = subparser.parse("--subkw")
        self.assertEqual(result, "foo")

    @temp_argv("-a", "3", "--b1", "4", "5", "6")
    def test_parse_combined_arguments(self):
        append_bound("-a", default=2)
        append_bound("--b1", default=7)
        append_bound("--flag", action="store_true")
        append_bound("positionals", nargs="*")

        namespace = get_namespace_from_pure_argparse()

        for bound in bounds:
            arg = get_arg(bound)
            with self.subTest(arg=arg):
                self.assertEqual(getattr(namespace, arg), clappy.parse(*bound.args, **bound.kwargs))

    @temp_argv("-kfoo")
    def test_value_without_space(self):
        append_bound("-k")
        namespace = get_namespace_from_pure_argparse()
        self.assertEqual(clappy.parse(*bounds[0].args, **bounds[0].kwargs), namespace.k)

    @temp_argv("-kw5", "wrong1", "-k", "correct", "-kw4", "wrong2")
    def test_same_first_char(self):
        append_bound("-k")
        append_bound("-kw4")
        append_bound("-kw5")
        namespace = get_namespace_from_pure_argparse()
        for bound in bounds:
            arg = get_arg(bound)
            with self.subTest(arg=arg):
                self.assertEqual(clappy.parse(*bound.args, **bound.kwargs), getattr(namespace, arg))

    @temp_argv("-a1", "-a2", "val")
    def test_stderr(self):
        """The value of k should be correct, but """
        append_bound("-a")
        append_bound("-a2")
        with captured_stderr() as stderr:
            clappy.parse(*bounds[0].args, **bounds[0].kwargs)
            clappy.parse(*bounds[1].args, **bounds[1].kwargs)
        stdout_list = stderr.getvalue().splitlines()
        expected_message = clappy.get_parser().VALUE_CHANGE_MESSAGE.format(
            input_arg_name="-a2", attr="a",
            last_time="2", this_time="1"
        )
        expected_list = expected_message.splitlines()
        self.assertEqual(stdout_list, expected_list)

    @temp_argv("--foo", "1", "--foo", "2")
    def test_append(self):
        append_bound("--foo", action="append")
        namespace = get_namespace_from_pure_argparse()
        for bound in bounds:
            arg = get_arg(bound)
            with self.subTest(arg=arg):
                self.assertEqual(clappy.parse(*bound.args, **bound.kwargs), getattr(namespace, arg))


if __name__ == '__main__':
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=MyTestResult))
