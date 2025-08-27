# Keyword Extraction and Word Cloud Generation Module
# modules/keyword_extractor.py

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import re
from collections import Counter
import os

# NLP libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

class KeywordExtractor:
    """
    Advanced keyword extraction and word cloud generation
    Uses TF-IDF, n-grams, and custom filtering for better results
    """
    
    def __init__(self, language: str = 'english'):
        """
        Initialize keyword extractor
        
        Args:
            language: Language for stopwords and processing
        """
        self.language = language
        self.stop_words = set(stopwords.words(language))
        
        # Add custom stopwords for comment analysis
        self.custom_stopwords = {
            'comment', 'text', 'said', 'say', 'says', 'think', 'believe',
            'feel', 'opinion', 'view', 'would', 'could', 'should', 'might',
            'also', 'really', 'just', 'like', 'get', 'go', 'want', 'need'
        }
        
        self.all_stopwords = self.stop_words.union(self.custom_stopwords)
        self.lemmatizer = WordNetLemmatizer()
        
    def extract_keywords(self, texts: List[str], method: str = 'tfidf', 
                        max_features: int = 50, ngram_range: Tuple[int, int] = (1, 2)) -> List[str]:
        """
        Extract keywords from a list of texts
        
        Args:
            texts: List of text documents
            method: Extraction method ('tfidf', 'count', 'hybrid')
            max_features: Maximum number of keywords to extract
            ngram_range: Range of n-grams to consider
            
        Returns:
            List of extracted keywords
        """
        if not texts:
            return []
        
        try:
            # Clean and preprocess texts
            cleaned_texts = [self._preprocess_text(text) for text in texts]
            cleaned_texts = [text for text in cleaned_texts if len(text.split()) > 2]
            
            if not cleaned_texts:
                return []
            
            if method == 'tfidf':
                keywords = self._extract_tfidf_keywords(cleaned_texts, max_features, ngram_range)
            elif method == 'count':
                keywords = self._extract_count_keywords(cleaned_texts, max_features, ngram_range)
            else:  # hybrid
                keywords = self._extract_hybrid_keywords(cleaned_texts, max_features, ngram_range)
            
            return keywords
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword extraction"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).lower()
        
        # Remove URLs, emails, and special characters
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_tfidf_keywords(self, texts: List[str], max_features: int, 
                               ngram_range: Tuple[int, int]) -> List[str]:
        """Extract keywords using TF-IDF"""
        vectorizer = TfidfVectorizer(
            max_features=max_features * 2,  # Get more features for filtering
            ngram_range=ngram_range,
            stop_words=list(self.all_stopwords),
            min_df=2,  # Keyword must appear in at least 2 documents
            max_df=0.8  # Ignore terms that appear in more than 80% of documents
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get mean TF-IDF scores for each feature
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Create feature-score pairs and sort
            feature_scores = list(zip(feature_names, mean_scores))
            feature_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Filter and return top keywords
            keywords = []
            for feature, score in feature_scores:
                if len(keywords) >= max_features:
                    break
                
                # Additional filtering
                if (len(feature.split()) <= 3 and  # Not too long
                    len(feature) > 2 and  # Not too short
                    not feature.replace(' ', '').isdigit()):  # Not just numbers
                    keywords.append(feature)
            
            return keywords
            
        except Exception as e:
            print(f"Error in TF-IDF extraction: {e}")
            return []
    
    def _extract_count_keywords(self, texts: List[str], max_features: int, 
                               ngram_range: Tuple[int, int]) -> List[str]:
        """Extract keywords using simple count vectorization"""
        vectorizer = CountVectorizer(
            max_features=max_features * 2,
            ngram_range=ngram_range,
            stop_words=list(self.all_stopwords),
            min_df=2
        )
        
        try:
            count_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get total counts for each feature
            total_counts = np.sum(count_matrix.toarray(), axis=0)
            
            # Create feature-count pairs and sort
            feature_counts = list(zip(feature_names, total_counts))
            feature_counts.sort(key=lambda x: x[1], reverse=True)
            
            # Return top keywords
            keywords = [feature for feature, _ in feature_counts[:max_features]]
            return keywords
            
        except Exception as e:
            print(f"Error in count-based extraction: {e}")
            return []
    
    def _extract_hybrid_keywords(self, texts: List[str], max_features: int, 
                                ngram_range: Tuple[int, int]) -> List[str]:
        """Combine TF-IDF and frequency-based extraction"""
        tfidf_keywords = self._extract_tfidf_keywords(texts, max_features // 2, ngram_range)
        count_keywords = self._extract_count_keywords(texts, max_features // 2, ngram_range)
        
        # Combine and deduplicate
        all_keywords = list(dict.fromkeys(tfidf_keywords + count_keywords))
        return all_keywords[:max_features]
    
    def get_word_frequencies(self, text: str, max_words: int = 100) -> Dict[str, int]:
        """
        Get word frequencies for word cloud generation
        
        Args:
            text: Input text (can be concatenated from multiple documents)
            max_words: Maximum number of words to return
            
        Returns:
            Dictionary of word frequencies
        """
        if not text:
            return {}
        
        try:
            # Preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Tokenize and filter
            words = word_tokenize(cleaned_text)
            words = [word for word in words if (
                len(word) > 2 and 
                word not in self.all_stopwords and
                word.isalpha()
            )]
            
            # Count frequencies
            word_freq = Counter(words)
            
            # Return top words
            return dict(word_freq.most_common(max_words))
            
        except Exception as e:
            print(f"Error getting word frequencies: {e}")
            return {}
    
    def generate_wordcloud_image(self, text: str, session_id: str, 
                                width: int = 800, height: int = 400) -> str:
        """
        Generate and save word cloud image
        
        Args:
            text: Input text for word cloud
            session_id: Session identifier for filename
            width: Image width
            height: Image height
            
        Returns:
            Path to saved image
        """
        try:
            # Create output directory
            output_dir = "static/wordclouds"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate word frequencies
            word_freq = self.get_word_frequencies(text, max_words=200)
            
            if not word_freq:
                # Create placeholder image if no words
                fig, ax = plt.subplots(figsize=(width/100, height/100))
                ax.text(0.5, 0.5, 'No keywords found', 
                       ha='center', va='center', fontsize=20, color='gray')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                
                output_path = os.path.join(output_dir, f"wordcloud_{session_id}.png")
                plt.savefig(output_path, bbox_inches='tight', dpi=100, 
                           facecolor='white', edgecolor='none')
                plt.close()
                
                return output_path
            
            # Create word cloud
            wordcloud = WordCloud(
                width=width,
                height=height,
                background_color='white',
                colormap='viridis',
                max_words=200,
                relative_scaling=0.5,
                min_font_size=10,
                stopwords=self.all_stopwords
            ).generate_from_frequencies(word_freq)
            
            # Save image
            output_path = os.path.join(output_dir, f"wordcloud_{session_id}.png")
            wordcloud.to_file(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Error generating word cloud: {e}")
            # Return placeholder image path
            return self._create_error_wordcloud(session_id)
    
    def _create_error_wordcloud(self, session_id: str) -> str:
        """Create an error placeholder word cloud"""
        try:
            output_dir = "static/wordclouds"
            os.makedirs(output_dir, exist_ok=True)
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, 'Error generating word cloud', 
                   ha='center', va='center', fontsize=16, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            output_path = os.path.join(output_dir, f"wordcloud_{session_id}.png")
            plt.savefig(output_path, bbox_inches='tight', dpi=100, 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return output_path
        except:
            return ""
    
    def extract_phrases(self, texts: List[str], min_freq: int = 3) -> List[Tuple[str, int]]:
        """
        Extract common phrases from texts
        
        Args:
            texts: List of text documents
            min_freq: Minimum frequency for phrase inclusion
            
        Returns:
            List of (phrase, frequency) tuples
        """
        try:
            # Extract 2-grams and 3-grams
            all_phrases = []
            
            for text in texts:
                cleaned_text = self._preprocess_text(text)
                words = word_tokenize(cleaned_text)
                words = [word for word in words if word not in self.all_stopwords]
                
                # Generate n-grams
                for n in [2, 3]:
                    ngrams = [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
                    all_phrases.extend(ngrams)
            
            # Count phrases and filter
            phrase_counts = Counter(all_phrases)
            common_phrases = [(phrase, count) for phrase, count in phrase_counts.items() 
                            if count >= min_freq and len(phrase.split()) > 1]
            
            # Sort by frequency
            common_phrases.sort(key=lambda x: x[1], reverse=True)
            
            return common_phrases[:50]  # Return top 50 phrases
            
        except Exception as e:
            print(f"Error extracting phrases: {e}")
            return []
    
    def analyze_keyword_sentiment_context(self, texts: List[str], sentiments: List[str]) -> Dict:
        """
        Analyze keywords in context of sentiment
        
        Args:
            texts: List of text documents
            sentiments: List of corresponding sentiments
            
        Returns:
            Dictionary with sentiment-specific keywords
        """
        try:
            if len(texts) != len(sentiments):
                return {}
            
            # Group texts by sentiment
            sentiment_groups = {}
            for text, sentiment in zip(texts, sentiments):
                if sentiment not in sentiment_groups:
                    sentiment_groups[sentiment] = []
                sentiment_groups[sentiment].append(text)
            
            # Extract keywords for each sentiment group
            sentiment_keywords = {}
            for sentiment, group_texts in sentiment_groups.items():
                keywords = self.extract_keywords(group_texts, max_features=20)
                sentiment_keywords[sentiment] = keywords
            
            return sentiment_keywords
            
        except Exception as e:
            print(f"Error in sentiment-keyword analysis: {e}")
            return {}
    
    def export_keywords(self, keywords: List[str], phrases: List[Tuple[str, int]], 
                       output_file: str):
        """
        Export keywords and phrases to CSV
        
        Args:
            keywords: List of keywords
            phrases: List of (phrase, frequency) tuples
            output_file: Output file path
        """
        try:
            # Create DataFrame with keywords and phrases
            data = []
            
            # Add keywords
            for i, keyword in enumerate(keywords):
                data.append({
                    'type': 'keyword',
                    'text': keyword,
                    'rank': i + 1,
                    'frequency': None
                })
            
            # Add phrases
            for phrase, freq in phrases:
                data.append({
                    'type': 'phrase',
                    'text': phrase,
                    'rank': None,
                    'frequency': freq
                })
            
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            print(f"Keywords and phrases exported to {output_file}")
            
        except Exception as e:
            print(f"Error exporting keywords: {e}")

# Example usage and testing
if __name__ == "__main__":
    extractor = KeywordExtractor()
    
    # Test data
    test_texts = [
        "The new government policy is excellent and will help many citizens.",
        "I disagree with this policy proposal and think it needs major changes.",
        "This policy implementation timeline seems reasonable and achievable.",
        "Great initiative from the government to address important social issues.",
        "The budget allocation for this policy is insufficient and problematic.",
        "This policy change is a positive step forward for our community development.",
        "The proposal lacks sufficient detail and clarity in several key areas.",
        "I fully support this new policy and its stated objectives.",
        "More stakeholder consultation would improve this policy significantly.",
        "This policy could have serious unintended consequences for businesses."
    ]
    
    # Test keyword extraction
    keywords = extractor.extract_keywords(test_texts, method='tfidf', max_features=10)
    print("Extracted Keywords:", keywords)
    
    # Test word frequencies
    combined_text = ' '.join(test_texts)
    word_freq = extractor.get_word_frequencies(combined_text, max_words=20)
    print("Word Frequencies:", word_freq)
    
    # Test phrase extraction
    phrases = extractor.extract_phrases(test_texts, min_freq=2)
    print("Common Phrases:", phrases)
    
    # Test word cloud generation
    try:
        image_path = extractor.generate_wordcloud_image(combined_text, "test_session")
        print(f"Word cloud saved to: {image_path}")
    except Exception as e:
        print(f"Error generating word cloud: {e}")