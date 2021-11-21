from io import StringIO

import pytest
from hypothesis import given
from hypothesis.strategies import integers, permutations, text
from logbook import StreamHandler

from iologger import *


@iologger
def logged_function(a_string: str, an_int: int) -> str:
    """
    Returns a str made from static text, a passed str, and a passed int.

    :param a_string: a str to be used in the returned string
    :param an_int: an int to be used in the returned string
    :return: a str which includes both a_string and an_int values
    """

    return "Your str was '{}' and your int was '{}'.".format(a_string, an_int)


@iologger
def logged_exception_graceful() -> None:
    """
    This function just raises an exception.

    :return: None
    """

    raise PermissionError


@iologger(catch_exceptions=False)
def logged_exception_ungraceful() -> None:
    """
    This function just raises an exception.

    :return: None
    """

    raise PermissionError


@pytest.fixture()
def setup_logging():
    logger = Logger('test_logger')
    return logger


@given(t_str=text(alphabet='azbef'), t_int=integers())
def test_iologger_runs(t_str, t_int):
    assert logged_function(a_string=t_str, an_int=t_int)


@given(t_str=permutations('azbef'), t_int=integers())
@pytest.mark.usefixtures('setup_logging')
def test_args_logging(t_str, t_int):
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile)
        stdout_handler.push_application()

        t_str = ''.join(t_str)
        logged_function(a_string=t_str, an_int=t_int)

        assert t_str in logfile.getvalue()
        assert str(t_int) in logfile.getvalue()

        stdout_handler.pop_application()


@given(t_str=text(alphabet='azbef'), t_int=integers())
@pytest.mark.usefixtures('setup_logging')
def test_iologger_debug_level(t_str, t_int):
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile)
        stdout_handler.push_application()

        t_str = ''.join(t_str)
        logged_function(a_string=t_str, an_int=t_int)

        # assert "Starting" in logfile.getvalue()
        # assert "args/kwargs" in logfile.getvalue()
        # assert "Finished" in logfile.getvalue()
        assert logfile.getvalue()
        assert len(logfile.getvalue().splitlines()) == 1

        stdout_handler.pop_application()


@given(t_str=text(alphabet='azbef'), t_int=integers())
@pytest.mark.usefixtures('setup_logging')
def test_iologger_info_level(t_str, t_int):
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile, level="INFO")
        stdout_handler.push_application()

        t_str = ''.join(t_str)
        logged_function(a_string=t_str, an_int=t_int)

        # assert "Starting" not in logfile.getvalue()
        # assert "args/kwargs" in logfile.getvalue()
        # assert "Finished" not in logfile.getvalue()
        assert logfile.getvalue()
        assert len(logfile.getvalue().splitlines()) == 1

        stdout_handler.pop_application()


@given(t_str=text(alphabet='azbef'), t_int=integers())
@pytest.mark.usefixtures('setup_logging')
def test_iologger_notice_level(t_str, t_int):
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile, level="NOTICE")
        stdout_handler.push_application()

        t_str = ''.join(t_str)
        logged_function(a_string=t_str, an_int=t_int)

        # assert "Starting" not in logfile.getvalue()
        # assert "args/kwargs" not in logfile.getvalue()
        # assert "Finished" not in logfile.getvalue()
        assert logfile.getvalue() == ""

        stdout_handler.pop_application()


@given(t_str=text(alphabet='azbef'), t_int=integers())
@pytest.mark.usefixtures('setup_logging')
def test_iologger_notice_level(t_str, t_int):
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile, level="NOTICE")
        stdout_handler.push_application()

        t_str = ''.join(t_str)
        logged_function(a_string=t_str, an_int=t_int)

        # assert "Starting" not in logfile.getvalue()
        # assert "args/kwargs" not in logfile.getvalue()
        # assert "Finished" not in logfile.getvalue()
        # assert logfile.getvalue() == ""

        stdout_handler.pop_application()


# @pytest.mark.usefixtures('setup_logging')
# def test_iologger_exception_catching_graceful():
#     logged_exception_graceful()
#
#
# @pytest.mark.usefixtures('setup_logging')
# def test_iologger_exception_catching_ungraceful():
#     with pytest.raises(FunctionExecutionError):
#         logged_exception_ungraceful()


@pytest.mark.usefixtures('setup_logging')
def test_iologger_exception_catching_logging():
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile)
        stdout_handler.push_application()

        logged_exception_graceful()

        # assert "Starting" in logfile.getvalue()
        # assert "args/kwargs" in logfile.getvalue()
        # assert "PermissionError" in logfile.getvalue()

        stdout_handler.pop_application()


@given(t_str=text(alphabet='azbef'), t_int=integers())
@pytest.mark.usefixtures('setup_logging')
def test_iologger_exception_catching_graceful_logging(t_str, t_int):
    with StringIO() as logfile:
        stdout_handler = StreamHandler(logfile)
        stdout_handler.push_application()

        logged_exception_graceful()
        t_str = ''.join(t_str)
        logged_function(a_string=t_str, an_int=t_int)

        # assert "Starting" in logfile.getvalue()
        # assert "args/kwargs" in logfile.getvalue()
        # assert "PermissionError" in logfile.getvalue()
        # assert "Finished" in logfile.getvalue()

        stdout_handler.pop_application()


if __name__ == "__main__":
    pytest.main(['-v'])
