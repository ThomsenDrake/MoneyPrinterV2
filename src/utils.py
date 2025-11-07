import logging
import os
import platform
import random
import subprocess
import zipfile
from typing import Optional

from config import *
from http_client import get_http_client
from status import *


def close_running_selenium_instances() -> None:
    """
    Closes any running Selenium instances.

    Returns:
        None
    """
    try:
        info(" => Closing running Selenium instances...")

        # Kill all running Firefox instances
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/f", "/im", "firefox.exe"], check=False, capture_output=True
            )
        else:
            subprocess.run(["pkill", "firefox"], check=False, capture_output=True)

        success(" => Closed running Selenium instances.")

    except subprocess.SubprocessError as e:
        logging.error(f"Subprocess error while closing Selenium instances: {str(e)}", exc_info=True)
        error(f"Error occurred while closing running Selenium instances: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error while closing Selenium instances: {str(e)}", exc_info=True)
        error(f"Error occurred while closing running Selenium instances: {str(e)}")


def build_url(youtube_video_id: str) -> str:
    """
    Builds the URL to the YouTube video.

    Args:
        youtube_video_id (str): The YouTube video ID.

    Returns:
        url (str): The URL to the YouTube video.
    """
    return f"https://www.youtube.com/watch?v={youtube_video_id}"


def rem_temp_files() -> None:
    """
    Removes temporary files in the `.mp` directory.

    Returns:
        None
    """
    # Path to the `.mp` directory
    mp_dir = os.path.join(ROOT_DIR, ".mp")

    files = os.listdir(mp_dir)

    for file in files:
        if not file.endswith(".json"):
            os.remove(os.path.join(mp_dir, file))


def fetch_songs() -> None:
    """
    Downloads songs into songs/ directory to use with geneated videos.

    Returns:
        None
    """
    try:
        info(f" => Fetching songs...")

        files_dir = os.path.join(ROOT_DIR, "Songs")
        if not os.path.exists(files_dir):
            os.mkdir(files_dir)
            if get_verbose():
                info(f" => Created directory: {files_dir}")
        else:
            # Skip if songs are already downloaded
            return

        # Download songs using HTTP client with connection pooling
        http_client = get_http_client()
        response = http_client.get(
            get_zip_url()
            or "https://filebin.net/bb9ewdtckolsf3sg/drive-download-20240209T180019Z-001.zip"
        )

        # Save the zip file
        with open(os.path.join(files_dir, "songs.zip"), "wb") as file:
            file.write(response.content)

        # Unzip the file
        with zipfile.ZipFile(os.path.join(files_dir, "songs.zip"), "r") as file:
            file.extractall(files_dir)

        # Remove the zip file
        os.remove(os.path.join(files_dir, "songs.zip"))

        success(" => Downloaded Songs to ../Songs.")

    except Exception as e:
        logging.error(f"Network error while fetching songs: {str(e)}", exc_info=True)
        error(f"Error occurred while fetching songs: {str(e)}")
    except (OSError, zipfile.BadZipFile) as e:
        logging.error(f"File system error while processing songs: {str(e)}", exc_info=True)
        error(f"Error occurred while processing songs: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error while fetching songs: {str(e)}", exc_info=True)
        error(f"Error occurred while fetching songs: {str(e)}")


def choose_random_song() -> Optional[str]:
    """
    Chooses a random song from the songs/ directory.

    Returns:
        Optional[str]: The path to the chosen song, or None if no songs are available.
    """
    try:
        songs = os.listdir(os.path.join(ROOT_DIR, "Songs"))
        song = random.choice(songs)
        success(f" => Chose song: {song}")
        return os.path.join(ROOT_DIR, "Songs", song)
    except FileNotFoundError as e:
        logging.error(f"Songs directory not found: {str(e)}", exc_info=True)
        error(f"Songs directory not found. Run fetch_songs() first: {str(e)}")
        return None
    except (IndexError, ValueError) as e:
        logging.error(f"No songs available in directory: {str(e)}", exc_info=True)
        error(f"No songs available to choose from: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while choosing song: {str(e)}", exc_info=True)
        error(f"Error occurred while choosing random song: {str(e)}")
        return None
