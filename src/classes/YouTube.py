import os
import re
import json
import time
import hashlib
import requests
import traceback
import assemblyai as aai
import numpy as np
from scipy.io import wavfile
from utils import *
from cache import *
from .Tts import TTS
from config import *
from status import *
from uuid import uuid4
from constants import *
from typing import List
from moviepy.editor import *
from termcolor import colored
from selenium_firefox import *
from selenium import webdriver
from moviepy.video.fx.all import crop
from moviepy.audio.fx import volumex
from moviepy.config import change_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from moviepy.video.tools.subtitles import SubtitlesClip
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime
import httplib2
import random
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

# Set ImageMagick Path
change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})

class YouTube:
    """
    Class for YouTube Automation using the YouTube Data API.
    """
    # YouTube API constants
    YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    CLIENT_SECRETS_FILE = os.path.join(ROOT_DIR, "client_secrets.json")
    MAX_RETRIES = 10
    RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
    RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

    def __init__(self, account_uuid: str, account_nickname: str, fp_profile_path: str, niche: str, language: str) -> None:
        """
        Constructor for YouTube Class.

        Args:
            account_uuid (str): The unique identifier for the YouTube account.
            account_nickname (str): The nickname for the YouTube account.
            fp_profile_path (str): Path to the firefox profile that is logged into the specificed YouTube Account.
            niche (str): The niche of the provided YouTube Channel.
            language (str): The language of the Automation.

        Returns:
            None
        """
        self._account_uuid: str = account_uuid
        self._account_nickname: str = account_nickname
        self._fp_profile_path: str = fp_profile_path
        self._niche: str = niche
        self._language: str = language
        self.subject: str = None  # Initialize subject attribute
        self.script: str = None   # Initialize script attribute
        self.metadata: dict = {}  # Initialize metadata dictionary
        self.images: list = []    # Initialize images list
        self.image_prompts: list = []  # Initialize image prompts list
        self.tts_path: str = None  # Initialize TTS path
        self.video_path: str = None  # Initialize video path
        self.uploaded_video_url: str = None  # Initialize uploaded video URL
        self.warnings: list = []  # Add warnings list to store non-critical issues
        self._youtube_service = None  # Initialize YouTube service
        self.browser = None
        self.using_api = os.path.exists(self.CLIENT_SECRETS_FILE)

        # Only initialize browser if not using API upload
        if not self.using_api:
            if get_verbose():
                info("No API credentials found, falling back to browser automation")
            try:
                # Initialize the Firefox profile
                self.options: Options = Options()
                
                # Set headless state of browser
                if get_headless():
                    self.options.add_argument("--headless")

                profile = webdriver.FirefoxProfile(self._fp_profile_path)
                self.options.profile = profile

                # Set the service
                self.service: Service = Service(GeckoDriverManager().install())

                # Initialize the browser
                self.browser: webdriver.Firefox = webdriver.Firefox(service=self.service, options=self.options)
            except Exception as e:
                if get_verbose():
                    warning(f"Failed to initialize browser: {str(e)}")
                    warning("This error can be ignored if using API upload")
        else:
            # Verify API access during initialization
            if not self.verify_api_access():
                error("YouTube API verification failed during initialization")
                raise Exception("YouTube API authentication failed. Please check your credentials.")
            # Sync video history during initialization
            self.sync_video_history()

    @property
    def niche(self) -> str:
        """
        Getter Method for the niche.

        Returns:
            niche (str): The niche
        """
        return self._niche
    
    @property
    def language(self) -> str:
        """
        Getter Method for the language to use.

        Returns:
            language (str): The language
        """
        return self._language
    
    def reassemble_chunked_response(self, response_text: str) -> str:
        """
        Attempt to reassemble a response that might have come in chunks.
        
        Args:
            response_text (str): The potentially chunked response text
            
        Returns:
            str: The reassembled response text
        """
        # Check if we have multiple JSON objects
        chunks = []
        current_chunk = ""
        brace_count = 0
        
        for char in response_text:
            current_chunk += char
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # We've found a complete JSON object
                    try:
                        json_obj = json.loads(current_chunk)
                        if isinstance(json_obj, dict) and "response" in json_obj:
                            chunks.append(json_obj["response"])
                    except json.JSONDecodeError:
                        pass
                    current_chunk = ""

        if chunks:
            if get_verbose():
                info(f"Found {len(chunks)} response chunks")
                for i, chunk in enumerate(chunks):
                    info(f"Chunk {i + 1}:\n{chunk}")
            
            # Combine chunks, removing any ellipsis at chunk boundaries
            combined = ""
            for chunk in chunks:
                chunk = chunk.strip()
                if chunk.startswith('...'):
                    chunk = chunk[3:]
                if chunk.endswith('...'):
                    chunk = chunk[:-3]
                combined += " " + chunk.strip()
            
            return combined.strip()
            
        return response_text

    def extract_content_from_response(self, response: str) -> str:
        """
        Extracts clean content from a potentially nested JSON response.
        
        Args:
            response (str): Raw response from the API
            
        Returns:
            str: Clean content with metadata removed
        """
        try:
            if get_verbose():
                info(f"Extracting content from raw response: {response}")

            # First try to handle chunked responses
            response = self.reassemble_chunked_response(response)
            if get_verbose():
                info(f"After chunk reassembly: {response}")

            # First try to parse as JSON
            data = response
            if isinstance(response, str):
                try:
                    # Remove any trailing ellipsis or incomplete JSON
                    response = re.sub(r'\.{3,}.*$', '', response)
                    # If we have an incomplete JSON object, try to complete it
                    if response.count('{') > response.count('}'):
                        response = response + '}' * (response.count('{') - response.count('}'))
                    data = json.loads(response)
                except json.JSONDecodeError as e:
                    if get_verbose():
                        warning(f"JSON parse error: {str(e)}")
                        warning("Attempting to clean response...")
                    # Try to extract content between quotes if JSON parsing failed
                    match = re.search(r'"response":\s*"([^"]+)"', response)
                    if match:
                        return match.group(1)
                    return response
                    
            # If we have a dict, extract the response
            if isinstance(data, dict):
                if "response" in data:
                    content = data["response"]
                    if get_verbose():
                        info(f"Found response field: {content}")
                    # The response itself might be JSON
                    try:
                        if isinstance(content, str) and (content.startswith('{') or content.startswith('[')):
                            content_json = json.loads(content)
                            if isinstance(content_json, dict) and "response" in content_json:
                                content = content_json["response"]
                    except (json.JSONDecodeError, TypeError) as e:
                        if get_verbose():
                            warning(f"Failed to parse nested JSON: {str(e)}")
                else:
                    error("Failed to generate script")
                    return None
                    error("Failed to generate script")
                    return None
                    # Try common field names
                    for key in ["content", "result", "text", "output"]:
                        if key in data:
                            content = data[key]
                            if get_verbose():
                                info(f"Found content in {key} field: {content}")
                            break
                    else:
                        content = str(data)
            else:
                content = str(data)
                
            # Clean up the content
            if isinstance(content, str):
                # Remove metadata
                content = re.sub(r'{"usage":{[^}]+}}', '', content)
                content = re.sub(r'"usage":\s*{[^}]+}', '', content)
                content = re.sub(r'"response":\s*"', '', content)
                # Remove any remaining JSON artifacts
                content = content.strip('"').strip("'").strip()
                # Remove trailing comma if present
                content = content.rstrip(",")
                # Remove any trailing ellipsis
                content = re.sub(r'\.{3,}$', '', content)
                
            if get_verbose():
                info(f"Final cleaned content: {content}")
                
            return content
            
        except Exception as e:
            if get_verbose():
                error(f"Error extracting content: {str(e)}")
                error(f"Error type: {type(e).__name__}")
                error(f"Raw response: {response}")
            return response

    def is_complete_response(self, content: str) -> bool:
        """
        Check if a response is complete and usable.
        
        Args:
            content (str): Content to check
            
        Returns:
            bool: True if the content is complete and usable
        """
        if not content:
            return False
            
        # Check for obvious truncation
        if any(content.endswith(x) for x in ['...', '…', '.'*3, ' ', ',', '"', "'"]):
            return False
            
        # Check for dangling words
        dangling_words = ['and', 'but', 'or', 'nor', 'yet', 'so', 'with', 'the', 'in', 'to', 'a', 'an']
        last_words = content.lower().split()[-3:]  # Look at last 3 words
        if any(word in dangling_words for word in last_words):
            return False
            
        # Check for JSON fragments
        if content.count('{') != content.count('}'):
            return False
        if content.count('[') != content.count(']'):
            return False
            
        # Check for missing end punctuation if it's meant to be a sentence
        first_word = content.split()[0] if content.split() else ""
        if first_word and first_word[0].isupper() and not content.rstrip().endswith(('.', '!', '?')):
            return False
            
        return True

    def is_response_truncated(self, response: str) -> bool:
        """
        Check if a response appears to be truncated.
        Only checks the actual content, ignoring metadata.
        
        Args:
            response (str): The response to check
            
        Returns:
            bool: True if the response appears truncated
        """
        # If it's a JSON response, extract just the content
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "response" in data:
                content = data["response"]
            else:
                content = response
        except json.JSONDecoder:
            content = response
            
        # Only check the actual content for truncation
        if any(content.endswith(x) for x in ['...', '…', '..']):
            return True
            
        return False

    def extract_boundary_content(self, text: str) -> str:
        """
        Extract content between response boundaries.
        
        Args:
            text (str): The text to extract from
            
        Returns:
            str: The extracted content
        """
        if '### Response ###' in text:
            # Extract everything after the response marker
            content = text.split('### Response ###')[-1]
            # Remove any subsequent boundary markers
            content = re.split(r'###[^#]+###', content)[0]
            return content.strip()
        return text

    def generate_response(self, prompt: str, model: any = None, max_length: int = 2000) -> str:
        """
        Generates text response using Cloudflare worker running Llama model.
        """
        # Ensure prompt isn't too long
        if len(prompt) > max_length:
            if get_verbose():
                warning(f"Prompt exceeds maximum length ({len(prompt)} > {max_length})")
            # Try to format it properly
            if "### Instruction ###" not in prompt:
                prompt = self.format_prompt(prompt, max_length=max_length)
        
        url = "https://mp-llm.drake-t.workers.dev/"  # Text generation endpoint
        MAX_RETRIES = 3
        retry_count = 0
        
        while (retry_count < MAX_RETRIES):
            try:
                if get_verbose():
                    info("\n" + "="*50 + " REQUEST " + "="*50)
                    info(f"Attempt {retry_count + 1} of {MAX_RETRIES}")
                    info(f"URL: {url}")
                    info("\nPROMPT:")
                    info("-"*100)
                    info(prompt)
                    info("-"*100)
                
                response = requests.post(url, json={
                    "prompt": prompt,
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "stop": ["###"]
                })
                
                if get_verbose():
                    info("\nRESPONSE:")
                    info("-"*100)
                    info(f"Status: {response.status_code}")
                    info(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
                    info("\nContent:")
                    info(response.text)
                    info("-"*100)
                
                if response.status_code == 200:
                    if self.is_response_truncated(response.text):
                        if get_verbose():
                            warning("\nTRUNCATION DETECTED")
                            warning("Truncation indicators:")
                            if response.text.endswith(('...', '…')):
                                warning("- Ends with ellipsis")
                            if response.text.count('{') != response.text.count('}'):
                                warning("- Unmatched braces")
                            if response.text.count('"') % 2 != 0:
                                warning("- Unmatched quotes")
                            warning("\nTruncated response:")
                            warning(response.text)
                        retry_count += 1
                        continue
                    
                    content = self.extract_content_from_response(response.text)
                    content = self.extract_boundary_content(content)
                    
                    if get_verbose():
                        info("\nEXTRACTED CONTENT:")
                        info("-"*100)
                        info(content)
                        info("-"*100)
                        info(f"Content length: {len(content)} chars")
                    
                    if not content or len(content.strip()) < 10:
                        if get_verbose():
                            warning("\nContent too short or empty")
                            warning(f"Length: {len(content) if content else 0}")
                        retry_count += 1
                        continue
                        
                    return content.strip()
                    
                else:
                    if get_verbose():
                        error("\nREQUEST FAILED")
                        error(f"Status: {response.status_code}")
                        error(f"Content: {response.text}")
                    retry_count += 1
                    continue
                    
            except Exception as e:
                if get_verbose():
                    error("\nERROR OCCURRED")
                    error(f"Type: {type(e).__name__}")
                    error(f"Message: {str(e)}")
                    if hasattr(e, 'response'):
                        error(f"Response status: {e.response.status_code}")
                        error(f"Response content: {e.response.text}")
                retry_count += 1
                continue
                
        if get_verbose():
            error("\nALL RETRIES FAILED")
            error(f"Made {MAX_RETRIES} attempts")
            
        return None

    def format_prompt(self, content: str, example: str = None, max_length: int = 2000) -> str:
        """
        Format a prompt with clear boundaries to prevent truncation.
        
        Args:
            content (str): The prompt content
            example (str, optional): An example to include
            max_length (int): Maximum allowed prompt length
            
        Returns:
            str: The formatted prompt
        """
        prompt = f"""### Instruction ###
{content.strip()}

### Format ###
- Return raw text only
- No metadata or markup
- No quotes unless part of content
- Must be complete (no trailing ellipsis)
"""
        
        if example:
            prompt += f"""
### Example ###
{example.strip()}
"""
            
        prompt += """
### Response ###
"""

        # If prompt is too long, try to shorten it
        if len(prompt) > max_length:
            if get_verbose():
                warning(f"Prompt too long ({len(prompt)} chars), truncating...")
            
            # Try to preserve the most important parts
            lines = content.split('\n')
            shortened_content = '\n'.join(lines[:5])  # Keep first 5 lines
            
            # Rebuild prompt with shortened content
            prompt = f"""### Instruction ###
{shortened_content.strip()}

### Format ###
- Return raw text only
- No metadata
- Must be complete
"""
            if example:
                prompt += f"""
### Example ###
{example.split('.')[0]}.
"""
                
            prompt += """
### Response ###
"""
            
            if get_verbose():
                info(f"Shortened prompt length: {len(prompt)} chars")
                
        return prompt

    def generate_topic(self) -> str:
        """
        Generates a topic based on the YouTube Channel niche.
        """
        prompt = self.format_prompt(
            f"""Create ONE engaging video topic about: {self.niche}

Rules:
- One complete sentence only
- Must end with . ! or ?
- No conjunctions at end
- Specific and detailed
- Under 200 chars""",
            "A quantum computing experiment accidentally opens a gateway to a parallel dimension, unleashing a terrifying entity that exists beyond the laws of physics."
        )
        
        completion = self.generate_response(prompt)

        if not completion:
            error("The generated topic is empty.")
            return None

        # Extract and clean up the topic
        topic = completion.strip()
        if isinstance(topic, str):
            try:
                data = json.loads(topic)
                if isinstance(data, dict) and "response" in data:
                    topic = data["response"]
            except json.JSONDecodeError:
                pass

        topic = re.sub(r'^["\']+|["\']+$', '', topic)  # Remove quotes at start/end only
        
        # Basic validation
        if len(topic) > 200:
            if get_verbose():
                warning(f"Topic too long ({len(topic)} chars), truncating...")
            topic = topic[:197] + "..."
                
        # Must be a complete sentence
        if not any(topic.endswith(x) for x in ['.', '!', '?']):
            topic += "."
                
        # Must start with capital letter
        if topic and not topic[0].isupper():
            topic = topic[0].upper() + topic[1:]
        
        # Topic looks good
        self.subject = topic
        if get_verbose():
            info(f"Generated topic: {topic}")
        return topic

    def is_complete_sentence(self, text: str) -> bool:
        """
        Checks if a piece of text forms a complete, natural-sounding sentence.
        
        Args:
            text (str): The text to check
            
        Returns:
            bool: True if the text appears to be a complete sentence
        """
        # Basic cleanup
        text = text.strip()
        if not text:
            return False
            
        # Must have enough words for a complete thought
        words = [w for w in text.split() if w.strip()]
        if len(words) < 5:  # Need at least subject, verb, and some context
            return False
            
        # Must end with proper punctuation
        if not text.endswith(('.', '!', '?')):
            return False
            
        # Check for sentence fragments or common speech patterns to avoid
        bad_starts = [
            'and ', 'but ', 'or ', 'because ', 'however ', 'whereas ',
            'while ', 'although ', 'unless ', 'since ', 'despite ',
            'therefore ', 'thus ', 'hence ', 'consequently '
        ]
        text_lower = text.lower()
        if any(text_lower.startswith(start) for start in bad_starts):
            return False
            
        # Check for natural speech cadence
        words_lower = [w.lower() for w in words]
        speech_patterns = ['um', 'uh', 'er', 'like', 'y\'know']
        if any(w in speech_patterns for w in words_lower):
            return False
            
        # Should have both a subject and a verb
        has_subject = any(w.lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those'] for w in words_lower[:3])
        has_verb = any(w.lower().endswith(('s', 'ed', 'ing')) for w in words_lower)
        
        return has_subject and has_verb

    def get_sentence_starter(self, sentence: str) -> str:
        """
        Get the meaningful starter word of a sentence, ignoring articles and common prepositions.
        
        Args:
            sentence (str): The sentence to analyze
            
        Returns:
            str: The meaningful starter word
        """
        # Get first actual word
        words = re.findall(r'\b\w+\b', sentence.lower())
        if not words:
            return ""
            
        # Skip articles and common prepositions
        skip_words = {'a', 'an', 'the', 'in', 'on', 'at', 'by', 'to', 'for', 'with', 'from'}
        
        # Look at first 3 words to find meaningful starter
        for word in words[:3]:
            if word not in skip_words:
                return word
                
        # If we only found skip words, use the first word
        return words[0]

    def validate_script(self, script: str) -> bool:
        """
        Validates that a script meets our specific requirements for a YouTube Short.
        Collects warnings for minor issues instead of failing immediately.
        
        Args:
            script (str): The script to validate
            
        Returns:
            bool: True if the script meets minimum requirements
        """
        def add_warning(msg: str, details: str = None) -> None:
            warning_msg = f"⚠️ {msg}"
            if details:
                warning_msg += f"\n{details}"
            self.warnings.append(warning_msg)
            if get_verbose():
                warning(warning_msg)

        # Extract and normalize content
        try:
            data = json.loads(script)
            if isinstance(data, dict) and "response" in data:
                script = data["response"]
        except json.JSONDecodeError:
            pass
        
        lines = [line.strip() for line in script.split('\n') if line.strip()]
        sentences = []
        
        for line in lines:
            # Clean up line (same as before)
            line = re.sub(r'"[^"]*"', '', line)
            line = re.sub(r"'[^']*'", '', line)
            line = re.sub(r'\([^)]*\)', '', line)
            line = re.sub(r'\[[^\]]*\]', '', line)
            line = line.strip()
            
            if not line or len(line.split()) < 5:
                continue
                
            if not line.endswith(('.', '!', '?')):
                line += '.'
                
            sentences.append(line)
        
        # Remove duplicates
        seen = set()
        sentences = [s for s in sentences if not (s in seen or seen.add(s))]
        
        # Critical checks that must pass
        if len(sentences) < 8:  # Reduced minimum from 10
            error("Script has too few sentences (minimum 8 required)")
            return False
            
        if len(sentences) > 15:  # Increased maximum from 12
            error("Script has too many sentences (maximum 15 allowed)")
            return False
        
        def count_words(text: str) -> int:
            return len([w for w in re.findall(r"[a-zA-Z0-9]+(?:[-'][a-zA-Z0-9]+)*", text.lower())])
        
        total_words = sum(count_words(s) for s in sentences)
        
        # Collect warnings instead of failing for minor issues
        if len(sentences) < 10 or len(sentences) > 12:
            add_warning(
                f"Script has {len(sentences)} sentences (recommended: 10-12)",
                "This may affect video pacing"
            )
            
        if total_words < 150 or total_words > 250:
            add_warning(
                f"Script has {total_words} words (recommended: 150-250)",
                f"Average words per sentence: {total_words/len(sentences):.1f}"
            )
        
        seen_starters = {}
        for i, sentence in enumerate(sentences, 1):
            word_count = count_words(sentence)
            if word_count < 8 or word_count > 25:  # Relaxed limits
                add_warning(
                    f"Sentence {i} has {word_count} words (recommended: 10-20)",
                    f"Sentence: {sentence}"
                )
            
            # Still check for critical issues
            if re.search(r'\b(INT\.|EXT\.|FADE |CUT TO|SCENE)\b', sentence, re.IGNORECASE):
                error("Contains screenplay formatting")
                return False
                
            if re.search(r'\b(I|me|my|mine|we|us|our)\b', sentence, re.IGNORECASE):
                error("Contains first-person narrative")
                return False
                
            if re.search(r'(?:[:"]|(?:\b(?:said|asked|replied|spoke|called|whispered|shouted)\b))', sentence, re.IGNORECASE):
                error("Contains dialogue")
                return False
            
            # Make sentence starters a warning instead of error
            starter = self.get_sentence_starter(sentence)
            if starter in seen_starters:
                add_warning(
                    f"Repeated sentence starter word: '{starter}'",
                    f"Used in sentences {seen_starters[starter]} and {i}"
                )
            seen_starters[starter] = i
                    
        if get_verbose():
            info(f"\nScript validation complete:")
            info(f"- {len(sentences)} sentences")
            info(f"- {total_words} total words")
            info(f"- {len(self.warnings)} minor issues found")
            
        return True

    def extract_text_from_json(self, json_data) -> str:
        """
        Recursively extract text content from nested JSON structures while preserving newlines.
        
        Args:
            json_data: The JSON data to extract text from
            
        Returns:
            str: The extracted text content with newlines preserved
        """
        if isinstance(json_data, str):
            # If it looks like JSON, try to parse it
            if json_data.strip().startswith('{') or json_data.strip().startswith('['):
                try:
                    parsed = json.loads(json_data)
                    return self.extract_text_from_json(parsed)
                except json.JSONDecodeError:
                    pass
            # Preserve newlines by replacing escaped newlines
            text = json_data.strip('"\'')
            text = text.replace('\\n', '\n')
            text = text.replace('\\r', '\n')
            return text
        elif isinstance(json_data, dict):
            # Try common field names for the content
            for key in ['response', 'content', 'text', 'result', 'output']:
                if key in json_data:
                    return self.extract_text_from_json(json_data[key])
            # If no known fields, try all string values
            for value in json_data.values():
                if isinstance(value, str) and len(value) > 20:
                    return self.extract_text_from_json(value)
        elif isinstance(json_data, list):
            # If it's a list, join all string items with newlines
            texts = []
            for item in json_data:
                if item:
                    text = self.extract_text_from_json(item)
                    if text:
                        texts.append(text)
            return '\n'.join(texts)
        return ""

    def clean_script(self, script: str) -> str:
        """
        Clean and normalize a script before validation.
        Preserves newline-separated sentence structure from LLM output.
        
        Args:
            script (str): The raw script to clean
            
        Returns:
            str: The cleaned script with one sentence per line
        """
        # First extract from any JSON wrapper
        try:
            data = json.loads(script)
            if isinstance(data, dict) and "response" in data:
                script = data["response"]
        except json.JSONDecodeError:
            pass
            
        # Normalize line endings
        script = script.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split on newlines to preserve sentence structure
        lines = [line.strip() for line in script.split('\n') if line.strip()]
        
        # Process each line
        sentences = []
        for line in lines:
            # Remove any metadata markers
            line = re.sub(r'^.*?###\s*Response\s*###\s*', '', line, flags=re.I)
            line = re.sub(r'###.*?$', '', line)
            
            # Basic cleanup
            line = re.sub(r'\s+', ' ', line).strip()
            
            # Skip if too short
            if len(line.split()) < 5:
                continue
                
            # Ensure proper sentence ending
            if not line.endswith(('.', '!', '?')):
                line += '.'
                
            sentences.append(line)
                
        # Remove any exact duplicates while preserving order
        seen = set()
        sentences = [s for s in sentences if not (s in seen or seen.add(s))]
        
        # Join with newlines to maintain separation
        script = '\n'.join(sentences)
        
        if get_verbose():
            info("\nCleaned sentences:")
            for i, s in enumerate(sentences, 1):
                info(f"{i}. {s}")
        
        return script

    def generate_script(self) -> str:
        """
        Generates a focused narrative script suitable for a YouTube Short.
        
        Returns:
            str: The generated script, or None if generation failed
        """
        MAX_RETRIES = 5
        retry_count = 0
        seen_scripts = set()

        while retry_count < MAX_RETRIES:
            # Clean up subject
            clean_subject = self.extract_text_from_json(self.subject)

            if retry_count > 0 and get_verbose():
                info(f"\nRetry {retry_count + 1} of {MAX_RETRIES}")

            prompt = f"""Write a dark atmospheric script about: {clean_subject}

FORMAT:
1. Write EXACTLY 10-12 lines of text
2. Put each line on its own row with a line break
3. Each line must be ONE complete sentence
4. Each sentence must end with . ! or ?
5. NO blank lines between sentences
6. Return ONLY the sentences, one per line

SENTENCE RULES:
1. Length: 10-20 words each
2. Style: Can use similes with "like" or "as"
3. Structure: One clear action or image per line
4. Flow: Each line connects to next
5. Variety: Each line starts differently

CONTENT:
- Rich sensory details
- Vivid visual imagery
- Mounting tension
- Atmospheric mood
- Strong resolution

AVOID:
- Starting with "The"
- Using I/we/us/our
- Dialogue or quotes
- Compound sentences
- Character names
- Semicolons

STRUCTURE:
Lines 1-2: Set striking scene
Lines 3-4: Add atmosphere
Lines 5-7: Build tension
Lines 8-9: Peak intensity
Lines 10-12: Dark resolution

STRONG STARTERS TO USE:
Glowing, Darkness, Shadows, Deep, Strange,
Ghostly, Beyond, Through, Within, Suddenly,
Twisted, Shattered, Distant, Beneath, Ancient,
Crimson, Massive, Swirling, Pulsing, Hollow

Remember: One complete sentence per line, separated by line breaks.
Return ONLY the sentences, no formatting or metadata."""

            completion = self.generate_response(prompt)
            
            if not completion:
                retry_count += 1
                continue
                
            # Clean up and normalize the script
            script = self.clean_script(completion)
            
            # Basic validation
            if not script or len(script) < 100:
                if get_verbose():
                    warning("Script too short, retrying...")
                retry_count += 1
                continue
                
            # Don't process duplicate scripts
            script_hash = hashlib.md5(script.encode()).hexdigest()
            if script_hash in seen_scripts:
                if get_verbose():
                    warning("Generated duplicate script, retrying...")
                retry_count += 1
                continue
                
            seen_starters = set()
            
            # Validate the script
            if self.validate_script(script):
                if get_verbose():
                    success(f"Generated valid script: {len(script)} chars")
                    info(script)
                self.script = script
                return script
            
            retry_count += 1

        # If we get here, we've exceeded our retry limit
        if get_verbose():
            error(f"Failed to generate valid script after {MAX_RETRIES} attempts")
        return None

    def generate_metadata(self) -> dict:
        """
        Generates Video metadata for the to-be-uploaded YouTube Short.
        """
        MAX_TITLE_ATTEMPTS = 3
        for attempt in range(MAX_TITLE_ATTEMPTS):
            # Simpler, more direct prompt
            prompt = self.format_prompt(
                f"""TASK: Create a short title with hashtags for YouTube Shorts
TOPIC: {self.subject}

REQUIREMENTS:
1. Title + 2-3 hashtags
2. Max 80 characters total
3. No quotes or special marks
4. No punctuation at end
5. Make it catchy

DESIRED FORMAT:
<Title Text> #Tag1 #Tag2

END REQUIREMENTS""",
                "Cosmic Horror Rises #Horror #SciFi #Multiverse"
            )
            
            title_response = self.generate_response(prompt)
            if not title_response:
                if get_verbose():
                    warning(f"Title attempt {attempt + 1} failed")
                continue
                
            # Clean up title
            title = title_response.strip()
            title = re.sub(r'^["\']+|["\']+$', '', title)  # Remove quotes
            title = re.sub(r'[\.,!?]+$', '', title)  # Remove trailing punctuation
            
            # Safety check - ensure we have hashtags
            if '#' not in title:
                title += " #Horror #SciFi #Cosmic"
                
            # Enforce length limit
            if len(title) > 100:
                # Try to truncate at a hashtag
                parts = title.split('#')
                title = parts[0].strip()
                # Add back minimum hashtags
                title += " #Horror #SciFi"
            
            if get_verbose():
                info(f"Title attempt {attempt + 1}: {title}")
                info(f"Length: {len(title)} chars")
                
            if len(title) <= 100 and '#' in title:
                break
                
            if get_verbose():
                warning("Title validation failed, retrying...")
        else:
            if get_verbose():
                warning("Using fallback title after all attempts failed")
            # Use a safe fallback title if all attempts fail
            title = f"Cosmic Horror Unleashed #Horror #SciFi"
            
        # Generate description with direct prompt for clarity
        desc_prompt = f"""Write a YouTube Shorts description:

CONTENT:
{self.script}

FORMAT:
2-3 short paragraphs + hashtags

RULES:
- Max 400 chars total
- Add 3-5 hashtags at end
- Keep it engaging
- No formatting marks
- No quotes

Return ONLY the description text."""

        description_response = self.generate_response(desc_prompt)
        
        if not description_response:
            error("Failed to generate description")
            return None
            
        # Clean up description
        description = description_response.strip()
        description = re.sub(r'^["\']+|["\']+$', '', description)
        description = re.sub(r'\.+$', '.', description)  # Fix multiple periods
        
        if get_verbose():
            info(f"Generated description ({len(description)} chars):\n{description}")
        
        if len(description) > 500:
            if get_verbose():
                warning("Description too long, truncating at sentence boundary...")
            # Try to truncate at a sentence boundary
            sentences = re.split(r'[.!?]+', description)
            description = ""
            for sentence in sentences:
                if len(description + sentence) > 450:
                    break
                description += sentence.strip() + ". "
            description = description.strip()
            # Add hashtags if they were cut off
            if '#' not in description:
                description += "\n\n#Horror #SciFi #Multiverse"
        
        metadata = {
            "title": title,
            "description": description
        }
        
        if get_verbose():
            info("Final metadata:")
            info(f"Title ({len(title)} chars): {title}")
            info(f"Description ({len(description)} chars):\n{description}")
        
        self.metadata = metadata
        return metadata

    def parse_image_prompts(self, completion: str) -> List[str]:
        """
        Parse image prompts from various possible formats with fallback methods.
        
        Args:
            completion (str): Raw completion from LLM
            
        Returns:
            List[str]: List of valid image prompts
        """
        prompts = []
        
        # Method 1: Try parsing as JSON array
        try:
            if isinstance(completion, str):
                # Clean up the string for JSON parsing
                clean_json = (completion.strip()
                            .replace('\n', '')
                            .replace('""', '"')
                            .strip('"'))
                            
                if not clean_json.startswith('['):
                    clean_json = f"[{clean_json}"
                if not clean_json.endswith(']'):
                    clean_json = f"{clean_json}]"
                    
                data = json.loads(clean_json)
                if isinstance(data, list):
                    # Clean each prompt individually
                    for prompt in data:
                        if isinstance(prompt, str) and len(prompt.strip()) > 20:
                            # Remove any list formatting artifacts and quotes
                            clean_prompt = re.sub(r'^[\'"[\s]*|[\'"]\s*,\s*[\'"]|\s*[\'"]\s*$', '', prompt.strip())
                            prompts.append(clean_prompt)
        except:
            if get_verbose():
                warning("JSON parsing failed, trying alternative methods")
        
        # Method 2: Try extracting from string list format
        if not prompts:
            try:
                # Match anything that looks like a list item
                items = re.findall(r'(?:^|\n)(?:\d+\.|[-•*]\s*|"\s*|\'|\[|\s+)([^"\'\[\]\n]+?)(?:"|\'|\]|$)', completion)
                for item in items:
                    clean_item = re.sub(r'^[\'"[\s]*|[\'"]\s*,\s*[\'"]|\s*[\'"]\s*$', '', item.strip())
                    if len(clean_item) > 20:
                        prompts.append(clean_item)
            except:
                if get_verbose():
                    warning("String list parsing failed, trying basic line split")
        
        # Method 3: Basic line splitting as last resort
        if not prompts:
            try:
                lines = [line.strip('"\' []') for line in completion.split('\n')]
                for line in lines:
                    clean_line = re.sub(r'^[\'"[\s]*|[\'"]\s*,\s*[\'"]|\s*[\'"]\s*$', '', line.strip())
                    if len(clean_line) > 20:
                        prompts.append(clean_line)
            except:
                if get_verbose():
                    warning("Basic line split parsing failed")
        
        # Deduplicate while preserving order
        seen = set()
        prompts = [p for p in prompts if not (p in seen or seen.add(p))]
        
        if get_verbose():
            info(f"Parsed {len(prompts)} prompts using {'JSON' if prompts else 'fallback'} method")
            
        return prompts

    def generate_prompts(self) -> List[str]:
        """
        Generates AI Image Prompts based on the provided Video Script.

        Returns:
            image_prompts (List[str]): Generated List of image prompts.
        """
        # Calculate number of prompts based on target video length
        n_prompts = max(12, min(36, len(self.script.split('.')) * 2))  # Between 12-36 images
        
        MAX_RETRIES = 3
        retry_count = 0
        image_prompts = []  # Initialize empty list
        
        while retry_count < MAX_RETRIES:
            prompt = f"""Generate {n_prompts} separate cinematic image prompts based on this topic: {self.subject}

RULES:
1. Return as a proper JSON array
2. One scene per prompt
3. Each prompt must be complete on its own
4. No numbering or bullet points
5. Include mood and lighting details
6. Keep each prompt under 200 characters

OUTPUT FORMAT:
[
  "First complete image prompt",
  "Second complete image prompt",
  "Third complete image prompt"
]

STYLE GUIDE:
- Vivid scene descriptions
- Cinematic composition
- Atmospheric lighting
- Focus on visual elements
- No character names
- No dialogue"""

            completion = self.generate_response(prompt)
            if not completion:
                retry_count += 1
                continue

            # Parse prompts with new method
            parsed_prompts = self.parse_image_prompts(completion)
            if parsed_prompts:
                image_prompts = parsed_prompts
                break
                
            retry_count += 1
            time.sleep(1)  # Short delay between retries

        # If we still don't have valid prompts after retries, use fallbacks
        if not image_prompts:
            if get_verbose():
                warning("No valid prompts generated after retries, using fallback prompts")
            # Generate some basic prompts based on the subject
            image_prompts = [
                f"{self.subject}, dramatic cinematic shot",
                f"{self.subject}, closeup detailed view",
                f"{self.subject}, wide establishing shot",
                f"{self.subject}, abstract artistic view",
                f"{self.subject}, high contrast scene",
                f"{self.subject}, emotional moment",
            ] * 3  # Repeat to get enough prompts

        # Ensure each prompt is complete and well-formed
        cleaned_prompts = []
        for prompt in image_prompts:
            # Remove any trailing quotes or commas
            prompt = prompt.strip().rstrip('",').strip('"\'')
            # Skip if too short
            if len(prompt) < 20:
                continue
            # Add cinematic style if not present
            if "cinematic" not in prompt.lower():
                prompt += ", cinematic style"
            # Add to cleaned list
            cleaned_prompts.append(prompt)
            
        image_prompts = cleaned_prompts

        # Ensure we have the right number of prompts
        if len(image_prompts) < n_prompts:
            if get_verbose():
                warning(f"Only got {len(image_prompts)} prompts, padding to {n_prompts}")
            # Pad with variations of existing prompts
            while len(image_prompts) < n_prompts:
                idx = len(image_prompts) % len(image_prompts)
                base_prompt = image_prompts[idx]
                # Add slight variations
                variations = [
                    ", different angle",
                    ", alternative view",
                    ", different lighting",
                    ", different style",
                    ", different mood"
                ]
                variation = variations[len(image_prompts) % len(variations)]
                # Only add variation if it won't make prompt too long
                if len(base_prompt) + len(variation) <= 200:
                    image_prompts.append(base_prompt + variation)
                else:
                    image_prompts.append(base_prompt)
        elif len(image_prompts) > n_prompts:
            if get_verbose():
                warning(f"Got {len(image_prompts)} prompts, trimming to {n_prompts}")
            # Keep the most diverse prompts
            image_prompts = image_prompts[:n_prompts]

        # Remove any duplicates while preserving order
        seen = set()
        image_prompts = [x for x in image_prompts if not (x in seen or seen.add(x))]

        self.image_prompts = image_prompts

        if get_verbose():
            success(f"Generated {len(image_prompts)} Image Prompts")
            for i, prompt in enumerate(image_prompts, 1):
                info(f"{i}. {prompt}")

        return image_prompts

    def validate_image_prompt(self, prompt: str) -> str:
        """
        Validates and cleans an image prompt to ensure it's a single, complete prompt.
        
        Args:
            prompt (str): The prompt to validate
            
        Returns:
            str: Cleaned prompt if valid, None if invalid
        """
        if not prompt:
            return None
            
        # Clean up the prompt
        prompt = prompt.strip()
        prompt = re.sub(r'^[\'"[\s]*|[\'"]\s*,\s*[\'"]|\s*[\'"]\s*$', '', prompt)
        
        # Check for invalid characters that might indicate multiple prompts
        if any(c in prompt for c in ['[', ']', '{', '}', '"', "'"]):
            if get_verbose():
                warning(f"Found invalid characters in prompt, cleaning: {prompt}")
            # Try to extract just the first complete prompt
            parts = re.split(r'["\'\[\]{}]', prompt)
            parts = [p.strip() for p in parts if len(p.strip()) > 20]
            if not parts:
                return None
            prompt = parts[0]
            
        # Check for common separators that might indicate multiple prompts
        if any(sep in prompt for sep in [', and', '; and', ' and ', ' then ']):
            if get_verbose():
                warning(f"Found potential prompt separator, splitting: {prompt}")
            # Take only the first complete part
            for sep in [', and', '; and', ' and ', ' then ']:
                if sep in prompt:
                    prompt = prompt.split(sep)[0]
                    
        # Enforce length limits
        if len(prompt) < 20:
            if get_verbose():
                warning(f"Prompt too short: {prompt}")
            return None
            
        if len(prompt) > 500:
            if get_verbose():
                warning(f"Prompt too long ({len(prompt)} chars), truncating")
            prompt = prompt[:497] + "..."
            
        # Add style keywords if missing
        style_keywords = ["cinematic", "dramatic", "detailed", "professional"]
        if not any(word in prompt.lower() for word in style_keywords):
            prompt += ", cinematic style, dramatic lighting"
            
        return prompt

    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the given prompt.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        # Validate and clean the prompt
        prompt = self.validate_image_prompt(prompt)
        if not prompt:
            error("Invalid image prompt")
            return None

        if get_verbose():
            info(f"Generating Image with prompt: {prompt}")

        # Use the dedicated image generation endpoint
        worker_url = "https://mp-image-gen.drake-t.workers.dev"

        if not worker_url:
            error("Image generation worker URL not configured")
            return None

        # Ensure the prompt is properly URL encoded
        encoded_prompt = requests.utils.quote(prompt)
        url = f"{worker_url}?prompt={encoded_prompt}&model=sdxl"

        MAX_RETRIES = 3
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            try:
                if get_verbose():
                    info(f"Requesting image generation (attempt {retry_count + 1}/{MAX_RETRIES})")
                
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Save the image
                    image_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".png")
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    
                    if os.path.exists(image_path) and os.path.getsize(image_path) > 1000:
                        if get_verbose():
                            info(f"Generated image saved to: {image_path}")
                        return image_path
                    else:
                        if get_verbose():
                            warning("Generated image file is invalid or too small")
                else:
                    if get_verbose():
                        warning(f"Image generation failed with status {response.status_code}")
                
            except Exception as e:
                if get_verbose():
                    warning(f"Error generating image: {str(e)}")
            
            retry_count += 1
            if retry_count < MAX_RETRIES:
                time.sleep(2 * retry_count)  # Exponential backoff
        
        # If we get here, all retries failed
        if get_verbose():
            error(f"Failed to generate image after {MAX_RETRIES} attempts")
        return None

    def generate_script_to_speech(self, tts_instance: TTS) -> str:
        """
        Converts the generated script into Speech using CoquiTTS and returns the path to the wav file.

        Args:
            tts_instance (tts): Instance of TTS Class.

        Returns:
            path_to_wav (str): Path to generated audio (WAV Format), or None if generation fails.
        """
        if not self.script:
            if get_verbose():
                error("No script available for TTS generation")
            return None

        # Clean script of special characters while preserving sentence structure
        cleaned_script = re.sub(r'[^\w\s.!?,]', '', self.script)
        cleaned_script = re.sub(r'\s+', ' ', cleaned_script).strip()

        if not cleaned_script:
            if get_verbose():
                error("Script is empty after cleaning")
            return None

        path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".wav")
        
        try:
            # Generate the speech
            if get_verbose():
                info("Generating TTS audio...")
                info(f"Script length: {len(cleaned_script)} chars")
                info(f"Output path: {path}")
                
            tts_instance.synthesize(cleaned_script, path)

            # Validate the generated audio with our new helper
            if not self.validate_audio_file(path):
                if get_verbose():
                    error("Generated audio failed validation")
                if os.path.exists(path):
                    os.remove(path)
                return None

            self.tts_path = path
            return path

        except Exception as e:
            if get_verbose():
                error(f"TTS generation failed: {str(e)}")
            if os.path.exists(path):
                os.remove(path)
            return None

    def add_video(self, video: dict) -> None:
        """
        Adds a video to the cache.

        Args:
            video (dict): The video to add

        Returns:
            None
        """
        videos = self.get_videos()
        videos.append(video)

        cache = get_youtube_cache_path()

        with open(cache, "r") as file:
            previous_json = json.loads(file.read())
            
            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    account["videos"].append(video)
            
            # Commit changes
            with open(cache, "w") as f:
                f.write(json.dumps(previous_json))

    def generate_subtitles(self, audio_path: str) -> str:
        """
        Generates subtitles for the audio using AssemblyAI.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            path (str): The path to the generated SRT File.
        """
        # Turn the video into audio
        aai.settings.api_key = get_assemblyai_api_key()
        config = aai.TranscriptionConfig()
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_path)
        subtitles = transcript.export_subtitles_srt()

        srt_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".srt")

        with open(srt_path, "w") as file:
            file.write(subtitles)

        return srt_path

    def archive_video(self, video_path: str) -> str:
        """
        Archives the video and its metadata to the archive directory.
        
        Args:
            video_path (str): Path to the video file to archive
            
        Returns:
            str: Path to the archived video file
        """
        # Create archive directory if it doesn't exist
        archive_dir = os.path.join(ROOT_DIR, "archive")
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
            
        # Create a timestamped subdirectory for this video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(x for x in self.metadata['title'] if x.isalnum() or x in (' ', '-', '_'))[:50]
        video_dir = os.path.join(archive_dir, f"{timestamp}_{safe_title}")
        os.makedirs(video_dir)
        
        # Copy video file
        video_ext = os.path.splitext(video_path)[1]
        archived_video_path = os.path.join(video_dir, f"video{video_ext}")
        import shutil
        shutil.copy2(video_path, archived_video_path)
        
        # Save metadata
        metadata_path = os.path.join(video_dir, "metadata.txt")
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write("YouTube Short Metadata\n")
                f.write("===================\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Title: {self.metadata['title']}\n\n")
                f.write(f"Description:\n{self.metadata['description']}\n")
                if self.script:
                    f.write(f"\nScript:\n{self.script}\n")
        except Exception as e:
            if get_verbose():
                warning(f"Failed to save metadata: {str(e)}")
                
        return archived_video_path

    def combine(self) -> str:
        """
        Combines everything into the final video with smooth transitions.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        # First check if we have enough valid images
        valid_images = []
        for img_path in self.images:
            if os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
                valid_images.append(img_path)
            elif get_verbose():
                warning(f"Skipping invalid or missing image: {img_path}")

        if len(valid_images) < 3:  # Minimum required for a decent video
            error(f"Not enough valid images to create video. Only have {len(valid_images)} valid images")
            return None

        output_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".mp4")
        threads = get_threads()
        
        # Verify audio file exists and is valid
        if not os.path.exists(self.tts_path):
            error("TTS audio file is missing")
            return None
            
        try:
            # Load and validate audio
            if get_verbose():
                info("Loading TTS audio...")
            try:
                tts_clip = AudioFileClip(self.tts_path)
                # Force audio loading to verify it works
                tts_clip.to_soundarray()
                max_duration = tts_clip.duration
                
                if max_duration < 0.1:
                    error("TTS audio is too short")
                    return None
                    
                if get_verbose():
                    info(f"Loaded TTS audio: {max_duration:.2f} seconds")
                    
            except Exception as e:
                error(f"Failed to load TTS audio: {str(e)}")
                return None
            
            # Calculate image duration to distribute them evenly across the video
            # but ensure each image shows for at least 3 seconds
            base_duration = max(3, max_duration / len(valid_images))

            if get_verbose():
                info(f"Base duration per image: {base_duration:.2f} seconds")

            # Make a generator that returns a TextClip when called
            text_generator = lambda txt: TextClip(
                txt,
                font=os.path.join(get_fonts_dir(), get_font()),
                fontsize=100,
                color="#FFFF00",
                stroke_color="black",
                stroke_width=5,
                size=(1080, 1920),
                method="caption",
            )

            if get_verbose():
                info("Combining images...")

            clips = []
            tot_dur = 0
            
            # Process each image and add transitions
            for idx, image_path in enumerate(valid_images):
                try:
                    clip = ImageClip(image_path)
                    clip = clip.set_duration(base_duration)
                    clip = clip.set_fps(30)

                    # Resize logic
                    if round((clip.w/clip.h), 4) < 0.5625:
                        if get_verbose():
                            info(f"Image {idx+1}: Portrait - cropping width")
                        clip = crop(clip, width=clip.w, height=round(clip.w/0.5625),
                                  x_center=clip.w / 2,
                                  y_center=clip.h / 2)
                    else:
                        if get_verbose():
                            info(f"Image {idx+1}: Landscape - cropping height")
                        clip = crop(clip, width=round(0.5625*clip.h), height=clip.h,
                                  x_center=clip.w / 2,
                                  y_center=clip.h / 2)
                    clip = clip.resize((1080, 1920))

                    # Add fade transitions
                    clip = clip.fadein(0.5)
                    clip = clip.fadeout(0.5)

                    # Add subtle zoom effect
                    clip = clip.resize(lambda t: 1 + 0.04 * t/clip.duration)

                    clips.append(clip)
                    tot_dur += clip.duration
                    
                except Exception as e:
                    if get_verbose():
                        warning(f"Failed to process image {image_path}: {str(e)}")
                    continue

            if not clips:
                error("No valid clips were created from images")
                return None

            try:
                # Combine all clips
                if get_verbose():
                    info("Concatenating video clips...")
                final_clip = concatenate_videoclips(clips, method="compose")
                final_clip = final_clip.set_fps(30)
                
                # Handle background music
                random_song = choose_random_song()
                if not os.path.exists(random_song):
                    warning("Background music file not found, continuing without music")
                    comp_audio = tts_clip
                else:
                    try:
                        if get_verbose():
                            info("Adding background music...")
                        random_song_clip = AudioFileClip(random_song)
                        # Calculate how many loops we need
                        song_duration = random_song_clip.duration
                        num_loops = int(np.ceil(max_duration / song_duration))
                        # Create looped audio by concatenating the clip with itself
                        looped_song = concatenate_audioclips([random_song_clip] * num_loops)
                        # Trim to exact duration needed
                        looped_song = looped_song.subclip(0, max_duration)
                        # Lower background volume (multiply amplitude by 0.1)
                        looped_song = looped_song.volumex(0.1)
                        
                        # Combine TTS with background music
                        comp_audio = CompositeAudioClip([
                            tts_clip,
                            looped_song
                        ])
                    except Exception as e:
                        if get_verbose():
                            warning(f"Failed to add background music: {str(e)}")
                        comp_audio = tts_clip

                # Set and validate audio
                if get_verbose():
                    info("Setting audio track...")
                final_clip = final_clip.set_audio(comp_audio)
                final_clip = final_clip.set_duration(max_duration)

                # Generate and add subtitles
                try:
                    if get_verbose():
                        info("Generating subtitles...")
                    subtitle_path = self.generate_subtitles(self.tts_path)
                    if subtitle_path and os.path.exists(subtitle_path):
                        equalize_subtitles(subtitle_path, 10)
                        subtitles = SubtitlesClip(subtitle_path, text_generator)
                        subtitles = subtitles.set_pos(("center", "center"))
                        final_clip = CompositeVideoClip([
                            final_clip,
                            subtitles
                        ])
                except Exception as e:
                    if get_verbose():
                        warning(f"Failed to add subtitles: {str(e)}")
                    # Continue without subtitles

                if get_verbose():
                    info("Writing final video file...")
                final_clip.write_videofile(
                    output_path, 
                    threads=threads,
                    fps=30, 
                    codec='libx264',
                    audio_codec='aac',
                    audio_fps=44100,
                    audio=True,  # Ensure audio is enabled
                    verbose=get_verbose(),
                    logger=None if not get_verbose() else 'bar'
                )

                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    if get_verbose():
                        success(f"Generated video: {output_path}")
                        info(f"Video size: {os.path.getsize(output_path)} bytes")
                        info(f"Duration: {max_duration:.2f} seconds")
                    # Archive the video before returning
                    archived_path = self.archive_video(output_path)
                    if get_verbose() and archived_path:
                        info(f"Video archived to: {archived_path}")
                    return output_path
                else:
                    error("Generated video file is invalid or too small")
                    return None

            except Exception as e:
                error(f"Error combining video: {str(e)}")
                if get_verbose():
                    error(f"Error type: {type(e).__name__}")
                    error(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
                return None
                
        except Exception as e:
            error(f"Error in combine: {str(e)}")
            return None

    def generate_video(self, tts_instance: TTS) -> str:
        """
        Generates a YouTube Short based on the provided niche and language.

        Args:
            tts_instance (TTS): Instance of TTS Class.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        try:
            # Only verify API if we're using it
            if self.using_api and not self.verify_api_access():
                error("YouTube API verification failed. Please check your credentials before generating video.")
                return None

            if get_verbose():
                info("Starting video generation process...")
                if self.using_api:
                    info("Using YouTube Data API for upload")
                else:
                    info("Using browser automation fallback")

            # Generate the Topic
            if get_verbose():
                info("Generating topic...")
            if not self.generate_topic():
                error("Failed to generate topic")
                return None

            # Generate the Script
            if get_verbose():
                info("Generating script...")
            if not self.generate_script():
                error("Failed to generate script")
                return None

            # Generate the Metadata
            if get_verbose():
                info("Generating metadata...")
            metadata = self.generate_metadata()
            if not metadata:
                error("Failed to generate metadata")
                return None

            # Export metadata as soon as it's generated
            self.export_metadata()

            # Generate the Image Prompts
            if get_verbose():
                info("Generating image prompts...")
            prompts = self.generate_prompts()
            if not prompts:
                error("Failed to generate image prompts")
                return None

            # Generate the Images
            if get_verbose():
                info(f"Generating {len(self.image_prompts)} images...")
            for prompt in self.image_prompts:
                image_path = self.generate_image(prompt)
                if not image_path:
                    warning(f"Failed to generate image for prompt: {prompt}")
                    continue
                self.images.append(image_path)

            if not self.images:
                error("No images were generated successfully")
                return None

            # Generate the TTS with enhanced error reporting
            if get_verbose():
                info("Generating text-to-speech...")
                info(f"Script length: {len(self.script)} chars")
                info(f"TTS model: {tts_instance._model_path}")
                
            tts_path = self.generate_script_to_speech(tts_instance)
            if not tts_path:
                error("Failed to generate text-to-speech")
                if get_verbose():
                    error("TTS Diagnostic Information:")
                    if hasattr(tts_instance, '_synthesizer'):
                        info(f"Synthesizer initialized: {tts_instance._synthesizer is not None}")
                        if tts_instance._synthesizer:
                            info(f"Model loaded: {hasattr(tts_instance._synthesizer, 'tts_model')}")
                            info(f"Sample rate: {getattr(tts_instance._synthesizer, 'output_sample_rate', 'unknown')}")
                    if self.script:
                        info(f"Script preview: {self.script[:100]}...")
                    if hasattr(self, 'tts_path') and self.tts_path:
                        if os.path.exists(self.tts_path):
                            info(f"TTS file exists but may be invalid: {self.tts_path}")
                            info(f"File size: {os.path.getsize(self.tts_path)} bytes")
                        else:
                            info("TTS file was not created")
                return None

            # Validate TTS audio before proceeding
            if not self.validate_audio_file(tts_path):
                error("Generated TTS audio failed validation")
                return None

            # Combine everything
            if get_verbose():
                info("Combining video...")
            path = self.combine()
            if not path:
                error("Failed to combine video")
                return None

            # Note: combine() now handles archiving the video automatically

            if get_verbose():
                success("Video generation complete!")

            self.video_path = os.path.abspath(path)
            return path
            
        except Exception as e:
            error(f"Error in generate_video: {str(e)}")
            error(f"Error type: {type(e).__name__}")
            error(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            if get_verbose():
                error(f"Stack trace: {traceback.format_exc()}")
            return None
    
    def get_channel_id(self) -> str:
        """
        Gets the Channel ID of the YouTube Account using the API.

        Returns:
            channel_id (str): The Channel ID.
        """
        try:
            youtube = self._get_authenticated_service()
            channels_response = youtube.channels().list(
                part='id',
                mine=True
            ).execute()

            if not channels_response.get('items'):
                error("No channels found for authenticated user")
                return None

            channel_id = channels_response['items'][0]['id']
            self.channel_id = channel_id
            if get_verbose():
                info(f"Retrieved channel ID: {channel_id}")

            return channel_id

        except HttpError as e:
            error(f"HTTP error retrieving channel ID: {e.resp.status} - {e.content}")
            return None
        except Exception as e:
            error(f"Error retrieving channel ID: {str(e)}")
            return None

    def cleanup_generated_content(self) -> None:
        """
        Cleans up all generated files for this video.
        """
        try:
            # Clean up images
            for img_path in self.images:
                if img_path and os.path.exists(img_path):
                    os.remove(img_path)
            
            # Clean up TTS audio
            if self.tts_path and os.path.exists(self.tts_path):
                os.remove(self.tts_path)
                
            # Clean up final video
            if self.video_path and os.path.exists(self.video_path):
                os.remove(self.video_path)
                
            # Reset instance variables
            self.images = []
            self.tts_path = None
            self.video_path = None
            
            # Close browser only if we were using it
            if self.browser and not self.using_api:
                try:
                    self.browser.quit()
                except Exception as e:
                    if get_verbose():
                        warning(f"Failed to close browser: {str(e)}")
            
            if get_verbose():
                info("Cleaned up all generated content")
                
        except Exception as e:
            if get_verbose():
                warning(f"Error during cleanup: {str(e)}")

    def export_metadata(self) -> str:
        """
        Exports video metadata to a text file in the metadata directory.
        
        Returns:
            str: Path to the metadata file
        """
        if not self.video_path or not self.metadata:
            return None
            
        # Create metadata directory if it doesn't exist
        metadata_dir = os.path.join(ROOT_DIR, "metadata")
        if not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir)
        
        # Create filename with timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(x for x in self.metadata['title'] if x.isalnum() or x in (' ', '-', '_'))[:50]
        metadata_filename = f"{timestamp}_{safe_title}.txt"
        metadata_path = os.path.join(metadata_dir, metadata_filename)
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write("YouTube Short Metadata\n")
                f.write("===================\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Title: {self.metadata['title']}\n\n")
                f.write(f"Description:\n{self.metadata['description']}\n")
                
            if get_verbose():
                info(f"Exported metadata to: {metadata_path}")
            return metadata_path
            
        except Exception as e:
            if get_verbose():
                warning(f"Failed to export metadata: {str(e)}")
            return None

    def _get_authenticated_service(self) -> any:
        """
        Get an authenticated YouTube API service instance using OAuth2.
        Uses client_secrets.json for authentication and stores credentials.
        
        Returns:
            googleapiclient.discovery.Resource: Authenticated YouTube API service
        """
        # If we already have a verified service, return it
        if self._youtube_service is not None:
            return self._youtube_service

        flow = flow_from_clientsecrets(
            self.CLIENT_SECRETS_FILE,
            scope=self.YOUTUBE_UPLOAD_SCOPE,
            message="Missing client secrets file"
        )

        storage = Storage(os.path.join(ROOT_DIR, ".mp", f"{self._account_uuid}-oauth2.json"))
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage)

        return build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION,
                    http=credentials.authorize(httplib2.Http()))

    def _resumable_upload(self, insert_request: any) -> str:
        """
        Implement resumable upload with exponential backoff strategy.
        Retries failed uploads using exponential backoff timing.
        
        Args:
            insert_request: YouTube API insert request object
            
        Returns:
            str: Uploaded video ID on success, None on failure
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                if get_verbose():
                    info("Uploading video file...")
                    
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        if get_verbose():
                            success(f"Video successfully uploaded with ID: {response['id']}")
                        return response['id']
                    else:
                        error("Upload failed with unexpected response")
                        return None
                        
            except HttpError as e:
                if e.resp.status in self.RETRIABLE_STATUS_CODES:
                    error = f"Retriable HTTP error {e.resp.status} occurred: {e.content}"
                else:
                    raise
                    
            except self.RETRIABLE_EXCEPTIONS as e:
                error = f"Retriable error occurred: {str(e)}"
                
            if error is not None:
                if get_verbose():
                    warning(error)
                retry += 1
                if retry > self.MAX_RETRIES:
                    error("No longer attempting to retry")
                    return None
                    
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                if get_verbose():
                    info(f"Sleeping {sleep_seconds} seconds before retry...")
                time.sleep(sleep_seconds)
                
        return None

    def upload_video(self) -> bool:
        try:
            if not os.path.exists(self.video_path):
                error("Video file does not exist")
                return False
                
            if get_verbose():
                info(f"Starting video upload: {self.video_path}")
                
            if self.using_api:
                # Use API upload path
                youtube = self._get_authenticated_service()
                
                # Prepare video metadata
                tags = []
                if "#" in self.metadata["title"]:
                    tags = [tag.strip() for tag in re.findall(r'#(\w+)', self.metadata["title"])]
                
                body = {
                    'snippet': {
                        'title': self.metadata["title"],
                        'description': self.metadata["description"],
                        'tags': tags,
                        'categoryId': "22"
                    },
                    'status': {
                        'privacyStatus': 'public',  # Changed from 'unlisted' to 'public'
                        'selfDeclaredMadeForKids': get_is_for_kids()
                    }
                }
                
                # Prepare upload request
                insert_request = youtube.videos().insert(
                    part=",".join(body.keys()),
                    body=body,
                    media_body=MediaFileUpload(
                        self.video_path, 
                        chunksize=-1,
                        resumable=True
                    )
                )
                
                video_id = self._resumable_upload(insert_request)
                
                if not video_id:
                    error("Failed to get video ID after upload")
                    return False
                    
                # Build video URL
                url = build_url(video_id)
                self.uploaded_video_url = url
                
                if get_verbose():
                    success(f"Video successfully uploaded: {url}")
                
                # Add to cache
                self.add_video({
                    "title": self.metadata["title"],
                    "description": self.metadata["description"],
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Export metadata
                self.export_metadata()

                # Sync video history after successful upload
                self.sync_video_history()
                
                return True
            else:
                error("Browser automation upload not implemented")
                return False
            
        except HttpError as e:
            error(f"HTTP error during upload: {e.resp.status} - {e.content}")
            return False
        except Exception as e:
            error(f"Error during upload: {str(e)}")
            return False

    def validate_audio_file(self, audio_path: str, min_duration: float = 1.0) -> bool:
        """
        Validates the generated audio file to ensure it meets minimum requirements.
        
        Args:
            audio_path (str): Path to the audio file to validate
            min_duration (float): Minimum required duration in seconds
            
        Returns:
            bool: True if the audio file is valid
        """
        if not os.path.exists(audio_path):
            if get_verbose():
                error(f"Audio file not found: {audio_path}")
            return False
            
        if os.path.getsize(audio_path) < 1024:  # Less than 1KB
            if get_verbose():
                error(f"Audio file too small: {os.path.getsize(audio_path)} bytes")
            return False
            
        try:
            # Try loading with scipy first
            try:
                sample_rate, data = wavfile.read(audio_path)
                if data.size == 0:
                    if get_verbose():
                        error("Audio file contains no data")
                    return False
                if np.max(np.abs(data)) == 0:
                    if get_verbose():
                        error("Audio file contains only silence")
                    return False
            except Exception as e:
                if get_verbose():
                    warning(f"scipy.io.wavfile failed: {str(e)}")
            
            # Also try with moviepy as a backup
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            
            if duration < min_duration:
                if get_verbose():
                    error(f"Audio duration too short: {duration:.2f}s < {min_duration}s")
                return False
                
            # Test that we can actually read the audio data
            array = audio.to_soundarray()
            if array.size == 0 or np.max(np.abs(array)) == 0:
                if get_verbose():
                    error("Audio contains no signal")
                return False
                
            if get_verbose():
                info(f"Audio file validated successfully:")
                info(f"- Duration: {duration:.2f}s")
                info(f"- File size: {os.path.getsize(audio_path)} bytes")
                info(f"- Sample rate: {getattr(audio, 'fps', None)} Hz")
                info(f"- Max amplitude: {np.max(np.abs(array)):.4f}")
                
            return True
            
        except Exception as e:
            if get_verbose():
                error(f"Audio validation failed: {str(e)}")
            return False

    def verify_api_access(self) -> bool:
        """
        Verifies that the YouTube API credentials are valid and working.
        
        Returns:
            bool: True if API access is verified, False otherwise
        """
        try:
            if get_verbose():
                info("Verifying YouTube API access...")

            if not os.path.exists(self.CLIENT_SECRETS_FILE):
                if get_verbose():
                    warning("No client_secrets.json found, API access not available")
                return False

            # Try to get authenticated service
            service = self._get_authenticated_service()
            
            # Test the service with a simple API call
            channels_response = service.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            if not channels_response.get('items'):
                error("No channels found for authenticated user")
                return False
                
            if get_verbose():
                success("YouTube API access verified successfully")
                
            # Store the service for reuse
            self._youtube_service = service
            self.using_api = True
            return True
            
        except HttpError as e:
            error(f"HTTP error during API verification: {e.resp.status} - {e.content}")
            return False
        except Exception as e:
            error(f"Error verifying API access: {str(e)}")
            return False

    def sync_video_history(self) -> bool:
        """
        Syncs the local video cache with the actual YouTube channel history.
        Fills in any missing videos and maintains reverse chronological order.
        
        Returns:
            bool: True if sync was successful, False otherwise
        """
        try:
            if not self.using_api:
                if get_verbose():
                    warning("Cannot sync video history without API access")
                return False

            if get_verbose():
                info("Syncing video history with YouTube channel...")

            # Get channel ID if we don't have it
            channel_id = self.get_channel_id()
            if not channel_id:
                error("Could not get channel ID")
                return False

            # Get videos from YouTube API
            youtube = self._get_authenticated_service()
            videos = []
            next_page_token = None

            while True:
                # Build request for video list
                request = youtube.search().list(
                    part="id,snippet",
                    channelId=channel_id,
                    maxResults=50,
                    order="date",
                    type="video",
                    pageToken=next_page_token
                )

                try:
                    response = request.execute()
                except HttpError as e:
                    error(f"HTTP error getting video list: {e.resp.status} - {e.content}")
                    return False

                # Process each video
                for item in response.get('items', []):
                    if item['id']['kind'] == 'youtube#video':
                        video_id = item['id']['videoId']
                        title = item['snippet']['title']
                        description = item['snippet']['description']
                        published_at = item['snippet']['publishedAt']

                        videos.append({
                            "title": title,
                            "description": description,
                            "url": build_url(video_id),
                            "date": datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
                        })

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            # Read current cache
            cache_path = get_youtube_cache_path()
            with open(cache_path, "r") as file:
                cache = json.loads(file.read())

            # Find our account in the cache
            for account in cache["accounts"]:
                if account["id"] == self._account_uuid:
                    # Get existing video URLs for deduplication
                    existing_urls = {v["url"] for v in account["videos"]}
                    
                    # Add new videos that aren't in cache
                    for video in videos:
                        if video["url"] not in existing_urls:
                            account["videos"].append(video)
                            if get_verbose():
                                info(f"Added missing video: {video['title']}")

                    # Sort all videos by date in reverse chronological order
                    account["videos"].sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"), reverse=True)
                    break

            # Save updated cache
            with open(cache_path, "w") as file:
                json.dump(cache, file, indent=2)

            if get_verbose():
                success("Video history sync complete")
                info(f"Total videos in cache: {len(videos)}")

            return True

        except Exception as e:
            error(f"Error syncing video history: {str(e)}")
            if get_verbose():
                error(f"Error type: {type(e).__name__}")
                error(f"Stack trace: {traceback.format_exc()}")
            return False
