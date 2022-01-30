__copyright__ = 'Copyright (C) 2021 Toshiyuki Yokoyama'
__version__ = '1.0.5'
__license__ = 'MIT'
__author__ = 'Toshiyuki Yokoyama'
__author_email__ = 'yokoyamacode@gmail.com'
__url__ = 'https://github.com/yoko72/clappy'

from .main import *
from logging import getLogger

logger = getLogger(__name__)

__all__ = ["parse", "get_parser", "auto_help_generator", "clear_parser",
           "get_group", "subcommand",
           "action", "nargs", "SUPPRESS", "ReturnOnHelp",
           "set_args_getting_parsed", "set_name_of_main_script"]
