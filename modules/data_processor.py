# Data Processing Module for CSV/Excel File Handling
# modules/data_processor.py

import pandas as pd
import numpy as np
import re
import os
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import chardet

class DataProcessor:
    """
    Handles data ingestion, cleaning, and preprocessing for comment analysis
    Supports CSV and Excel files with automatic format detection
    """
    
    def __init__(self):
        """Initialize the data processor"""
        self.supported_formats = ['.csv', '.xlsx', '.xls']
        self.text_columns = ['comment', 'text', 'feedback', 'review', 'message', 'content']
        self.id_columns = ['id', 'comment_id', 'user_id', 'index']
        self.timestamp_columns = ['timestamp', 'date', 'created_at', 'submitted_at']
        
    def load_and_clean_data(self, filepath: str) -> pd.DataFrame:
        """
        Load data from file and perform basic cleaning
        
        Args:
            filepath: Path to the data file
            
        Returns:
            Cleaned pandas DataFrame
        """
        try:
            # Check file extension
            file_extension = os.path.splitext(filepath)[1].lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Load data based on file type
            if file_extension == '.csv':
                df = self._load_csv(filepath)
            else:
                df = self._load_excel(filepath)
            
            # Basic validation
            if df.empty:
                raise ValueError("File is empty or could not be read")
            
            # Clean and standardize column names
            df = self._standardize_columns(df)
            
            # Clean text data
            df = self._clean_text_data(df)
            
            # Add metadata
            df = self._add_metadata(df, filepath)
            
            print(f"Successfully loaded {len(df)} rows from {filepath}")
            return df
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def _load_csv(self, filepath: str) -> pd.DataFrame:
        """Load CSV file with encoding detection"""
        try:
            # Detect encoding
            with open(filepath, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
            
            # Try loading with detected encoding
            try:
                df = pd.read_csv(filepath, encoding=encoding)
            except UnicodeDecodeError:
                # Fallback encodings
                for fallback_encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(filepath, encoding=fallback_encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode file with any encoding")
            
            return df
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            raise
    
    def _load_excel(self, filepath: str) -> pd.DataFrame:
        """Load Excel file"""
        try:
            # Try to load the first sheet
            df = pd.read_excel(filepath, sheet_name=0)
            
            # If first sheet is empty, try other sheets
            if df.empty:
                excel_file = pd.ExcelFile(filepath)
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    if not df.empty:
                        break
            
            return df
            
        except Exception as e:
            print(f"Error loading Excel: {e}")
            raise
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names and identify text columns"""
        # Clean column names
        df.columns = df.columns.str.lower().str.strip()
        df.columns = df.columns.str.replace(r'[^\w\s]', '', regex=True)
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        
        # Find text column
        text_col = self._identify_text_column(df)
        if text_col:
            df = df.rename(columns={text_col: 'comment_text'})
        else:
            # If no obvious text column, use the first string column
            for col in df.columns:
                if df[col].dtype == 'object':
                    df = df.rename(columns={col: 'comment_text'})
                    break
            else:
                raise ValueError("No text column found in the data")
        
        # Find ID column
        id_col = self._identify_id_column(df)
        if id_col:
            df = df.rename(columns={id_col: 'comment_id'})
        else:
            # Create sequential IDs
            df['comment_id'] = range(1, len(df) + 1)
        
        # Find timestamp column
        timestamp_col = self._identify_timestamp_column(df)
        if timestamp_col:
            df = df.rename(columns={timestamp_col: 'timestamp'})
        
        return df
    
    def _identify_text_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identify the main text column"""
        # Check for obvious text column names
        for col in df.columns:
            col_lower = col.lower()
            if any(text_name in col_lower for text_name in self.text_columns):
                return col
        
        # Find column with longest average text length
        text_candidates = []
        for col in df.columns:
            if df[col].dtype == 'object':
                avg_length = df[col].astype(str).str.len().mean()
                if avg_length > 50:  # Assume comments are at least 50 chars on average
                    text_candidates.append((col, avg_length))
        
        if text_candidates:
            # Return column with longest average length
            return max(text_candidates, key=lambda x: x[1])[0]
        
        return None
    
    def _identify_id_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identify ID column"""
        for col in df.columns:
            col_lower = col.lower()
            if any(id_name in col_lower for id_name in self.id_columns):
                return col
        return None
    
    def _identify_timestamp_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identify timestamp column"""
        for col in df.columns:
            col_lower = col.lower()
            if any(time_name in col_lower for time_name in self.timestamp_columns):
                return col
        return None
    
    def _clean_text_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess text data"""
        if 'comment_text' not in df.columns:
            return df
        
        # Convert to string and handle NaN values
        df['comment_text'] = df['comment_text'].astype(str)
        df = df[df['comment_text'] != 'nan']
        df = df[df['comment_text'].str.strip() != '']
        
        # Basic text cleaning
        df['comment_text'] = df['comment_text'].apply(self._clean_single_text)
        
        # Remove very short texts (likely not meaningful comments)
        df = df[df['comment_text'].str.len() >= 10]
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['comment_text'])
        duplicates_removed = initial_count - len(df)
        
        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate comments")
        
        return df.reset_index(drop=True)
    
    def _clean_single_text(self, text: str) -> str:
        """Clean individual text entry"""
        if pd.isna(text) or text == 'nan':
            return ""
        
        text = str(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _add_metadata(self, df: pd.DataFrame, filepath: str) -> pd.DataFrame:
        """Add metadata columns"""
        df['file_source'] = os.path.basename(filepath)
        df['processed_at'] = datetime.now()
        df['text_length'] = df['comment_text'].str.len()
        df['word_count'] = df['comment_text'].str.split().str.len()
        
        return df
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for the dataset"""
        if df.empty:
            return {"error": "Dataset is empty"}
        
        summary = {
            'total_comments': len(df),
            'avg_text_length': df['text_length'].mean() if 'text_length' in df.columns else 0,
            'avg_word_count': df['word_count'].mean() if 'word_count' in df.columns else 0,
            'shortest_comment': df['text_length'].min() if 'text_length' in df.columns else 0,
            'longest_comment': df['text_length'].max() if 'text_length' in df.columns else 0,
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_values': df.isnull().sum().to_dict(),
        }
        
        # Add timestamp analysis if available
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                summary['date_range'] = {
                    'earliest': df['timestamp'].min().isoformat(),
                    'latest': df['timestamp'].max().isoformat()
                }
            except:
                summary['timestamp_parsing_error'] = True
        
        return summary
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validate data quality and provide recommendations"""
        issues = []
        recommendations = []
        
        # Check for minimum data requirements
        if len(df) < 10:
            issues.append("Very small dataset (< 10 comments)")
            recommendations.append("Consider collecting more data for meaningful analysis")
        
        # Check text quality
        if 'text_length' in df.columns:
            very_short = (df['text_length'] < 20).sum()
            if very_short > len(df) * 0.5:
                issues.append(f"Many comments are very short ({very_short}/{len(df)})")
                recommendations.append("Review data collection process for comment completeness")
        
        # Check for missing data
        if 'comment_text' in df.columns:
            missing_text = df['comment_text'].isnull().sum()
            if missing_text > 0:
                issues.append(f"{missing_text} comments have missing text")
                recommendations.append("Clean or remove comments with missing text")
        
        # Check language consistency (basic check)
        sample_texts = df['comment_text'].head(100).tolist() if 'comment_text' in df.columns else []
        non_english_chars = sum(1 for text in sample_texts if any(ord(char) > 127 for char in text))
        if non_english_chars > len(sample_texts) * 0.3:
            recommendations.append("Consider multi-language sentiment analysis models")
        
        return {
            'quality_score': max(0, 100 - len(issues) * 20),
            'issues': issues,
            'recommendations': recommendations,
            'data_ready_for_analysis': len(issues) == 0
        }
    
    def create_sample_data(self, output_path: str, num_comments: int = 100):
        """Create sample data for testing"""
        sample_comments = [
            "This new policy is excellent and will benefit many citizens.",
            "I strongly disagree with this proposal and think it needs revision.",
            "The implementation timeline seems reasonable but could be improved.",
            "Great initiative! This addresses a long-standing issue.",
            "I have concerns about the budget allocation for this project.",
            "This is a step in the right direction for our community.",
            "The proposal lacks clarity in several important areas.",
            "Fully support this policy change and its objectives.",
            "More consultation with stakeholders would be beneficial.",
            "This could have unintended consequences that need consideration.",
        ]
        
        # Generate sample data
        data = []
        for i in range(num_comments):
            comment = np.random.choice(sample_comments)
            data.append({
                'comment_id': i + 1,
                'comment_text': comment + f" (Sample comment {i + 1})",
                'timestamp': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(0, 30)),
                'user_id': f"user_{np.random.randint(1, 50)}"
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        print(f"Created sample data with {num_comments} comments at {output_path}")
        
        return df

# Example usage and testing
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Create sample data for testing
    sample_path = "data/sample_comments.csv"
    os.makedirs("data", exist_ok=True)
    sample_df = processor.create_sample_data(sample_path, 50)
    
    # Test loading and processing
    loaded_df = processor.load_and_clean_data(sample_path)
    
    # Get summary
    summary = processor.get_data_summary(loaded_df)
    print("Data Summary:", summary)
    
    # Validate quality
    quality = processor.validate_data_quality(loaded_df)
    print("Data Quality:", quality)