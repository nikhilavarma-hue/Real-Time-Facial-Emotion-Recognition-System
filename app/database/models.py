"""
Database models for the facial emotion recognition application.
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

db = SQLAlchemy()

class EmotionRecord(db.Model):
    """
    Model for storing emotion recognition results.
    """
    __tablename__ = 'emotion_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    emotions_data = db.Column(db.Text, nullable=False)  # JSON string of emotion probabilities
    
    # Define relationship
    user = db.relationship('User', backref=db.backref('emotion_records', lazy=True))
    
    def __init__(self, user_id, emotions_data):
        """
        Initialize an emotion record.
        
        Args:
            user_id (int): ID of the user who generated this record
            emotions_data (dict): Dictionary of emotion probabilities
        """
        self.user_id = user_id
        
        # Convert dict to JSON string
        if isinstance(emotions_data, dict):
            self.emotions_data = json.dumps(emotions_data)
        else:
            self.emotions_data = emotions_data
    
    @property
    def emotions(self):
        """
        Get the emotions data as a dictionary.
        
        Returns:
            dict: Dictionary of emotion probabilities
        """
        try:
            return json.loads(self.emotions_data)
        except Exception as e:
            print(f"Error parsing emotions data: {str(e)}")
            return {}
    
    @property
    def dominant_emotion(self):
        """
        Get the dominant emotion.
        
        Returns:
            tuple: (emotion_name, probability)
        """
        emotions = self.emotions
        if not emotions:
            return ('neutral', 0.0)
        
        return max(emotions.items(), key=lambda x: x[1])
    
    def to_dict(self):
        """
        Convert the record to a dictionary for API responses.
        
        Returns:
            dict: Dictionary representation of the record
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'emotions': self.emotions,
            'dominant_emotion': self.dominant_emotion
        }
    
    def save(self):
        """
        Save the record to the database.
        """
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error saving emotion record: {str(e)}")
            db.session.rollback()
            return False
    
    @classmethod
    def get_recent_by_user(cls, user_id, limit=10):
        """
        Get recent emotion records for a user.
        
        Args:
            user_id (int): ID of the user
            limit (int, optional): Maximum number of records to return
            
        Returns:
            list: List of EmotionRecord objects
        """
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.timestamp.desc()).limit(limit).all()
        except Exception as e:
            print(f"Error fetching emotion records: {str(e)}")
            return []

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    settings = db.Column(db.Text, default='{}')  # JSON string of user settings

    def __init__(self, username, email, password_hash=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    # Existing methods...

    @classmethod
    def get_by_username(cls, username):
        """
        Retrieve a user by their username.
        
        Args:
            username (str): The username to search for.
        
        Returns:
            User: The matching user record, or None if not found.
        """
        return cls.query.filter_by(username=username).first()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'settings': self.user_settings
        }
    
    @property
    def user_settings(self):
        try:
            return json.loads(self.settings)
        except Exception:
            return {}
    
    # Relationship with Session etc.
    sessions = db.relationship('Session', back_populates='user', cascade='all, delete-orphan')

class Session(db.Model):
    """
    Model for storing user session data.
    """
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime)
    emotion_data = db.Column(db.Text)  # JSON string of session emotion data
    
    # Define relationship with User
    user = db.relationship('User', back_populates='sessions')

    def __init__(self, user_id, emotion_data=None):
        self.user_id = user_id
        self.emotion_data = json.dumps(emotion_data) if emotion_data else '{}'

    @property
    def emotions(self):
        try:
            return json.loads(self.emotion_data)
        except Exception as e:
            current_app.logger.error(f"Error parsing emotion data: {str(e)}")
            return {}

    def add_emotion_data(self, new_data):
        try:
            current_data = self.emotions
            current_data.update(new_data)
            self.emotion_data = json.dumps(current_data)
            return True
        except Exception as e:
            current_app.logger.error(f"Error updating emotion data: {str(e)}")
            return False

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"Error saving session: {str(e)}")
            db.session.rollback()
            return False

    @classmethod
    def get_active_session(cls, user_id):
        return cls.query.filter_by(user_id=user_id, end_time=None).first()

    def close_session(self):
        self.end_time = datetime.utcnow()
        return self.save()