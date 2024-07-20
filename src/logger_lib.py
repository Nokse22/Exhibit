import logging

class CustomFormatter(logging.Formatter):

    log_end = ": %(message)s"
    log_start = "%(asctime)s (%(filename)s:%(lineno)d) "
    level_name = "\x1b[31;20m%(levelname)s\x1b[0m"
    time_format = "%H:%M:%S"

    FORMATS = {
        logging.DEBUG: log_start + "\x1b[34;1m%(levelname)s\x1b[0m" + log_end,
        logging.INFO: log_start + "\x1b[32;1m%(levelname)s\x1b[0m" + log_end,
        logging.WARNING: log_start + "\x1b[33;1m%(levelname)s\x1b[0m" + log_end,
        logging.ERROR: log_start + "\x1b[31;1m%(levelname)s\x1b[0m" + log_end,
        logging.CRITICAL: log_start + "\x1b[31;1m%(levelname)s\x1b[0m" + log_end
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.time_format)
        return formatter.format(record)

def init():
    global logger

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    ch.setFormatter(CustomFormatter())

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)
