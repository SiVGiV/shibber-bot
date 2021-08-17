import enum
from colorama import init, Fore
from datetime import date, time


class LogType(enum.IntEnum):
    STANDARD = 0
    EVENT = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4


class Loggable:
    def __init__(self, log_path: str, colors: list, log_to: list, **kwargs):
        """
        Creates a new instance of a Loggable class
        :param log_path: File path (str) to log to
        :param colors: An enum indexed list (LogType) of colorama colors
        :param log_to: An enum indexed list (LogType) of (bool, bool) tuples representing (console,file)
        """
        self.log_path = log_path
        self.colors = colors
        self.log_to = log_to
        if kwargs["print_wrapper"]:
            self.print_wrapper = kwargs["print_wrapper"]
        else:
            self.print_wrapper = lambda st: st
        if kwargs["file_wrapper"]:
            self.file_wrapper = kwargs["file_wrapper"]
        else:
            self.file_wrapper = lambda st: st

    def log(self, log_entry: str, log_type: LogType = 0) -> None:
        """

        :param log_entry: String to log
        :param log_type: Type of log item to print
        :return:
        """
        if self.log_to[log_type]["console"]:
            print(self.colors[log_type] + self.print_wrapper(log_entry, log_type))
        if self.log_to[log_type]["file"]:
            with open(self.log_path, "a+") as f:
                f.write(self.file_wrapper(log_entry, log_type))

    @property
    def log_path(self):
        return self.__log_path

    @log_path.setter
    def log_path(self, lp: str):
        self.__log_path = lp

    @property
    def colors(self):
        return self.__colors

    @colors.setter
    def colors(self, clrs: list):
        self.__colors = clrs

    @property
    def log_to(self):
        return self.__log_to

    @log_to.setter
    def log_to(self, ld: list):
        self.__log_to = ld

    @property
    def print_wrapper(self):
        return self.__print_wrapper

    @print_wrapper.setter
    def print_wrapper(self, pw):
        self.__print_wrapper = pw

    @property
    def file_wrapper(self):
        return self.__file_wrapper

    @file_wrapper.setter
    def file_wrapper(self, fw):
        self.__file_wrapper = fw
