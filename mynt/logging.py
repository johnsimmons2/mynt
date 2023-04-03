from datetime import datetime
from abc import abstractmethod
from enum import Enum

class Log:
    def __init__(self, lvl, msg, ref = None, err = None, time = None):
        self._timestamp = datetime.now() if time is None else time
        self._lvl = lvl
        self._msg = msg
        self._ref = ref
        self._err = err
        self._logstr = self._get_timeless_log()

    def __str__(self):
        result = self._get_timestamp_format()
        result = result + self._get_timeless_log()
        return result

    def _get_timestamp_format(self):
        return '[' + str(self._timestamp) + ']: '

    def _get_timeless_log(self):
        result = '[' + str(self._lvl) + '] - '
        result = result + str(self._msg)
        if self._ref is not None:
            result = result + "\n\t"
            result = result + str(self._ref)
        if self._err is not None:
            if isinstance(self._err, Exception):
                result = result + "\n\t"
                result = result + str(self._err.args[0])
        return result

class LogLevel(Enum):
    DEBUG = 0,
    WARN = 1,
    ERROR = 2,
    SUCCESS = 3

class LogHandler:
    @abstractmethod
    def handle(self, log:Log):
        pass

class Logger:
    _handler = None
    _handler_validated = False

    def _log(log:Log):
        if Logger._handler_validated or Logger._handler is not None:
            # If there is a log handler set up.
            Logger._handler_validated = True
            handler = Logger._handler
            handler.handle(log)
        else:
            # Basic control is to print stringified log.
            print(str(log))

    def log(lvl:LogLevel, msg:str, ref:any = None, err:any = None, time:datetime = None):
        if str(msg).find('\n'):
            msgs = str(msg).split('\n')
            for x in msgs:
                Logger._log(Log(lvl, x, ref, err, time))
        else:
            Logger._log(Log(lvl, msg, ref, err, time))
        
    def debug(msg:str, ref:any = None, err:any = None, time:datetime = None):
        Logger.log(LogLevel.DEBUG, msg, ref, err, time)
    
    def warn(msg:str, ref:any = None, err:any = None, time:datetime = None):
        Logger.log(LogLevel.WARN, msg, ref, err, time)

    def error(msg:str, ref:any = None, err:any = None, time:datetime = None):
        Logger.log(LogLevel.ERROR, msg, ref, err, time)
    
    def success(msg:str, ref:any = None, err:any = None, time:datetime = None):
        Logger.log(LogLevel.SUCCESS, msg, ref, err, time)

    def config_set_handler(handler):
        if isinstance(type(handler), type(LogHandler)):
            Logger._handler = handler
            Logger.debug('Setup log handler - ' + str(type(handler)))
        else:
            raise TypeError('Cannot set log handler to invalid log handler object type')

class FormattedLogHandler(LogHandler):
    class Colors:
        # NON RESERVED
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        # RESERVED
        WARNING = '\033[93m'
        ERROR = '\033[91m'
        ENDC = '\033[0m'
        # MISC
        HEADER = '\033[95m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    _color_dates = False
    _color_logs = True
    _default_timestamp_color = Colors.BOLD

    def handle(self, log:Log):
        log_col = ''
        ts_col = FormattedLogHandler._default_timestamp_color if FormattedLogHandler._color_dates else ''
        if FormattedLogHandler._color_logs:
            match log._lvl:
                case LogLevel.DEBUG:
                    log_col = FormattedLogHandler.Colors.BLUE
                case LogLevel.WARN:
                    log_col = FormattedLogHandler.Colors.WARNING
                    ts_col = FormattedLogHandler.Colors.WARNING
                case LogLevel.ERROR:
                    log_col = FormattedLogHandler.Colors.ERROR \
                        + FormattedLogHandler.Colors.UNDERLINE
                    ts_col = FormattedLogHandler.Colors.ERROR  \
                        + FormattedLogHandler.Colors.UNDERLINE
                case LogLevel.SUCCESS:
                    log_col = FormattedLogHandler.Colors.GREEN
                    ts_col = FormattedLogHandler.Colors.GREEN
        message = FormattedLogHandler._apply_color(log._get_timeless_log(), log_col)
        timestamp = FormattedLogHandler._apply_color(log._get_timestamp_format(), ts_col)
        print(timestamp + message, end="\n" if message.rfind("\r") == -1 else "")

    def config_set_color_dates(self, val):
        FormattedLogHandler._color_dates = val

    def config_set_color_logs(self, val):
        FormattedLogHandler._color_logs = val

    def _apply_color(text, color):
        return str(color) + str(text) + FormattedLogHandler.Colors.ENDC
    