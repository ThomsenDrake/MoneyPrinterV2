import os
import re
import json
import time
import hashlib
import requests
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

# Set ImageMagick Path
change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})

class YouTube:
    """
    Class for YouTube Automation.

    Steps to create a YouTube Short:
    1. Generate a topic [DONE]
    2. Generate a script [DONE]
    3. Generate metadata (Title, Description, Tags) [DONE]
    4. Generate AI Image Prompts [DONE]
    4. Generate Images based on generated Prompts [DONE]
    5. Convert Text-to-Speech [DONE]
    6. Show images each for n seconds, n: Duration of TTS / Amount of images [DONE]
    7. Combine Concatenated Images with the Text-to-Speech [DONE]
    """
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
        
        Args:
            script (str): The script to validate
            
        Returns:
            bool: True if the script meets all requirements
        """
        def format_error(msg: str, details: str = None) -> None:
            if get_verbose():
                error_msg = f"⚠️ {msg}"
                if details:
                    error_msg += f"\n{details}"
                warning(error_msg)

        # Extract and normalize content
        try:
            data = json.loads(script)
            if isinstance(data, dict) and "response" in data:
                script = data["response"]
        except json.JSONDecodeError:
            pass
        
        # First split on newlines to preserve intentional line breaks
        # This is critical for properly parsing the sentence structure
        lines = [line.strip() for line in script.split('\n') if line.strip()]
        
        # Process each line as a potential sentence
        sentences = []
        for line in lines:
            # Remove any dialogue or other unwanted elements
            line = re.sub(r'"[^"]*"', '', line)
            line = re.sub(r"'[^']*'", '', line)
            line = re.sub(r'\([^)]*\)', '', line)
            line = re.sub(r'\[[^\]]*\]', '', line)
            line = line.strip()
            
            # Skip empty lines or very short fragments
            if not line or len(line.split()) < 5:
                continue
                
            # Ensure proper sentence ending
            if not line.endswith(('.', '!', '?')):
                line += '.'
                
            sentences.append(line)
        
        # Remove any exact duplicates while preserving order
        seen = set()
        sentences = [s for s in sentences if not (s in seen or seen.add(s))]
        
        # Basic validations
        if len(sentences) < 10 or len(sentences) > 12:
            format_error(
                f"Script has {len(sentences)} sentences, must be 10-12",
                "Sentences found:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
            )
            return False
                
        # Word count validation using more accurate tokenization
        def count_words(text: str) -> int:
            # Count words but don't split on apostrophes or hyphens
            return len([w for w in re.findall(r"[a-zA-Z0-9]+(?:[-'][a-zA-Z0-9]+)*", text.lower())])
        
        total_words = sum(count_words(s) for s in sentences)
        if total_words < 150 or total_words > 250:
            format_error(
                f"Script has {total_words} words, must be 150-250",
                f"Average words per sentence: {total_words/len(sentences):.1f}"
            )
            return False
        
        # Validate each sentence
        seen_starters = {}
        for i, sentence in enumerate(sentences, 1):
            # Check sentence length
            word_count = count_words(sentence)
            if word_count < 10 or word_count > 20:
                format_error(
                    f"Sentence {i} has {word_count} words, must be 10-20",
                    f"Sentence: {sentence}"
                )
                return False
                
            # No screenplay formatting
            if re.search(r'\b(INT\.|EXT\.|FADE |CUT TO|SCENE)\b', sentence, re.IGNORECASE):
                format_error(
                    "Contains screenplay formatting",
                    f"Sentence {i}: {sentence}"
                )
                return False
                    
            # No first-person narrative
            if re.search(r'\b(I|me|my|mine|we|us|our)\b', sentence, re.IGNORECASE):
                format_error(
                    "Contains first-person narrative",
                    f"Sentence {i}: {sentence}"
                )
                return False
                    
            # No dialogue indicators
            if re.search(r'(?:[:"]|(?:\b(?:said|asked|replied|spoke|called|whispered|shouted)\b))', sentence, re.IGNORECASE):
                format_error(
                    "Contains dialogue",
                    f"Sentence {i}: {sentence}"
                )
                return False
            
            # Check for varied sentence starters
            starter = self.get_sentence_starter(sentence)
            if starter in seen_starters:
                prev_i = seen_starters[starter]
                format_error(
                    f"Repeated sentence starter word: '{starter}'",
                    f"First use in sentence {prev_i}: {sentences[prev_i-1]}\n" +
                    f"Repeated in sentence {i}: {sentence}"
                )
                return False
            seen_starters[starter] = i
                    
        if get_verbose():
            info(f"\nScript validation passed:")
            info(f"- {len(sentences)} sentences")
            info(f"- {total_words} total words")
            info(f"- Average {total_words/len(sentences):.1f} words per sentence")
            info("- All sentences start with different meaningful words")
            info("\nFinal validated sentences:")
            for i, s in enumerate(sentences, 1):
                info(f"{i}. {s}")
            
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

            prompt = f"""Write an engaging script about: {clean_subject}

FORMAT:
1. Write EXACTLY 10-12 lines of text
2. Put each line on its own row with a line break
3. Each line must be ONE complete sentence
4. Each sentence must end with . ! or ?
5. NO blank lines between sentences
6. Return ONLY the sentences, one per line

SENTENCE RULES:
1. Length: 10-20 words each
2. Style: Use vivid descriptive language with strong imagery
3. Structure: One clear concept or point per line
4. Flow: Each line builds on previous ones
5. Variety: Each line starts differently

CONTENT:
- Clear main message
- Engaging details
- Natural progression
- Memorable moments
- Strong conclusion

AVOID:
- Starting with "The"
- Using I/we/us/our
- Dialogue or quotes
- Compound sentences
- Character names
- Semicolons

STRUCTURE:
Lines 1-2: Introduce main concept
Lines 3-4: Build context
Lines 5-7: Develop key points
Lines 8-9: Present insights
Lines 10-12: Compelling conclusion

STRONG STARTERS TO USE:
Inside, Beyond, Through, Above, Below,
Every, Around, Across, Within, Among,
Moving, Growing, Rising, Deep, High,
Fresh, Bold, Swift, Pure, Clear,
Bright, Strong, Sure, True, Now

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
1. Title + 2-3 relevant hashtags
2. Max 80 characters total
3. No quotes or special marks
4. No punctuation at end
5. Make it catchy and engaging

DESIRED FORMAT:
<Title Text> #Tag1 #Tag2
""")
            
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
                # Extract relevant words from subject for hashtags
                keywords = [word.strip() for word in self.subject.split() 
                          if len(word.strip()) > 3 and word.strip().isalnum()]
                # Take up to 2 unique keywords for hashtags
                hashtags = list(set(keywords))[:2]
                title += f" #{hashtags[0].capitalize() if hashtags else 'Trending'}"
                title += f" #{hashtags[1].capitalize() if len(hashtags) > 1 else 'Viral'}"
            
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
            # Use a generic fallback title based on the subject
            clean_subject = self.subject.split('.')[0]  # Take first sentence if multiple
            if len(clean_subject) > 50:
                clean_subject = clean_subject[:47] + "..."
            title = f"{clean_subject} #Trending #Viral"
            
        # Generate description with direct prompt for clarity
        desc_prompt = f"""Write a YouTube Shorts description:

CONTENT:
{self.script}

FORMAT:
2-3 short paragraphs + hashtags

RULES:
- Max 400 chars total
- Add 3-5 relevant hashtags at end
- Keep it engaging and informative
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
        
        while retry_count < MAX_RETRIES:
            prompt = f"""Generate {n_prompts} professional image prompts about: {self.subject}

Format: JSON array of detailed image descriptions

Rules for each prompt:
- Start with an engaging visual focus
- Include lighting and composition details
- Describe mood and atmosphere
- Add artistic style elements
- Keep descriptions clear and specific
- Focus on visual impact
- Include camera angle or perspective
- Mention color themes where relevant

Example format:
["Close-up shot with dramatic lighting, shallow depth of field, vibrant colors",
"Wide establishing shot, golden hour lighting, balanced composition"]

Return a JSON array of unique, varied image prompts."""

            completion = self.generate_response(prompt)
            if not completion:
                retry_count += 1
                continue

            # Clean up the response
            completion = completion.strip()
            
            try:
                # First try to parse as JSON array
                if completion.startswith("[") and completion.endswith("]"):
                    # Fix any truncated JSON first
                    if not completion.endswith('"]'):
                        completion = completion + '"]'
                    
                    image_prompts = json.loads(completion)
                    if isinstance(image_prompts, list) and len(image_prompts) > 0:
                        # Basic validation of prompts
                        image_prompts = [
                            p.strip().rstrip('",').strip('"\'') 
                            for p in image_prompts 
                            if isinstance(p, str) and len(p.strip()) > 20
                        ]
                        if image_prompts:
                            break
                
                # If JSON parsing fails, try other formats
                lines = re.split(r'\d+\.|•|-|\*|\n', completion)
                image_prompts = [
                    line.strip().strip('"\'"[]') 
                    for line in lines 
                    if line.strip() and len(line.strip()) > 20
                ]
                if image_prompts:
                    break
                    
            except Exception as e:
                if get_verbose():
                    warning(f"Failed to parse prompts: {str(e)}")
                retry_count += 1
                continue

        # If we still don't have valid prompts after retries, use fallbacks
        if not image_prompts:
            if get_verbose():
                warning("No valid prompts generated after retries, using fallback prompts")
            # Generate some content-appropriate fallback prompts based on the subject
            image_prompts = [
                f"{self.subject}, professional photography",
                f"{self.subject}, detailed view",
                f"{self.subject}, wide establishing shot",
                f"{self.subject}, artistic composition",
                f"{self.subject}, dramatic lighting",
                f"{self.subject}, dynamic perspective",
            ] * 3  # Repeat to get enough prompts

        # Ensure each prompt is complete and well-formed
        cleaned_prompts = []
        for prompt in image_prompts:
            # Remove any trailing quotes or commas
            prompt = prompt.strip().rstrip('",').strip('"\'')
            # Skip if too short
            if len(prompt) < 20:
                continue
            # Add professional quality markers if not present
            if not any(x in prompt.lower() for x in ["cinematic", "professional", "high quality"]):
                prompt += ", professional quality"
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
                image_prompts.append(base_prompt + variations[len(image_prompts) % len(variations)])
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

    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the given prompt.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        if get_verbose():
            info(f"Generating Image with prompt: {prompt}")

        # Use the dedicated image generation endpoint
        worker_url = "https://mp-image-gen.drake-t.workers.dev"

        if not worker_url:
            error("Image generation worker URL not configured")
            return None

        # Clean up and format prompt
        prompt = prompt.strip()
        if len(prompt) > 500:  # Truncate very long prompts
            prompt = prompt[:497] + "..."

        # Add some style keywords if they're not present
        style_keywords = ["cinematic", "dramatic", "detailed", "professional"]
        if not any(word in prompt.lower() for word in style_keywords):
            prompt += ", cinematic style, dramatic lighting"

        url = f"{worker_url}?prompt={prompt}&model=sdxl"

        MAX_RETRIES = 3
        retry_count = 0
        
        while retry_count < MAX_RETRIES:
            try:
                if get_verbose():
                    info(f"Attempt {retry_count + 1} of {MAX_RETRIES}")
                    info(f"Sending request to: {url}")
                
                response = requests.get(url, timeout=30)  # Add timeout
                
                if response.status_code == 200:
                    if response.headers.get('content-type') == 'image/png':
                        image_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".png")
                        
                        with open(image_path, "wb") as image_file:
                            image_file.write(response.content)
                        
                        # Verify the image was written successfully
                        if os.path.exists(image_path) and os.path.getsize(image_path) > 1000:
                            if get_verbose():
                                info(f"Image generated successfully: {image_path}")
                                info(f"Image size: {os.path.getsize(image_path)} bytes")
                            
                            self.images.append(image_path)
                            return image_path
                        else:
                            if get_verbose():
                                warning("Generated image file is too small or invalid")
                            os.remove(image_path)  # Clean up invalid file
                    else:
                        if get_verbose():
                            warning(f"Unexpected content type: {response.headers.get('content-type')}")
                else:
                    if get_verbose():
                        warning(f"Request failed with status {response.status_code}")
                        if response.text:
                            warning(f"Error response: {response.text[:200]}")
                
            except Exception as e:
                if get_verbose():
                    error(f"Error generating image: {str(e)}")
                    if hasattr(e, 'response'):
                        error(f"Response status: {e.response.status_code}")
                        error(f"Response content: {e.response.text[:200]}")
            
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
            if get_verbose():
                info("Starting video generation process...")

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
                info("Combining video elements...")
                info(f"Using TTS file: {tts_path}")
                info(f"Number of images: {len(self.images)}")
                
            path = self.combine()
            if not path:
                error("Failed to combine video elements")
                return None

            if get_verbose():
                info(f" => Generated Video: {path}")
                info(f" => Video size: {os.path.getsize(path)} bytes")

            self.video_path = os.path.abspath(path)
            return path
            
        except Exception as e:
            error(f"Error in generate_video: {str(e)}")
            error(f"Error type: {type(e).__name__}")
            error(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            if get_verbose():
                error(f"Current state:")
                error(f"Subject: {self.subject}")
                error(f"Script: {self.script}")
                error(f"Metadata: {self.metadata}")
                error(f"Image prompts: {len(self.image_prompts) if self.image_prompts else 0}")
                error(f"Images generated: {len(self.images) if self.images else 0}")
                if hasattr(self, 'tts_path') and self.tts_path:
                    error(f"TTS path: {self.tts_path}")
                    if os.path.exists(self.tts_path):
                        error(f"TTS file size: {os.path.getsize(self.tts_path)} bytes")
            return None
    
    def get_channel_id(self) -> str:
        """
        Gets the Channel ID of the YouTube Account.

        Returns:
            channel_id (str): The Channel ID.
        """
        driver = self.browser
        driver.get("https://studio.youtube.com")
        time.sleep(2)
        channel_id = driver.current_url.split("/")[-1]
        self.channel_id = channel_id

        return channel_id

    def upload_video(self) -> bool:
        """
        Uploads the video to YouTube.

        Returns:
            success (bool): Whether the upload was successful or not.
        """
        try:
            self.get_channel_id()

            driver = self.browser
            verbose = get_verbose()

            # Go to youtube.com/upload
            driver.get("https://www.youtube.com/upload")

            # Set video file
            FILE_PICKER_TAG = "ytcp-uploads-file-picker"
            file_picker = driver.find_element(By.TAG_NAME, FILE_PICKER_TAG)
            INPUT_TAG = "input"
            file_input = file_picker.find_element(By.TAG_NAME, INPUT_TAG)
            file_input.send_keys(self.video_path)

            # Wait for upload to finish
            time.sleep(5)

            # Set title
            textboxes = driver.find_elements(By.ID, YOUTUBE_TEXTBOX_ID)

            title_el = textboxes[0]
            description_el = textboxes[-1]

            if verbose:
                info("\t=> Setting title...")

            title_el.click()
            time.sleep(1)
            title_el.clear()
            title_el.send_keys(self.metadata["title"])

            if verbose:
                info("\t=> Setting description...")

            # Set description
            time.sleep(10)
            description_el.click()
            time.sleep(0.5)
            description_el.clear()
            description_el.send_keys(self.metadata["description"])

            time.sleep(0.5)

            # Set `made for kids` option
            if verbose:
                info("\t=> Setting `made for kids` option...")

            is_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_MADE_FOR_KIDS_NAME)
            is_not_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_NOT_MADE_FOR_KIDS_NAME)

            if not get_is_for_kids():
                is_not_for_kids_checkbox.click()
            else:
                is_for_kids_checkbox.click()

            time.sleep(0.5)

            # Click next
            if verbose:
                info("\t=> Clicking next...")

            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Click next again
            if verbose:
                info("\t=> Clicking next again...")
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Wait for 2 seconds
            time.sleep(2)

            # Click next again
            if verbose:
                info("\t=> Clicking next again...")
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Set as unlisted
            if verbose:
                info("\t=> Setting as unlisted...")
            
            radio_button = driver.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)
            radio_button[2].click()

            if verbose:
                info("\t=> Clicking done button...")

            # Click done button
            done_button = driver.find_element(By.ID, YOUTUBE_DONE_BUTTON_ID)
            done_button.click()

            # Wait for 2 seconds
            time.sleep(2)

            # Get latest video
            if verbose:
                info("\t=> Getting video URL...")

            # Get the latest uploaded video URL
            driver.get(f"https://studio.youtube.com/channel/{self.channel_id}/videos/short")
            time.sleep(2)
            videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
            first_video = videos[0]
            anchor_tag = first_video.find_element(By.TAG_NAME, "a")
            href = anchor_tag.get_attribute("href")
            if verbose:
                info(f"\t=> Extracting video ID from URL: {href}")
            video_id = href.split("/")[-2]

            # Build URL
            url = build_url(video_id)

            self.uploaded_video_url = url

            if verbose:
                success(f" => Uploaded Video: {url}")

            # Add video to cache
            self.add_video({
                "title": self.metadata["title"],
                "description": self.metadata["description"],
                "url": url,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Close the browser
            driver.quit()

            return True
        except:
            self.browser.quit()
            return False


    def get_videos(self) -> List[dict]:
        """
        Gets the uploaded videos from the YouTube Channel.

        Returns:
            videos (List[dict]): The uploaded videos.
        """
        if not os.path.exists(get_youtube_cache_path()):
            # Create the cache file
            with open(get_youtube_cache_path(), 'w') as file:
                json.dump({
                    "videos": []
                }, file, indent=4)
            return []

        videos = []
        # Read the cache file
        with open(get_youtube_cache_path(), 'r') as file:
            previous_json = json.loads(file.read())
            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    videos = account["videos"]

        return videos

    def validate_audio_file(self, audio_path: str, min_duration: float = 0.1) -> bool:
        """
        Validates that an audio file exists and contains valid audio data.
        
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
