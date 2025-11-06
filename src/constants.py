"""
This file contains all the constants used in the program.

All default values are centralized here to avoid hard-coding throughout the codebase.
This makes it easier to modify defaults and maintain consistency.
"""

# ============================================================================
# UI Options
# ============================================================================

OPTIONS = ["YouTube Shorts Automation", "Twitter Bot", "Affiliate Marketing", "Outreach", "Quit"]

TWITTER_OPTIONS = ["Post something", "Show all Posts", "Setup CRON Job", "Quit"]
TWITTER_CRON_OPTIONS = ["Once a day", "Twice a day", "Thrice a day", "Quit"]

YOUTUBE_OPTIONS = ["Upload Short", "Show all Shorts", "Setup CRON Job", "Quit"]
YOUTUBE_CRON_OPTIONS = ["Once a day", "Twice a day", "Thrice a day", "Quit"]

# ============================================================================
# Selenium Element Selectors
# ============================================================================

# Twitter Section
TWITTER_TEXTAREA_CLASS = "public-DraftStyleDefault-block public-DraftStyleDefault-ltr"
TWITTER_POST_BUTTON_XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div/div[3]"

# YouTube Section
YOUTUBE_TEXTBOX_ID = "textbox"
YOUTUBE_MADE_FOR_KIDS_NAME = "VIDEO_MADE_FOR_KIDS_MFK"
YOUTUBE_NOT_MADE_FOR_KIDS_NAME = "VIDEO_MADE_FOR_KIDS_NOT_MFK"
YOUTUBE_NEXT_BUTTON_ID = "next-button"
YOUTUBE_RADIO_BUTTON_XPATH = '//*[@id="radioLabel"]'
YOUTUBE_DONE_BUTTON_ID = "done-button"

# Amazon Section (AFM)
AMAZON_PRODUCT_TITLE_ID = "productTitle"
AMAZON_FEATURE_BULLETS_ID = "feature-bullets"

# ============================================================================
# Selenium Wait Timeouts (seconds)
# ============================================================================

DEFAULT_WAIT_TIMEOUT = 10  # Default wait for elements
UPLOAD_WAIT_TIMEOUT = 60  # Timeout for video upload completion
VIDEO_LIST_WAIT_TIMEOUT = 15  # Timeout for video list to load

# ============================================================================
# Video Generation Configuration
# ============================================================================

SCRIPT_TO_PROMPTS_RATIO = 3  # One image prompt per 3 script words
MAX_PROMPTS_G4F = 25  # Maximum prompts when using G4F
SUBTITLE_FONTSIZE = 100  # Font size for video subtitles
SUBTITLE_MAX_CHARS = 10  # Maximum characters per subtitle line

# ============================================================================
# Configuration Defaults
# ============================================================================

# Application Settings
DEFAULT_VERBOSE = False
DEFAULT_HEADLESS = False
DEFAULT_IS_FOR_KIDS = False
DEFAULT_THREADS = 1
DEFAULT_SCRIPT_SENTENCE_LENGTH = 4
DEFAULT_TWITTER_LANGUAGE = "en"

# Network/Scraper Settings
DEFAULT_SCRAPER_TIMEOUT = 300  # 5 minutes
DEFAULT_HTTP_TIMEOUT = 5  # For quick network checks
DEFAULT_GO_VERSION_CHECK_TIMEOUT = 5  # For subprocess version checks

# Default URLs
DEFAULT_ZIP_URL = "https://filebin.net/bb9ewdtckolsf3sg/drive-download-20240209T180019Z-001.zip"

# SMTP/Email Settings
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587

# ============================================================================
# HTTP Client Defaults
# ============================================================================

DEFAULT_POOL_CONNECTIONS = 10  # Number of connection pools
DEFAULT_POOL_MAXSIZE = 10  # Max connections per pool

# ============================================================================
# Rate Limiting Defaults
# ============================================================================

# Mistral AI Rate Limits
MISTRAL_AI_MAX_CALLS = 5
MISTRAL_AI_PERIOD = 1.0  # seconds

# Venice AI Rate Limits
VENICE_AI_MAX_CALLS = 10
VENICE_AI_PERIOD = 1.0  # seconds

# AssemblyAI Rate Limits
ASSEMBLY_AI_MAX_CALLS = 5
ASSEMBLY_AI_PERIOD = 1.0  # seconds

# Generic HTTP Rate Limits
GENERIC_HTTP_MAX_CALLS = 100
GENERIC_HTTP_PERIOD = 60.0  # seconds (100 requests per minute)

# ============================================================================
# Logging Defaults
# ============================================================================

# Application Log File
APP_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
APP_LOG_BACKUP_COUNT = 5

# Error Log File
ERROR_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
ERROR_LOG_BACKUP_COUNT = 3

# ============================================================================
# Font File Extensions
# ============================================================================

VALID_FONT_EXTENSIONS = (".ttf", ".otf", ".ttc", ".woff", ".woff2")
