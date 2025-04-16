"""
API routes for the facial emotion recognition application.
"""
from flask import Blueprint, jsonify, g, request, Response, current_app, session
from app.database.db import get_db
from app.models.video_processor import VideoStream, active_streams
import time
import json
import functools
from datetime import datetime, timedelta

# Create a Blueprint for the API
api_bp = Blueprint('api', __name__)

# Helper function to get the current user ID
def get_current_user_id():
    """
    Get the current user ID from session.
    
    Returns:
        int: User ID or None if not authenticated
    """
    # First try Flask-Login current_user if it's available
    try:
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            return current_user.id
    except (ImportError, AttributeError):
        pass
    
    # Next try the user_id from session
    if 'user_id' in session:
        return session.get('user_id')
    
    # Finally try g.user if it's set
    if hasattr(g, 'user') and g.user:
        return g.user.get('id')
    
    # No user found
    return None

# Authentication decorator that doesn't use Flask-Login dependency
def login_required(f):
    """
    Decorator to require login for a route.
    
    Args:
        f: The function to decorate
        
    Returns:
        function: The decorated function
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# FIXED: Removed duplicate route decorator
@api_bp.route('/video_feed')
@login_required
def video_feed():
    """
    Video streaming route for emotion recognition.
    This continuously serves MJPEG frames.
    """
    # Get user_id from session if authentication is required
    user_id = session.get('user_id')
    
    # Check if a stream for this user already exists
    from app.models.video_processor import active_streams, VideoStream
    
    if user_id and user_id in active_streams:
        stream = active_streams[user_id]
        # Make sure stream is running
        if not stream.running:
            stream.start()
    else:
        # Create a new stream for this user or session
        stream = VideoStream(user_id=user_id)
        if not stream.start():
            return jsonify({"error": "Failed to start video stream"}), 500
    
    # Define MJPEG streaming response generator
    def generate():
        try:
            while True:
                # Get JPEG frame
                frame = stream.get_jpeg_frame(processed=True)
                
                # Yield the frame in multipart MIME format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                
                # Small sleep to control frame rate and reduce CPU usage
                time.sleep(0.03)  # ~30 FPS
                
        except Exception as e:
            print(f"Error in video feed generator: {str(e)}")
            # Clean yield to prevent browser hanging
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')
    
    # Return streaming response
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@api_bp.route('/analyze_current_emotion')
@login_required
def analyze_current_emotion():
    """
    API endpoint to get the current emotion analysis results.
    Returns the current emotion probabilities from the active video stream.
    """
    # Get user_id from session if authentication is required
    user_id = session.get('user_id')
    
    try:
        # Get the active stream for this user
        from app.models.video_processor import active_streams, VideoStream
        
        # Check if there's an active stream for this user
        if user_id and user_id in active_streams:
            stream = active_streams[user_id]
        else:
            # For demo/anonymous users, get the first active stream or create a new one
            if not active_streams:
                stream = VideoStream(user_id=user_id)
                stream.start()
            else:
                stream = next(iter(active_streams.values()))
        
        # Get the latest processed frame to extract emotions
        frame = stream.get_frame(processed=True)
        
        # Check if emotion history exists
        if not stream.emotion_history or not stream.emotion_history[-1]:
            return jsonify({
                "emotions": {
                    "angry": 0, "disgust": 0, "fear": 0, 
                    "happy": 0, "neutral": 1, "sad": 0, "surprise": 0
                },
                "dominant_emotion": "neutral"
            })
        
        # Get the latest emotion results
        latest_emotions = stream.emotion_history[-1][0]
        
        # Find dominant emotion
        dominant_emotion = max(latest_emotions.items(), key=lambda x: x[1])
        
        # Return emotion data
        return jsonify({
            "emotions": latest_emotions,
            "dominant_emotion": dominant_emotion[0]
        })
        
    except Exception as e:
        print(f"Error analyzing current emotion: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return default neutral values on error
        return jsonify({
            "emotions": {
                "angry": 0, "disgust": 0, "fear": 0, 
                "happy": 0, "neutral": 1, "sad": 0, "surprise": 0
            },
            "dominant_emotion": "neutral",
            "error": str(e)
        })

@api_bp.route('/performance_metrics')
@login_required
def performance_metrics():
    """
    API endpoint to get performance metrics of the video stream.
    Returns FPS and inference time metrics.
    """
    # Get user_id from session if authentication is required
    user_id = session.get('user_id')
    
    try:
        # Get the active stream for this user
        from app.models.video_processor import active_streams, VideoStream
        
        # Check if there's an active stream for this user
        if user_id and user_id in active_streams:
            stream = active_streams[user_id]
        else:
            # For demo/anonymous users, get the first active stream
            if not active_streams:
                return jsonify({
                    "fps": 0,
                    "avg_inference_time": 0,
                    "max_inference_time": 0
                })
            stream = next(iter(active_streams.values()))
        
        # Get performance metrics
        metrics = stream.get_performance_metrics()
        return jsonify(metrics)
        
    except Exception as e:
        print(f"Error getting performance metrics: {str(e)}")
        
        # Return default values on error
        return jsonify({
            "fps": 0,
            "avg_inference_time": 0,
            "max_inference_time": 0,
            "error": str(e)
        })

@api_bp.route('/start_video', methods=['POST'])
@login_required
def start_video():
    """
    Start the video stream.
    
    Returns:
        JSON: Success/error message
    """
    user_id = get_current_user_id()
    
    # Check if the user already has an active stream
    if user_id in active_streams:
        return jsonify({"message": "Video stream already running"})
    
    # Create a new stream for this user
    stream = VideoStream(user_id=user_id)
    if stream.start():
        return jsonify({"message": "Video stream started"})
    else:
        return jsonify({"error": "Failed to start video stream"}), 500

@api_bp.route('/stop_video', methods=['POST'])
@login_required
def stop_video():
    """
    Stop the video stream.
    
    Returns:
        JSON: Success/error message
    """
    user_id = get_current_user_id()
    
    # Check if the user has an active stream
    if user_id in active_streams:
        stream = active_streams[user_id]
        if stream.stop():
            return jsonify({"message": "Video stream stopped"})
        else:
            return jsonify({"error": "Failed to stop video stream"}), 500
    else:
        return jsonify({"message": "No active stream to stop"})