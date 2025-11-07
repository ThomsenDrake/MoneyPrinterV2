"""
Platform integration classes for MoneyPrinterV2.

This package contains automation classes for various social media platforms
and marketing activities. Each class provides a high-level interface for
platform-specific operations while maintaining consistent patterns for:
- Browser automation
- Content generation
- API interactions
- Account management

Available Classes:
    YouTube: YouTube video creation and management
    Twitter: Twitter posting and engagement
    AffiliateMarketing: Affiliate marketing automation (AFM)
    Outreach: Outreach campaign management
    TTS: Text-to-speech synthesis

Example:
    >>> from classes.YouTube import YouTube
    >>> youtube = YouTube(account_uuid="...", video_topic="...")
    >>> youtube.generate_video()

Note:
    Classes are not imported by default to avoid loading heavy dependencies.
    Import them explicitly as shown in the example above.
"""

# Note: We don't eagerly import classes to avoid loading dependencies
# Users should import directly: from classes.YouTube import YouTube
__all__ = [
    "YouTube",
    "Twitter",
    "AffiliateMarketing",
    "Outreach",
    "TTS",
]
