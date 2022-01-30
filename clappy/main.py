from sys import argv
import logging
import argparse
import functools
from typing import Optional, Union, List, Dict
import types
from collections import namedtuple
from textwrap import dedent

from .modified_argparse import ModifiedParser
from . import utils

logger = logging.getLogger(__name__)
SUPPRESS = argparse.SUPPRESS


class _HelpContextManager:
    singleton_instance = None
    _help_chars = ("-h", "--help")
    MESSAGE_ON_DUPLICATE = dedent("""\
        Another instance is already in use as context manager. 
        Use only once to print help.""")
    HELP_ALERT = f"To print help run all parse functions within the block of with clappy.get_parser."
    _default_args_getting_parsed = argv[1::]

    def __init__(self, alerts_to_use_with_block=True):
        object.__init__(self)
        self._args_getting_parsed: list = self._default_args_getting_parsed
        self.count_of_active_with_block = 0  # indicates amount of currently being used in with statement
        self.alerts_to_use_with_block = alerts_to_use_with_block
        self.exits_after_help_message = True

    def __enter__(self):
        self.count_of_active_with_block += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is exc_val is exc_tb is None:
            self.count_of_active_with_block -= 1
            if self.count_of_active_with_block <= 0:
                self.on_end_with_blocks()
        else:
            raise exc_val

    def on_end_with_blocks(self):  # need override
        pass

    def runs_for_help(self):
        for help_char in self._help_chars:
            # noinspection PyProtectedMember
            if help_char in self.singleton_instance._args_getting_parsed:
                return True
        return False

    def validate_usage_of_help(self):
        """If runs with help option with invalid state, logger.warning() to use with block."""
        if self.runs_for_help():
            if not self.count_of_active_with_block:
                if self.alerts_to_use_with_block:
                    logger.warning(self.HELP_ALERT)
                    self.alerts_to_use_with_block = False
                return True


def _auto_construct_parser(func):
    """Constructs parser instance as singleton if not constructed."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        active_parser = _Parser.singleton_instance
        if active_parser is None:
            _Parser.singleton_instance = _Parser()
        return func(*args, **kwargs)
    return wrapper


class ReturnOnHelp:
    """Returns this instance as a result of parse on running script with help option."""
    def __bool__(self):
        return False


# noinspection PyUnresolvedReferences,PyProtectedMember
class _Parser(_HelpContextManager, ModifiedParser):
    singleton_instance: Optional["_Parser"] = None
    VERBOSE_VALUE_CHANGE_MESSAGE = dedent("""\
        While parsing {parsing_dest}, the value of "{name_of_changed_arg}" changed from {last_val} to {current_val}.
        This usually happens because of similar names of arguments or confusing order of arguments.
        Consider to change them if you actually got invalid result.""")
    VALUE_CHANGE_MESSAGE = '''"{changed_arg}" changed from {last_val} to {current_val} during parsing {parsing_dest}.'''
    UNRECOGNIZED_ERROR_MESSAGE = "unrecognized args: %s"
    default_returns_on_help = ReturnOnHelp()

    def __init__(self, *args, generates_help=True, auto_grouping=True, **kwargs):
        self._adds_help = kwargs.get("add_help", True)
        kwargs["add_help"] = False
        ModifiedParser.__init__(self, *args, **kwargs)

        self._last_namespace = None
        self._subparsers_list = []
        self._subparsers_action = None

        self._printed_verbose_log = False
        self.auto_grouping = auto_grouping

        self.return_on_help = self.default_returns_on_help
        _HelpContextManager.__init__(self, alerts_to_use_with_block=generates_help)


    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls.singleton_instance:
            parser = cls.singleton_instance = cls(*args, **kwargs)
            if parser._adds_help:  # runs add_help after init to avoid RecursionError.
                parser._add_argument("-h", "--help", help="show this help message and exit", action="help",
                                     not_group=True)
        return cls.singleton_instance

    @utils.normalize_bound
    @functools.lru_cache()
    def add_argument(self, *args, is_flag=False, **kwargs):
        if len(args) == 1:
            args = args[0].split(" ")
        if is_flag:
            if kwargs.get("action", None) is None:
                kwargs["action"] = "store_true"
            else:
                raise ValueError(dedent(f"""\
                    {self.add_argument.__name__} got multiple values for action,
                    since is_flag=True is alias of action='store_true'."""))

        try:
            action = self._add_argument(*args, **kwargs)
        except argparse.ArgumentError as e:
            if e.message.startswith("conflicting"):
                msg = dedent(f"""\
                    Tried to register same argument.
                    Usually, the cache is returned in such case. However, cache is not returned this time 
                    since some of given arguments are different from last time. 
                    Use same arguments for {self.parse.__name__}() to get cache.""")
                raise ValueError(msg) from e
            else:
                raise e

        def _parse_from_action():
            if self.runs_for_help():
                self.validate_usage_of_help()
                return self.return_on_help
            latest_namespace, unrecognized_args = self.parse_known_args()
            logger.debug(f"Unrecognized args while parsing {action.dest}: {unrecognized_args}")
            if self._last_namespace:
                for attr in self._last_namespace.__dict__:
                    last_time = getattr(self._last_namespace, attr)
                    this_time = getattr(latest_namespace, attr)
                    if last_time != this_time:
                        if self._printed_verbose_log:
                            message = self.VALUE_CHANGE_MESSAGE.format(
                                changed_arg=attr, last_val=last_time, current_val=this_time, parsing_dest=action.dest)
                        else:
                            self._printed_verbose_log = True
                            message = self.VERBOSE_VALUE_CHANGE_MESSAGE.format(
                                parsing_dest=action.dest, name_of_changed_arg=attr,
                                last_val=last_time, current_val=this_time)
                        logger.error(message)
            self._last_namespace = latest_namespace
            return getattr(latest_namespace, action.dest)

        action.parse = _parse_from_action
        return action

    def _add_argument(self, *args, not_group=False, **kwargs):
        if not_group:
            return super().add_argument(*args, **kwargs)
        active_group = _Group._get_active_group()
        if active_group:
            action = active_group.add_argument(*args, **kwargs)
        else:  # if not within with block
            if not utils.is_called_from_main() and self.auto_grouping:
                group = _Group.get()
                action = group.add_argument(*args, **kwargs)
            else:
                action = super().add_argument(*args, **kwargs)
        return action

    @classmethod
    @_auto_construct_parser
    def parse(cls, *args, is_flag=False, **kwargs):
        action = cls.singleton_instance.add_argument(*args, is_flag=is_flag, **kwargs)
        return action.parse()

    def add_argument_group(self, *args, **kwargs):
        group = _Group(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def parse_known_args(self, args=None, namespace=None):
        args = args or self._args_getting_parsed
        result = super().parse_known_args(args, namespace)
        for act in self._actions:
            if hasattr(act, "parsed_currently"):
                act.parsed_currently = False
        return result

    @staticmethod
    def _get_action_name(argument):
        if argument is None:
            return None
        elif argument.option_strings:
            return '/'.join(argument.option_strings)
        elif argument.metavar not in (None, SUPPRESS):
            return argument.metavar
        elif argument.dest not in (None, SUPPRESS):
            return argument.dest
        else:
            return None

    def add_subparsers(self, *, title="subcommand", parser_class=None, **kwargs):
        parser_class = parser_class or _SubCommand
        self._subparsers_action = super().add_subparsers(title=title, parser_class=parser_class, **kwargs)
        return self._subparsers_action

    def on_end_with_blocks(self):
        if self.runs_for_help():
            for subparser in self._subparsers_list:
                if subparser.invoked:
                    subparser.print_help()
                    break
            else:
                self.print_help()
            if self.exits_after_help_message:
                exit()
        else:
            parsed, unrecognized = self.parse_known_args()
            if unrecognized:
                logger.error(_Parser.singleton_instance.UNRECOGNIZED_ERROR_MESSAGE % unrecognized)


# noinspection PyIncorrectDocstring
@_auto_construct_parser
def parse(*args, is_flag=False, **kwargs):
    """
    Parse a command line argument.
    The same arguments as argparse.ArgumentParser.add_argument are available.
    https://docs.python.org/3/library/argparse.html#the-add-argument-method

    Additionally is_flag is available as a keyword argument. It's an alias of action="store_True".

    Parameters
    ----------
    *args: str
        Name of arguments. e.g. '-f', `--foo`.
        "-f --foo" is also treated as equivalent as above.
    is_flag: bool, default False
        Represents flag or not. If True, action="store_True" in argparse will be set.
    action: str
        Represents the kind of action for given argument.
        You can get all acceptable patterns like following.

        e.g. clappy.action.STORE, clappy.action.APPEND_CONST
    nargs: int or str
        Indicates the amount of given values.
        You can get all acceptable patterns as string like following.

        e.g. clappy.nargs.ONE_OR_MORE
    **kwargs:
        Same as argparse.ArgumentParser.add_argument
    """
    return _Parser.singleton_instance.parse(*args, is_flag=is_flag, **kwargs)


@_auto_construct_parser
def get_group(name=None, description=None) -> "_Group":
    # noinspection PyUnresolvedReferences
    """
        Returns group which can be a context manager to allocate groups.
        If same name is specified, same instance is returned even from different modules.

        Examples
        --------
        >>> with get_group('sample', 'This is sample.'):
        >>>     foo = clappy.parse("--foo")  # This foo belongs 'sample' group on output of help.
        >>> bar = clappy.parse("--bar")  # This DOESN'T belong to 'sample' group.

        Parameters
        ----------
        name: str
            Name of group to get or create newly.
        description: str
            Instruction about the group.
        """
    return _Group.get(name=name, description=description)


def clear_parser():
    """Reset parser so that you can recreate new parser with different args."""
    _Parser.singleton_instance = None


@functools.lru_cache()
def get_parser(*args, generates_help=True, auto_grouping=True, **kwargs):
    """
    Returns already existing parser, or newly constructed one.
    The parser is usually used as context manager for auto help generation.

    e.g.
    with get_parser():
        # Usage for help option is automatically created for all command line arguments parsed in this block
        foo = clappy.parse("--foo", help="description")

    Consider to use auto_help_generator function if the purpose of calling this func is just for auto help generation.
    It's an alias of this function for better readability.
    "with get_parser() as auto_help_generator:" also looks good.

    You can just construct parser with some specific arguments without auto help generation.

    e.g.
    get_parser(default=2)
    bar = clappy.parser("--bar")  # No help text for this.

    Same arguments as argparse.ArgumentParser are available.
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser

    Additional arguments are

    generates_help: bool
        Represents if clappy will create help or not. If you want to create by your own, give False to deter warning.
    auto_grouping: bool
        Represents if clappy will automatically allocate command line argument in a group.
        In default, clappy groups when the argument is set not in __main__ module and has not specified group.
        The name of group automatically allocated becomes the name of module.
    """

    if _Parser.singleton_instance is None:
        _Parser.singleton_instance = _Parser.get_instance(
            *args, generates_help=generates_help, auto_grouping=auto_grouping, **kwargs
        )
    else:
        if args or kwargs:
            logger.warning(f"Instanced parser already exists, but you ran {get_parser.__name__} with {args, kwargs}."
                           f"This func returned the existing parser, and your {args} and {kwargs} were ignored.")
    return _Parser.singleton_instance


def auto_help_generator(auto_grouping=True):
    """Alias of get_parser for readable code.
    Consider to use this when you call get_parser without giving arguments and the purpose is only for help generation.
    It makes readers understand easier the purpose."""
    return get_parser(auto_grouping=auto_grouping)


_Nargs = namedtuple("Nargs", "OPTIONAL ZERO_OR_MORE ONE_OR_MORE")
nargs = _Nargs(OPTIONAL=argparse.OPTIONAL, ZERO_OR_MORE=argparse.ZERO_OR_MORE, ONE_OR_MORE=argparse.ONE_OR_MORE)

_actions = (
    'STORE',
    'STORE_CONST',
    'STORE_TRUE',
    'STORE_FALSE',
    'APPEND',
    'APPEND_CONST',
    'COUNT',
    'HELP',
    'VERSION',
    'PARSERS',
    'EXTEND')
_Action = namedtuple("_Action", _actions)
action = _Action(**{name: name.lower() for name in _actions})


# noinspection PyUnresolvedReferences,PyProtectedMember
class _Group(argparse._ArgumentGroup):
    active_groups: List["_Group"] = []
    title_group_dict: Dict = {}  # Dict[str:"_GroupForWith"]

    def __enter__(self):
        _Group.active_groups.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _Group.active_groups.remove(self)

    @classmethod
    def _get_active_group(cls):
        if cls.active_groups:
            return cls.active_groups[-1]
        else:
            return None

    @classmethod
    def get(cls, name=None, description=None):
        parser = _Parser.singleton_instance
        if name is None and parser.auto_grouping:
            if not utils.is_called_from_main():
                name = utils.get_caller_name(4)

        cached_group = cls.title_group_dict.get(name, None)

        if cached_group is not None:
            return cached_group

        group = parser.add_argument_group(name, description)
        cls.title_group_dict[name] = group
        return group


def set_name_of_main_script(filename: str):
    """filename should be without .py."""
    utils.filename_of_main = filename


def set_args_getting_parsed(args: Union[List[str], str]):
    """Clappy will parse not commandline arguments but given 'args' here."""
    if isinstance(args, str):
        args = args.split(" ")
    _Parser._default_args_getting_parsed = args
    active_parser = _Parser.singleton_instance
    if active_parser:
        active_parser._args_getting_parsed = args
        active_parser._last_namespace = None


def set_return_value_on_help(val):
    _Parser.default_returns_on_help = val
    if _Parser.singleton_instance:
        _Parser.singleton_instance.return_on_help = val


# noinspection PyUnresolvedReferences,PyProtectedMember
class _SubCommand(_Parser):
    name_of_subcommand_group = "commands"
    active_instance = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._invoked = None
        if self._adds_help:
            self._add_argument("-h", "--help", action="help", help="show this help message and exit")

    def parse(self, *args, is_flag=False, **kwargs):
        main_parser = _Parser.singleton_instance
        action = _Parser.add_argument(self, *args, is_flag=is_flag, **kwargs)
        namespace, _ = main_parser.parse_known_args()
        return getattr(namespace, action.dest)

    def _add_argument(self, *args, **kwargs):
        return argparse.ArgumentParser.add_argument(self, *args, **kwargs)

    def __bool__(self):
        return self.invoked

    @property
    def invoked(self):
        if self._invoked is None:
            self._invoked = False
            try:
                namespace, _ = _Parser.singleton_instance.parse_known_args()
            except self.SubCommandNotFound:
                pass
            else:
                if namespace._invoked_command == self._defaults["_invoked_command"]:
                    self._invoked = True
        return self._invoked

    class MultipleActivated(Exception):
        pass

    def __enter__(self):
        if self.active_instance:
            raise self.MultipleActivated("Already in with block of another subcommand.")
        self.__class__.active_instance = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True

    @classmethod
    def set_name_of_subcommand_group(cls, name: str):
        cls.name_of_subcommand_group = name

    # noinspection PyShadowingBuiltins
    @classmethod
    @_auto_construct_parser
    def create(cls, name, *, help=None, **kwargs):
        active_parser = _Parser.singleton_instance
        if not active_parser._subparsers_list:
            active_parser.add_subparsers(title=cls.name_of_subcommand_group)
        subcommand = active_parser._subparsers_action.add_parser(name, help=help, **kwargs)
        subcommand.set_defaults(_invoked_command=name)

        active_parser._subparsers_list.append(subcommand)
        return subcommand


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
@functools.singledispatch
def subcommand(arg):
    raise NotImplementedError

#
# @subcommand.register(types.FunctionType)
# def _(arg: types.FunctionType, **kwargs):
#     """
#     Decorated func becomes subcommand.
#
#     Examples
#     --------
#
#     >>> # example.py
#     >>> @clappy.subcommand
#     >>> def sub(posi, *, kw1, kw2="default"):
#     >>>     '''help example''' # should use "
#     >>>     print(posi, kw1, kw2)
#
#     >>> $ python example.py sub positional --kw1 first_opt
#     positional, first_opt, default
#
#     >>> $ python above_module.py -h
#     # make example of help
#     """
#
#     import inspect
#
#     func = arg
#     subcommand = _SubCommand.create(func.__name__, help=func.__doc__, **kwargs)
#     subcommand.func = func
#     if not subcommand.invoked:
#         return subcommand
#
#     empty = inspect.Signature.empty
#     signature = inspect.signature(subcommand)
#
#     names = []
#     has_variable_length_kwargs = False
#     for name, param in signature.parameters.items():
#         names.append(name)
#         if param.kind == param.VAR_KEYWORD:
#             has_variable_length_kwargs = True
#             continue
#         param_flag, default, _type, action, required = name, None, None, None, None
#         if param.kind == param.KEYWORD_ONLY:
#             param_flag = f"--{param_flag}"
#         if param.annotation is not empty:
#             if param.annotation == bool:
#                 action = action.STORE_TRUE
#             else:
#                 _type = param.annotation
#         if param.default is not empty:
#             default = param.default
#         elif param.kind == param.KEYWORD_ONLY:
#             required = True
#         if param.kind == param.VAR_POSITIONAL:
#             action = action.APPEND
#         subcommand.add_argument(param_flag, action=action, default=default, type=_type, required=required)
#     args, unrecognized_args = subcommand.parse_known_args()
#     if unrecognized_args and len(unrecognized_args) > 1 and has_variable_length_kwargs:
#         _kwargs = {}
#         for option_flag, value in zip(unrecognized_args[0::2], unrecognized_args[1::2]):
#             if not option_flag.startswith(subcommand.prefix):  # prefix check
#                 raise TypeError(f"Unexpected argument:'{option_flag}' was given.")
#             _kwargs[option_flag.lstrip(subcommand.prefix)] = value
#     _args, _kwargs = args  # なんとかしてここつくる boundとか
#     func(*_args, **_kwargs)
#     exit()


@subcommand.register(str)
def _(arg: str, *, help=None, **kwargs):
    """
        Examples
        --------
        >>> sub1 = clappy.subcommand("sub1")
        >>> if sub1.invoked:
        >>>     foo = sub1.parse("--foo")
        >>>     print(f"foo value: {foo}")
        >>>
        >>> sub2 = clappy.subcommand("sub2", help="description here")
        >>> if sub2:
        >>>     bar = sub2.parse("--bar")
        >>>     print("Here is not reachable in this example")

        >>> $ python following_example.py sub1 --foo value
        foo value: value

        Parameters
        ----------
        name: str
            Name of subcommand.
        help: str
            Description of subcommand for help message.
        **kwargs:
            Same arguments as argparse.ArgumentParser are available as keyword argument.
            List: https://docs.python.org/3/library/argparse.html#argumentparser-objects

        Returns
        -------
        subcommand: _SubCommand
            Instance of _SubCommand class. bool() represents if the subcommand is invoked or not.
        """
    return _SubCommand.create(arg, help=help, **kwargs)
