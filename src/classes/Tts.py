import os
import logging
from typing import Optional
import numpy as np
from scipy.io import wavfile
from config import ROOT_DIR, get_verbose
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer

class TTS:
    """
    Class for Text-to-Speech using Coqui TTS.
    """
    def __init__(self, model_name: str = "tts_models/en/ljspeech/vits") -> None:
        """
        Initializes the TTS class with improved error handling.

        Args:
            model_name (str): Name of the TTS model to use
        """
        try:
            venv_site_packages = "venv/lib/python3.9/site-packages"
            
            # Path to the .models.json file
            models_json_path = os.path.join(
                ROOT_DIR,
                venv_site_packages,
                "TTS",
                ".models.json",
            )

            if not os.path.exists(models_json_path):
                if get_verbose():
                    logging.error(f"Models file not found at: {models_json_path}")
                raise FileNotFoundError("TTS models configuration not found")

            # Initialize the ModelManager with better error handling
            try:
                self._model_manager = ModelManager(models_json_path)
            except Exception as e:
                if get_verbose():
                    logging.error(f"Failed to initialize ModelManager: {str(e)}")
                raise

            # Download and setup model with validation
            try:
                self._model_path, self._config_path, self._model_item = \
                    self._model_manager.download_model(model_name)
                    
                if not all([self._model_path, self._config_path, self._model_item]):
                    raise ValueError("Model download failed to return required paths")
                    
                if not os.path.exists(self._model_path):
                    raise FileNotFoundError(f"Model file not found at: {self._model_path}")
                    
                if not os.path.exists(self._config_path):
                    raise FileNotFoundError(f"Config file not found at: {self._config_path}")
                    
            except Exception as e:
                if get_verbose():
                    logging.error(f"Model setup failed: {str(e)}")
                raise

            # Initialize the Synthesizer with optimal settings
            self._synthesizer = Synthesizer(
                tts_checkpoint=self._model_path,
                tts_config_path=self._config_path,
                tts_speakers_file=None,
                tts_languages_file=None,
                vocoder_checkpoint=None,
                vocoder_config=None,
                encoder_checkpoint="",
                encoder_config="",
                use_cuda=False  # Set to True if CUDA is available
            )

        except Exception as e:
            if get_verbose():
                logging.error(f"TTS initialization failed: {str(e)}")
            raise

    @property
    def synthesizer(self) -> Synthesizer:
        """
        Returns the synthesizer.

        Returns:
            Synthesizer: The synthesizer.
        """
        return self._synthesizer

    def preprocess_text(self, text: str) -> str:
        """
        Enhanced text preprocessing for better speech synthesis.
        
        Args:
            text (str): Text to preprocess
            
        Returns:
            str: Processed text ready for synthesis
        """
        if not text:
            return ""
            
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Improve prosody with strategic pauses
        replacements = {
            '.': '... ',
            '!': '...! ',
            '?': '...? ',
            ',': '... ',
            ';': '... ',
            ':': '... ',
            '(': ' ... ',
            ')': ' ... ',
            '-': ' ... ',
        }
        
        for key, value in replacements.items():
            text = text.replace(key, value)
        
        # Ensure proper sentence endings
        if not text.endswith(('.', '!', '?')):
            text += '.'
            
        # Add slight pause between sentences for better flow
        text = text.replace('. ', '... ')
        
        # Remove any double spaces
        text = ' '.join(text.split())
        
        return text.strip()

    def synthesize(
        self, 
        text: str, 
        output_file: str = os.path.join(ROOT_DIR, ".mp", "audio.wav"),
        speaking_rate: float = 1.0,
        voice_emotion: Optional[str] = None
    ) -> str:
        """
        Enhanced speech synthesis with better audio quality and validation.

        Args:
            text (str): The text to synthesize
            output_file (str): Output file path
            speaking_rate (float): Speaking rate (0.5-2.0, default 1.0)
            voice_emotion (Optional[str]): Emotion to apply ("happy", "sad", "angry", None)
            
        Returns:
            str: Path to the generated audio file
        """
        if not text:
            raise ValueError("No text provided for synthesis")
            
        try:
            # Preprocess text for better synthesis
            processed_text = self.preprocess_text(text)
            if get_verbose():
                logging.info(f"Preprocessed text ({len(processed_text)} chars)")
                logging.info(f"Text: {processed_text}")
            
            # Split long text into manageable chunks while preserving sentence structure
            chunks = []
            for sentence in processed_text.split('.'):
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Add back the period that was removed by split
                chunks.append(sentence + '.')
                
            if get_verbose():
                logging.info(f"Split text into {len(chunks)} chunks")
            
            # Process each chunk and combine
            all_wavs = []
            sample_rate = 22050  # Standard sample rate for this model
            
            for i, chunk in enumerate(chunks, 1):
                if get_verbose():
                    logging.info(f"Processing chunk {i}/{len(chunks)} ({len(chunk)} chars)")
                    logging.info(f"Chunk text: {chunk}")
                
                # Generate speech for chunk
                try:
                    outputs = self.synthesizer.tts(
                        chunk,
                        speaker_id=None,
                        language_id=None,
                        speed=speaking_rate
                    )
                    
                    if outputs is None:
                        raise ValueError(f"Null output from synthesizer for chunk {i}")
                        
                    # Convert outputs to numpy array if needed
                    wav = np.array(outputs) if not isinstance(outputs, np.ndarray) else outputs
                    
                    if wav.size == 0:
                        raise ValueError(f"Empty audio data for chunk {i}")
                        
                    if wav.dtype != np.float32:
                        wav = wav.astype(np.float32)
                        
                    # Normalize chunk
                    if np.max(np.abs(wav)) > 0:
                        wav = wav / np.max(np.abs(wav))
                        
                    all_wavs.append(wav)
                    
                except Exception as e:
                    if get_verbose():
                        logging.error(f"Failed to synthesize chunk {i}: {str(e)}")
                        logging.error(f"Chunk text: {chunk}")
                    raise
                
            if not all_wavs:
                raise ValueError("No audio data generated")
                
            # Add small silence between chunks for natural pauses
            silence = np.zeros(int(0.1 * sample_rate))  # 100ms silence
            combined_wav = np.concatenate([wav for pair in zip(all_wavs, [silence]*len(all_wavs)) for wav in pair][:-1])
            
            # Final normalization
            if np.max(np.abs(combined_wav)) > 0:
                combined_wav = combined_wav / np.max(np.abs(combined_wav))
            else:
                raise ValueError("Generated audio has zero amplitude")
                
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Save with proper sample rate and bit depth
            try:
                if get_verbose():
                    logging.info(f"Saving audio to {output_file}")
                    logging.info(f"Audio shape: {combined_wav.shape}")
                    logging.info(f"Sample rate: {sample_rate}")
                    
                wavfile.write(output_file, sample_rate, combined_wav)
                
                # Validate output file
                if not os.path.exists(output_file):
                    raise FileNotFoundError("Failed to save audio file")
                    
                file_size = os.path.getsize(output_file)
                if file_size < 1024:  # Less than KB
                    raise ValueError(f"Generated audio file too small: {file_size} bytes")
                    
                # Load file back to verify it's valid
                try:
                    verify_rate, verify_data = wavfile.read(output_file)
                    if verify_rate != sample_rate:
                        raise ValueError(f"Sample rate mismatch: {verify_rate} != {sample_rate}")
                    if len(verify_data) == 0:
                        raise ValueError("Empty audio data in saved file")
                except Exception as e:
                    raise ValueError(f"Failed to verify audio file: {str(e)}")
                    
                if get_verbose():
                    logging.info(f"Successfully saved audio file: {output_file}")
                    logging.info(f"File size: {file_size} bytes")
                    logging.info(f"Audio length: {len(combined_wav)/sample_rate:.2f} seconds")
                
                return output_file
                
            except Exception as e:
                if get_verbose():
                    logging.error(f"Failed to save audio file: {str(e)}")
                raise
            
        except Exception as e:
            if get_verbose():
                logging.error(f"Speech synthesis failed: {str(e)}")
            raise

