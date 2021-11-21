from time import sleep

import logbook
from iologger import iologger

from requests_handler import RequestsHandler, DatabaseHandler


def test_iologger_database():
    @iologger()
    def my_func(string: str, integer: int) -> str:
        sleep(1.25)
        return f"my string was {string} and my integer was {integer}."

    database_handler = DatabaseHandler(f"postgresql://data_loads_user:HILLS!@localhost:5433/data_loads",
                                       process_id=12,
                                       level='DEBUG')
    database_handler.push_application()
    my_func("Abraham", integer=15)
    my_func("Isaac", 0)
    database_handler.pop_application()


def test_handler():
    logger = logbook.Logger("TestLogger")
    requests_handler = RequestsHandler(
        "https://autosweet-data.com/api/v1/logs",
        auth=('admin', 'aut0sw33t'))

    requests_handler.push_application()
    logger.debug("A debug message")
    logger.critical("A critical message!")
    requests_handler.pop_application()


def test_iologger():
    @iologger()
    def my_func(string: str, integer: int) -> str:
        return f"my string was {string} and my integer was {integer}."

    requests_handler = RequestsHandler(
        "https://autosweet-data.com/api/v1/logs",
        auth=('admin', 'aut0sw33t'),
        logger='TestLogger'
    )

    requests_handler.push_application()
    my_func("Abraham", integer=15)
    my_func("Isaac", 0)
    requests_handler.pop_application()


def main():
    pass


if __name__ == '__main__':
    test_iologger_database()
