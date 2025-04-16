"""
Dashboard blueprint for the facial emotion recognition application.

This module provides views for the user dashboard, history, and reports.
"""
from flask import Blueprint, render_template, g, redirect, url_for, request, flash
from app.routes import login_required
from app.database.models import EmotionRecord
from app.database.db import get_db
from app.factory import AppContextManager
import json
from datetime import datetime

# Create blueprint
dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    """Render the main dashboard."""
    user_id = g.user['id'] if g.user else None
    
    if not user_id:
        return redirect(url_for('main_bp.login'))
    
    # Get recent emotion records
    try:
        # Try using the SQLAlchemy method if available
        try:
            records = EmotionRecord.get_recent_by_user(user_id, limit=100)
        except (AttributeError, Exception) as e:
            # Fall back to direct database query
            db = get_db()
            records = db.execute(
                'SELECT * FROM emotion_records WHERE user_id = ? ORDER BY timestamp DESC LIMIT 100',
                (user_id,)
            ).fetchall()
        
        # Process records for the template
        emotion_stats = {}
        emotion_history = []
        most_common_emotion = 'neutral'
        most_common_count = 0
        
        for record in records:
            # Get emotion data
            if hasattr(record, 'emotions_data'):
                # SQLAlchemy model
                emotions_data = json.loads(record.emotions_data)
                timestamp = record.timestamp
                dominant = record.dominant_emotion if hasattr(record, 'dominant_emotion') else 'neutral'
            else:
                # SQLite row
                emotions_data = json.loads(record['emotions_data'])
                timestamp = record['timestamp']
                dominant = record.get('dominant_emotion', 'neutral')
            
            # Update stats
            if dominant not in emotion_stats:
                emotion_stats[dominant] = 1
            else:
                emotion_stats[dominant] += 1
            
            # Update most common emotion
            if emotion_stats[dominant] > most_common_count:
                most_common_emotion = dominant
                most_common_count = emotion_stats[dominant]
            
            # Add to history
            emotion_history.append({
                'timestamp': timestamp,
                'emotions': emotions_data
            })
        
        # Calculate total records
        total_records = sum(emotion_stats.values())
        
        # Generate insights and suggestions (simplified)
        insights = [
            f"Your most common emotion is {most_common_emotion}.",
            "Your emotion patterns show your general mood."
        ]
        
        suggestions = [
            "Try different activities to observe how they affect your emotions.",
            "Regular emotion tracking can help improve emotional awareness."
        ]
        
        return render_template(
            'dashboard.html',
            emotion_stats=emotion_stats,
            emotion_history=emotion_history,
            most_common_emotion=most_common_emotion,
            total_records=total_records,
            insights=insights,
            suggestions=suggestions
        )
    
    except Exception as e:
        # Log the error and show a simple dashboard
        print(f"Error loading dashboard data: {str(e)}")
        return render_template(
            'dashboard.html',
            emotion_stats={},
            emotion_history=[],
            most_common_emotion='neutral',
            total_records=0,
            insights=["Start tracking your emotions to see insights."],
            suggestions=["Use the emotion recognition feature to begin."]
        )

@dashboard_bp.route('/history')
@login_required
def history():
    """Render the emotion history page."""
    user_id = g.user['id'] if g.user and isinstance(g.user, dict) else session.get('user_id')
    
    # Get emotion records
    try:
        # Try using the SQLAlchemy method if available
        try:
            records = EmotionRecord.get_recent_by_user(user_id, limit=500)
        except (AttributeError, Exception) as e:
            # Fall back to direct database query
            db = get_db()
            records = db.execute(
                'SELECT * FROM emotion_records WHERE user_id = ? ORDER BY timestamp DESC LIMIT 500',
                (user_id,)
            ).fetchall()
        
        # Convert records to a format suitable for the template
        history_records = []
        for record in records:
            if hasattr(record, 'to_dict'):
                # SQLAlchemy model with to_dict method
                history_records.append(record.to_dict())
            elif hasattr(record, 'emotions_data'):
                # SQLAlchemy model without to_dict
                history_records.append({
                    'id': record.id,
                    'timestamp': record.timestamp.isoformat() if hasattr(record.timestamp, 'isoformat') else record.timestamp,
                    'emotions': json.loads(record.emotions_data),
                    'dominant_emotion': record.dominant_emotion if hasattr(record, 'dominant_emotion') else 'neutral'
                })
            else:
                # SQLite row
                history_records.append({
                    'id': record['id'],
                    'timestamp': record['timestamp'],
                    'emotions': json.loads(record['emotions_data']),
                    'dominant_emotion': record.get('dominant_emotion', 'neutral')
                })
        
        return render_template('history.html', records=history_records)
    
    except Exception as e:
        # Log the error and show empty history
        print(f"Error loading history data: {str(e)}")
        return render_template('history.html', records=[])

@dashboard_bp.route('/reports')
@login_required
def reports():
    """Render the reports page."""
    # Define report options
    report_options = [
        {
            'id': 'weekly',
            'name': 'Weekly Report',
            'description': 'Summary of your emotions over the past week.'
        },
        {
            'id': 'monthly',
            'name': 'Monthly Report',
            'description': 'Analysis of your emotional patterns over the past month.'
        },
        {
            'id': 'yearly',
            'name': 'Yearly Report',
            'description': 'Comprehensive overview of your emotional trends for the year.'
        }
    ]
    
    # Check if OpenAI API is configured
    openai_configured = bool(current_app.config.get('OPENAI_API_KEY'))
    
    return render_template('reports.html', report_options=report_options, openai_configured=openai_configured)

@dashboard_bp.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    """Generate and display an emotion report."""
    user_id = g.user['id'] if g.user and isinstance(g.user, dict) else session.get('user_id')
    
    # Get report parameters
    report_type = request.form.get('report_type')
    
    # For custom reports, get date range
    start_date = None
    end_date = None
    if report_type == 'custom':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    else:
        # Set default date ranges based on report type
        now = datetime.now()
        if report_type == 'weekly':
            end_date = now.strftime('%Y-%m-%d')
            start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        elif report_type == 'monthly':
            end_date = now.strftime('%Y-%m-%d')
            start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        elif report_type == 'yearly':
            end_date = now.strftime('%Y-%m-%d')
            start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Generate a sample report (in a real app, this would analyze actual data)
    report = {
        'summary': 'This is a sample emotion analysis report. In a complete application, this would contain actual insights derived from your emotion data.',
        'sections': [
            {
                'title': 'Emotion Distribution',
                'items': [
                    'Your dominant emotion during this period was happiness.',
                    'You experienced negative emotions approximately 20% of the time.'
                ]
            },
            {
                'title': 'Patterns and Triggers',
                'items': [
                    'Your emotions tend to be more positive in the mornings.',
                    'There appears to be a correlation between your activities and emotional state.'
                ]
            },
            {
                'title': 'Recommendations',
                'items': [
                    'Consider mindfulness exercises during periods of stress.',
                    'Regular physical activity appears to correlate with improved mood.'
                ]
            }
        ]
    }
    
    return render_template('report_result.html', report=report, report_type=report_type, start_date=start_date, end_date=end_date)