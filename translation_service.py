# translation_service.py

import py3langid as langid
from googletrans import Translator
import logging
import time

class TranslationService:
    def __init__(self):
        self.translator = Translator()
        self.logger = logging.getLogger(__name__)
        self.cache = {}  # Simple cache to avoid repeated translations
        self.rate_limit_delay = 0.1  # Small delay between requests
        
        # Configure langid (optional: you can set specific languages if needed)
        # langid.set_languages(['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar', 'hi'])
        
    def detect_language(self, text):
        """Detect the language of the input text using langid with improvements for short text"""
        try:
            if not text or not text.strip():
                return 'en'
                
            # Remove extra whitespace and ensure minimum length
            clean_text = text.strip()
            if len(clean_text) < 3:
                return 'en'  # Default to English for very short text
            
            # Common English words that langid often misclassifies
            common_english_words = {
                'hello', 'hi', 'hey', 'thanks', 'thank', 'you', 'yes', 'no', 
                'please', 'sorry', 'ok', 'okay', 'bye', 'goodbye', 'help',
                'what', 'when', 'where', 'why', 'how', 'who', 'can', 'will',
                'the', 'and', 'or', 'but', 'for', 'with', 'this', 'that'
            }
            
            # Check if it's a short common English word/phrase
            words = clean_text.lower().split()
            if len(words) <= 2 and all(word.strip('.,!?') in common_english_words for word in words):
                self.logger.info(f"Detected common English word/phrase: {clean_text[:50]}")
                return 'en'
            
            # Use langid to detect language
            detected_lang, confidence = langid.classify(clean_text)
            
            # Log the detection result with confidence score
            self.logger.info(f"Detected language: {detected_lang} (confidence: {confidence:.3f}) for text: {clean_text[:50]}...")
            
            # Apply confidence threshold and length-based corrections
            if confidence < 0.8 and len(clean_text) < 20:
                # For short text with low confidence, default to English
                self.logger.info(f"Short text with low confidence, defaulting to English")
                return 'en'
            elif confidence < 0.6:
                # For any text with very low confidence, default to English
                self.logger.info(f"Very low confidence detection, defaulting to English")
                return 'en'
            
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