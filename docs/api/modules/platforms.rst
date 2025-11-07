Platform Integration Classes
============================

Platform-specific automation classes for YouTube, Twitter,
affiliate marketing, and outreach campaigns.

YouTube Automation
------------------

Automated YouTube video creation, uploading, and management.

.. automodule:: classes.YouTube
   :members:
   :undoc-members:
   :show-inheritance:

Features:
~~~~~~~~~

- AI-generated video scripts
- Parallel image generation (3-4x faster)
- Automated video rendering
- Direct YouTube upload
- Video scheduling

Usage Example:

.. code-block:: python

   from classes.YouTube import YouTube

   youtube = YouTube(
       account_uuid="uuid-here",
       fp_profile_path="/path/to/profile",
       video_topic="AI Technology",
       video_length=300
   )

   youtube.generate_video()

Twitter Automation
------------------

Twitter posting and engagement automation.

.. automodule:: classes.Twitter
   :members:
   :undoc-members:
   :show-inheritance:

Features:
~~~~~~~~~

- Automated posting
- Engagement automation (likes, retweets)
- Account rotation
- Rate limiting compliance

Affiliate Marketing
-------------------

Affiliate marketing campaign automation.

.. automodule:: classes.AFM
   :members:
   :undoc-members:
   :show-inheritance:

Note:
~~~~~

AFM stands for "Affiliate Marketing" - a well-known abbreviation in the domain.
The class is named ``AffiliateMarketing`` but the file is ``AFM.py`` for brevity.

Outreach Automation
-------------------

Automated outreach campaign management.

.. automodule:: classes.Outreach
   :members:
   :undoc-members:
   :show-inheritance:

Text-to-Speech
--------------

Text-to-speech synthesis for video narration.

.. automodule:: classes.Tts
   :members:
   :undoc-members:
   :show-inheritance:

Features:
~~~~~~~~~

- Multiple TTS engines supported
- Voice selection
- Audio processing
- Format conversion
