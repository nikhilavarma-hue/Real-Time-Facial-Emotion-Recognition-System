"""
Facial emotion recognition model based on MobileNetV2.

This module handles loading, inference, and potentially training of the 
facial emotion recognition model.
"""
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from flask import current_app

class EmotionRecognitionModel:
    """
    Facial emotion recognition model class.
    
    Handles loading the model, preprocessing images, and running inference.
    """
    
    def __init__(self, model_path=None):
        """
        Initialize the emotion recognition model.
        
        Args:
            model_path (str, optional): Path to the pretrained model. If None,
                                        uses the path from app config.
        """
        self.model = None
        self.model_path = model_path
        self.emotions = current_app.config['EMOTIONS']
        self.img_size = current_app.config['IMG_SIZE']
        self.confidence_threshold = current_app.config.get('EMOTION_CONFIDENCE_THRESHOLD', 0.4)
        
    def load(self):
        """
        Load the pre-trained model.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            # Get model paths from config
            model_paths = current_app.config['MODEL_PATHS']
            
            # If model_path is explicitly provided, try that first
            if self.model_path:
                model_paths.insert(0, self.model_path)
            
            # Try loading from each path in the list
            for path in model_paths:
                if os.path.exists(path):
                    try:
                        print(f"Attempting to load model from {path}")
                        
                        # Handle TensorFlow 2.x .keras format
                        # Note: We're explicitly telling TF to use custom_objects={} to avoid any issues
                        # with missing custom layers/objects
                        with tf.keras.utils.custom_object_scope({}):
                            # Load without compiling first to avoid any optimizer state issues
                            self.model = load_model(path, compile=False)
                        
                        # Compile the model with appropriate optimizer settings
                        self.model.compile(
                            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
                            loss='categorical_crossentropy',
                            metrics=['accuracy']
                        )
                        
                        print(f"Model loaded successfully from {path}")
                        self.model_path = path  # Update model_path to the successful one
                        
                        # Print model summary for verification
                        print("Model summary:")
                        self.model.summary()
                        
                        # Warm up the model with a dummy prediction
                        dummy_input = np.zeros((1, self.img_size, self.img_size, 3), dtype=np.float32)
                        self.model.predict(dummy_input, verbose=0)
                        print("Model warmed up successfully")
                        
                        return True
                    except Exception as e:
                        print(f"Could not load model from {path}: {str(e)}")
                        continue
            
            # If we get here, no model was loaded
            print("No model found in any of the specified paths.")
            print("Paths checked:", model_paths)
            print("Current working directory:", os.getcwd())
            print("Creating a new model for development purposes...")
            self.model = self._create_model()
            return True
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False
    
    def _create_model(self):
        """
        Create a new model if pretrained model is not available.
        This is mainly for development purposes.
        
        Returns:
            tf.keras.Model: Created model
        """
        print("Creating a backup model with MobileNetV2 architecture...")
        
        # Create base model with pre-trained weights
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(self.img_size, self.img_size, 3)
        )
        
        # Freeze base model layers
        base_model.trainable = False
        
        # Create model with custom top layers
        inputs = tf.keras.Input(shape=(self.img_size, self.img_size, 3), name="input_layer")
        
        # Preprocess input (scale pixel values to [-1, 1])
        x = tf.keras.layers.Lambda(lambda x: x / 127.5 - 1.0, name="preprocess")(inputs)
        
        # Pass through the base model
        x = base_model(x, training=False)
        
        # Add custom top layers matching your model architecture
        x = GlobalAveragePooling2D()(x)
        x = Dropout(0.5)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.3)(x)
        outputs = Dense(len(self.emotions), activation='softmax')(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        
        # Compile model
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.0001)
        model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print("Backup model created - WARNING: This model has not been trained for emotion recognition")
        return model
    
    def preprocess_image(self, image):
        """
        Preprocess an image for model inference.
        
        Args:
            image (numpy.ndarray): Input image (RGB, any size)
            
        Returns:
            numpy.ndarray: Preprocessed image ready for the model
        """
        # Resize if needed
        if image.shape[0] != self.img_size or image.shape[1] != self.img_size:
            image = tf.image.resize(image, (self.img_size, self.img_size)).numpy()
        
        # Ensure the image is in the correct format (RGB, float32)
        if image.dtype != np.float32:
            image = image.astype(np.float32)
        
        # Scale to [-1, 1] as per MobileNetV2 requirements
        if image.max() > 1.0:  # If the image is in [0, 255] range
            image = image / 127.5 - 1.0
        
        return image
    
    def predict(self, image):
        """
        Run inference on an image.
        
        Args:
            image (numpy.ndarray): Input image (RGB, self.img_size x self.img_size)
            
        Returns:
            dict: Dictionary mapping emotion names to probabilities
        """
        if self.model is None:
            print("Model not loaded. Call load() first.")
            return None
        
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        # Ensure image has correct shape (add batch dimension if needed)
        if len(processed_image.shape) == 3:
            processed_image = np.expand_dims(processed_image, axis=0)
        
        # Make prediction
        try:
            predictions = self.model.predict(processed_image, verbose=0)
            
            # Map predictions to emotions
            result = dict(zip(self.emotions, predictions[0].tolist()))
            
            # Apply confidence thresholding
            max_prob = max(result.values())
            if max_prob < self.confidence_threshold:
                # If below threshold, increase probability of 'neutral'
                for emotion in result:
                    if emotion == 'neutral':
                        result[emotion] = max(result[emotion], 0.6)
                    else:
                        result[emotion] *= 0.8
                
                # Normalize so probabilities sum to 1
                sum_probs = sum(result.values())
                for emotion in result:
                    result[emotion] /= sum_probs
            
            return result
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            # Return a fallback prediction (neutral emotion)
            fallback = {emotion: 0.0 for emotion in self.emotions}
            fallback['neutral'] = 1.0
            return fallback
    
    def save(self, save_path=None):
        """
        Save the model to disk.
        
        Args:
            save_path (str, optional): Path to save the model. If None,
                                      uses the model_path from initialization.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self.model is None:
            print("No model to save. Call load() or _create_model() first.")
            return False
        
        try:
            save_path = save_path or self.model_path
            # Ensure the directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save the model
            self.model.save(save_path)
            print(f"Model saved to {save_path}")
            return True
            
        except Exception as e:
            print(f"Error saving model: {str(e)}")
            return False