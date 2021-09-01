from argparse import ArgumentParser
from dataclasses import dataclass
from sys import exit, argv
from gettext import gettext as _
import logging


logger = logging.getLogger(__name__)


@dataclass
class ArgumentsQueue:
    positional_args: tuple
    kwargs: dict


class Parser(ArgumentParser):
    arguments = []
    args_for_parser = tuple()
    kwargs_for_parser = dict(add_help=False)

    @classmethod
    def set_args_for_parser_getter(cls, *args, **kwargs):
        cls.args_for_parser = args
        cls.kwargs_for_parser = kwargs

    @classmethod
    def get_parser(cls):
        return cls(*cls.args_for_parser, **cls.kwargs_for_parser)

    @classmethod
    def get_arg(cls, *args, **kwargs):
        parser = cls.get_parser()
        if args or kwargs:
            cls.arguments.append(ArgumentsQueue(args, kwargs))
        for arg_info in cls.arguments:
            parser.add_argument(*arg_info.positional_args, **arg_info.kwargs)
        parsed_args = parser.parse_args()
        return getattr(parsed_args, args[0].lstrip("-"))

    @classmethod
    def create_help(cls, *args, **kwargs):
        """Create help and exit program. If help message by -h is not required, this method is not needed."""
        if len(argv) == 1:
            logger.info("Script started without arguments.")
            return
        elif len(argv) == 2 and argv[1] in ["-h", "--help"]:
            if not cls.arguments:
                raise TypeError("No argument was given for help.")
            if cls.kwargs_for_parser["add_help"] is True:
                return
            cls.kwargs_for_parser["add_help"] = True
            cls.get_arg(*args, **kwargs)
            exit()

    def parse_args(self, *args, **kwargs):
        args, _ = self.parse_known_args()
        return args

    def _parse_optional(self, arg_string):
        if not arg_string:
            return None

        if not arg_string[0] in self.prefix_chars:
            return None

        if arg_string in self._option_string_actions:
            action = self._option_string_actions[arg_string]
            return action, arg_string, None

        if len(arg_string) == 1:
            return None

        if '=' in arg_string:
            option_string, explicit_arg = arg_string.split('=', 1)
            if option_string in self._option_string_actions:
                action = self._option_string_actions[option_string]
                return action, option_string, explicit_arg

        option_tuples = self._get_option_tuples(arg_string)

        if len(option_tuples) > 1:
            options = ', '.join([option_string for action, option_string, explicit_arg in option_tuples])
            args = {'option': arg_string, 'matches': options}
            msg = _('ambiguous option: %(option)s could match %(matches)s')
            self.error(msg % args)

        # Added "and option_tuples[0][0].option_strings == arg_string:" to ArgumentParser
        elif len(option_tuples) == 1 and option_tuples[0][0].option_strings == arg_string:
            option_tuple, = option_tuples
            return option_tuple

        if self._negative_number_matcher.match(arg_string):
            if not self._has_negative_number_optionals:
                return None

        if ' ' in arg_string:
            return None

        return None, arg_string, None


def parse(*args, **kwargs):
    """alias of Parser.get_arg"""
    return Parser.get_arg(*args, **kwargs)

def create_help(*args, **kwargs):
    """alias of Parser.create_help(*args, **kwargs)"""


if __name__ == "__main__":

    def example():
        arg1 = parse("--arg1", help="Keyword optional arg")
        i = Parser.get_arg("-i")
        hoge = parse("--hoge")
        posi = parse("aiueo", nargs="*")
        print("arg1: ", arg1)
        print("i: ", i)
        print("hoge: ", hoge)
        print("aiueo: ", posi)
        create_help()  # write this only when you need help with -h or --help.
        print("after help")

    example()
