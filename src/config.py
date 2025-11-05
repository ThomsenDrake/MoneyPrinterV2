import os
import sys
import json
import srt_equalizer
import logging
from typing import Optional, Dict, Any
from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])


class ConfigManager:
    """
    Singleton configuration manager that caches config.json in memory.
    This eliminates the performance bottleneck of reading the file repeatedly.

    Optionally supports Pydantic validation for type safety and early error detection.
    """
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None
    _config_path: str = None
    _validated: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._config_path = os.path.join(ROOT_DIR, "config.json")
            cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls, validate: bool = False) -> None:
        """
        Load configuration from config.json file.

        Args:
            validate: If True, validate config using Pydantic schema
        """
        try:
            with open(cls._config_path, "r") as file:
                cls._config = json.load(file)

            # Optional validation using Pydantic
            if validate:
                cls.validate()

        except FileNotFoundError:
            logging.error(f"Config file not found: {cls._config_path}")
            cls._config = {}
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {str(e)}")
            cls._config = {}

    @classmethod
    def reload(cls, validate: bool = False) -> None:
        """
        Reload configuration from disk.

        Args:
            validate: If True, validate config using Pydantic schema
        """
        cls._load_config(validate=validate)

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration using Pydantic schema.

        Returns:
            True if validation succeeds

        Raises:
            ValidationError: If configuration is invalid

        Example:
            >>> ConfigManager.validate()
            True
        """
        try:
            from config_schema import validate_config
            from pydantic import ValidationError

            # Validate the configuration
            validated_config = validate_config(cls._config)
            cls._validated = True
            logging.info("Configuration validated successfully")
            return True

        except ValidationError as e:
            logging.error(f"Configuration validation failed: {str(e)}")
            cls._validated = False
            raise
        except ImportError:
            logging.warning("Pydantic not available, skipping validation")
            return False

    @classmethod
    def is_validated(cls) -> bool:
        """
        Check if configuration has been validated.

        Returns:
            True if configuration has been validated successfully
        """
        return cls._validated

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key
            default: Default value if key not found

        Returns:
            The configuration value or default
        """
        instance = cls()
        return instance._config.get(key, default)


# Global config manager instance
_config = ConfigManager()


def assert_folder_structure() -> None:
    """
    Make sure that the necessary folder structure is present.

    Returns:
        None
    """
    # Create the .mp folder
    if not os.path.exists(os.path.join(ROOT_DIR, ".mp")):
        if get_verbose():
            print(colored(f"=> Creating .mp folder at {os.path.join(ROOT_DIR, '.mp')}", "green"))
        os.makedirs(os.path.join(ROOT_DIR, ".mp"))


def get_first_time_running() -> bool:
    """
    Checks if the program is running for the first time by checking if .mp folder exists.

    Returns:
        exists (bool): True if the program is running for the first time, False otherwise
    """
    return not os.path.exists(os.path.join(ROOT_DIR, ".mp"))


def get_email_credentials() -> dict:
    """
    Gets the email credentials from the config file.

    Returns:
        credentials (dict): The email credentials
    """
    return _config.get("email", {})


def get_verbose() -> bool:
    """
    Gets the verbose flag from the config file.

    Returns:
        verbose (bool): The verbose flag
    """
    return _config.get("verbose", False)


def get_firefox_profile_path() -> str:
    """
    Gets the path to the Firefox profile.

    Returns:
        path (str): The path to the Firefox profile
    """
    return _config.get("firefox_profile", "")


def get_headless() -> bool:
    """
    Gets the headless flag from the config file.

    Returns:
        headless (bool): The headless flag
    """
    return _config.get("headless", False)


def get_model() -> str:
    """
    Gets the model from the config file.

    Returns:
        model (str): The model
    """
    return _config.get("llm", "")


def get_twitter_language() -> str:
    """
    Gets the Twitter language from the config file.

    Returns:
        language (str): The Twitter language
    """
    return _config.get("twitter_language", "en")


def get_image_model() -> str:
    """
    Gets the Image Model from the config file.

    Returns:
        model (str): The image model
    """
    return _config.get("image_model", "")


def get_threads() -> int:
    """
    Gets the amount of threads to use for example when writing to a file with MoviePy.

    Returns:
        threads (int): Amount of threads
    """
    return _config.get("threads", 1)


def get_image_prompt_llm() -> str:
    """
    Gets the image prompt for LLM from the config file.

    Returns:
        prompt (str): The image prompt
    """
    return _config.get("image_prompt_llm", "")


def get_zip_url() -> str:
    """
    Gets the URL to the zip file containing the songs.

    Returns:
        url (str): The URL to the zip file
    """
    return _config.get("zip_url", "https://filebin.net/bb9ewdtckolsf3sg/drive-download-20240209T180019Z-001.zip")


def get_is_for_kids() -> bool:
    """
    Gets the is for kids flag from the config file.

    Returns:
        is_for_kids (bool): The is for kids flag
    """
    return _config.get("is_for_kids", False)


def get_google_maps_scraper_zip_url() -> str:
    """
    Gets the URL to the zip file containing the Google Maps scraper.

    Returns:
        url (str): The URL to the zip file
    """
    return _config.get("google_maps_scraper", "")


def get_google_maps_scraper_niche() -> str:
    """
    Gets the niche for the Google Maps scraper.

    Returns:
        niche (str): The niche
    """
    return _config.get("google_maps_scraper_niche", "")


def get_scraper_timeout() -> int:
    """
    Gets the timeout for the scraper.

    Returns:
        timeout (int): The timeout
    """
    return _config.get("scraper_timeout", 300)


def get_outreach_message_subject() -> str:
    """
    Gets the outreach message subject.

    Returns:
        subject (str): The outreach message subject
    """
    return _config.get("outreach_message_subject", "")


def get_outreach_message_body_file() -> str:
    """
    Gets the outreach message body file.

    Returns:
        file (str): The outreach message body file
    """
    return _config.get("outreach_message_body_file", "")


def get_assemblyai_api_key() -> str:
    """
    Gets the AssemblyAI API key.

    Returns:
        key (str): The AssemblyAI API key
    """
    return _config.get("assembly_ai_api_key", "")


def get_mistral_api_key() -> str:
    """
    Gets the Mistral AI API key.

    Returns:
        key (str): The Mistral AI API key
    """
    return _config.get("mistral_api_key", "")


def get_venice_api_key() -> str:
    """
    Gets the Venice AI API key.

    Returns:
        key (str): The Venice AI API key
    """
    return _config.get("venice_api_key", "")


def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
    """
    Equalizes the subtitles in a SRT file.

    Args:
        srt_path (str): The path to the SRT file
        max_chars (int): The maximum amount of characters in a subtitle

    Returns:
        None
    """
    srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)


def get_font() -> str:
    """
    Gets the font from the config file.

    Returns:
        font (str): The font
    """
    return _config.get("font", "")


def get_fonts_dir() -> str:
    """
    Gets the fonts directory.

    Returns:
        dir (str): The fonts directory
    """
    return os.path.join(ROOT_DIR, "fonts")


def get_imagemagick_path() -> str:
    """
    Gets the path to ImageMagick.

    Returns:
        path (str): The path to ImageMagick
    """
    return _config.get("imagemagick_path", "")


def get_script_sentence_length() -> int:
    """
    Gets the forced script's sentence length.
    In case there is no sentence length in config, returns 4 when none

    Returns:
        length (int): Length of script's sentence
    """
    return _config.get("script_sentence_length", 4)
