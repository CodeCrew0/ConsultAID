# Sentiment Analysis Module using HuggingFace Transformers
# modules/sentiment_analyzer.py

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import logging

class SentimentAnalyzer:
    """
    Advanced sentiment analysis using pre-trained transformer models
    Supports multiple languages and provides confidence scores
    """
    
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Initialize the sentiment analyzer with a pre-trained model
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.classifier = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._load_model()
        
    def _load_model(self):
        """Load the tokenizer and model"""
        try:
            print(f"Loading sentiment analysis model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Create pipeline for easier inference
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                return_all_scores=True
            )
            
            print(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to a simpler model
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load a simpler fallback model if the primary fails"""
        try:
            print("Loading fallback model...")
            self.classifier = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if self.device == "cuda" else -1,
                return_all_scores=True
            )
            print("Fallback model loaded successfully")
        except Exception as e:
            print(f"Error loading fallback model: {e}")
            raise
    
    def analyze_single(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment label and confidence scores
        """
        if not text or len(text.strip()) == 0:
            return {"label": "neutral", "confidence": 0.5, "scores": {}}
        
        try:
            # Truncate text if too long (BERT models have token limits)
            if len(text) > 500:
                text = text[:500]
            
            # Get predictions
            results = self.classifier(text)
            
            # Process results based on model type
            if isinstance(results[0], list):
                # Model returns all scores
                scores = {result['label'].lower(): result['score'] for result in results[0]}
                best_prediction = max(results[0], key=lambda x: x['score'])
                label = best_prediction['label'].lower()
                confidence = best_prediction['score']
            else:
                # Model returns single prediction
                label = results[0]['label'].lower()
                confidence = results[0]['score']
                scores = {label: confidence}
            
            # Normalize labels
            label = self._normalize_label(label)
            
            return {
                "label": label,
                "confidence": confidence,
                "scores": scores
            }
            
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return {"label": "neutral", "confidence": 0.5, "scores": {}}
    
    def analyze_batch(self, texts: List[str], batch_size: int = 32) -> List[str]:
        """
        Analyze sentiment for a batch of texts
        
        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process at once
            
        Returns:
            List of sentiment labels
        """
        if not texts:
            return []
        
        sentiments = []
        
        # Process in batches to avoid memory issues
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                # Clean and truncate texts
                cleaned_batch = []
                for text in batch:
                    if not text or len(str(text).strip()) == 0:
                        cleaned_batch.append("neutral text")
                    else:
                        # Truncate long texts
                        text_str = str(text)[:500]
                        cleaned_batch.append(text_str)
                
                # Get predictions for batch
                results = self.classifier(cleaned_batch)
                
                # Extract labels
                for result in results:
                    if isinstance(result, list):
                        best_pred = max(result, key=lambda x: x['score'])
                        label = self._normalize_label(best_pred['label'].lower())
                    else:
                        label = self._normalize_label(result['label'].lower())
                    
                    sentiments.append(label)
                    
            except Exception as e:
                print(f"Error processing batch {i//batch_size + 1}: {e}")
                # Add neutral labels for failed batch
                sentiments.extend(["neutral"] * len(batch))
        
        return sentiments
    
    def get_confidence_scores(self, texts: List[str]) -> List[Dict]:
        """
        Get detailed confidence scores for a list of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of dictionaries with detailed scores
        """
        detailed_results = []
        
        for text in texts:
            result = self.analyze_single(text)
            detailed_results.append(result)
        
        return detailed_results
    
    def _normalize_label(self, label: str) -> str:
        """
        Normalize different label formats to standard positive/negative/neutral
        
        Args:
            label: Original label from model
            
        Returns:
            Normalized label
        """
        label = label.lower()
        
        # Map various label formats
        if label in ['positive', 'pos', 'label_2', '2']:
            return 'positive'
        elif label in ['negative', 'neg', 'label_0', '0']:
            return 'negative'
        elif label in ['neutral', 'label_1', '1']:
            return 'neutral'
        else:
            return 'neutral'  # Default fallback
    
    def get_sentiment_statistics(self, texts: List[str]) -> Dict:
        """
        Get comprehensive sentiment statistics for a collection of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary with sentiment statistics
        """
        if not texts:
            return {}
        
        sentiments = self.analyze_batch(texts)
        confidence_scores = self.get_confidence_scores(texts[:100])  # Sample for performance
        
        # Calculate statistics
        sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
        total = len(sentiments)
        
        # Calculate percentages
        sentiment_percentages = {
            sentiment: (count / total) * 100 
            for sentiment, count in sentiment_counts.items()
        }
        
        # Average confidence scores
        avg_confidence = np.mean([score['confidence'] for score in confidence_scores])
        
        # Most confident predictions
        sorted_confidence = sorted(confidence_scores, key=lambda x: x['confidence'], reverse=True)
        most_confident = sorted_confidence[:5]
        least_confident = sorted_confidence[-5:]
        
        return {
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': sentiment_percentages,
            'total_analyzed': total,
            'average_confidence': avg_confidence,
            'most_confident_predictions': most_confident,
            'least_confident_predictions': least_confident
        }
    
    def analyze_by_category(self, df: pd.DataFrame, text_column: str, category_column: str) -> Dict:
        """
        Analyze sentiment by categories (e.g., by topic, department, etc.)
        
        Args:
            df: DataFrame containing texts and categories
            text_column: Name of column containing text data
            category_column: Name of column containing categories
            
        Returns:
            Dictionary with sentiment analysis by category
        """
        results = {}
        
        for category in df[category_column].unique():
            category_texts = df[df[category_column] == category][text_column].tolist()
            category_sentiments = self.analyze_batch(category_texts)
            
            # Calculate statistics for this category
            sentiment_counts = pd.Series(category_sentiments).value_counts().to_dict()
            total = len(category_sentiments)
            sentiment_percentages = {
                sentiment: (count / total) * 100 
                for sentiment, count in sentiment_counts.items()
            }
            
            results[category] = {
                'sentiment_counts': sentiment_counts,
                'sentiment_percentages': sentiment_percentages,
                'total_comments': total
            }
        
        return results
    
    def export_results(self, texts: List[str], output_file: str):
        """
        Export sentiment analysis results to CSV
        
        Args:
            texts: List of texts to analyze
            output_file: Path to output CSV file
        """
        results = []
        
        for i, text in enumerate(texts):
            analysis = self.analyze_single(text)
            results.append({
                'comment_id': i + 1,
                'text': text,
                'sentiment': analysis['label'],
                'confidence': analysis['confidence'],
                'positive_score': analysis['scores'].get('positive', 0),
                'negative_score': analysis['scores'].get('negative', 0),
                'neutral_score': analysis['scores'].get('neutral', 0)
            })
        
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        print(f"Results exported to {output_file}")

# Example usage and testing
if __name__ == "__main__":
    # Test the sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    # Test single analysis
    test_text = "I love this new feature! It's amazing and works perfectly."
    result = analyzer.analyze_single(test_text)
    print(f"Single analysis result: {result}")
    
    # Test batch analysis
    test_texts = [
        "This is great!",
        "I hate this feature",
        "It's okay, nothing special",
        "Absolutely fantastic work!",
        "Terrible experience, very disappointed"
    ]
    
    batch_results = analyzer.analyze_batch(test_texts)
    print(f"Batch analysis results: {batch_results}")
    
    # Test statistics
    stats = analyzer.get_sentiment_statistics(test_texts)
    print(f"Statistics: {stats}")