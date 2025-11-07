import csv
import io
import logging
import os
import platform
import re
import subprocess
import time
import zipfile
from typing import List

import yagmail

from cache import *
from config import *
from constants import DEFAULT_GO_VERSION_CHECK_TIMEOUT
from http_client import get_http_client
from status import *


class Outreach:
    """
    Class that houses the methods to reach out to businesses.
    """

    def __init__(self) -> None:
        """
        Constructor for the Outreach class.

        Returns:
            None
        """
        # Initialize HTTP client for connection pooling
        self.http_client = get_http_client()

        # Check if go is installed
        try:
            subprocess.run(
                ["go", "version"],
                check=True,
                capture_output=True,
                timeout=DEFAULT_GO_VERSION_CHECK_TIMEOUT,
            )
            self.go_installed = True
        except (subprocess.SubprocessError, FileNotFoundError):
            self.go_installed = False

        # Set niche
        self.niche = get_google_maps_scraper_niche()

        # Set email credentials
        self.email_creds = get_email_credentials()

    def is_go_installed(self) -> bool:
        """
        Check if go is installed.

        Returns:
            bool: True if go is installed, False otherwise.
        """
        # Check if go is installed
        try:
            subprocess.run(
                ["go", "version"],
                check=True,
                capture_output=True,
                timeout=DEFAULT_GO_VERSION_CHECK_TIMEOUT,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logging.debug(f"Go not installed or not accessible: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error checking Go installation: {str(e)}", exc_info=True)
            return False

    def unzip_file(self, zip_link: str) -> None:
        """
        Unzip the file.

        Args:
            zip_link (str): The link to the zip file.

        Returns:
            None
        """
        # Check if the scraper is already unzipped, if not, unzip it
        if os.path.exists("google-maps-scraper-0.9.7"):
            info("=> Scraper already unzipped. Skipping unzip.")
            return

        try:
            r = self.http_client.request("GET", zip_link)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall()
        except Exception as e:
            logging.error(f"Failed to download and extract scraper: {str(e)}", exc_info=True)
            raise

    def build_scraper(self) -> None:
        """
        Build the scraper.

        Returns:
            None
        """
        # Check if the scraper is already built, if not, build it
        scraper_executable = (
            "google-maps-scraper.exe" if platform.system() == "Windows" else "google-maps-scraper"
        )
        if os.path.exists(scraper_executable):
            print(colored("=> Scraper already built. Skipping build.", "blue"))
            return

        original_dir = os.getcwd()
        try:
            os.chdir("google-maps-scraper-0.9.7")
            subprocess.run(["go", "mod", "download"], check=True)
            subprocess.run(["go", "build"], check=True)

            # Move the built executable to parent directory
            if platform.system() == "Windows":
                subprocess.run(
                    ["move", "google-maps-scraper.exe", "..\\google-maps-scraper.exe"],
                    check=True,
                )
            else:
                subprocess.run(["mv", "google-maps-scraper", "../google-maps-scraper"], check=True)
        finally:
            os.chdir(original_dir)

    def run_scraper_with_args_for_30_seconds(self, args: str, timeout: int = 300) -> None:
        """
        Run the scraper with the specified arguments for 30 seconds.

        Args:
            args (str): The arguments to run the scraper with.
            timeout (int): The time to run the scraper for.

        Returns:
            None
        """
        # Run the scraper with the specified arguments
        info(" => Running scraper...")

        # Build command as list for secure subprocess execution
        scraper_executable = (
            "./google-maps-scraper.exe"
            if platform.system() == "Windows"
            else "./google-maps-scraper"
        )
        command_list = [scraper_executable] + args.split()

        try:
            scraper_process = subprocess.run(
                command_list, timeout=float(timeout), capture_output=True, text=True
            )

            if scraper_process.returncode == 0:
                self._kill_scraper_process()
                print(colored("=> Scraper finished successfully.", "green"))
            else:
                self._kill_scraper_process()
                logging.error(
                    f"Scraper finished with error code {scraper_process.returncode}: {scraper_process.stderr}"
                )
                print(colored("=> Scraper finished with an error.", "red"))

        except subprocess.TimeoutExpired as e:
            self._kill_scraper_process()
            logging.warning(f"Scraper timed out after {timeout} seconds: {str(e)}")
            print(colored(f"Scraper timed out after {timeout} seconds", "yellow"))
        except subprocess.SubprocessError as e:
            self._kill_scraper_process()
            logging.error(f"Subprocess error while running scraper: {str(e)}", exc_info=True)
            print(colored(f"An error occurred while running the scraper: {str(e)}", "red"))
        except Exception as e:
            self._kill_scraper_process()
            logging.error(f"Unexpected error while running scraper: {str(e)}", exc_info=True)
            print(colored(f"An unexpected error occurred: {str(e)}", "red"))

    def _kill_scraper_process(self) -> None:
        """
        Kill the scraper process safely.

        Returns:
            None
        """
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/f", "/im", "google-maps-scraper.exe"],
                    check=False,
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["pkill", "-f", "google-maps-scraper"], check=False, capture_output=True
                )
        except Exception as e:
            logging.debug(f"Error killing scraper process: {str(e)}")

    def get_items_from_file(self, file_name: str) -> List[str]:
        """
        Read and return items from a file.

        Args:
            file_name (str): The name of the file to read from.

        Returns:
            List[str]: The items from the file.
        """
        # Read and return items from a file
        with open(file_name, "r", errors="ignore") as f:
            items = f.readlines()
            items = [item.strip() for item in items[1:]]
            return items

    def set_email_for_website(self, index: int, website: str, output_file: str) -> None:
        """Extracts an email address from a website and updates a CSV file with it.

        This method sends a GET request to the specified website, searches for the
        first email address in the HTML content, and appends it to the specified
        row in a CSV file. If no email address is found, no changes are made to
        the CSV file.

        Args:
            index (int): The row index in the CSV file where the email should be appended.
            website (str): The URL of the website to extract the email address from.
            output_file (str): The path to the CSV file to update with the extracted email.

        Returns:
            None
        """
        # Extract and set an email for a website
        email = ""

        try:
            r = self.http_client.request("GET", website)
        except Exception as e:
            logging.warning(f"Failed to fetch website {website}: {str(e)}")
            return

        if r.status_code == 200:
            # Define a regular expression pattern to match email addresses
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

            # Find all email addresses in the HTML string
            email_addresses = re.findall(email_pattern, r.text)

            email = email_addresses[0] if len(email_addresses) > 0 else ""

        if email:
            print(f"=> Setting email {email} for website {website}")
            with open(output_file, "r", newline="", errors="ignore") as csvfile:
                csvreader = csv.reader(csvfile)
                items = list(csvreader)
                items[index].append(email)

            with open(output_file, "w", newline="", errors="ignore") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(items)

    def start(self) -> None:
        """
        Start the outreach process.

        Returns:
            None
        """
        # Check if go is installed
        if not self.is_go_installed():
            error("Go is not installed. Please install go and try again.")
            return

        # Unzip the scraper
        self.unzip_file(get_google_maps_scraper_zip_url())

        # Build the scraper
        self.build_scraper()

        # Write the niche to a file
        with open("niche.txt", "w") as f:
            f.write(self.niche)

        output_path = get_results_cache_path()
        message_subject = get_outreach_message_subject()
        message_body = get_outreach_message_body_file()

        # Run
        self.run_scraper_with_args_for_30_seconds(
            f'-input niche.txt -results "{output_path}"', timeout=get_scraper_timeout()
        )

        # Get the items from the file
        items = self.get_items_from_file(output_path)
        success(f" => Scraped {len(items)} items.")

        # Remove the niche file
        os.remove("niche.txt")

        time.sleep(2)

        # Create a yagmail SMTP client outside the loop
        yag = yagmail.SMTP(
            user=self.email_creds["username"],
            password=self.email_creds["password"],
            host=self.email_creds["smtp_server"],
            port=self.email_creds["smtp_port"],
        )

        # Get the email for each business
        for item in items:
            try:
                # Check if the item"s website is valid
                website = item.split(",")
                website = [w for w in website if w.startswith("http")]
                website = website[0] if len(website) > 0 else ""
                if website != "":
                    try:
                        test_r = self.http_client.request("GET", website)
                    except Exception as e:
                        logging.warning(f"Failed to validate website {website}: {str(e)}")
                        warning(f" => Website {website} is not accessible. Skipping...")
                        continue

                    if test_r.status_code == 200:
                        self.set_email_for_website(items.index(item), website, output_path)

                        # Send emails using the existing SMTP connection
                        receiver_email = item.split(",")[-1]

                        if "@" not in receiver_email:
                            warning(f" => No email provided. Skipping...")
                            continue

                        subject = message_subject.replace("{{COMPANY_NAME}}", item[0])
                        body = open(message_body, "r").read().replace("{{COMPANY_NAME}}", item[0])

                        info(f" => Sending email to {receiver_email}...")

                        yag.send(
                            to=receiver_email,
                            subject=subject,
                            contents=body,
                        )

                        success(f" => Sent email to {receiver_email}")
                    else:
                        warning(f" => Website {website} is invalid. Skipping...")
            except requests.RequestException as err:
                logging.error(f"Network error processing item {item}: {str(err)}", exc_info=True)
                error(f" => Network error: {err}...")
                continue
            except (IndexError, ValueError) as err:
                logging.error(f"Data parsing error for item {item}: {str(err)}", exc_info=True)
                error(f" => Data error: {err}...")
                continue
            except Exception as err:
                logging.error(f"Unexpected error processing item {item}: {str(err)}", exc_info=True)
                error(f" => Unexpected error: {err}...")
                continue
