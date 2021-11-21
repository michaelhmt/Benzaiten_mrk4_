"""
Handler for logging records to a Restful API.

:param api_url: URL to post records to.
:param auth: Credentials in format (username, password).
:param level: Logging level (DEBUG, INFO, ERROR, WARNING, CRITICAL).
:param filter: Minimum record level to emit.
:param bubble: Should bubble.
"""

import json

import arrow
import requests
import records
from logbook import LogRecord, Handler

__version__ = "0.0.8"


class RequestsHandler(Handler):
    """
    Handler for logging records to a Restful API.
    
    :param logger: str to use for the logger name.
    :param api_url: URL to post records to.
    :param auth: Credentials in format (username, password).
    :param level: Logging level (DEBUG, INFO, ERROR, WARNING, CRITICAL).
    :param filter: Minimum record level to emit.
    :param bubble: Should bubble.
    """

    def __init__(self, api_url: str, auth: tuple, level: str = 'INFO',
                 logger: str = None, filter: str = None, bubble: bool = False):
        Handler.__init__(self, level, filter, bubble)
        self.api_url = api_url
        self.auth = auth
        self.logger = logger
        self.log_record_fields = [
            "logger",
            "channel",
            "level",
            "lineno",
            "filename",
            "module",
            "func_name",
            "message",
            "log_time"
        ]

    def emit(self, record: LogRecord):
        log_record = record.to_dict()
        log_record["log_time"] = arrow.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S.%f")
        log_record['logger'] = self.logger
        log_record = {k: v for k, v in log_record.items() if
                      k in self.log_record_fields}

        try:
            requests.post(url=self.api_url, data=log_record,
                          auth=self.auth)
        except Exception as e:
            print(e)


class DatabaseHandler(Handler):
    """
    Handler for logging records to a database.

    :param connection_string: database connection string.
    :param level: Logging level (DEBUG, INFO, ERROR, WARNING, CRITICAL).
    :param filter: Minimum record level to emit.
    :param bubble: Should bubble.
    """

    def __init__(self, connection_string: str, process_id: int,
                 level: str = 'INFO', filter: str = None, bubble: bool = False):
        Handler.__init__(self, level, filter, bubble)
        self.connection_string = connection_string
        self.process_id = process_id
        self.log_record_fields = [
            "channel",
            "level",
            "lineno",
            "filename",
            "module",
            "func_name",
            "message",
            "log_time"
        ]

        self.db = records.Database(self.connection_string)

    def emit(self, record: LogRecord):
        log_record = record.to_dict()
        log_record["log_time"] = arrow.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S.%f")
        log_record = {k: v for k, v in log_record.items() if
                      k in self.log_record_fields}
        log_record['message'] = log_record.get("message").replace("'", '"')
        try:
            self.db.query("INSERT INTO data_processors.logs"
                          "(process_id, channel, level, lineno, filename, "
                          "module, func_name, message, log_time)"
                          f"VALUES({self.process_id}, "
                          f"'{log_record.get('channel')}',"
                          f"{log_record.get('level')},"
                          f"{log_record.get('lineno')},"
                          f"'{log_record.get('filename')}',"
                          f"'{log_record.get('module')}',"
                          f"'{log_record.get('func_name')}',"
                          f"'{log_record.get('message')}',"
                          f"'{log_record.get('log_time')}')")
        except Exception as e:
            print(e)


def main():
    pass


if __name__ == '__main__':
    main()
