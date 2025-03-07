import os
import time
import pytest
import responses
import requests

from spec0.cacheddownload import *

@responses.activate
def test_get_file_file_does_not_exist(tmp_path):
    # If the file doesn't exist, should we download it.
    cache_file = tmp_path / "test_file.txt"
    assert not cache_file.exists()

    responses.add(
        responses.GET,
        "https://example.com/data.csv",
        body="test data",
        status=200,
        content_type="text/plain"
    )

    returned_path = get_file(
        url="https://example.com/data.csv",
        cache_path=str(cache_file),
        ttl=3600
    )

    assert returned_path == str(cache_file)
    assert cache_file.exists()
    with open(cache_file, "r") as f:
        content = f.read()
    assert content == "test data"
    assert len(responses.calls) == 1


@responses.activate
def test_file_exists_but_older(tmp_path):
    """
    Test that if the file exists but is older than the TTL, we download it again.
    """
    # Arrange
    cache_file = tmp_path / "test_file.txt"
    with open(cache_file, "w") as f:
        f.write("old data")

    ttl = 3600
    # Force the file's modification time to be 'old'
    old_mtime = time.time() - (2 * ttl)
    os.utime(cache_file, (old_mtime, old_mtime))

    responses.add(
        responses.GET,
        "https://example.com/data.csv",
        body="new data",
        status=200,
        content_type="text/plain"
    )

    # Act
    returned_path = get_file(
        url="https://example.com/data.csv",
        cache_path=str(cache_file),
        ttl=ttl
    )

    # Assert
    assert returned_path == str(cache_file), "The function should return the cache file path."
    with open(cache_file, "r") as f:
        content = f.read()
    assert content == "new data", "File should have been overwritten with new data."
    assert len(responses.calls) == 1, "One request should have been made to refresh the file."


@responses.activate
def test_file_exists_and_fresh(tmp_path):
    """
    Test that if the file exists and is younger than the TTL, no download occurs.
    """
    # Arrange
    cache_file = tmp_path / "test_file.txt"
    with open(cache_file, "w") as f:
        f.write("fresh data")

    ttl = 3600
    fresh_mtime = time.time() - (ttl / 2)
    os.utime(cache_file, (fresh_mtime, fresh_mtime))

    # We do not add any responses here because we expect no request.

    # Act
    returned_path = get_file(
        url="https://example.com/data.csv",
        cache_path=str(cache_file),
        ttl=ttl
    )

    # Assert
    assert returned_path == str(cache_file), "The function should return the cache file path."
    with open(cache_file, "r") as f:
        content = f.read()
    assert content == "fresh data", "File should remain unchanged."
    assert len(responses.calls) == 0, "No request should be sent for a fresh (not expired) cache."


@pytest.mark.parametrize("status_code", [404, 500])
@responses.activate
def test_http_error(status_code, tmp_path):
    """
    Test that if the server returns an HTTP error, a requests.HTTPError is raised.
    """
    # Arrange
    cache_file = tmp_path / "test_file.txt"

    responses.add(
        responses.GET,
        "https://example.com/data.csv",
        body=f"Error {status_code}",
        status=status_code,
        content_type="text/plain"
    )

    # Act & Assert
    with pytest.raises(requests.HTTPError):
        get_file(url="https://example.com/data.csv", cache_path=str(cache_file), ttl=3600)

    assert len(responses.calls) == 1, "Exactly one request call should have been made."
