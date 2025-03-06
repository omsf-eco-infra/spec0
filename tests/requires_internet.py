import socket
import functools
import pytest

_HAS_INTERNET = None


def _check_internet():
    """Checks internet connectivity exactly once per session run."""
    global _HAS_INTERNET
    if _HAS_INTERNET is None:
        try:
            socket.create_connection(("www.google.com", 80), timeout=2)
            _HAS_INTERNET = True
        except OSError:
            _HAS_INTERNET = False
    return _HAS_INTERNET


def requires_internet(test_func):
    """
    Decorator: Skip test if there is no internet connection.
    """

    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        if not _check_internet():
            pytest.skip("Skipping test because there is no internet connection.")
        return test_func(*args, **kwargs)

    return wrapper
