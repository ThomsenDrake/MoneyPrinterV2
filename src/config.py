import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from termcolor import colored

# Try to load dotenv for environment variable support
try:
    from dotenv import load_dotenv

    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # dotenv is optional

# Import centralized default values
from constants import (
    DEFAULT_HEADLESS,
    DEFAULT_IS_FOR_KIDS,
    DEFAULT_SCRAPER_TIMEOUT,
    DEFAULT_SCRIPT_SENTENCE_LENGTH,
    DEFAULT_SMTP_PORT,
    DEFAULT_SMTP_SERVER,
    DEFAULT_THREADS,
    DEFAULT_TWITTER_LANGUAGE,
    DEFAULT_VERBOSE,
    DEFAULT_ZIP_URL,
    VALID_FONT_EXTENSIONS,
)

ROOT_DIR = os.path.dirname(sys.path[0])


class ConfigManager:
    """
    Singleton configuration manager that caches config.json in memory.
    This eliminates the performance bottleneck of reading the file repeatedly.

    Optionally supports Pydantic validation for type safety and early error detection.
    """

    _instance: Optional["ConfigManager"] = None
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
            from pydantic import ValidationError

            from config_schema import validate_config

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

    @classmethod
    def get_with_env(cls, key: str, env_var: str, default: Any = None) -> Any:
        """
        Get a configuration value with environment variable priority.

        Order of precedence:
        1. Environment variable (if set and not empty)
        2. config.json value (if key exists)
        3. Default value

        Args:
            key: The configuration key in config.json
            env_var: The environment variable name to check first
            default: Default value if neither env var nor config key found

        Returns:
            The configuration value from env, config, or default

        Example:
            >>> ConfigManager.get_with_env("mistral_api_key", "MISTRAL_API_KEY", "")
            # Returns MISTRAL_API_KEY env var if set, else config.json value, else ""
        """
        # Check environment variable first
        env_value = os.getenv(env_var)
        if env_value is not None and env_value.strip() != "":
            return env_value

        # Fall back to config.json
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
    Gets the email credentials from environment variables or config file.

    Checks SMTP_USERNAME and SMTP_PASSWORD environment variables first,
    then falls back to config.json email object.

    Returns:
        credentials (dict): The email credentials with keys:
            - username: Email username (from SMTP_USERNAME or config)
            - password: Email password (from SMTP_PASSWORD or config)
            - smtp_server: SMTP server (from SMTP_SERVER or config)
            - smtp_port: SMTP port (from SMTP_PORT or config)
    """
    # Get base email config from config.json
    email_config = _config.get("email", {})

    # Override with environment variables if present
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")

    # Build result with env vars taking precedence
    result = {
        "smtp_server": (
            smtp_server if smtp_server else email_config.get("smtp_server", DEFAULT_SMTP_SERVER)
        ),
        "smtp_port": (
            int(smtp_port) if smtp_port else email_config.get("smtp_port", DEFAULT_SMTP_PORT)
        ),
        "username": username if username else email_config.get("username", ""),
        "password": password if password else email_config.get("password", ""),
    }

    return result


def get_verbose() -> bool:
    """
    Gets the verbose flag from environment or config file.

    Checks VERBOSE environment variable first,
    then falls back to config.json.

    Returns:
        verbose (bool): The verbose flag
    """
    verbose_env = os.getenv("VERBOSE")
    if verbose_env is not None:
        return verbose_env.lower() in ("true", "1", "yes")
    return _config.get("verbose", DEFAULT_VERBOSE)


def get_firefox_profile_path() -> str:
    """
    Gets the path to the Firefox profile.

    Checks FIREFOX_PROFILE environment variable first,
    then falls back to config.json.

    Returns:
        path (str): The path to the Firefox profile
    """
    return _config.get_with_env("firefox_profile", "FIREFOX_PROFILE", "")


def get_headless() -> bool:
    """
    Gets the headless flag from environment or config file.

    Checks HEADLESS environment variable first,
    then falls back to config.json.

    Returns:
        headless (bool): The headless flag
    """
    headless_env = os.getenv("HEADLESS")
    if headless_env is not None:
        return headless_env.lower() in ("true", "1", "yes")
    return _config.get("headless", DEFAULT_HEADLESS)


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
    return _config.get("twitter_language", DEFAULT_TWITTER_LANGUAGE)


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
    return _config.get("threads", DEFAULT_THREADS)


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
    return _config.get("zip_url", DEFAULT_ZIP_URL)


def get_is_for_kids() -> bool:
    """
    Gets the is for kids flag from the config file.

    Returns:
        is_for_kids (bool): The is for kids flag
    """
    return _config.get("is_for_kids", DEFAULT_IS_FOR_KIDS)


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
    return _config.get("scraper_timeout", DEFAULT_SCRAPER_TIMEOUT)


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

    Checks ASSEMBLYAI_API_KEY environment variable first,
    then falls back to config.json.

    Returns:
        key (str): The AssemblyAI API key
    """
    return _config.get_with_env("assembly_ai_api_key", "ASSEMBLYAI_API_KEY", "")


def get_mistral_api_key() -> str:
    """
    Gets the Mistral AI API key.

    Checks MISTRAL_API_KEY environment variable first,
    then falls back to config.json.

    Returns:
        key (str): The Mistral AI API key
    """
    return _config.get_with_env("mistral_api_key", "MISTRAL_API_KEY", "")


def get_venice_api_key() -> str:
    """
    Gets the Venice AI API key.

    Checks VENICE_API_KEY environment variable first,
    then falls back to config.json.

    Returns:
        key (str): The Venice AI API key
    """
    return _config.get_with_env("venice_api_key", "VENICE_API_KEY", "")


def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
    """
    Equalizes the subtitles in a SRT file.

    Args:
        srt_path (str): The path to the SRT file
        max_chars (int): The maximum amount of characters in a subtitle

    Returns:
        None
    """
    import srt_equalizer  # Lazy import to avoid dependency issues

    srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)


def get_font() -> str:
    """
    Gets the font from the config file.

    Returns validated font filename (basename only for security).

    Returns:
        font (str): The font filename (basename only)
    """
    import os.path

    font = _config.get("font", "")
    if not font:
        return ""

    # Security: Only allow basename, prevent directory traversal
    # E.g., "../../../etc/passwd" becomes just "passwd"
    safe_font = os.path.basename(font)

    # Additional validation: Must have valid font extension
    if not safe_font.lower().endswith(VALID_FONT_EXTENSIONS):
        logging.warning(f"Font file has invalid extension: {safe_font}")

    return safe_font


def get_fonts_dir() -> str:
    """
    Gets the fonts directory.

    Returns:
        dir (str): The fonts directory
    """
    return os.path.join(ROOT_DIR, "fonts")


def get_imagemagick_path() -> str:
    """
    Gets the validated path to ImageMagick binary.

    Performs security validation to prevent command injection.

    Returns:
        path (str): The validated path to ImageMagick

    Raises:
        ValueError: If path contains suspicious characters
    """
    import os.path
    import re

    path = _config.get("imagemagick_path", "")
    if not path:
        return ""

    # Security: Check for suspicious characters that could enable command injection
    # Allow only: alphanumeric, /, \, -, _, ., space, :
    if not re.match(r"^[a-zA-Z0-9/\\\-_.:\s]+$", path):
        raise ValueError(
            f"ImageMagick path contains invalid characters: {path}. "
            "Only alphanumeric, /, \\, -, _, ., :, and spaces are allowed."
        )

    # Additional security: Block command chaining attempts
    dangerous_sequences = [";", "&&", "||", "`", "$", "$(", "|", "<", ">"]
    for seq in dangerous_sequences:
        if seq in path:
            raise ValueError(f"ImageMagick path contains dangerous sequence '{seq}': {path}")

    # Validate path exists (log warning if not, but don't fail)
    if not os.path.exists(path):
        logging.warning(
            f"ImageMagick path does not exist: {path}. " "Video subtitle generation may fail."
        )

    return path


def get_script_sentence_length() -> int:
    """
    Gets the forced script's sentence length.
    In case there is no sentence length in config, returns default value.

    Returns:
        length (int): Length of script's sentence
    """
    return _config.get("script_sentence_length", DEFAULT_SCRIPT_SENTENCE_LENGTH)
