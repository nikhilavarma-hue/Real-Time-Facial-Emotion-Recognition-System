"""Configuration settings for the facial emotion recognition application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///instance/facial_emotion.db')
    
    # Model paths
    MODEL_PATH = os.getenv('MODEL_PATH', 'emotion_model_final.keras')
    MODEL_PATHS = [
        os.getenv('MODEL_PATH', 'emotion_model_final.keras'),
        'app/models/saved_models/emotion_model_final.keras',
        'model/emotion_model_final.keras',
        './emotion_model_final.keras'
    ]
    
    # Emotion classes matching the trained model
    EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
    
    # Image size for model input
    IMG_SIZE = 96
    
    # Face detector settings
    FACE_DETECTOR = os.getenv('FACE_DETECTOR', 'haar')
    FACE_CONFIDENCE_THRESHOLD = 0.5
    
    # API keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Video settings
    FRAME_INTERVAL = float(os.getenv('FRAME_INTERVAL', '0.1'))
    STORAGE_INTERVAL = float(os.getenv('STORAGE_INTERVAL', '2.0'))
    MAX_CONCURRENT_USERS = int(os.getenv('MAX_CONCURRENT_USERS', '10'))
    
    # Performance settings
    MAX_INFERENCE_TIME = float(os.getenv('MAX_INFERENCE_TIME', '0.5'))
    
    # UI settings
    UI_UPDATE_INTERVAL = int(os.getenv('UI_UPDATE_INTERVAL', '100'))
    
    # Confidence threshold for emotion predictions
    EMOTION_CONFIDENCE_THRESHOLD = float(os.getenv('EMOTION_CONFIDENCE_THRESHOLD', '0.4'))
    
    # Face detection model paths
    FACE_DNN_PROTOTXT = os.getenv('FACE_DNN_PROTOTXT', 'app/models/detectors/deploy.prototxt')
    FACE_DNN_MODEL = os.getenv('FACE_DNN_MODEL', 'app/models/detectors/res10_300x300_ssd_iter_140000.caffemodel')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    # Use absolute path for development database
    DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              'instance', 
                                              'facial_emotion.db')
    # Shorter intervals for faster development feedback
    FRAME_INTERVAL = float(os.getenv('FRAME_INTERVAL', '0.1'))
    STORAGE_INTERVAL = float(os.getenv('STORAGE_INTERVAL', '5.0'))

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    DATABASE_URI = 'sqlite:///:memory:'
    # Use mock data for testing
    MOCK_EMOTION_DATA = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, ensure SECRET_KEY is properly set
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Higher intervals for better performance
    FRAME_INTERVAL = float(os.getenv('FRAME_INTERVAL', '0.2'))
    
    # Make sure we have a proper error if SECRET_KEY is not set
    assert SECRET_KEY, "SECRET_KEY environment variable must be set in production!"
    
    # Default to DNN face detector in production for better accuracy
    FACE_DETECTOR = os.getenv('FACE_DETECTOR', 'dnn')

# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}