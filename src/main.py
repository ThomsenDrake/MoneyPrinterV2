import subprocess
from typing import Any, Dict, Optional
from uuid import uuid4

import schedule
from prettytable import PrettyTable
from termcolor import colored

from art import *
from cache import *
from classes.AFM import AffiliateMarketing
from classes.Outreach import Outreach
from classes.Tts import TTS
from classes.Twitter import Twitter
from classes.YouTube import YouTube
from config import *
from constants import *

# Initialize logging framework
from logger import setup_logger
from status import *
from utils import *
from validation import validate_choice, validate_integer, validate_non_empty_string

# Get logger for main module
logger = setup_logger(__name__)


def get_user_choice(options: list) -> int:
    """
    Display menu options and get validated user choice.

    Args:
        options (list): List of menu options to display

    Returns:
        int: The selected option number (1-indexed)

    Raises:
        ValueError: If input is invalid
    """
    info("\n============ OPTIONS ============", False)
    for idx, option in enumerate(options):
        print(colored(f" {idx + 1}. {option}", "cyan"))
    info("=================================\n", False)

    user_input = input("Select an option: ").strip()
    return validate_integer(user_input, min_value=1, max_value=len(options), field_name="Option")


def create_youtube_account() -> Optional[Dict[str, Any]]:
    """
    Create a new YouTube account configuration.

    Returns:
        Optional[Dict[str, Any]]: Account data dictionary, or None if cancelled
    """
    generated_uuid = str(uuid4())

    success(f" => Generated ID: {generated_uuid}")
    nickname = validate_non_empty_string(
        question(" => Enter a nickname for this account: "), "Nickname"
    )
    fp_profile = validate_non_empty_string(
        question(" => Enter the path to the Firefox profile: "), "Firefox profile path"
    )
    niche = validate_non_empty_string(question(" => Enter the account niche: "), "Niche")
    language = validate_non_empty_string(question(" => Enter the account language: "), "Language")

    # Add image generation options
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

    account_data = {
        "id": generated_uuid,
        "nickname": nickname,
        "firefox_profile": fp_profile,
        "niche": niche,
        "language": language,
        "use_g4f": image_gen_choice == "1",
        "videos": [],
    }

    if image_gen_choice == "2":
        worker_url = validate_non_empty_string(
            question(" => Enter your Cloudflare worker URL for image generation: "), "Worker URL"
        )
        account_data["worker_url"] = worker_url

    return account_data


def create_twitter_account() -> Optional[Dict[str, Any]]:
    """
    Create a new Twitter account configuration.

    Returns:
        Optional[Dict[str, Any]]: Account data dictionary, or None if cancelled
    """
    generated_uuid = str(uuid4())

    success(f" => Generated ID: {generated_uuid}")
    nickname = validate_non_empty_string(
        question(" => Enter a nickname for this account: "), "Nickname"
    )
    fp_profile = validate_non_empty_string(
        question(" => Enter the path to the Firefox profile: "), "Firefox profile path"
    )
    topic = validate_non_empty_string(question(" => Enter the account topic: "), "Topic")

    return {
        "id": generated_uuid,
        "nickname": nickname,
        "firefox_profile": fp_profile,
        "topic": topic,
        "posts": [],
    }


def setup_cron_job(command: str, schedule_option: int, platform: str) -> None:
    """
    Set up a scheduled CRON job for automated posting.

    Args:
        command (str): The command to execute
        schedule_option (int): The schedule option selected by user
        platform (str): The platform (youtube or twitter)
    """

    def job():
        """Executes the scheduled command."""
        subprocess.run(command, shell=False)

    if platform == "youtube":
        if schedule_option == 1:
            schedule.every(1).day.do(job)
            success("Set up CRON Job: Upload once per day")
        elif schedule_option == 2:
            schedule.every().day.at("10:00").do(job)
            schedule.every().day.at("16:00").do(job)
            success("Set up CRON Job: Upload twice per day (10:00, 16:00)")
    elif platform == "twitter":
        if schedule_option == 1:
            schedule.every(1).day.do(job)
            success("Set up CRON Job: Post once per day")
        elif schedule_option == 2:
            schedule.every().day.at("10:00").do(job)
            schedule.every().day.at("16:00").do(job)
            success("Set up CRON Job: Post twice per day (10:00, 16:00)")
        elif schedule_option == 3:
            schedule.every().day.at("08:00").do(job)
            schedule.every().day.at("12:00").do(job)
            schedule.every().day.at("18:00").do(job)
            success("Set up CRON Job: Post three times per day (08:00, 12:00, 18:00)")


def run_youtube_operations(selected_account: Dict[str, Any]) -> None:
    """
    Run YouTube automation operations for a selected account.

    Args:
        selected_account (Dict[str, Any]): The selected YouTube account data
    """
    youtube = YouTube(
        selected_account["id"],
        selected_account["nickname"],
        selected_account["firefox_profile"],
        selected_account["niche"],
        selected_account["language"],
    )

    while True:
        rem_temp_files()
        user_input = get_user_choice(YOUTUBE_OPTIONS)
        tts = TTS()

        if user_input == 1:
            # Generate and optionally upload video
            youtube.generate_video(tts)
            upload_to_yt = validate_choice(
                question("Do you want to upload this video to YouTube? (Yes/No): "),
                valid_choices=["yes", "no"],
                case_sensitive=False,
                field_name="Upload choice",
            )
            if upload_to_yt.lower() == "yes":
                youtube.upload_video()

        elif user_input == 2:
            # View uploaded videos
            videos = youtube.get_videos()
            if len(videos) > 0:
                videos_table = PrettyTable()
                videos_table.field_names = ["ID", "Date", "Title"]
                for video in videos:
                    videos_table.add_row(
                        [
                            videos.index(video) + 1,
                            colored(video["date"], "blue"),
                            colored(video["title"][:60] + "...", "green"),
                        ]
                    )
                print(videos_table)
            else:
                warning(" No videos found.")

        elif user_input == 3:
            # Setup CRON job
            info("How often do you want to upload?")
            schedule_option = get_user_choice(YOUTUBE_CRON_OPTIONS)

            cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
            command = f"python {cron_script_path} youtube {selected_account['id']}"
            setup_cron_job(command, schedule_option, "youtube")

        elif user_input == 4:
            # Exit to main menu
            if get_verbose():
                info(" => Climbing Options Ladder...", False)
            break


def run_twitter_operations(selected_account: Dict[str, Any]) -> None:
    """
    Run Twitter bot operations for a selected account.

    Args:
        selected_account (Dict[str, Any]): The selected Twitter account data
    """
    twitter = Twitter(
        selected_account["id"],
        selected_account["nickname"],
        selected_account["firefox_profile"],
        selected_account["topic"],
    )

    while True:
        user_input = get_user_choice(TWITTER_OPTIONS)

        if user_input == 1:
            # Create and post a tweet
            twitter.post()

        elif user_input == 2:
            # View post history
            posts = twitter.get_posts()
            posts_table = PrettyTable()
            posts_table.field_names = ["ID", "Date", "Content"]
            for post in posts:
                posts_table.add_row(
                    [
                        posts.index(post) + 1,
                        colored(post["date"], "blue"),
                        colored(post["content"][:60] + "...", "green"),
                    ]
                )
            print(posts_table)

        elif user_input == 3:
            # Setup CRON job
            info("How often do you want to post?")
            schedule_option = get_user_choice(TWITTER_CRON_OPTIONS)

            cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
            command = f"python {cron_script_path} twitter {selected_account['id']}"
            setup_cron_job(command, schedule_option, "twitter")

        elif user_input == 4:
            # Exit to main menu
            if get_verbose():
                info(" => Climbing Options Ladder...", False)
            break


def main():
    """Main entry point for the application, providing a menu-driven interface
    to manage YouTube, Twitter bots, Affiliate Marketing, and Outreach tasks.

    This function allows users to:
    1. Start the YouTube Shorts Automater to manage YouTube accounts,
       generate and upload videos, and set up CRON jobs.
    2. Start a Twitter Bot to manage Twitter accounts, post tweets, and
       schedule posts using CRON jobs.
    3. Manage Affiliate Marketing by creating pitches and sharing them via
       Twitter accounts.
    4. Initiate an Outreach process for engagement and promotion tasks.
    5. Exit the application.

    The function continuously prompts users for input, validates it, and
    executes the selected option until the user chooses to quit.

    Args:
        None

    Returns:
        None
    """
    try:
        user_input = get_user_choice(OPTIONS)
    except ValueError as e:
        error(f"Invalid input: {e}")
        return

    # Start the selected option
    if user_input == 1:
        # YouTube Shorts Automater
        info("Starting YT Shorts Automater...")
        cached_accounts = get_accounts("youtube")

        if len(cached_accounts) == 0:
            # No accounts found - create new one
            warning("No accounts found in cache. Create one now?")
            create_choice = validate_choice(
                question("Yes/No: "),
                valid_choices=["yes", "no"],
                case_sensitive=False,
                field_name="Create account",
            )

            if create_choice.lower() == "yes":
                try:
                    account_data = create_youtube_account()
                    add_account("youtube", account_data)
                    success("Account configured successfully!")
                except ValueError as e:
                    error(f"Failed to create account: {e}")
                    return
        else:
            # Display existing accounts
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Niche"]
            for account in cached_accounts:
                table.add_row(
                    [
                        cached_accounts.index(account) + 1,
                        colored(account["id"], "cyan"),
                        colored(account["nickname"], "blue"),
                        colored(account["niche"], "green"),
                    ]
                )
            print(table)

            # Select account
            try:
                account_choice = validate_integer(
                    question("Select an account to start: "),
                    min_value=1,
                    max_value=len(cached_accounts),
                    field_name="Account selection",
                )
                selected_account = cached_accounts[account_choice - 1]
                run_youtube_operations(selected_account)
            except (ValueError, IndexError) as e:
                error(f"Invalid account selected: {e}")
                return
    elif user_input == 2:
        # Twitter Bot
        info("Starting Twitter Bot...")
        cached_accounts = get_accounts("twitter")

        if len(cached_accounts) == 0:
            # No accounts found - create new one
            warning("No accounts found in cache. Create one now?")
            create_choice = validate_choice(
                question("Yes/No: "),
                valid_choices=["yes", "no"],
                case_sensitive=False,
                field_name="Create account",
            )

            if create_choice.lower() == "yes":
                try:
                    account_data = create_twitter_account()
                    add_account("twitter", account_data)
                    success("Account configured successfully!")
                except ValueError as e:
                    error(f"Failed to create account: {e}")
                    return
        else:
            # Display existing accounts
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Account Topic"]
            for account in cached_accounts:
                table.add_row(
                    [
                        cached_accounts.index(account) + 1,
                        colored(account["id"], "cyan"),
                        colored(account["nickname"], "blue"),
                        colored(account["topic"], "green"),
                    ]
                )
            print(table)

            # Select account
            try:
                account_choice = validate_integer(
                    question("Select an account to start: "),
                    min_value=1,
                    max_value=len(cached_accounts),
                    field_name="Account selection",
                )
                selected_account = cached_accounts[account_choice - 1]
                run_twitter_operations(selected_account)
            except (ValueError, IndexError) as e:
                error(f"Invalid account selected: {e}")
                return
    elif user_input == 3:
        # Affiliate Marketing
        info("Starting Affiliate Marketing...")
        cached_products = get_products()

        if len(cached_products) == 0:
            warning("No products found in cache. Create one now?")
            create_choice = validate_choice(
                question("Yes/No: "),
                valid_choices=["yes", "no"],
                case_sensitive=False,
                field_name="Create product",
            )

            if create_choice.lower() == "yes":
                try:
                    affiliate_link = validate_non_empty_string(
                        question(" => Enter the affiliate link: "), "Affiliate link"
                    )
                    twitter_uuid = validate_non_empty_string(
                        question(" => Enter the Twitter Account UUID: "), "Twitter UUID"
                    )

                    # Find the account
                    twitter_accounts = get_accounts("twitter")
                    account = next(
                        (acc for acc in twitter_accounts if acc["id"] == twitter_uuid), None
                    )

                    if not account:
                        error(f"Twitter account with UUID {twitter_uuid} not found")
                        return

                    # Add product to cache
                    add_product(
                        {
                            "id": str(uuid4()),
                            "affiliate_link": affiliate_link,
                            "twitter_uuid": twitter_uuid,
                        }
                    )

                    # Generate and share pitch
                    afm = AffiliateMarketing(
                        affiliate_link,
                        account["firefox_profile"],
                        account["id"],
                        account["nickname"],
                        account["topic"],
                    )
                    afm.generate_pitch()
                    afm.share_pitch("twitter")

                except ValueError as e:
                    error(f"Failed to create product: {e}")
                    return
        else:
            # Display existing products
            table = PrettyTable()
            table.field_names = ["ID", "Affiliate Link", "Twitter Account UUID"]
            for product in cached_products:
                table.add_row(
                    [
                        cached_products.index(product) + 1,
                        colored(product["affiliate_link"], "cyan"),
                        colored(product["twitter_uuid"], "blue"),
                    ]
                )
            print(table)

            # Select product
            try:
                product_choice = validate_integer(
                    question("Select a product to start: "),
                    min_value=1,
                    max_value=len(cached_products),
                    field_name="Product selection",
                )
                selected_product = cached_products[product_choice - 1]

                # Find associated Twitter account
                twitter_accounts = get_accounts("twitter")
                account = next(
                    (
                        acc
                        for acc in twitter_accounts
                        if acc["id"] == selected_product["twitter_uuid"]
                    ),
                    None,
                )

                if not account:
                    error(f"Twitter account {selected_product['twitter_uuid']} not found")
                    return

                # Generate and share pitch
                afm = AffiliateMarketing(
                    selected_product["affiliate_link"],
                    account["firefox_profile"],
                    account["id"],
                    account["nickname"],
                    account["topic"],
                )
                afm.generate_pitch()
                afm.share_pitch("twitter")

            except (ValueError, IndexError) as e:
                error(f"Invalid product selected: {e}")
                return

    elif user_input == 4:
        info("Starting Outreach...")

        outreach = Outreach()

        outreach.start()
    elif user_input == 5:
        if get_verbose():
            print(colored(" => Quitting...", "blue"))
        sys.exit(0)
    else:
        error("Invalid option selected. Please try again.", "red")
        main()


if __name__ == "__main__":
    # Print ASCII Banner
    print_banner()

    first_time = get_first_time_running()

    if first_time:
        print(
            colored(
                "Hey! It looks like you're running MoneyPrinter V2 for the first time. Let's get you setup first!",
                "yellow",
            )
        )

    # Setup file tree
    assert_folder_structure()

    # Remove temporary files
    rem_temp_files()

    # Fetch MP3 Files
    fetch_songs()

    while True:
        main()
