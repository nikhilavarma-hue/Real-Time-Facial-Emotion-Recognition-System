"""
OpenAI API integration for enhanced emotion analysis.

This module provides integration with OpenAI's GPT models for:
1. Generating insights based on emotion data
2. Providing suggestions based on emotional patterns
3. Enhancing the emotion recognition system with contextual analysis
"""
import os
import json
import time
from flask import current_app
import openai
from app.database.models import EmotionRecord

class OpenAIAnalyzer:
    """
    Class for OpenAI-powered emotion analysis.
    """
    
    def __init__(self):
        """Initialize the OpenAI analyzer."""
        # Set API key from config
        self.api_key = current_app.config['OPENAI_API_KEY']
        if self.api_key:
            openai.api_key = self.api_key
    
    def is_configured(self):
        """Check if OpenAI API is configured."""
        return bool(self.api_key)
    
    def analyze_emotion_data(self, user_id, time_period="day"):
        """
        Analyze emotion data for insights using OpenAI.
        
        Args:
            user_id (int): User ID to analyze
            time_period (str): Time period for analysis (day, week, month)
        
        Returns:
            dict: Analysis results with insights and suggestions
        """
        if not self.is_configured():
            return {
                "error": "OpenAI API not configured",
                "insights": [],
                "suggestions": []
            }
        
        try:
            # Get emotion records for the user
            records = EmotionRecord.get_by_user_id(user_id, limit=50)
            if not records:
                return {
                    "insights": ["Not enough data for analysis"],
                    "suggestions": ["Continue using the app to get personalized insights"]
                }
            
            # Prepare data for OpenAI
            emotions_data = []
            for record in records:
                emotions = json.loads(record['emotions_data'])
                dominant = record['dominant_emotion']
                timestamp = record['timestamp']
                emotions_data.append({
                    "timestamp": timestamp,
                    "dominant_emotion": dominant,
                    "emotions": emotions
                })
            
            # Construct prompt for OpenAI
            prompt = self._construct_analysis_prompt(emotions_data, time_period)
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an emotional intelligence assistant that analyzes emotion data and provides insights and suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Extract insights and suggestions
            try:
                result = self._parse_analysis_response(response_text)
                return result
            except Exception as e:
                print(f"Error parsing analysis response: {str(e)}")
                return {
                    "insights": ["Analysis generated but could not be parsed"],
                    "suggestions": ["Please try again later"],
                    "raw_response": response_text
                }
            
        except Exception as e:
            print(f"Error in OpenAI analysis: {str(e)}")
            return {
                "error": str(e),
                "insights": ["Error during analysis"],
                "suggestions": ["Please try again later"]
            }
    
    def generate_emotion_report(self, user_id, start_date=None, end_date=None):
        """
        Generate a detailed report of emotion data.
        
        Args:
            user_id (int): User ID to analyze
            start_date (str, optional): Start date for the report (ISO format)
            end_date (str, optional): End date for the report (ISO format)
        
        Returns:
            dict: Report data with summary and detailed analysis
        """
        if not self.is_configured():
            return {
                "error": "OpenAI API not configured",
                "summary": "API not configured"
            }
        
        try:
            # Get emotion records for the user
            records = EmotionRecord.get_by_user_id(user_id, limit=100)
            if not records:
                return {
                    "summary": "Not enough data for report generation",
                    "sections": []
                }
            
            # Prepare data for OpenAI
            emotions_data = []
            for record in records:
                emotions = json.loads(record['emotions_data'])
                dominant = record['dominant_emotion']
                timestamp = record['timestamp']
                emotions_data.append({
                    "timestamp": timestamp,
                    "dominant_emotion": dominant,
                    "emotions": emotions
                })
            
            # Get emotion statistics
            stats = EmotionRecord.get_user_stats(user_id)
            emotion_counts = {row['dominant_emotion']: row['count'] for row in stats}
            
            # Construct prompt for report generation
            prompt = self._construct_report_prompt(emotions_data, emotion_counts, start_date, end_date)
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an emotional intelligence assistant that creates detailed reports from emotion data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Extract report sections
            try:
                report = self._parse_report_response(response_text)
                return report
            except Exception as e:
                print(f"Error parsing report response: {str(e)}")
                return {
                    "summary": "Report generated but could not be parsed",
                    "sections": [],
                    "raw_response": response_text
                }
            
        except Exception as e:
            print(f"Error in OpenAI report generation: {str(e)}")
            return {
                "error": str(e),
                "summary": "Error during report generation"
            }
    
    def _construct_analysis_prompt(self, emotions_data, time_period):
        """Construct a prompt for emotion analysis."""
        # Count dominant emotions
        emotion_counts = {}
        for entry in emotions_data:
            dominant = entry["dominant_emotion"]
            emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
        
        # Format the data for the prompt
        formatted_counts = "\n".join([f"- {emotion}: {count} times" for emotion, count in emotion_counts.items()])
        
        prompt = f"""
        I have emotion recognition data from a user over the past {time_period}. 
        Here's a summary of their dominant emotions:
        
        {formatted_counts}
        
        Based on this data, please provide:
        1. Three insights about the user's emotional state (be empathetic and specific)
        2. Three practical suggestions for the user (concrete actions they can take)
        
        Format your response like this:
        INSIGHTS:
        - First insight
        - Second insight
        - Third insight
        
        SUGGESTIONS:
        - First suggestion
        - Second suggestion
        - Third suggestion
        """
        
        return prompt
    
    def _parse_analysis_response(self, response_text):
        """Parse the OpenAI response into insights and suggestions."""
        insights = []
        suggestions = []
        
        # Simple parsing based on the expected format
        sections = response_text.split("INSIGHTS:")
        if len(sections) > 1:
            insights_section = sections[1].split("SUGGESTIONS:")[0]
            insights = [i.strip() for i in insights_section.split("-") if i.strip()]
        
        if "SUGGESTIONS:" in response_text:
            suggestions_section = response_text.split("SUGGESTIONS:")[1]
            suggestions = [s.strip() for s in suggestions_section.split("-") if s.strip()]
        
        return {
            "insights": insights,
            "suggestions": suggestions
        }
    
    def _construct_report_prompt(self, emotions_data, emotion_counts, start_date, end_date):
        """Construct a prompt for report generation."""
        date_range = f"from {start_date} to {end_date}" if start_date and end_date else "from the available data"
        
        # Format emotion counts
        formatted_counts = "\n".join([f"- {emotion}: {count} times" for emotion, count in emotion_counts.items()])
        
        prompt = f"""
        I need to generate an emotion analysis report {date_range}. 
        Here's a summary of the user's dominant emotions:
        
        {formatted_counts}
        
        Based on this data, please create a comprehensive report with:
        1. A brief executive summary of the emotional patterns
        2. Key findings and patterns
        3. Actionable recommendations
        
        Format your response like this:
        SUMMARY:
        [A paragraph summarizing the overall emotional patterns]
        
        PATTERNS:
        - [First pattern/finding]
        - [Second pattern/finding]
        - [Third pattern/finding]
        
        RECOMMENDATIONS:
        - [First recommendation]
        - [Second recommendation]
        - [Third recommendation]
        """
        
        return prompt
    
    def _parse_report_response(self, response_text):
        """Parse the OpenAI response into a structured report."""
        summary = ""
        patterns = []
        recommendations = []
        
        # Extract summary
        if "SUMMARY:" in response_text:
            summary_section = response_text.split("SUMMARY:")[1].split("PATTERNS:")[0]
            summary = summary_section.strip()
        
        # Extract patterns
        if "PATTERNS:" in response_text:
            patterns_section = response_text.split("PATTERNS:")[1].split("RECOMMENDATIONS:")[0]
            patterns = [p.strip() for p in patterns_section.split("-") if p.strip()]
        
        # Extract recommendations
        if "RECOMMENDATIONS:" in response_text:
            recommendations_section = response_text.split("RECOMMENDATIONS:")[1]
            recommendations = [r.strip() for r in recommendations_section.split("-") if r.strip()]
        
        # Structure the report
        report = {
            "summary": summary,
            "sections": [
                {"title": "Key Patterns", "items": patterns},
                {"title": "Recommendations", "items": recommendations}
            ]
        }
        
        return report