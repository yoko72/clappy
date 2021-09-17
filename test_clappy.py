import clappy
import unittest
import argparse


def get_parsed_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", default=2)
    parser.add_argument("--b1", default=7)
    parser.add_argument("--flag", action="store_true")
    parser.add_argument("positionals", nargs="*")
    parsed_args = parser.parse_args(args)
    return parsed_args


def get_parsed_args_with_sub(args):
    parser = argparse.ArgumentParser()
    # parser.add_argument("--kw", default=3)
    subparsers = parser.add_subparsers()
    subparser1 = subparsers.add_parser("sub")
    subparser1.add_argument("--subopt")
    # subparser2 = subparsers.add_parser("sub2")
    # subparser2.add_argument("--second_sub_opt")
    result = parser.parse_args(args)
    return result


class TestClappy(unittest.TestCase):
    """Checks the result of parsing if it's same between clappy and argparse. """
    def test_parse(self):
        args = ("-a", "3", "--b1", "4", "5", "6")
        namespace = get_parsed_args(args)
        clappy.set_args_on_parse(*args)
        self.assertEqual(namespace.a, clappy.parse("-a"))
        self.assertEqual(namespace.b1, clappy.parse("--b1"))
        self.assertEqual(namespace.flag, clappy.parse("--flag", action="store_true"))
        self.assertEqual(namespace.positionals, clappy.parse("positionals", nargs="*"))

    def test_subcommand(self):
        args = ("sub", "--subopt", "3")
        namespace = get_parsed_args_with_sub(args)
        clappy.set_args_on_parse(*args)
        subparser = clappy.get_subcommand_parser("sub")
        self.assertEqual(namespace.subopt, subparser.parse("--subopt"))


if __name__ == '__main__':
    unittest.main()
