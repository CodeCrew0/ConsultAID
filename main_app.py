# AI-Driven Comment Analysis Website - Main Flask Application
# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import pandas as pd
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3

# Import custom modules
from modules.data_processor import DataProcessor
from modules.sentiment_analyzer import SentimentAnalyzer
from modules.text_summarizer import TextSummarizer
from modules.keyword_extractor import KeywordExtractor
from modules.visualization import VisualizationGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize processing modules
data_processor = DataProcessor()
sentiment_analyzer = SentimentAnalyzer()
text_summarizer = TextSummarizer()
keyword_extractor = KeywordExtractor()
viz_generator = VisualizationGenerator()

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload and initial processing"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Process the uploaded file
                df = data_processor.load_and_clean_data(filepath)
                
                # Store processing session info
                session_id = timestamp.rstrip('_')
                
                # Redirect to dashboard with session info
                return redirect(url_for('dashboard', session_id=session_id, filename=filename))
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload CSV or Excel files only.')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/dashboard/<session_id>/<filename>')
def dashboard(session_id, filename):
    """Main dashboard with analysis results"""
    try:
        # Load the processed data
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = data_processor.load_and_clean_data(filepath)
        
        # Get basic statistics
        total_comments = len(df)
        
        # Perform sentiment analysis
        sentiments = sentiment_analyzer.analyze_batch(df['comment_text'].tolist())
        df['sentiment'] = sentiments
        
        # Generate sentiment distribution
        sentiment_dist = df['sentiment'].value_counts().to_dict()
        
        # Generate visualizations
        charts = viz_generator.create_sentiment_charts(sentiment_dist)
        
        return render_template('dashboard.html', 
                             session_id=session_id,
                             filename=filename,
                             total_comments=total_comments,
                             sentiment_dist=sentiment_dist,
                             charts=charts)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}')
        return redirect(url_for('upload_file'))

@app.route('/api/analyze/<session_id>/<filename>')
def api_analyze(session_id, filename):
    """API endpoint for real-time analysis"""
    try:
        # Load data
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = data_processor.load_and_clean_data(filepath)
        
        # Perform complete analysis
        results = {
            'sentiment_analysis': {},
            'summarization': {},
            'keywords': {},
            'word_cloud': {}
        }
        
        # Sentiment Analysis
        sentiments = sentiment_analyzer.analyze_batch(df['comment_text'].tolist())
        df['sentiment'] = sentiments
        results['sentiment_analysis'] = {
            'distribution': df['sentiment'].value_counts().to_dict(),
            'confidence_scores': sentiment_analyzer.get_confidence_scores(df['comment_text'].tolist())
        }
        
        # Text Summarization
        sample_comments = df['comment_text'].head(100).tolist()  # Summarize first 100 comments
        summary = text_summarizer.summarize_batch(sample_comments)
        results['summarization'] = {
            'summary': summary,
            'original_count': len(sample_comments)
        }
        
        # Keyword Extraction
        all_text = ' '.join(df['comment_text'].tolist())
        keywords = keyword_extractor.extract_keywords(all_text)
        results['keywords'] = keywords
        
        # Word Cloud Data
        word_freq = keyword_extractor.get_word_frequencies(all_text)
        results['word_cloud'] = word_freq
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/word-cloud/<session_id>/<filename>')
def generate_wordcloud(session_id, filename):
    """Generate and return word cloud image"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = data_processor.load_and_clean_data(filepath)
        
        all_text = ' '.join(df['comment_text'].tolist())
        
        # Generate word cloud image
        img_path = keyword_extractor.generate_wordcloud_image(all_text, session_id)
        
        return send_file(img_path, mimetype='image/png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/<session_id>/<filename>')
def export_results(session_id, filename):
    """Export analysis results as Excel/PDF"""
    try:
        # Load and analyze data
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = data_processor.load_and_clean_data(filepath)
        
        # Perform analysis
        sentiments = sentiment_analyzer.analyze_batch(df['comment_text'].tolist())
        df['sentiment'] = sentiments
        
        # Add summaries for long comments
        df['summary'] = df['comment_text'].apply(
            lambda x: text_summarizer.summarize_single(x) if len(x) > 200 else x
        )
        
        # Export to Excel
        export_path = f"static/exports/analysis_results_{session_id}.xlsx"
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        with pd.ExcelWriter(export_path) as writer:
            df.to_excel(writer, sheet_name='Analysis Results', index=False)
            
            # Summary sheet
            summary_df = pd.DataFrame({
                'Metric': ['Total Comments', 'Positive', 'Negative', 'Neutral'],
                'Count': [
                    len(df),
                    len(df[df['sentiment'] == 'positive']),
                    len(df[df['sentiment'] == 'negative']),
                    len(df[df['sentiment'] == 'neutral'])
                ]
            })
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        return send_file(export_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Get analysis progress for real-time updates"""
    # This would track progress for long-running analyses
    # For now, return a simple response
    return jsonify({'progress': 100, 'status': 'complete'})

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 16MB.')
    return redirect(url_for('upload_file'))

@app.errorhandler(500)
def internal_error(e):
    flash('An internal error occurred. Please try again.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/exports', exist_ok=True)
    os.makedirs('static/wordclouds', exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)