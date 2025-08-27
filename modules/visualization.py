# Visualization Generator Module for Charts and Graphs
# modules/visualization.py

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import os

class VisualizationGenerator:
    """
    Generate interactive visualizations for sentiment analysis and comment data
    Uses Plotly for web-ready charts and graphs
    """
    
    def __init__(self):
        """Initialize visualization generator"""
        self.color_scheme = {
            'positive': '#28a745',
            'negative': '#dc3545', 
            'neutral': '#6c757d',
            'primary': '#007bff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }
        
    def create_sentiment_charts(self, sentiment_data: Dict[str, int]) -> Dict[str, str]:
        """
        Create sentiment analysis charts
        
        Args:
            sentiment_data: Dictionary with sentiment counts
            
        Returns:
            Dictionary with chart HTML/JSON data
        """
        charts = {}
        
        try:
            # Pie chart for sentiment distribution
            charts['pie_chart'] = self._create_sentiment_pie_chart(sentiment_data)
            
            # Bar chart for sentiment counts
            charts['bar_chart'] = self._create_sentiment_bar_chart(sentiment_data)
            
            # Donut chart variation
            charts['donut_chart'] = self._create_sentiment_donut_chart(sentiment_data)
            
            return charts
            
        except Exception as e:
            print(f"Error creating sentiment charts: {e}")
            return {}
    
    def _create_sentiment_pie_chart(self, sentiment_data: Dict[str, int]) -> str:
        """Create interactive pie chart for sentiment distribution"""
        try:
            labels = list(sentiment_data.keys())
            values = list(sentiment_data.values())
            colors = [self.color_scheme.get(label.lower(), '#6c757d') for label in labels]
            
            fig = go.Figure(data=[go.Pie(
                labels=[label.capitalize() for label in labels],
                values=values,
                hole=0.3,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='outside',
                hovertemplate='<b>%{label}</b><br>' +
                             'Count: %{value}<br>' +
                             'Percentage: %{percent}<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title={
                    'text': 'Sentiment Distribution',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20}
                },
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(t=50, b=50, l=20, r=20),
                font=dict(size=12)
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating pie chart: {e}")
            return "{}"
    
    def _create_sentiment_bar_chart(self, sentiment_data: Dict[str, int]) -> str:
        """Create bar chart for sentiment counts"""
        try:
            labels = [label.capitalize() for label in sentiment_data.keys()]
            values = list(sentiment_data.values())
            colors = [self.color_scheme.get(label.lower(), '#6c757d') 
                     for label in sentiment_data.keys()]
            
            fig = go.Figure(data=[go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=values,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>' +
                             'Count: %{y}<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title={
                    'text': 'Sentiment Count Distribution',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Sentiment',
                yaxis_title='Number of Comments',
                showlegend=False,
                margin=dict(t=50, b=50, l=50, r=20)
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating bar chart: {e}")
            return "{}"
    
    def _create_sentiment_donut_chart(self, sentiment_data: Dict[str, int]) -> str:
        """Create donut chart with center text"""
        try:
            labels = list(sentiment_data.keys())
            values = list(sentiment_data.values())
            colors = [self.color_scheme.get(label.lower(), '#6c757d') for label in labels]
            total = sum(values)
            
            fig = go.Figure(data=[go.Pie(
                labels=[label.capitalize() for label in labels],
                values=values,
                hole=0.6,
                marker_colors=colors,
                textinfo='percent',
                textposition='outside'
            )])
            
            # Add center text
            fig.add_annotation(
                text=f"Total<br>{total}<br>Comments",
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )
            
            fig.update_layout(
                title={
                    'text': 'Comment Sentiment Overview',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=50, b=50, l=20, r=20)
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating donut chart: {e}")
            return "{}"
    
    def create_confidence_histogram(self, confidence_scores: List[float]) -> str:
        """Create histogram of confidence scores"""
        try:
            if not confidence_scores:
                return "{}"
            
            fig = go.Figure(data=[go.Histogram(
                x=confidence_scores,
                nbinsx=20,
                marker_color=self.color_scheme['primary'],
                opacity=0.7,
                hovertemplate='Confidence Range: %{x}<br>' +
                             'Count: %{y}<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title={
                    'text': 'Distribution of Confidence Scores',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Confidence Score',
                yaxis_title='Number of Comments',
                bargap=0.2,
                margin=dict(t=50, b=50, l=50, r=20)
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating confidence histogram: {e}")
            return "{}"
    
    def create_keyword_frequency_chart(self, word_frequencies: Dict[str, int], 
                                     top_n: int = 20) -> str:
        """Create horizontal bar chart for top keywords"""
        try:
            if not word_frequencies:
                return "{}"
            
            # Get top N keywords
            sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:top_n]
            words, frequencies = zip(*sorted_words) if sorted_words else ([], [])
            
            # Reverse for better display (highest at top)
            words = words[::-1]
            frequencies = frequencies[::-1]
            
            fig = go.Figure(data=[go.Bar(
                x=frequencies,
                y=words,
                orientation='h',
                marker_color=self.color_scheme['info'],
                text=frequencies,
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>' +
                             'Frequency: %{x}<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title={
                    'text': f'Top {len(words)} Most Frequent Keywords',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Frequency',
                yaxis_title='Keywords',
                margin=dict(t=50, b=50, l=100, r=20),
                height=max(400, len(words) * 25)  # Adjust height based on number of words
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating keyword frequency chart: {e}")
            return "{}"
    
    def create_sentiment_timeline(self, df: pd.DataFrame) -> str:
        """Create timeline chart showing sentiment over time"""
        try:
            if 'timestamp' not in df.columns or 'sentiment' not in df.columns:
                return "{}"
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            
            if df.empty:
                return "{}"
            
            # Group by date and sentiment
            daily_sentiment = df.groupby([df['timestamp'].dt.date, 'sentiment']).size().unstack(fill_value=0)
            
            fig = go.Figure()
            
            for sentiment in daily_sentiment.columns:
                color = self.color_scheme.get(sentiment.lower(), '#6c757d')
                fig.add_trace(go.Scatter(
                    x=daily_sentiment.index,
                    y=daily_sentiment[sentiment],
                    mode='lines+markers',
                    name=sentiment.capitalize(),
                    line=dict(color=color, width=2),
                    marker=dict(color=color, size=6),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Date: %{x}<br>' +
                                 'Count: %{y}<br>' +
                                 '<extra></extra>'
                ))
            
            fig.update_layout(
                title={
                    'text': 'Sentiment Trends Over Time',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Date',
                yaxis_title='Number of Comments',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
                margin=dict(t=50, b=50, l=50, r=20)
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating sentiment timeline: {e}")
            return "{}"
    
    def create_text_length_distribution(self, text_lengths: List[int]) -> str:
        """Create histogram of text lengths"""
        try:
            if not text_lengths:
                return "{}"
            
            fig = go.Figure(data=[go.Histogram(
                x=text_lengths,
                nbinsx=30,
                marker_color=self.color_scheme['secondary'],
                opacity=0.7,
                hovertemplate='Text Length Range: %{x}<br>' +
                             'Count: %{y}<br>' +
                             '<extra></extra>'
            )])
            
            # Add vertical lines for mean and median
            mean_length = np.mean(text_lengths)
            median_length = np.median(text_lengths)
            
            fig.add_vline(x=mean_length, line_dash="dash", line_color="red",
                         annotation_text=f"Mean: {mean_length:.0f}")
            fig.add_vline(x=median_length, line_dash="dot", line_color="blue",
                         annotation_text=f"Median: {median_length:.0f}")
            
            fig.update_layout(
                title={
                    'text': 'Distribution of Comment Lengths',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='Comment Length (characters)',
                yaxis_title='Number of Comments',
                bargap=0.2,
                margin=dict(t=50, b=50, l=50, r=20)
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating text length distribution: {e}")
            return "{}"
    
    def create_summary_dashboard(self, analysis_data: Dict) -> str:
        """Create comprehensive dashboard with multiple subplots"""
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Sentiment Distribution', 'Confidence Scores',
                               'Top Keywords', 'Text Length Distribution'),
                specs=[[{'type': 'pie'}, {'type': 'histogram'}],
                       [{'type': 'bar'}, {'type': 'histogram'}]]
            )
            
            # Sentiment pie chart (top-left)
            if 'sentiment_distribution' in analysis_data:
                sentiment_data = analysis_data['sentiment_distribution']
                labels = list(sentiment_data.keys())
                values = list(sentiment_data.values())
                colors = [self.color_scheme.get(label.lower(), '#6c757d') for label in labels]
                
                fig.add_trace(go.Pie(
                    labels=[label.capitalize() for label in labels],
                    values=values,
                    marker_colors=colors,
                    name="Sentiment"
                ), row=1, col=1)
            
            # Confidence histogram (top-right)
            if 'confidence_scores' in analysis_data:
                confidence_scores = analysis_data['confidence_scores']
                fig.add_trace(go.Histogram(
                    x=confidence_scores,
                    marker_color=self.color_scheme['primary'],
                    name="Confidence"
                ), row=1, col=2)
            
            # Keywords bar chart (bottom-left)
            if 'word_frequencies' in analysis_data:
                word_freq = analysis_data['word_frequencies']
                if word_freq:
                    words = list(word_freq.keys())[:10]
                    frequencies = list(word_freq.values())[:10]
                    
                    fig.add_trace(go.Bar(
                        x=words,
                        y=frequencies,
                        marker_color=self.color_scheme['info'],
                        name="Keywords"
                    ), row=2, col=1)
            
            # Text length histogram (bottom-right)
            if 'text_lengths' in analysis_data:
                text_lengths = analysis_data['text_lengths']
                fig.add_trace(go.Histogram(
                    x=text_lengths,
                    marker_color=self.color_scheme['secondary'],
                    name="Text Length"
                ), row=2, col=2)
            
            fig.update_layout(
                title_text="Comment Analysis Dashboard",
                title_x=0.5,
                height=800,
                showlegend=False
            )
            
            return fig.to_json()
            
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            return "{}"
    
    def save_chart_as_html(self, chart_json: str, output_path: str, title: str = "Chart"):
        """Save chart as standalone HTML file"""
        try:
            if not chart_json or chart_json == "{}":
                return False
            
            fig_dict = json.loads(chart_json)
            fig = go.Figure(fig_dict)
            
            fig.write_html(output_path, include_plotlyjs='cdn')
            print(f"Chart saved as HTML: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving chart as HTML: {e}")
            return False
    
    def export_charts_data(self, charts_data: Dict, output_file: str):
        """Export chart data to JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(charts_data, f, indent=2)
            print(f"Charts data exported to {output_file}")
            
        except Exception as e:
            print(f"Error exporting charts data: {e}")

# Example usage and testing
if __name__ == "__main__":
    viz_gen = VisualizationGenerator()
    
    # Test data
    sentiment_data = {'positive': 45, 'negative': 23, 'neutral': 32}
    confidence_scores = np.random.beta(2, 5, 100).tolist()  # Sample confidence scores
    word_frequencies = {
        'policy': 25, 'government': 20, 'citizen': 18, 'support': 15,
        'change': 12, 'improvement': 10, 'community': 8, 'service': 7
    }
    text_lengths = np.random.normal(150, 50, 100).astype(int).tolist()
    
    # Test individual charts
    sentiment_charts = viz_gen.create_sentiment_charts(sentiment_data)
    print("Sentiment charts created")
    
    confidence_chart = viz_gen.create_confidence_histogram(confidence_scores)
    print("Confidence histogram created")
    
    keyword_chart = viz_gen.create_keyword_frequency_chart(word_frequencies)
    print("Keyword frequency chart created")
    
    # Test dashboard
    analysis_data = {
        'sentiment_distribution': sentiment_data,
        'confidence_scores': confidence_scores,
        'word_frequencies': word_frequencies,
        'text_lengths': text_lengths
    }
    
    dashboard = viz_gen.create_summary_dashboard(analysis_data)
    print("Summary dashboard created")
    
    # Save example chart
    if sentiment_charts.get('pie_chart'):
        viz_gen.save_chart_as_html(
            sentiment_charts['pie_chart'], 
            'test_sentiment_pie.html', 
            'Test Sentiment Distribution'
        )