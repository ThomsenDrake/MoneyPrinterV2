import json
import logging
import os
import platform
from typing import List

from config import ROOT_DIR

# Import appropriate file locking module based on platform
if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl


class FileLock:
    """
    Cross-platform file locking context manager to prevent race conditions.
    """

    def __init__(self, file_handle):
        self.file_handle = file_handle

    def __enter__(self):
        """Acquire exclusive lock on file."""
        try:
            if platform.system() == "Windows":
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_EX)
        except Exception as e:
            logging.error(f"Failed to acquire file lock: {str(e)}")
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock on file."""
        try:
            if platform.system() == "Windows":
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logging.debug(f"Error releasing file lock: {str(e)}")


def _atomic_read_json(file_path: str, default: dict) -> dict:
    """
    Atomically read JSON file with file locking.

    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is empty

    Returns:
        Parsed JSON data or default
    """
    if not os.path.exists(file_path):
        return default

    try:
        with open(file_path, "r") as file:
            with FileLock(file):
                content = file.read()
                if not content:
                    return default
                return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error reading cache file {file_path}: {str(e)}")
        return default


def _atomic_write_json(file_path: str, data: dict) -> None:
    """
    Atomically write JSON file with file locking.

    Args:
        file_path: Path to JSON file
        data: Data to write

    Returns:
        None
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as file:
            with FileLock(file):
                json.dump(data, file, indent=4)
    except IOError as e:
        logging.error(f"Error writing cache file {file_path}: {str(e)}")
        raise


def _atomic_update_json(file_path: str, update_fn, default: dict) -> None:
    """
    Atomically update JSON file with file locking.

    Args:
        file_path: Path to JSON file
        update_fn: Function that takes current data and returns updated data
        default: Default value if file doesn't exist

    Returns:
        None
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open file in read-write mode, create if doesn't exist
        with open(file_path, "a+") as file:
            with FileLock(file):
                # Move to beginning to read
                file.seek(0)
                content = file.read()

                # Parse existing data or use default
                if content:
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = default
                else:
                    data = default

                # Apply update function
                updated_data = update_fn(data)

                # Write updated data
                file.seek(0)
                file.truncate()
                json.dump(updated_data, file, indent=4)
    except IOError as e:
        logging.error(f"Error updating cache file {file_path}: {str(e)}")
        raise


def get_cache_path() -> str:
    """
    Gets the path to the cache file.

    Returns:
        path (str): The path to the cache folder
    """
    return os.path.join(ROOT_DIR, ".mp")


def get_afm_cache_path() -> str:
    """
    Gets the path to the Affiliate Marketing cache file.

    Returns:
        path (str): The path to the AFM cache folder
    """
    return os.path.join(get_cache_path(), "afm.json")


def get_twitter_cache_path() -> str:
    """
    Gets the path to the Twitter cache file.

    Returns:
        path (str): The path to the Twitter cache folder
    """
    return os.path.join(get_cache_path(), "twitter.json")


def get_youtube_cache_path() -> str:
    """
    Gets the path to the YouTube cache file.

    Returns:
        path (str): The path to the YouTube cache folder
    """
    return os.path.join(get_cache_path(), "youtube.json")


def get_accounts(provider: str) -> List[dict]:
    """
    Gets the accounts from the cache.

    Args:
        provider (str): The provider to get the accounts for

    Returns:
        account (List[dict]): The accounts
    """
    cache_path = ""

    if provider == "twitter":
        cache_path = get_twitter_cache_path()
    elif provider == "youtube":
        cache_path = get_youtube_cache_path()
    else:
        logging.warning(f"Unknown provider: {provider}")
        return []

    default_data = {"accounts": []}
    data = _atomic_read_json(cache_path, default_data)

    return data.get("accounts", [])


def add_account(provider: str, account: dict) -> None:
    """
    Adds an account to the cache.

    Args:
        provider (str): The provider (twitter or youtube)
        account (dict): The account to add

    Returns:
        None
    """
    cache_path = None

    if provider == "twitter":
        cache_path = get_twitter_cache_path()
    elif provider == "youtube":
        cache_path = get_youtube_cache_path()
    else:
        logging.error(f"Unknown provider: {provider}")
        return

    def update_fn(data):
        accounts = data.get("accounts", [])
        accounts.append(account)
        return {"accounts": accounts}

    _atomic_update_json(cache_path, update_fn, {"accounts": []})


def remove_account(provider: str, account_id: str) -> None:
    """
    Removes an account from the cache.

    Args:
        provider (str): The provider (twitter or youtube)
        account_id (str): The ID of the account to remove

    Returns:
        None
    """
    cache_path = None

    if provider == "twitter":
        cache_path = get_twitter_cache_path()
    elif provider == "youtube":
        cache_path = get_youtube_cache_path()
    else:
        logging.error(f"Unknown provider: {provider}")
        return

    def update_fn(data):
        accounts = data.get("accounts", [])
        accounts = [account for account in accounts if account.get("id") != account_id]
        return {"accounts": accounts}

    _atomic_update_json(cache_path, update_fn, {"accounts": []})


def get_products() -> List[dict]:
    """
    Gets the products from the cache.

    Returns:
        products (List[dict]): The products
    """
    default_data = {"products": []}
    data = _atomic_read_json(get_afm_cache_path(), default_data)
    return data.get("products", [])


def add_product(product: dict) -> None:
    """
    Adds a product to the cache.

    Args:
        product (dict): The product to add

    Returns:
        None
    """

    def update_fn(data):
        products = data.get("products", [])
        products.append(product)
        return {"products": products}

    _atomic_update_json(get_afm_cache_path(), update_fn, {"products": []})


def get_results_cache_path() -> str:
    """
    Gets the path to the results cache file.

    Returns:
        path (str): The path to the results cache folder
    """
    return os.path.join(get_cache_path(), "scraper_results.csv")
