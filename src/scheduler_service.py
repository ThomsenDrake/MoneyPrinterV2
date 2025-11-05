"""
Scheduler Service for automating social media posts.

This module eliminates code duplication for CRON job setup between
YouTube and Twitter automation.
"""

import logging
import subprocess
from typing import List, Optional

import schedule

from status import success


class ScheduleConfig:
    """Configuration for a scheduled job."""

    def __init__(
        self,
        platform: str,
        frequency: str,
        times: Optional[List[str]] = None,
        interval_days: int = 1,
    ):
        """
        Initialize schedule configuration.

        Args:
            platform: Platform name (youtube, twitter, etc.)
            frequency: Frequency description for logging
            times: List of times in "HH:MM" format (e.g., ["10:00", "16:00"])
            interval_days: Number of days between runs (default: 1)
        """
        self.platform = platform
        self.frequency = frequency
        self.times = times or []
        self.interval_days = interval_days


class SchedulerService:
    """
    Centralized scheduling service for automation tasks.

    This class eliminates the duplication between YouTube and Twitter
    CRON job setup by providing a unified interface.
    """

    # Platform-specific schedule configurations
    YOUTUBE_SCHEDULES = {
        1: ScheduleConfig("youtube", "Upload once per day", interval_days=1),
        2: ScheduleConfig(
            "youtube", "Upload twice per day (10:00, 16:00)", times=["10:00", "16:00"]
        ),
    }

    TWITTER_SCHEDULES = {
        1: ScheduleConfig("twitter", "Post once per day", interval_days=1),
        2: ScheduleConfig("twitter", "Post twice per day (10:00, 16:00)", times=["10:00", "16:00"]),
        3: ScheduleConfig(
            "twitter",
            "Post three times per day (08:00, 12:00, 18:00)",
            times=["08:00", "12:00", "18:00"],
        ),
    }

    @staticmethod
    def create_job_command(platform: str, account_id: str, script_path: str) -> List[str]:
        """
        Create the command to execute for a scheduled job.

        Args:
            platform: Platform name (youtube or twitter)
            account_id: Account UUID
            script_path: Path to the cron.py script

        Returns:
            List[str]: Command as list of arguments for subprocess
        """
        return ["python", script_path, platform, account_id]

    @staticmethod
    def setup_schedule(command: List[str], schedule_config: ScheduleConfig) -> schedule.Job:
        """
        Set up a schedule based on configuration.

        Args:
            command: Command to execute as list
            schedule_config: Schedule configuration

        Returns:
            schedule.Job: The scheduled job
        """

        def job():
            """Execute the scheduled command."""
            try:
                logging.info(
                    f"Running scheduled {schedule_config.platform} job: {' '.join(command)}"
                )
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                logging.error(
                    f"Scheduled {schedule_config.platform} job failed: {str(e)}",
                    exc_info=True,
                )

        # If specific times are configured, schedule at those times
        if schedule_config.times:
            for time in schedule_config.times:
                schedule.every().day.at(time).do(job)
        else:
            # Otherwise schedule by interval
            schedule.every(schedule_config.interval_days).day.do(job)

        success(f"Set up CRON Job: {schedule_config.frequency}")

        # Return the first job (or the job if only one was created)
        return schedule.jobs[0] if schedule.jobs else None

    @classmethod
    def setup_youtube_schedule(
        cls, account_id: str, schedule_option: int, cron_script_path: str
    ) -> Optional[schedule.Job]:
        """
        Set up a YouTube upload schedule.

        Args:
            account_id: YouTube account UUID
            schedule_option: Schedule option (1=daily, 2=twice daily)
            cron_script_path: Path to cron.py script

        Returns:
            schedule.Job: The scheduled job, or None if invalid option

        Example:
            >>> SchedulerService.setup_youtube_schedule("uuid-123", 1, "./src/cron.py")
        """
        if schedule_option not in cls.YOUTUBE_SCHEDULES:
            logging.error(f"Invalid YouTube schedule option: {schedule_option}")
            return None

        schedule_config = cls.YOUTUBE_SCHEDULES[schedule_option]
        command = cls.create_job_command("youtube", account_id, cron_script_path)

        return cls.setup_schedule(command, schedule_config)

    @classmethod
    def setup_twitter_schedule(
        cls, account_id: str, schedule_option: int, cron_script_path: str
    ) -> Optional[schedule.Job]:
        """
        Set up a Twitter posting schedule.

        Args:
            account_id: Twitter account UUID
            schedule_option: Schedule option (1=daily, 2=twice daily, 3=thrice daily)
            cron_script_path: Path to cron.py script

        Returns:
            schedule.Job: The scheduled job, or None if invalid option

        Example:
            >>> SchedulerService.setup_twitter_schedule("uuid-456", 2, "./src/cron.py")
        """
        if schedule_option not in cls.TWITTER_SCHEDULES:
            logging.error(f"Invalid Twitter schedule option: {schedule_option}")
            return None

        schedule_config = cls.TWITTER_SCHEDULES[schedule_option]
        command = cls.create_job_command("twitter", account_id, cron_script_path)

        return cls.setup_schedule(command, schedule_config)

    @staticmethod
    def get_youtube_schedule_options() -> List[str]:
        """
        Get list of YouTube schedule options for display.

        Returns:
            List[str]: Human-readable schedule options
        """
        return [
            "Upload once per day",
            "Upload twice per day (10:00, 16:00)",
        ]

    @staticmethod
    def get_twitter_schedule_options() -> List[str]:
        """
        Get list of Twitter schedule options for display.

        Returns:
            List[str]: Human-readable schedule options
        """
        return [
            "Post once per day",
            "Post twice per day (10:00, 16:00)",
            "Post three times per day (08:00, 12:00, 18:00)",
        ]

    @staticmethod
    def run_pending():
        """
        Run all pending scheduled jobs.

        This should be called in a loop to execute scheduled tasks.

        Example:
            >>> import time
            >>> while True:
            ...     SchedulerService.run_pending()
            ...     time.sleep(60)  # Check every minute
        """
        schedule.run_pending()

    @staticmethod
    def clear_all():
        """
        Clear all scheduled jobs.

        Useful for cleanup or testing.
        """
        schedule.clear()
        logging.info("All scheduled jobs cleared")


# Convenience functions for backward compatibility
def setup_youtube_schedule(
    account_id: str, schedule_option: int, cron_script_path: str
) -> Optional[schedule.Job]:
    """
    Convenience function to setup YouTube schedule.

    Args:
        account_id: YouTube account UUID
        schedule_option: Schedule option
        cron_script_path: Path to cron.py

    Returns:
        schedule.Job: The scheduled job
    """
    return SchedulerService.setup_youtube_schedule(account_id, schedule_option, cron_script_path)


def setup_twitter_schedule(
    account_id: str, schedule_option: int, cron_script_path: str
) -> Optional[schedule.Job]:
    """
    Convenience function to setup Twitter schedule.

    Args:
        account_id: Twitter account UUID
        schedule_option: Schedule option
        cron_script_path: Path to cron.py

    Returns:
        schedule.Job: The scheduled job
    """
    return SchedulerService.setup_twitter_schedule(account_id, schedule_option, cron_script_path)
