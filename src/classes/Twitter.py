import logging
import re
import sys
from datetime import datetime
from typing import Any, List, Optional

from mistralai import Mistral
from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_firefox import *
from termcolor import colored
from webdriver_manager.firefox import GeckoDriverManager

from cache import *
from config import *
from constants import *
from status import *
from browser_factory import BrowserFactory
from protocols import BrowserProtocol


class Twitter:
    """
    Class for the Bot, that grows a Twitter account.
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        fp_profile_path: str,
        topic: str,
        browser: Optional[webdriver.Firefox] = None,
    ) -> None:
        """
        Initializes the Twitter Bot.

        Args:
            account_uuid (str): The account UUID
            account_nickname (str): The account nickname
            fp_profile_path (str): The path to the Firefox profile
            topic (str): The topic for tweets
            browser (Optional[webdriver.Firefox]): Optional pre-configured browser instance.
                If not provided, a new browser will be created using BrowserFactory.

        Returns:
            None
        """
        self.account_uuid: str = account_uuid
        self.account_nickname: str = account_nickname
        self.fp_profile_path: str = fp_profile_path
        self.topic: str = topic

        # Dependency injection: Use provided browser or create new one
        if browser is not None:
            # Use injected browser instance
            self.browser = browser
            logging.info("Using injected browser instance")
        else:
            # Create browser using BrowserFactory for consistency
            # Note: This maintains backward compatibility by creating browser if not injected
            headless = get_headless()
            self.browser = BrowserFactory.create_firefox_browser(
                profile_path=fp_profile_path,
                headless=headless,
                use_profile_object=False,  # Twitter uses add_argument method
            )
            logging.info("Created new browser instance via BrowserFactory")

    def __enter__(self) -> "Twitter":
        """
        Context manager entry point.

        Returns:
            Twitter: This instance for use in with statement.
        """
        return self

    def __exit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]
    ) -> None:
        """
        Context manager exit point - ensures browser cleanup.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        try:
            if hasattr(self, "browser") and self.browser:
                self.browser.quit()
                logging.info("Browser instance closed successfully")
        except Exception as e:
            logging.warning(f"Error while closing browser: {str(e)}")

    def post(self, text: str = None) -> None:
        """
        Starts the Twitter Bot.

        Args:
            text (str): The text to post

        Returns:
            None
        """
        bot: webdriver.Firefox = self.browser
        verbose: bool = get_verbose()

        bot.get("https://twitter.com")

        # Wait for page to load
        WebDriverWait(bot, DEFAULT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']")
            )
        )

        post_content: str = self.generate_post()
        now: datetime = datetime.now()

        print(colored(f" => Posting to Twitter:", "blue"), post_content[:30] + "...")

        # Click new tweet button with retry
        new_tweet_button = WebDriverWait(bot, DEFAULT_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']"))
        )
        new_tweet_button.click()

        # Wait for textbox and send keys
        body = post_content if text is None else text
        textbox = WebDriverWait(bot, DEFAULT_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']"))
        )
        textbox.send_keys(body)

        # Wait for tweet button to be clickable
        WebDriverWait(bot, DEFAULT_WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='tweetButton']"))
        )
        bot.find_element(By.CLASS_NAME, "notranslate").send_keys(keys.Keys.ENTER)
        bot.find_element(By.XPATH, "//button[@data-testid='tweetButton']").click()

        if verbose:
            print(colored(" => Pressed [ENTER] Button on Twitter..", "blue"))

        # Wait for post to complete
        WebDriverWait(bot, DEFAULT_WAIT_TIMEOUT).until(
            lambda d: len(d.find_elements(By.XPATH, "//button[@data-testid='tweetButton']")) == 0
        )

        # Add the post to the cache
        self.add_post({"content": post_content, "date": now.strftime("%m/%d/%Y, %H:%M:%S")})

        success("Posted to Twitter successfully!")

    def get_posts(self) -> List[dict]:
        """
        Gets the posts from the cache.

        Returns:
            posts (List[dict]): The posts
        """
        if not os.path.exists(get_twitter_cache_path()):
            # Create the cache file
            with open(get_twitter_cache_path(), "w") as file:
                json.dump({"posts": []}, file, indent=4)

        with open(get_twitter_cache_path(), "r") as file:
            parsed = json.load(file)

            # Find our account
            accounts = parsed["accounts"]
            for account in accounts:
                if account["id"] == self.account_uuid:
                    posts = account["posts"]

                    if posts is None:
                        return []

                    # Return the posts
                    return posts

    def add_post(self, post: dict) -> None:
        """
        Adds a post to the cache.

        Args:
            post (dict): The post to add

        Returns:
            None
        """
        posts = self.get_posts()
        posts.append(post)

        with open(get_twitter_cache_path(), "r") as file:
            previous_json = json.loads(file.read())

            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self.account_uuid:
                    account["posts"].append(post)

            # Commit changes
            with open(get_twitter_cache_path(), "w") as f:
                f.write(json.dumps(previous_json))

    def generate_post(self) -> str:
        """
        Generates a post for the Twitter account based on the topic using Mistral AI.

        Returns:
            post (str): The post
        """
        try:
            client = Mistral(api_key=get_mistral_api_key())

            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate a Twitter post about: {self.topic} in {get_twitter_language()}. The Limit is 2 sentences. Choose a specific sub-topic of the provided topic.",
                    }
                ],
            )

            if get_verbose():
                info("Generating a post...")

            completion = response.choices[0].message.content

            if completion is None:
                error("Failed to generate a post. Please try again.")
                sys.exit(1)

            # Apply Regex to remove all *
            completion = re.sub(r"\*", "", completion).replace('"', "")

            if get_verbose():
                info(f"Length of post: {len(completion)}")
            if len(completion) >= 260:
                return self.generate_post()

            return completion

        except Exception as e:
            error(f"Failed to generate post with Mistral AI: {str(e)}")
            sys.exit(1)
