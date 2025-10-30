import logging
from datetime import datetime
from flask import current_app
import os


class Logger:
    """
    Custom logger class
    """
    logger = None
    logger_folder = None
    logger_handler = None
    logger_level = None
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s', '%d-%m-%Y %H:%M:%S')

    def __init__(self, logger_type):

        today = datetime.today().strftime("%d-%m-%Y")
        root_dir = os.path.dirname(current_app.instance_path)
        self.logger = logging.getLogger(logger_type)

        if logger_type == 'INFO_LOGGER':
            self.logger_level = logging.INFO
            self.logger.setLevel(self.logger_level)
            self.logger_folder = 'app_info_logs'
            self.logger_handler = logging.FileHandler(
                f'{root_dir}/logs/{self.logger_folder}/{today}_info.log')
            self.logger_handler.setFormatter(self.formatter)
        else:
            # Default logger is error logger.
            self.logger_level = logging.ERROR
            self.logger.setLevel(self.logger_level)
            self.logger_folder = 'app_errors'
            self.logger_handler = logging.FileHandler(
                f'{root_dir}/logs/{self.logger_folder}/{today}_errors.log')

        self.logger_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.logger_handler)

    def get_logger(self):
        return self.logger


def error_logger():
    """
    Function to get an error logger, object of Logger class.
    @return: custom logger
    """
    logger = Logger('ERROR_LOGGER')
    return logger.get_logger()


def info_logger():
    """
   Function to get a info logger, an object of Logger class.
   @return: custom logger
   """
    logger = Logger('INFO_LOGGER')
    return logger.get_logger()
