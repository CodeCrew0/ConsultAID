# Text Summarization Module using HuggingFace Transformers
# modules/text_summarizer.py

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import re
import nltk
from nltk.tokenize import sent_tokenize
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class TextSummarizer:
    """
    Advanced text summarization using pre-trained transformer models
    Supports both extractive and abstractive summarization
    """
    
    def __init__(self, 
                 model_name: str = "facebook/bart-large-cnn",
                 max_length: int = 150,
                 min_length: int = 30):
        """
        Initialize the text summarizer
        
        Args:
            model_name: HuggingFace model identifier for summarization
            max_length: Maximum length of generated summaries
            min_length: Minimum length of generated summaries
        """
        self.model_name = model_name
        self.max_length = max_length
        self.min_length = min_length
        self.summarizer = None
        self.tokenizer = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the summarization model and tokenizer"""
        try:
            print(f"Loading summarization model: {self.model_name}")
            
            # Load the summarization pipeline
            self.summarizer = pipeline(
                "summarization",
                model=self.model_name,
                tokenizer=self.model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Load tokenizer separately for text length checking
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            print("Summarization model loaded successfully")
            
        except Exception as e:
            print(f"Error loading summarization model: {e}")
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a fallback model if primary model fails"""
        try:
            print("Loading fallback summarization model...")
            self.summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-6-6",
                device=0 if torch.cuda.is_available() else -1
            )
            self.tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-6-6")
            print("Fallback summarization model loaded successfully")
        except Exception as e:
            print(f"Error loading fallback model: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better summarization
        
        Args:
            text: Input text to preprocess
            
        Returns:
            Cleaned and preprocessed text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        return text
    
    def _check_text_length(self, text: str) -> bool:
        """
        Check if text is within model's token limits
        
        Args:
            text: Input text to check
            
        Returns:
            True if text is within limits, False otherwise
        """
        try:
            tokens = self.tokenizer.encode(text, truncation=False)
            return len(tokens) <= 1024  # Most models have 1024 token limit
        except:
            return len(text.split()) <= 500  # Fallback word count check
    
    def summarize_single(self, text: str, custom_max_length: Optional[int] = None) -> str:
        """
        Summarize a single text
        
        Args:
            text: Input text to summarize
            custom_max_length: Custom maximum length for this summary
            
        Returns:
            Generated summary
        """
        if not text or len(text.strip()) < 50:
            return text  # Return original if too short
        
        try:
            # Preprocess the text
            cleaned_text = self._preprocess_text(text)
            
            # Check text length and truncate if necessary
            if not self._check_text_length(cleaned_text):
                # Truncate to fit model limits
                words = cleaned_text.split()
                cleaned_text = ' '.join(words[:400])  # Keep first 400 words
            
            # Set summary length based on input length
            max_len = custom_max_length or min(self.max_length, len(cleaned_text.split()) // 3)
            min_len = min(self.min_length, max_len - 10)
            
            # Generate summary
            summary_result = self.summarizer(
                cleaned_text,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,
                truncation=True
            )
            
            summary = summary_result[0]['summary_text']
            
            # Post-process summary
            summary = summary.strip()
            if not summary.endswith(('.', '!', '?')):
                summary += '.'
            
            return summary
            
        except Exception as e:
            print(f"Error summarizing text: {e}")
            # Fallback to extractive summarization
            return self._extractive_summary(text)
    
    def _extractive_summary(self, text: str, num_sentences: int = 2) -> str:
        """
        Simple extractive summarization fallback
        
        Args:
            text: Input text
            num_sentences: Number of sentences to extract
            
        Returns:
            Extractive summary
        """
        try:
            sentences = sent_tokenize(text)
            
            if len(sentences) <= num_sentences:
                return text
            
            # Simple scoring based on sentence length and position
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                # Score based on length (medium length preferred)
                length_score = min(len(sentence.split()), 20) / 20
                
                # Position score (earlier sentences get higher score)
                position_score = (len(sentences) - i) / len(sentences)
                
                total_score = length_score * 0.7 + position_score * 0.3
                scored_sentences.append((sentence, total_score))
            
            # Select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            summary_sentences = [sent[0] for sent in scored_sentences[:num_sentences]]
            
            # Maintain original order
            original_order = []
            for sentence in sentences:
                if sentence in summary_sentences:
                    original_order.append(sentence)
            
            return ' '.join(original_order)
            
        except Exception as e:
            print(f"Error in extractive summarization: {e}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def summarize_batch(self, texts: List[str], batch_size: int = 8) -> List[str]:
        """
        Summarize a batch of texts
        
        Args:
            texts: List of texts to summarize
            batch_size: Number of texts to process at once
            
        Returns:
            List of summaries
        """
        if not texts:
            return []
        
        summaries = []
        
        # Process in batches to avoid memory issues
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_summaries = []
            
            for text in batch:
                summary = self.summarize_single(text)
                batch_summaries.append(summary)
            
            summaries.extend(batch_summaries)
            
            # Progress update
            if i % (batch_size * 5) == 0:
                progress = min(100, (i / len(texts)) * 100)
                print(f"Summarization progress: {progress:.1f}%")
        
        return summaries
    
    def create_mega_summary(self, texts: List[str], target_length: int = 200) -> str:
        """
        Create a summary of multiple texts combined
        
        Args:
            texts: List of texts to combine and summarize
            target_length: Target length for the mega summary
            
        Returns:
            Combined summary of all texts
        """
        if not texts:
            return ""
        
        try:
            # First, get individual summaries to reduce length
            individual_summaries = []
            for text in texts[:50]:  # Limit to first 50 texts for performance
                if len(text) > 100:  # Only summarize longer texts
                    summary = self.summarize_single(text, custom_max_length=50)
                    individual_summaries.append(summary)
                else:
                    individual_summaries.append(text)
            
            # Combine summaries
            combined_text = ' '.join(individual_summaries)
            
            # Create final mega summary
            if len(combined_text) > 200:
                mega_summary = self.summarize_single(combined_text, custom_max_length=target_length)
            else:
                mega_summary = combined_text
            
            return mega_summary
            
        except Exception as e:
            print(f"Error creating mega summary: {e}")
            # Fallback: take first few sentences from random texts
            sentences = []
            for text in texts[:10]:
                text_sentences = sent_tokenize(text)
                if text_sentences:
                    sentences.append(text_sentences[0])
            
            return ' '.join(sentences[:3])
    
    def summarize_by_sentiment(self, df: pd.DataFrame, text_column: str, sentiment_column: str) -> Dict[str, str]:
        """
        Create summaries grouped by sentiment
        
        Args:
            df: DataFrame containing texts and sentiments
            text_column: Name of column containing text data
            sentiment_column: Name of column containing sentiment labels
            
        Returns:
            Dictionary with summaries for each sentiment category
        """
        sentiment_summaries = {}
        
        for sentiment in df[sentiment_column].unique():
            sentiment_texts = df[df[sentiment_column] == sentiment][text_column].tolist()
            
            if sentiment_texts:
                # Combine and summarize texts for this sentiment
                sentiment_summary = self.create_mega_summary(sentiment_texts, target_length=150)
                sentiment_summaries[sentiment] = sentiment_summary
            else:
                sentiment_summaries[sentiment] = "No comments available for this sentiment."
        
        return sentiment_summaries
    
    def get_summary_statistics(self, original_texts: List[str], summaries: List[str]) -> Dict:
        """
        Calculate statistics about the summarization process
        
        Args:
            original_texts: List of original texts
            summaries: List of generated summaries
            
        Returns:
            Dictionary with summarization statistics
        """
        if len(original_texts) != len(summaries):
            return {"error": "Mismatch between original texts and summaries"}
        
        # Calculate compression ratios
        compression_ratios = []
        for orig, summ in zip(original_texts, summaries):
            orig_len = len(orig.split())
            summ_len = len(summ.split())
            if orig_len > 0:
                ratio = summ_len / orig_len
                compression_ratios.append(ratio)
        
        # Calculate statistics
        avg_compression = np.mean(compression_ratios) if compression_ratios else 0
        avg_original_length = np.mean([len(text.split()) for text in original_texts])
        avg_summary_length = np.mean([len(summary.split()) for summary in summaries])
        
        return {
            'total_texts_processed': len(original_texts),
            'average_original_length': avg_original_length,
            'average_summary_length': avg_summary_length,
            'average_compression_ratio': avg_compression,
            'compression_ratios': compression_ratios
        }
    
    def export_summaries(self, original_texts: List[str], summaries: List[str], output_file: str):
        """
        Export original texts and summaries to CSV
        
        Args:
            original_texts: List of original texts
            summaries: List of summaries
            output_file: Path to output CSV file
        """
        if len(original_texts) != len(summaries):
            raise ValueError("Mismatch between original texts and summaries")
        
        results = []
        for i, (original, summary) in enumerate(zip(original_texts, summaries)):
            results.append({
                'comment_id': i + 1,
                'original_text': original,
                'summary': summary,
                'original_length': len(original.split()),
                'summary_length': len(summary.split()),
                'compression_ratio': len(summary.split()) / len(original.split()) if len(original.split()) > 0 else 0
            })
        
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"Summaries exported to {output_file}")

# Example usage and testing
if __name__ == "__main__":
    import torch
    
    # Test the text summarizer
    summarizer = TextSummarizer()
    
    # Test single summarization
    test_text = """
    The new policy implementation has been a significant challenge for our department. 
    While the initial goals were well-intentioned, the execution has faced several hurdles. 
    Staff members have expressed concerns about the increased workload and tight deadlines. 
    However, some positive outcomes have emerged, including improved documentation processes 
    and better interdepartmental communication. Moving forward, we need to address the 
    training gaps and provide more resources to ensure successful implementation.
    """
    
    summary = summarizer.summarize_single(test_text)
    print(f"Original length: {len(test_text.split())} words")
    print(f"Summary: {summary}")
    print(f"Summary length: {len(summary.split())} words")
    
    # Test batch summarization
    test_texts = [
        "This is a great product that exceeds expectations in every way.",
        "The service was terrible and I would not recommend it to anyone.",
        "Average quality, nothing special but does the job adequately.",
        "Outstanding customer support and quick resolution of issues.",
        "Disappointed with the recent changes to the platform interface."
    ]
    
    batch_summaries = summarizer.summarize_batch(test_texts)
    print(f"\\nBatch summaries: {batch_summaries}")
    
    # Test mega summary
    mega_summary = summarizer.create_mega_summary(test_texts)
    print(f"\\nMega summary: {mega_summary}")