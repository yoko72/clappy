from sys import exit, argv
from gettext import gettext as _
from typing import Optional
import logging
import argparse
from argparse import *
import functools
import inspect


logger = logging.getLogger(__name__)
HELP_OPTIONS = ["-h", "--help"]


if len(argv) == 2 and argv[1].lower() in HELP_OPTIONS:
    runs_with_help_option = True
    argv[1] = argv[1].lower()
else:
    runs_with_help_option = False


def normalize_bound_of_args(func):
    """Same hash by same values.
    This converts each keyword arg to positional arg as much as possible.
    If default arguments don't get actual argument, explicitly give the default value.
    """
    signature = inspect.signature(func)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        print(bound.args)
        print(bound.kwargs)
        return func(*bound.args, **bound.kwargs)
    return wrapper


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args_on_parse: Optional[tuple] = None
        self.kwargs_on_parse: Optional[dict] = {}
        self.namespace = None

    @normalize_bound_of_args
    @functools.lru_cache()  # so that parse can be called multiple times to get result in multiple places.
    def parse(self, *args, **kwargs):
        try:
            self.add_argument(*args, **kwargs)
        except argparse.ArgumentError as e:
            if e.message.startswith("conflicting"):
                msg = \
                    f"""Same arguments were registered to parser beforehand.
Usually, a cache was returned in such a case. However, cache is not returned this time 
since you run {self.parse.__name__}() this time with different arguments from last time. 
Try to use completely same arguments for {self.parse.__name__}()."""
                raise ValueError(msg) from e
        if not runs_with_help_option:
            namespace, _ = self.parse_known_args()
            self.namespace = namespace
            try:
                arg = args[0]
            except IndexError:
                arg = kwargs["dest"]
            finally:
                # noinspection PyUnboundLocalVariable
                arg = arg.lstrip(self.prefix_chars)
            return getattr(namespace, arg)

    def parse_known_args(self, *args, **kwargs):
        if args or kwargs:
            return super().parse_known_args(*args, **kwargs)
        else:
            return super().parse_known_args(self.args_on_parse, **self.kwargs_on_parse)

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

    def _get_values(self, action, arg_strings):
        # for everything but PARSER, REMAINDER args, strip out first '--'
        if action.nargs not in [PARSER, REMAINDER]:
            try:
                arg_strings.remove('--')
            except ValueError:
                pass

        # optional argument produces a default when not present
        if not arg_strings and action.nargs == OPTIONAL:
            if action.option_strings:
                value = action.const
            else:
                value = action.default
            if isinstance(value, str):
                value = self._get_value(action, value)
                self._check_value(action, value)

        # when nargs='*' on a positional, if there were no command-line
        # args, use the default if it is anything other than None
        elif (not arg_strings and action.nargs == ZERO_OR_MORE and
              not action.option_strings):
            if action.default is not None:
                value = action.default
            else:
                value = arg_strings
            self._check_value(action, value)

        # single argument or optional argument produces a single value
        elif len(arg_strings) == 1 and action.nargs in [None, OPTIONAL]:
            arg_string, = arg_strings
            value = self._get_value(action, arg_string)
            self._check_value(action, value)

        # REMAINDER arguments convert all values, checking none
        elif action.nargs == REMAINDER:
            value = [self._get_value(action, v) for v in arg_strings]

        # PARSER arguments convert all values, but check only the first
        # Here is modified from argparse. In clappy, not only value[0] but also other elements are considered.
        # Since there might be argument
        elif action.nargs == PARSER:
            value = [self._get_value(action, v) for v in arg_strings]
            validated_val = None
            for val in value:
                try:
                    self._check_value(action, val)
                except ArgumentError:
                    continue
                else:
                    validated_val = val
                    break
            if validated_val is not None:
                value = [validated_val] + value
            else:
                if action.choices:
                    if isinstance(action.choices, dict):
                        raise ArgumentError(action, f"Failed to find subcommand "
                                                    f"{list(action.choices.keys())} in args: {value}")
                    else:
                        raise ArgumentError(action, f"Failed to find subcommand "
                                                    f"{list(action.choices)} in args: {value}")
                else:
                    raise ArgumentError(action, f"Valid value for {str(action)} is not found in value: {value}")

        # SUPPRESS argument does not put anything in the namespace
        elif action.nargs == SUPPRESS:
            value = SUPPRESS

        # all other types of nargs produce a list
        else:
            value = [self._get_value(action, v) for v in arg_strings]
            for v in value:
                self._check_value(action, v)

        # return the converted value
        return value


_parser: Optional[Parser] = None


def initialize_parser(*args, **kwargs):
    global _parser
    if _parser is not None:
        if isinstance(_parser, Parser):
            raise ValueError("Tried to initialize parser although it is already initialized."
                             "If you want to remake it, set_parser(None) first, then initialize again.")
        else:
            raise ValueError(f"Tried to initialize parser, but parser is already not None."
                             f"Something wrong happend. The type of parser is {type(_parser)}.")
    if kwargs.get("add_help", None) is not None:
        add_help = kwargs["add_help"]
    else:
        if runs_with_help_option:
            add_help = True
        else:
            add_help = False
    _parser = Parser(*args, add_help=add_help, **kwargs)
    return _parser


def init_parser(func):
    global _parser

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if _parser is None:
            initialize_parser()
        return func(*args, **kwargs)
    return wrapper


def clear_actions():
    global _parser
    if _parser:
        _parser._actions = list()


def set_parser(parser: Parser):
    global _parser
    _parser = parser


@init_parser
def parse(*args, **kwargs):
    """alias of parser.parse"""
    return _parser.parse(*args, **kwargs)


@init_parser
def set_args_on_parse(*args, **kwargs):
    _parser.args_on_parse = args
    _parser.kwargs_on_parse = kwargs


def create_help(*args, **kwargs):
    """Create help and exit program. If help message by -h is not required, this method is not needed.
    Run this only when you want to show help by -h or --help"""
    if runs_with_help_option:
        _parser.parse_args(*args, **kwargs)
        exit()
    elif len(argv) == 1:
        logger.info("Script runs without arguments.")
        return


_subparsers = None


@init_parser
def initialize_subparsers(**kwargs):
    global _subparsers
    if _subparsers is None:
        _subparsers = _parser.add_subparsers(**kwargs)
    elif _subparsers is not None:
        if isinstance(_subparsers, Action):
            raise ValueError("Tried to initialize subparsers although it is already initialized.")
        else:
            raise ValueError(f"Tried to initialize subparsers, but parser is already not None."
                             f"The type of parser is {type(_subparsers)}.")
    return _subparsers


@init_parser
def get_subcommand_parser(*args, **kwargs):
    global _subparsers
    if _subparsers is None:
        initialize_subparsers()
    # noinspection PyUnresolvedReferences
    sub_parser = _subparsers.add_parser(*args, **kwargs)

    def parse(*args, **kwargs):
        sub_parser.add_argument(*args, **kwargs)
        if not runs_with_help_option:
            parsed_args, _ = _parser.parse_known_args()
            if hasattr(parsed_args, args[0].lstrip("-")):
                return getattr(parsed_args, args[0].lstrip("-"))
            else:
                return None

    sub_parser.parse = parse
    return sub_parser


if __name__ == "__main__":

    def example():
        print("Given args:", argv[1::])

        a_parser = get_subcommand_parser("a")
        sub_a = a_parser.parse("--sub_a")
        create_help()  # write this only when you need help with -h or --help.
        print(sub_a)

    example()
