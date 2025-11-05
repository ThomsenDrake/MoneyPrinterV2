from termcolor import colored

from config import ROOT_DIR


def print_banner() -> None:
    """
    Prints the introductory ASCII Art Banner.

    Returns:
        None
    """
    with open(f"{ROOT_DIR}/assets/banner.txt", "r") as file:
        print(colored(file.read(), "green"))
