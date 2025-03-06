import os
import time
import requests


def get_file(url: str, cache_path: str, ttl: int = 3600) -> str:
    """
    Retrieve a file from either a local cache or a remote URL.

    Parameters
    ----------
    url : str
        The URL from which to download the file if needed.
    cache_path : str
        Path on the local filesystem to store (and check for) the cached file.
    ttl : int, optional
        Time-to-live (in seconds). If the file in the cache is older than this,
        it is re-downloaded. The default is 3600 (1 hour).

    Returns
    -------
    str
        The path to the locally cached file.

    Raises
    ------
    requests.HTTPError
        If the request returned an unsuccessful status code (4xx or 5xx).
    """
    file_needs_download = True

    if os.path.exists(cache_path):
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        file_age = time.time() - os.path.getmtime(cache_path)
        if file_age < ttl:
            file_needs_download = False

    if file_needs_download:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(cache_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    return cache_path
