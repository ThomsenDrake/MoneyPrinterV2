"""
Account Management Service for social media platforms.

This module eliminates code duplication in account creation and selection
workflows across YouTube and Twitter automation.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from prettytable import PrettyTable
from termcolor import colored

from cache import add_account, get_accounts
from status import error, info, question, success, warning
from validation import validate_choice, validate_integer, validate_non_empty_string

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Centralized account management for YouTube, Twitter, and other platforms.

    This class consolidates common account operations:
    - Creating new accounts with validation
    - Listing existing accounts
    - Selecting accounts interactively
    - Common field prompts (nickname, Firefox profile, etc.)

    Eliminates ~50+ lines of duplicated code from main.py.
    """

    @staticmethod
    def create_base_account() -> Dict[str, Any]:
        """
        Create base account data with common fields.

        Prompts for fields common to all account types:
        - UUID (auto-generated)
        - Nickname
        - Firefox profile path

        Returns:
            Dictionary with base account fields

        Example:
            >>> base = AccountManager.create_base_account()
            >>> base['id']
            '123e4567-e89b-12d3-a456-426614174000'
        """
        generated_uuid = str(uuid4())
        success(f" => Generated ID: {generated_uuid}")

        nickname = validate_non_empty_string(
            question(" => Enter a nickname for this account: "), "Nickname"
        )

        fp_profile = validate_non_empty_string(
            question(" => Enter the path to the Firefox profile: "), "Firefox profile path"
        )

        return {
            "id": generated_uuid,
            "nickname": nickname,
            "firefox_profile": fp_profile,
        }

    @staticmethod
    def create_youtube_account() -> Optional[Dict[str, Any]]:
        """
        Create a new YouTube account configuration.

        Prompts for YouTube-specific fields:
        - Niche
        - Language
        - Image generation method (Venice AI or Cloudflare)

        Returns:
            Complete YouTube account data dictionary

        Raises:
            ValueError: If validation fails for any field
        """
        logger.info("Creating new YouTube account")

        # Get base account data
        account_data = AccountManager.create_base_account()

        # YouTube-specific fields
        niche = validate_non_empty_string(question(" => Enter the account niche: "), "Niche")
        language = validate_non_empty_string(
            question(" => Enter the account language: "), "Language"
        )

        # Image generation options
        info("\n============ IMAGE GENERATION ============", False)
        print(colored(" 1. Venice AI (qwen-image)", "cyan"))
        print(colored(" 2. Cloudflare Worker", "cyan"))
        info("=======================================", False)
        print(colored("\nRecommendation: If you're unsure, select Venice AI (Option 1)", "yellow"))
        info("=======================================\n", False)

        image_gen_choice = validate_choice(
            question(" => Select image generation method (1/2): "),
            valid_choices=["1", "2"],
            field_name="Image generation method",
        )

        # Update account data with YouTube-specific fields
        account_data.update(
            {
                "niche": niche,
                "language": language,
                "use_g4f": image_gen_choice == "1",
                "videos": [],
            }
        )

        # Cloudflare worker URL if selected
        if image_gen_choice == "2":
            worker_url = validate_non_empty_string(
                question(" => Enter your Cloudflare worker URL for image generation: "),
                "Worker URL",
            )
            account_data["worker_url"] = worker_url

        logger.info(f"Created YouTube account: {account_data['nickname']}")
        return account_data

    @staticmethod
    def create_twitter_account() -> Optional[Dict[str, Any]]:
        """
        Create a new Twitter account configuration.

        Prompts for Twitter-specific fields:
        - Topic

        Returns:
            Complete Twitter account data dictionary

        Raises:
            ValueError: If validation fails for any field
        """
        logger.info("Creating new Twitter account")

        # Get base account data
        account_data = AccountManager.create_base_account()

        # Twitter-specific fields
        topic = validate_non_empty_string(question(" => Enter the account topic: "), "Topic")

        # Update account data with Twitter-specific fields
        account_data.update(
            {
                "topic": topic,
                "posts": [],
            }
        )

        logger.info(f"Created Twitter account: {account_data['nickname']}")
        return account_data

    @staticmethod
    def display_accounts_table(accounts: List[Dict[str, Any]], platform: str = "generic") -> None:
        """
        Display accounts in a formatted table.

        Args:
            accounts: List of account dictionaries
            platform: Platform type for custom column headers

        Example:
            >>> accounts = get_accounts("youtube")
            >>> AccountManager.display_accounts_table(accounts, "youtube")
            # Displays table with YouTube-specific columns
        """
        if not accounts:
            warning(" No accounts found.")
            return

        table = PrettyTable()

        # Customize table headers based on platform
        if platform == "youtube":
            table.field_names = ["ID", "UUID", "Nickname", "Niche"]
            for account in accounts:
                table.add_row(
                    [
                        accounts.index(account) + 1,
                        colored(account["id"], "cyan"),
                        colored(account["nickname"], "blue"),
                        colored(account.get("niche", "N/A"), "green"),
                    ]
                )
        elif platform == "twitter":
            table.field_names = ["ID", "UUID", "Nickname", "Account Topic"]
            for account in accounts:
                table.add_row(
                    [
                        accounts.index(account) + 1,
                        colored(account["id"], "cyan"),
                        colored(account["nickname"], "blue"),
                        colored(account.get("topic", "N/A"), "green"),
                    ]
                )
        else:
            # Generic table
            table.field_names = ["ID", "UUID", "Nickname"]
            for account in accounts:
                table.add_row(
                    [
                        accounts.index(account) + 1,
                        colored(account["id"], "cyan"),
                        colored(account["nickname"], "blue"),
                    ]
                )

        print(table)

    @staticmethod
    def select_account(accounts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Prompt user to select an account from a list.

        Args:
            accounts: List of account dictionaries

        Returns:
            Selected account dictionary, or None if selection fails

        Raises:
            ValueError: If invalid account number is provided
        """
        if not accounts:
            error("No accounts available to select")
            return None

        try:
            account_choice = validate_integer(
                question("Select an account to start: "),
                min_value=1,
                max_value=len(accounts),
                field_name="Account selection",
            )

            selected = accounts[account_choice - 1]
            logger.info(f"Selected account: {selected['nickname']}")
            return selected

        except (ValueError, IndexError) as e:
            error(f"Invalid account selected: {e}")
            logger.error(f"Account selection error: {e}")
            return None

    @staticmethod
    def get_or_create_account(
        platform: str, create_fn: Callable[[], Optional[Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing account or prompt to create new one.

        This consolidates the common pattern of:
        1. Check for cached accounts
        2. If none exist, offer to create
        3. If accounts exist, display and select
        4. Return selected account

        Args:
            platform: Platform name ('youtube', 'twitter', etc.)
            create_fn: Function to call for creating new account

        Returns:
            Selected or newly created account, or None if user declines

        Example:
            >>> account = AccountManager.get_or_create_account(
            ...     "youtube",
            ...     AccountManager.create_youtube_account
            ... )
        """
        cached_accounts = get_accounts(platform)

        if len(cached_accounts) == 0:
            # No accounts found - offer to create
            warning("No accounts found in cache. Create one now?")
            create_choice = validate_choice(
                question("Yes/No: "),
                valid_choices=["yes", "no"],
                case_sensitive=False,
                field_name="Create account",
            )

            if create_choice.lower() == "yes":
                try:
                    account_data = create_fn()
                    if account_data:
                        add_account(platform, account_data)
                        success("Account configured successfully!")
                        logger.info(f"New {platform} account created and saved")
                        return account_data
                except ValueError as e:
                    error(f"Failed to create account: {e}")
                    logger.error(f"Account creation failed: {e}")
                    return None
            else:
                info("Account creation cancelled")
                return None
        else:
            # Display and select existing account
            AccountManager.display_accounts_table(cached_accounts, platform)
            return AccountManager.select_account(cached_accounts)

    @staticmethod
    def manage_youtube_account() -> Optional[Dict[str, Any]]:
        """
        Manage YouTube account workflow.

        Convenience method that combines get_or_create_account
        with YouTube-specific logic.

        Returns:
            Selected YouTube account, or None
        """
        info("Starting YT Shorts Automater...")
        return AccountManager.get_or_create_account(
            "youtube", AccountManager.create_youtube_account
        )

    @staticmethod
    def manage_twitter_account() -> Optional[Dict[str, Any]]:
        """
        Manage Twitter account workflow.

        Convenience method that combines get_or_create_account
        with Twitter-specific logic.

        Returns:
            Selected Twitter account, or None
        """
        info("Starting Twitter Bot...")
        return AccountManager.get_or_create_account(
            "twitter", AccountManager.create_twitter_account
        )


# Backward compatibility: expose functions at module level
create_youtube_account = AccountManager.create_youtube_account
create_twitter_account = AccountManager.create_twitter_account
