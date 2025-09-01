# translation_service.py

from langdetect import detect, DetectorFactory
from googletrans import Translator
import logging
import time

# Set seed for consistent language detection
DetectorFactory.seed = 0

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        self.logger = logging.getLogger(__name__)
        self.cache = {}  # Simple cache to avoid repeated translations
        self.rate_limit_delay = 0.1  # Small delay between requests
        
    def detect_language(self, text):
        """Detect the language of the input text"""
        try:
            if not text or not text.strip():
                return 'en'
                
            # Remove extra whitespace and ensure minimum length
            clean_text = text.strip()
            if len(clean_text) < 3:
                return 'en'  # Default to English for very short text
                
            detected_lang = detect(clean_text)
            self.logger.info(f"Detected language: {detected_lang} for text: {clean_text[:50]}...")
            return detected_lang
            
        except Exception as e:
            self.logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def translate_text(self, text, target_language, source_language='auto'):
        """Translate text to target language"""
        try:
            if not text or not text.strip():
                return text
                
            # If target is English and source is English, no translation needed
            if target_language == 'en' and source_language == 'en':
                return text
                
            # Check cache first
            cache_key = f"{source_language}:{target_language}:{text[:100]}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Add small delay to respect rate limits
            time.sleep(self.rate_limit_delay)
            
            # Perform translation
            result = self.translator.translate(
                text, 
                src=source_language, 
                dest=target_language
            )
            
            translated_text = result.text
            
            # Cache the result
            self.cache[cache_key] = translated_text
            
            self.logger.info(f"Translated from {source_language} to {target_language}: {text[:30]}... -> {translated_text[:30]}...")
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Translation failed: {e}")
            return text  # Return original text if translation fails
    
    def translate_to_english(self, text, source_language='auto'):
        """Translate any text to English"""
        return self.translate_text(text, 'en', source_language)
    
    def translate_from_english(self, text, target_language):
        """Translate English text to target language"""
        if target_language == 'en':
            return text
        return self.translate_text(text, target_language, 'en')
    
    def clear_cache(self):
        """Clear translation cache"""
        self.cache.clear()
        self.logger.info("Translation cache cleared")