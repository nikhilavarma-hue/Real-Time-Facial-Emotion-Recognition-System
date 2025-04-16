"""
Video processing module for real-time facial emotion recognition.

This module handles webcam capture, processing, and real-time analysis
for the emotion recognition system.
"""
import time
import threading
import cv2
import numpy as np
from datetime import datetime
from flask import current_app, g

from app.models.preprocessing import FacePreprocessor
from app.models.emotion_model import EmotionRecognitionModel
from app.database.db import get_db

# Dictionary to store all active video streams
active_streams = {}

def cleanup_video_streams():
    """Clean up all active video streams when the application exits."""
    for stream in list(active_streams.values()):
        try:
            stream.stop()
        except Exception as e:
            print(f"Error stopping video stream: {e}")
    active_streams.clear()

class VideoStream:
    """
    Class to handle video streaming and processing.
    
    This class manages the webcam stream, frame processing, and
    emotion recognition in real-time.
    """
    
    def __init__(self, user_id=None, camera_id=0):
        """
        Initialize the video stream.
        
        Args:
            user_id (int, optional): User ID for storing results in the database
            camera_id (int, optional): Camera device ID (default: 0)
        """
        self.user_id = user_id
        self.camera_id = camera_id
        self.frame = None
        self.processed_frame = None
        self.running = False
        self.lock = threading.Lock()
        self.fps = 0
        
        # Initialize face preprocessor
        self.face_preprocessor = FacePreprocessor()
        
        # Initialize emotion model
        self.emotion_model = None
        
        # Frame processing interval (seconds)
        self.frame_interval = current_app.config.get('FRAME_INTERVAL', 0.1)
        self.last_process_time = 0
        
        # Storage interval (seconds) - don't store every processed frame
        self.storage_interval = current_app.config.get('STORAGE_INTERVAL', 2.0)
        self.last_storage_time = 0
        
        # Emotion history for smoothing
        self.emotion_history = []
        self.max_history_length = 5
        
        # Performance monitoring
        self.inference_times = []
        self.max_inference_times = 100  # Keep track of this many recent times
        
        # Debug mode
        self.debug = current_app.config.get('DEBUG', False)
        
        # Add to active streams dictionary
        if user_id:
            active_streams[user_id] = self
    
    def start(self):
        """
        Start the video stream.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            print("Video stream is already running")
            return False
        
        # Initialize the emotion model
        self.emotion_model = EmotionRecognitionModel()
        if not self.emotion_model.load():
            print("Failed to load emotion model")
            return False
        
        # Start the video capture thread
        self.running = True
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True
        self.thread.start()
        print("Video stream started")
        return True
    
    def stop(self):
        """
        Stop the video stream.
        
        Returns:
            bool: True if stopped successfully
        """
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        
        # Release the camera
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        
        # Remove from active streams
        if self.user_id in active_streams:
            del active_streams[self.user_id]
        
        print("Video stream stopped")
        return True
    
    def _update(self):
        """Video capture thread function."""
        # Initialize camera
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            print(f"ERROR: Could not open camera {self.camera_id}")
            self.running = False
            return
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Calculate FPS
        fps_counter = 0
        fps_start_time = time.time()
        last_process_time = time.time()
        
        print("Camera initialized. Starting video processing loop...")
        
        while self.running:
            try:
                # Read frame from camera
                ret, frame = self.cap.read()
                
                if not ret:
                    print("ERROR: Failed to grab frame")
                    # Try to reinitialize the camera
                    self.cap.release()
                    time.sleep(1)
                    self.cap = cv2.VideoCapture(self.camera_id)
                    continue
                
                # Update FPS counter
                fps_counter += 1
                current_time = time.time()
                if (current_time - fps_start_time) > 1.0:
                    self.fps = fps_counter
                    fps_counter = 0
                    fps_start_time = current_time
                
                # Store the original frame
                with self.lock:
                    self.frame = frame.copy()
                
                # Process frame at specified interval
                if (current_time - last_process_time) >= self.frame_interval:
                    # THIS IS THE CRITICAL PART - Process the frame
                    self._process_frame(frame)
                    last_process_time = current_time
                    
            except Exception as e:
                print(f"Error in video capture thread: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)  # Prevent CPU spinning on persistent errors
            """Video capture thread function."""
            # Initialize camera
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {self.camera_id}")
                self.running = False
                return
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Calculate FPS
            fps_counter = 0
            fps_start_time = time.time()
            frame_count = 0  # Added frame counter for potential frame skipping
            
            while self.running:
                try:
                    # Read frame from camera
                    ret, frame = self.cap.read()
                    
                    if not ret:
                        print("Error: Failed to grab frame")
                        # Try to reinitialize the camera
                        self.cap.release()
                        time.sleep(1)
                        self.cap = cv2.VideoCapture(self.camera_id)
                        continue
                    
                    # Update FPS counter
                    fps_counter += 1
                    if (time.time() - fps_start_time) > 1.0:
                        self.fps = fps_counter
                        fps_counter = 0
                        fps_start_time = time.time()
                    
                    # Store the original frame
                    with self.lock:
                        self.frame = frame.copy()
                    
                    # Process frame at specified interval
                    current_time = time.time()
                    frame_count += 1
                    
                    # Process every other frame to improve performance if needed
                    # Remove the modulo check if you want to process every frame
                    if (current_time - self.last_process_time) >= self.frame_interval:
                        self.last_process_time = current_time
                        
                        # Process the frame - THIS WAS MISSING
                        self._process_frame(frame)
                        
                except Exception as e:
                    print(f"Error in video capture thread: {str(e)}")
                    time.sleep(0.1)  # Prevent CPU spinning on persistent errors
                """Video capture thread function."""
                # Initialize camera
                self.cap = cv2.VideoCapture(self.camera_id)
                
                if not self.cap.isOpened():
                    print(f"Error: Could not open camera {self.camera_id}")
                    self.running = False
                    return
                
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                # Calculate FPS
                fps_counter = 0
                fps_start_time = time.time()
                
                while self.running:
                    # Read frame from camera
                    ret, frame = self.cap.read()
                    
                    if not ret:
                        print("Error: Failed to grab frame")
                        # Try to reinitialize the camera
                        self.cap.release()
                        time.sleep(1)
                        self.cap = cv2.VideoCapture(self.camera_id)
                        continue
                    
                    # Update FPS counter
                    fps_counter += 1
                    if (time.time() - fps_start_time) > 1.0:
                        self.fps = fps_counter
                        fps_counter = 0
                        fps_start_time = time.time()
                    
                    # Store the original frame
                    with self.lock:
                        self.frame = frame.copy()
                    
                    # Process frame at specified interval
                    current_time = time.time()
                    # Ensure emotion_results is defined
                    emotion_results = []
                    if self.user_id is not None and emotion_results and (current_time - self.last_storage_time) >= self.storage_interval:
                        self.last_storage_time = current_time
                        
                        # For simplicity, just use the first face
                        try:
                            # Use application context manager to ensure proper database access
                            with current_app.app_context_manager():
                                db = get_db()
                                # Store emotion data as JSON
                                import json
                                emotion_data = json.dumps(emotion_results[0])
                                
                                # Insert emotion record
                                db.execute(
                                    "INSERT INTO emotion_records (user_id, timestamp, emotions_data) VALUES (?, ?, ?)",
                                    (self.user_id, datetime.utcnow().isoformat(), emotion_data)
                                )
                                db.commit()
                        except Exception as e:
                            print(f"Error saving emotion record: {str(e)}")
        
    
    
    
    def _process_frame(self, frame):
        """
        Process a video frame for emotion recognition.
        
        Args:
            frame (numpy.ndarray): Input video frame
        """
        # Start timer
        start_time = time.time()
        
        try:
            # Detect and preprocess faces
            preprocessed_faces, face_rects = self.face_preprocessor.detect_and_preprocess(frame)
            
            # Skip if no faces detected
            if not preprocessed_faces:
                # Draw debug info on frame
                debug_frame = frame.copy()
                cv2.putText(debug_frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(debug_frame, f"FPS: {self.fps}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                with self.lock:
                    self.processed_frame = debug_frame
                return
            
            # Run emotion recognition for each face
            emotion_results = []
            for face in preprocessed_faces:
                # Get emotion predictions
                emotion_result = self.emotion_model.predict(face)
                
                # Apply temporal smoothing if we have history
                if self.emotion_history:
                    # Get the last prediction for this face
                    if len(self.emotion_history) > 0:
                        last_emotions = self.emotion_history[-1]
                        if last_emotions:  # If we have previous emotions
                            # Apply weighted average (70% new, 30% previous)
                            smoothed_result = {}
                            for emotion, prob in emotion_result.items():
                                smoothed_result[emotion] = 0.7 * prob + 0.3 * last_emotions[0].get(emotion, 0)
                            
                            # Normalize probabilities
                            total = sum(smoothed_result.values())
                            for emotion in smoothed_result:
                                smoothed_result[emotion] /= total
                            
                            emotion_result = smoothed_result
                
                emotion_results.append(emotion_result)
            
            # Update emotion history
            self.emotion_history.append(emotion_results)
            if len(self.emotion_history) > self.max_history_length:
                self.emotion_history.pop(0)
            
            # Store inference time
            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)
            if len(self.inference_times) > self.max_inference_times:
                self.inference_times.pop(0)
            
            # Save to database if user_id is provided, but not every frame
            current_time = time.time()
            if self.user_id is not None and emotion_results and (current_time - self.last_storage_time) >= self.storage_interval:
                self.last_storage_time = current_time
                
                # For simplicity, just use the first face
                try:
                    # Use standard Flask application context
                    with current_app.app_context():
                        # Try SQLAlchemy first
                        try:
                            from app.database.models import EmotionRecord
                            
                            # Create a new emotion record
                            emotion_record = EmotionRecord(
                                user_id=self.user_id,
                                emotions_data=emotion_results[0]
                            )
                            
                            # Save the record
                            emotion_record.save()
                            print(f"Saved emotion record for user {self.user_id}")
                            
                        except ImportError:
                            # Fall back to direct database access
                            db = get_db()
                            import json
                            emotion_data = json.dumps(emotion_results[0])
                            
                            # Insert emotion record
                            db.execute(
                                "INSERT INTO emotion_records (user_id, timestamp, emotions_data) VALUES (?, ?, ?)",
                                (self.user_id, datetime.utcnow().isoformat(), emotion_data)
                            )
                            db.commit()
                            print(f"Saved emotion record for user {self.user_id}")
                            
                except Exception as e:
                    print(f"Error saving emotion record: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # Draw results on frame
            processed_frame = self.face_preprocessor.draw_results(frame, face_rects, emotion_results)
            
            # Add performance metrics to the frame
            avg_inference_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0
            cv2.putText(processed_frame, f"FPS: {self.fps}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(processed_frame, f"Inference: {avg_inference_time*1000:.1f}ms", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw emotion distribution meter
            if emotion_results:
                self._draw_emotion_meter(processed_frame, emotion_results[0])
            
            # Update the processed frame
            with self.lock:
                self.processed_frame = processed_frame
                
        except Exception as e:
            # Handle any unexpected errors
            print(f"Error processing frame: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Create an error frame
            error_frame = frame.copy()
            cv2.putText(error_frame, f"Error: {str(e)[:50]}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            with self.lock:
                self.processed_frame = error_frame
            """
            Process a video frame for emotion recognition.
            
            Args:
                frame (numpy.ndarray): Input video frame
            """
            # Start timer
            start_time = time.time()
            
            # Detect and preprocess faces
            preprocessed_faces, face_rects = self.face_preprocessor.detect_and_preprocess(frame)
            
            # Skip if no faces detected
            if not preprocessed_faces:
                # Draw debug info on frame
                debug_frame = frame.copy()
                cv2.putText(debug_frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(debug_frame, f"FPS: {self.fps}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                with self.lock:
                    self.processed_frame = debug_frame
                return
            
            # Run emotion recognition for each face
            emotion_results = []
            for face in preprocessed_faces:
                # Get emotion predictions
                emotion_result = self.emotion_model.predict(face)
                
                # Apply temporal smoothing if we have history
                if self.emotion_history:
                    # Get the last prediction for this face
                    # This is a simplified approach - in a real app you'd need face tracking/matching
                    if len(self.emotion_history) > 0:
                        last_emotions = self.emotion_history[-1]
                        if last_emotions:  # If we have previous emotions
                            # Apply weighted average (70% new, 30% previous)
                            smoothed_result = {}
                            for emotion, prob in emotion_result.items():
                                smoothed_result[emotion] = 0.7 * prob + 0.3 * last_emotions[0].get(emotion, 0)
                            
                            # Normalize probabilities
                            total = sum(smoothed_result.values())
                            for emotion in smoothed_result:
                                smoothed_result[emotion] /= total
                            
                            emotion_result = smoothed_result
                
                emotion_results.append(emotion_result)
            
            # Update emotion history
            self.emotion_history.append(emotion_results)
            if len(self.emotion_history) > self.max_history_length:
                self.emotion_history.pop(0)
            
            # Store inference time
            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)
            if len(self.inference_times) > self.max_inference_times:
                self.inference_times.pop(0)
            
            # Save to database if user_id is provided, but not every frame
            # Save to database if user_id is provided, but not every frame
            current_time = time.time()
            if self.user_id is not None and emotion_results and (current_time - self.last_storage_time) >= self.storage_interval:
                self.last_storage_time = current_time
                
                # For simplicity, just use the first face
                try:
                    # Use standard Flask application context instead of custom manager
                    with current_app.app_context():
                        # Use SQLAlchemy models (preferred) if available
                        try:
                            from app.database.models import EmotionRecord
                            
                            # Create a new emotion record
                            emotion_record = EmotionRecord(
                                user_id=self.user_id,
                                emotions_data=emotion_results[0]
                            )
                            
                            # Save the record using SQLAlchemy
                            emotion_record.save()
                            print(f"Saved emotion record for user {self.user_id} using SQLAlchemy")
                            
                        except ImportError:
                            # Fall back to direct database access if needed
                            db = get_db()
                            import json
                            emotion_data = json.dumps(emotion_results[0])
                            
                            # Insert emotion record with direct SQL
                            db.execute(
                                "INSERT INTO emotion_records (user_id, timestamp, emotions_data) VALUES (?, ?, ?)",
                                (self.user_id, datetime.utcnow().isoformat(), emotion_data)
                            )
                            db.commit()
                            print(f"Saved emotion record for user {self.user_id} using direct SQL")
                    
                except Exception as e:
                    print(f"Error saving emotion record: {str(e)}")
                    import traceback
                    traceback.print_exc()  # Print full stack trace for debugging
        
     
     
     
     
     
     
     
            
    def _draw_emotion_meter(self, frame, emotion_result):
        """
        Draw a visual emotion meter on the frame.
        
        Args:
            frame (numpy.ndarray): Input frame
            emotion_result (dict): Emotion recognition result
        """
        # Define emotions and their colors (BGR format)
        emotions = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
        colors = [
            (0, 0, 255),    # Red (angry)
            (0, 140, 255),  # Orange (disgust)
            (0, 255, 255),  # Yellow (fear)
            (0, 255, 0),    # Green (happy)
            (255, 255, 0),  # Cyan (neutral)
            (255, 0, 0),    # Blue (sad)
            (255, 0, 255)   # Magenta (surprise)
        ]
        
        # Starting position and dimensions
        x, y = 10, frame.shape[0] - 120
        width, height = 200, 100
        
        # Draw background
        cv2.rectangle(frame, (x-10, y-10), (x+width+10, y+height+10), (0, 0, 0), -1)
        cv2.rectangle(frame, (x-10, y-10), (x+width+10, y+height+10), (255, 255, 255), 1)
        
        # Draw title
        cv2.putText(frame, "Emotion Distribution", (x, y-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw emotion bars
        bar_height = height // len(emotions)
        for i, emotion in enumerate(emotions):
            prob = emotion_result.get(emotion, 0)
            bar_width = int(prob * width)
            bar_y = y + i * bar_height
            
            # Draw emotion label
            cv2.putText(frame, f"{emotion.capitalize()}", (x, bar_y + bar_height//2 + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Draw probability bar
            cv2.rectangle(frame, (x + 70, bar_y + 5), (x + 70 + bar_width, bar_y + bar_height - 5),
                         colors[i], -1)
            
            # Draw probability text
            text_x = x + 75 + bar_width
            text_y = bar_y + bar_height//2 + 5
            cv2.putText(frame, f"{prob:.2f}", (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    def get_frame(self, processed=True):
        """
        Get the current frame.
        
        Args:
            processed (bool, optional): Whether to return the processed frame
                                       with emotion results (default: True)
        
        Returns:
            numpy.ndarray: Current frame
        """
        with self.lock:
            if processed and self.processed_frame is not None:
                frame = self.processed_frame.copy()
            elif self.frame is not None:
                frame = self.frame.copy()
            else:
                # Return an empty frame if no frames are available
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "No camera feed available", (120, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        return frame
    
    def get_jpeg_frame(self, processed=True):
        """
        Get the current frame encoded as JPEG.
        
        Args:
            processed (bool, optional): Whether to return the processed frame
                                       with emotion results (default: True)
        
        Returns:
            bytes: JPEG encoded frame
        """
        frame = self.get_frame(processed)
        
        # Encode frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            # Return an empty JPEG if encoding fails
            empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(empty_frame, "Error encoding frame", (120, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            ret, jpeg = cv2.imencode('.jpg', empty_frame)
        
        return jpeg.tobytes()
    
    def get_performance_metrics(self):
        """
        Get performance metrics for the video processing.
        
        Returns:
            dict: Dictionary with performance metrics
        """
        avg_inference_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0
        max_inference_time = max(self.inference_times) if self.inference_times else 0
        
        return {
            'fps': self.fps,
            'avg_inference_time': avg_inference_time,
            'max_inference_time': max_inference_time,
            'frame_interval': self.frame_interval,
            'face_detection_method': self.face_preprocessor.detector_type
        }