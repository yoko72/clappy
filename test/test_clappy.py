import unittest
import sys
import functools
import importlib
import pathlib
from test.support import captured_stderr, captured_stdout
from textwrap import dedent

# noinspection PyPackageRequirements
import pyperclip
import clappy as cl

import for_another_group


python_version = float(sys.version[:3])
this_module_path = pathlib.Path(__file__)
name_of_this_file = this_module_path.stem


def temp_argv(*outer_args):
    def get_decorated_func(test_func):
        @functools.wraps(test_func)
        def parse_with_args(*args, **kwargs):
            nonlocal outer_args
            if len(outer_args) == 1:
                outer_args = outer_args[0].split(" ")
            cl.set_args_getting_parsed(outer_args)
            result = test_func(*args, **kwargs)
            return result
        return parse_with_args
    return get_decorated_func


def generate_help_text(stdout, func, subcommand_name):
    """Helper function to make tests."""
    chars_for_sub = f"_with_{subcommand_name}" if subcommand_name else ""
    help_messages_list = [f"""    HELP_FOR_{func.__name__}{chars_for_sub} = dedent(\"\"\"\\"""]
    for line in stdout:
        indent = " " * 8
        help_messages_list.append(indent + line)
    help_messages_list.append("        \"\"\")")
    return "\n".join(help_messages_list)


def expected_help_is(expected_help_message: str = "", *, cl_args_for_help="-h"):
    def wrapper(func):
        func = func.__wrapped__ if hasattr(func, "__wrapped__") else func
        cl_args_list = cl_args_for_help.split(" ")
        subcommand_name = "" if len(cl_args_list) == 1 else cl_args_list[0]

        @functools.wraps(func)
        def test_parse_and_help(self):
            def test_parse():
                with self.subTest("parse"):
                    with cl.get_parser(prog=f"{name_of_this_file}.py"):
                        func(self)
                self.tearDown()
                self.runs_assert = False

            def test_help():
                with self.subTest("help"):
                    cl.set_name_of_main_script(name_of_this_file)
                    self.stop_assert_methods()
                    cl.set_args_getting_parsed(cl_args_list)
                    with captured_stdout() as stdout:
                        with self.assertRaises(SystemExit):
                            with cl.get_parser(prog=f"{name_of_this_file}.py"):
                                func(self)
                    self.runs_assert = True
                    expected = expected_help_message.splitlines()
                    actual = stdout.getvalue().splitlines()
                    if expected != actual:
                        help_text = generate_help_text(actual, func, subcommand_name)
                        pyperclip.copy(help_text)
                        print("Actual help output is copied to clipboard.")
                    try:
                        self.assertEqual(expected, actual)
                    except AssertionError as e:
                        raise_exception_from_line_of_direct_cause(func, e.args[0])

            test_parse()
            test_help()
        return test_parse_and_help
    return wrapper


class HelpNotMatched(Exception):
    def __init__(self, *args):
        self.args = args


def raise_exception_from_line_of_direct_cause(wrapped_func, exception_message=""):
    code = wrapped_func.__code__
    message = f'File "{code.co_filename}", line {code.co_firstlineno}'
    if exception_message:
        print(exception_message + "\n", file=sys.stderr)
    raise HelpNotMatched(message) from None


class TestBase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.runs_assert = True  # assertEqual in test method is ignored on checking if help works.

    def assertEqual(self, *args, **kwargs):
        if self.runs_assert:
            return super().assertEqual(*args, **kwargs)
        else:
            return super().assertEqual(True, True)

    def assertTrue(self, *args, **kwargs):
        if self.runs_assert:
            return super().assertTrue(*args, **kwargs)
        else:
            return super().assertTrue(True, True)

    def tearDown(self) -> None:
        self.runs_assert = True
        importlib.reload(cl.utils)
        importlib.reload(cl.main)
        importlib.reload(cl)

    def stop_assert_methods(self):
        self.runs_assert = False


# noinspection SpellCheckingInspection
class TestClappy(TestBase):

    def test_returns_on_help(self):
        cl.set_args_getting_parsed("-h")
        with captured_stdout():
            with self.assertRaises(SystemExit):
                with cl.get_parser():
                    foo = cl.parse("-f")
                    self.assertTrue(isinstance(foo, cl.ReturnOnHelp))
                    self.assertFalse(foo)

    def test_help_without_with_block(self):
        def test_run():
            cl.set_args_getting_parsed(["-h"])
            with captured_stderr() as stderr:
                cl.parse("-f")
            return stderr.getvalue()

        with self.subTest("when generates_help=True"):
            stderr = test_run()
            expected = dedent("""\
                To print help run all parse functions within the block of with clappy.get_parser.""")
            expected = expected.splitlines()
            actual = stderr.splitlines()
            self.assertEqual(expected, actual)

        with self.subTest("when generates_help=False"):
            self.tearDown()
            cl.get_parser(generates_help=False)
            stderr = test_run()
            self.assertEqual(stderr, "")

    def test_alias_auto_help_generator(self):
        with self.subTest("parse"):
            cl.set_args_getting_parsed("1 2 foo")
            with cl.auto_help_generator():
                vals = cl.parse("aiueo", nargs=cl.nargs.ONE_OR_MORE)
                self.assertEqual(vals, ["1", "2", "foo"])
        with self.subTest("help"):
            self.tearDown()
            cl.set_args_getting_parsed("-h")
            with self.assertRaises(SystemExit):
                with captured_stdout() as stdout:
                    with cl.auto_help_generator():
                        cl.parse("aiueo", nargs=cl.nargs.ONE_OR_MORE)
            printed_usage = stdout.getvalue().splitlines()
            jointed_chars = "\n".join(printed_usage).replace("_jb_unittest_runner", name_of_this_file)

        expected_help = dedent("""\
            usage: test_clappy.py [-h] aiueo [aiueo ...]
            
            optional arguments:
              -h, --help  show this help message and exit
            
            test_clappy:
              aiueo""")

        self.assertEqual(jointed_chars, expected_help)

    def test_help_with_multiple_get_parser_block(self):
        expected = dedent("""\
            usage: test_clappy.py [-h] [-one ONE] [-two TWO]
            
            optional arguments:
              -h, --help  show this help message and exit
              -one ONE
              -two TWO
            """)

        cl.get_parser(prog=name_of_this_file + ".py")
        cl.set_args_getting_parsed("-h")
        cl.set_name_of_main_script(name_of_this_file)

        with self.assertRaises(SystemExit):
            with captured_stdout() as stdout:
                with cl.get_parser():
                    cl.parse("-one")
                    with cl.get_parser():
                        cl.parse("-two")
        actual_output = stdout.getvalue().splitlines()
        self.assertEqual(expected.splitlines(), actual_output)

    HELP_FOR_test_only_positional_base = dedent("""\
        positional arguments:
          positionals

        optional arguments:
          -h, --help   show this help message and exit
        """)

    if python_version == 3.6:
        usage_chars = "usage: test_clappy.py [-h] [positionals [positionals ...]]"
    else:  # only 3.9 is passed in test, and others are not tested yet
        usage_chars = "usage: test_clappy.py [-h] [positionals ...]"
    HELP_FOR_test_only_positional = usage_chars + "\n\n" + HELP_FOR_test_only_positional_base

    @temp_argv("a", "b", "c")
    @expected_help_is(HELP_FOR_test_only_positional)
    def test_only_positional(self):
        self.assertEqual(cl.parse("positionals", nargs=cl.nargs.ZERO_OR_MORE), ["a", "b", "c"])


    HELP_FOR_test_long_option = dedent("""\
        usage: test_clappy.py [-h] [--kw KW]

        optional arguments:
          -h, --help  show this help message and exit
          --kw KW
        """)

    @temp_argv("--kw", "hoge")
    @expected_help_is(HELP_FOR_test_long_option)
    def test_long_option(self):
        self.assertEqual(cl.parse("--kw"), "hoge")

    HELP_FOR_test_short_option = dedent("""\
        usage: test_clappy.py [-h] [--keyword KEYWORD]

        optional arguments:
          -h, --help            show this help message and exit
          --keyword KEYWORD, -k KEYWORD, -kw KEYWORD
        """)

    @temp_argv("-k", "val")
    @expected_help_is(HELP_FOR_test_short_option)
    def test_short_option(self):
        self.assertEqual(cl.parse("--keyword", "-k", "-kw"), "val")

    HELP_FOR_test_shorter_name_than_given_arg = dedent("""\
        usage: test_clappy.py [-h] [-keyword KEYWORD]

        optional arguments:
          -h, --help        show this help message and exit
          -keyword KEYWORD
        """)
    
    @temp_argv("-ke", "foo")
    @expected_help_is(HELP_FOR_test_shorter_name_than_given_arg)
    def test_shorter_name_than_given_arg(self):
        self.assertEqual(cl.parse("-keyword"), "foo")

    HELP_FOR_test_subcommand = dedent("""\
        usage: test_clappy.py [-h] {sub1} ...

        optional arguments:
          -h, --help  show this help message and exit

        commands:
          {sub1}
            sub1
        """)

    HELP_FOR_test_subcommand_with_sub1 = dedent("""\
        usage: test_clappy.py sub1 [-h] [--subkw SUBKW]

        optional arguments:
          -h, --help     show this help message and exit
          --subkw SUBKW
        """)

    @temp_argv("sub1", "--subkw", "foo")
    @expected_help_is(HELP_FOR_test_subcommand_with_sub1, cl_args_for_help="sub1 -h")
    @expected_help_is(HELP_FOR_test_subcommand)
    def test_subcommand(self):
        sc1 = cl.subcommand("sub1")
        if sc1.invoked:
            self.assertEqual(sc1.parse("--subkw"), "foo")

        sc2 = cl.subcommand("sub2")
        if sc2.invoked:
            self.assertEqual(sc2.parse("--subopt2"), "bar")

    @temp_argv("sub2 --subopt2 bar")
    def test_subcommand2(self):
        # noinspection PyUnresolvedReferences
        self.test_subcommand.__wrapped__(self)

    HELP_FOR_test_group = dedent("""\
        usage: test_clappy.py [-h] [--m2 M2] [--s1 S1] [--s2 S2] m1 [m1 ...]

        optional arguments:
          -h, --help  show this help message and exit

        main:
          m1          help of m1
          --m2 M2

        sub:
          --s1 S1     help of s1
          --s2 S2
        """)

    @temp_argv("a", "b", "c", "--m2", "2", "--s1", "d", "--s2", "2")
    @expected_help_is(HELP_FOR_test_group)
    def test_group(self):  #
        with cl.get_group("main"):
            self.assertEqual(cl.parse("m1", nargs=cl.nargs.ONE_OR_MORE,
                                      help="help of m1"), ["a", "b", "c"])
            self.assertEqual(cl.parse("--m2"), "2")
        with cl.get_group("sub"):
            self.assertEqual(cl.parse("--s1", help="help of s1"), "d")
            self.assertEqual(cl.parse("--s2"), "2")

    HELP_FOR_test_auto_groups = dedent("""\
        usage: test_clappy.py [-h] [-f F] [--another ANOTHER]

        optional arguments:
          -h, --help         show this help message and exit
          -f F

        for_another_group:
          --another ANOTHER
        """)

    @temp_argv("-f foo --another bar")
    @expected_help_is(HELP_FOR_test_auto_groups)
    def test_auto_groups(self):
        self.assertEqual(cl.parse("-f"), "foo")
        self.assertEqual(for_another_group.parse(), "bar")

    HELP_FOR_test_deep_indented_groups = dedent("""\
        usage: test_clappy.py [-h] [-f F] [-b B] [--baz BAZ] [-s S]

        optional arguments:
          -h, --help  show this help message and exit

        group1:
          -f F
          -b B

        group2:
          --baz BAZ
          -s S
        """)

    @temp_argv("-f foo -b bar --baz bazu -s squx")
    @expected_help_is(HELP_FOR_test_deep_indented_groups)
    def test_deep_indented_groups(self):
        with cl.get_group("group1"):
            cl.parse("-f")
            cl.parse("-b")
            with cl.get_group("group2"):
                cl.parse("--baz")
                cl.parse("-s")


    def for_test_with_many_settings(self):
        self.assertEqual(cl.parse(
            "-f", "--foo", help="help message", action=cl.action.APPEND, nargs=2, type=int, required=True),
            [[1, 2], [3, 4]])
        self.assertEqual(cl.parse(
            "-b", "--bar", help="help message2", default="default_value",
            choices=("a", "b", "c"), metavar="META", dest="dest"), "a")

    HELP_FOR_test_parse_with_many_args = dedent("""\
        usage: test_clappy.py [-h] -f FOO FOO [-b META]

        optional arguments:
          -h, --help            show this help message and exit
          -f FOO FOO, --foo FOO FOO
                                help message
          -b META, --bar META   help message2
        """)

    @temp_argv("-f 1 2 -f 3 4 -b a")
    @expected_help_is(HELP_FOR_test_parse_with_many_args)
    def test_parse_with_many_settings(self):  #
        self.for_test_with_many_settings()

    @temp_argv("-f 1 2 -f 3 4 -b invalid_choice")
    def test_invalid_choice(self):
        with captured_stderr() as stderr:
            with self.assertRaises(SystemExit):
                self.for_test_with_many_settings()
        self.assertTrue("invalid choice" in stderr.getvalue())

    @temp_argv("-f not_int_type d -f 3 4 -b b")
    def test_invalid_type(self):
        with captured_stderr() as stderr:
            with self.assertRaises(SystemExit):
                self.for_test_with_many_settings()
        self.assertTrue("invalid int value" in stderr.getvalue())

    @temp_argv("-kval_for_k -kw4 val_for_kw4 -tval_for_t -tw5 val_for_kw5 ")
    def test_value_changes(self):
        with self.subTest("1st"):
            with captured_stderr() as stderr:
                self.assertEqual(cl.parse("-k"), "w4")
                self.assertEqual(cl.parse("-kw4"), "val_for_kw4")
            expected_output = cl.get_parser().VERBOSE_VALUE_CHANGE_MESSAGE.format(
                parsing_dest="kw4", name_of_changed_arg="k", last_val="w4", current_val="val_for_k")
            expected_output = expected_output.splitlines()
            actual_output = stderr.getvalue().splitlines()
            self.assertEqual(actual_output, expected_output)

        with self.subTest("2nd"):
            with captured_stderr() as stderr:
                self.assertEqual(cl.parse("-t"), "w5")
                self.assertEqual(cl.parse("-tw5"), "val_for_kw5")
            expected_output = cl.get_parser().VALUE_CHANGE_MESSAGE.format(
                parsing_dest="tw5", changed_arg="t", last_val="w5", current_val="val_for_t")
            expected_output = expected_output.splitlines()
            actual_output = stderr.getvalue().splitlines()
            self.assertEqual(actual_output, expected_output)

    @temp_argv("--foo val")
    def test_meaningless_dest(self):
        val = cl.parse("-f", "--foo", dest="aiueo")
        self.assertEqual(val, "val")


if __name__ == '__main__':
    unittest.main()
