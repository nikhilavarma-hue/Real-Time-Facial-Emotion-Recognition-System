"""
Image preprocessing module for facial emotion recognition.

This module handles face detection and preprocessing of images before
being fed to the emotion recognition model.
"""
import cv2
import numpy as np
from flask import current_app

class FacePreprocessor:
    """
    Face preprocessing class for the emotion recognition system.
    
    Detects faces in images and preprocesses them for the model.
    """
    
    def __init__(self):
        """Initialize the face preprocessor."""
        # Load face detection model
        self.detector_type = current_app.config.get('FACE_DETECTOR', 'haar')
        
        if self.detector_type == 'haar':
            # Use Haar Cascade (faster but less accurate)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            # Use DNN-based detector (more accurate but slower)
            try:
                self.face_net = cv2.dnn.readNetFromCaffe(
                    'app/models/detectors/deploy.prototxt',
                    'app/models/detectors/res10_300x300_ssd_iter_140000.caffemodel'
                )
                self.detector_type = 'dnn'
                print("Using DNN face detector")
            except Exception as e:
                print(f"Could not load DNN face detector: {str(e)}")
                print("Falling back to Haar Cascade detector")
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                self.detector_type = 'haar'
        
        # Get image size from config
        self.img_size = current_app.config['IMG_SIZE']
        
        # Face tracking for stability
        self.prev_faces = []
        self.tracking_threshold = 30  # pixel distance threshold for face tracking
        self.max_tracking_history = 5  # number of frames to keep track of
    
    def detect_faces(self, image):
        """
        Detect faces in an image.
        
        Args:
            image (numpy.ndarray): Input image (BGR format from OpenCV)
            
        Returns:
            list: List of face rectangles (x, y, w, h)
        """
        if self.detector_type == 'dnn':
            return self._detect_faces_dnn(image)
        else:
            return self._detect_faces_haar(image)
    
    def _detect_faces_haar(self, image):
        """
        Detect faces using Haar Cascade.
        
        Args:
            image (numpy.ndarray): Input image (BGR format from OpenCV)
            
        Returns:
            list: List of face rectangles (x, y, w, h)
        """
        # Convert image to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Convert to list of tuples if faces were found
        faces_list = [tuple(face) for face in faces] if len(faces) > 0 else []
        
        # If no faces detected, try with more aggressive parameters
        if not faces_list:
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=3,
                minSize=(20, 20),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            faces_list = [tuple(face) for face in faces] if len(faces) > 0 else []
        
        # Apply face tracking for stability
        return self._track_faces(faces_list)
    
    def _detect_faces_dnn(self, image):
        """
        Detect faces using DNN-based detector.
        
        Args:
            image (numpy.ndarray): Input image (BGR format from OpenCV)
            
        Returns:
            list: List of face rectangles (x, y, w, h)
        """
        (h, w) = image.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0,
            (300, 300), (104.0, 177.0, 123.0)
        )
        
        self.face_net.setInput(blob)
        detections = self.face_net.forward()
        
        faces = []
        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            # Filter out weak detections
            if confidence > 0.5:
                # Compute the (x, y)-coordinates of the bounding box
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Convert to (x, y, w, h) format
                x = startX
                y = startY
                w = endX - startX
                h = endY - startY
                
                # Ensure the bounding box falls within the image
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0] and w > 0 and h > 0:
                    faces.append((x, y, w, h))
        
        # Apply face tracking for stability
        return self._track_faces(faces)
    
    def _track_faces(self, detected_faces):
        """
        Track faces across frames for stability.
        
        Args:
            detected_faces (list): List of detected face rectangles (x, y, w, h)
            
        Returns:
            list: List of tracked face rectangles (x, y, w, h)
        """
        if not self.prev_faces:
            # First frame or no previous faces
            self.prev_faces = [detected_faces]
            return detected_faces
        
        # If no faces detected in current frame but we have previous faces
        if not detected_faces and self.prev_faces:
            # Use the most recent previous face
            return self.prev_faces[-1]
        
        # Get the most recent previous faces
        last_faces = self.prev_faces[-1]
        
        # Map current faces to previous faces for tracking continuity
        if last_faces and detected_faces:
            matched_faces = []
            for curr_face in detected_faces:
                curr_x, curr_y, curr_w, curr_h = curr_face
                curr_center = (curr_x + curr_w//2, curr_y + curr_h//2)
                
                best_match = None
                min_distance = float('inf')
                
                # Find the closest previous face
                for prev_face in last_faces:
                    prev_x, prev_y, prev_w, prev_h = prev_face
                    prev_center = (prev_x + prev_w//2, prev_y + prev_h//2)
                    
                    # Calculate distance between centers
                    distance = np.sqrt((curr_center[0] - prev_center[0])**2 + 
                                      (curr_center[1] - prev_center[1])**2)
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match = prev_face
                
                # If close enough to a previous face, apply smoothing
                if best_match and min_distance < self.tracking_threshold:
                    prev_x, prev_y, prev_w, prev_h = best_match
                    smooth_x = int(0.7 * curr_x + 0.3 * prev_x)
                    smooth_y = int(0.7 * curr_y + 0.3 * prev_y)
                    smooth_w = int(0.7 * curr_w + 0.3 * prev_w)
                    smooth_h = int(0.7 * curr_h + 0.3 * prev_h)
                    matched_faces.append((smooth_x, smooth_y, smooth_w, smooth_h))
                else:
                    matched_faces.append(curr_face)
            
            # Update history
            self.prev_faces.append(matched_faces)
            if len(self.prev_faces) > self.max_tracking_history:
                self.prev_faces.pop(0)
            
            return matched_faces
        
        # Update history
        self.prev_faces.append(detected_faces)
        if len(self.prev_faces) > self.max_tracking_history:
            self.prev_faces.pop(0)
        
        return detected_faces
    
    def preprocess_face(self, image, face_rect):
        """
        Preprocess a detected face for the emotion recognition model.
        
        Args:
            image (numpy.ndarray): Input image (BGR format from OpenCV)
            face_rect (tuple): Face rectangle (x, y, w, h)
            
        Returns:
            numpy.ndarray: Preprocessed face image ready for the model
        """
        x, y, w, h = face_rect
        
        # Extract face region with some margin
        # Add 20% margin to each side if possible
        margin_x = int(w * 0.2)
        margin_y = int(h * 0.2)
        
        # Ensure margins don't go outside the image
        start_x = max(0, x - margin_x)
        start_y = max(0, y - margin_y)
        end_x = min(image.shape[1], x + w + margin_x)
        end_y = min(image.shape[0], y + h + margin_y)
        
        # Extract face region with margins
        face_img = image[start_y:end_y, start_x:end_x]
        
        # Resize to the required input size
        face_img = cv2.resize(face_img, (self.img_size, self.img_size))
        
        # Convert to RGB (from BGR)
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        
        return face_img
    
    def detect_and_preprocess(self, image):
        """
        Detect and preprocess all faces in an image.
        
        Args:
            image (numpy.ndarray): Input image (BGR format from OpenCV)
            
        Returns:
            tuple: (List of preprocessed face images, List of face rectangles)
        """
        # Detect faces
        face_rects = self.detect_faces(image)
        
        # Preprocess each face
        preprocessed_faces = []
        for face_rect in face_rects:
            preprocessed_face = self.preprocess_face(image, face_rect)
            preprocessed_faces.append(preprocessed_face)
        
        return preprocessed_faces, face_rects
    
    def draw_results(self, frame, face_rects, emotion_results):
        """
        Draw emotion recognition results on a video frame with enhanced visualization.
        
        Args:
            frame (numpy.ndarray): Input video frame
            face_rects (list): List of face rectangles (x, y, w, h)
            emotion_results (list): List of emotion recognition results
            
        Returns:
            numpy.ndarray: Frame with results drawn
        """
        # Create a copy of the frame
        result_frame = frame.copy()
        
        # Define colors for different emotions (BGR format)
        emotion_colors = {
            'angry': (0, 0, 255),     # Red
            'disgust': (0, 140, 255),  # Orange
            'fear': (0, 255, 255),    # Yellow
            'happy': (0, 255, 0),     # Green
            'neutral': (255, 255, 0),  # Cyan
            'sad': (255, 0, 0),       # Blue
            'surprise': (255, 0, 255)  # Magenta
        }
        
        # Process each face
        for i, (face_rect, emotion_result) in enumerate(zip(face_rects, emotion_results)):
            x, y, w, h = face_rect
            
            # Get top 2 emotions and their probabilities
            emotions_sorted = sorted(emotion_result.items(), key=lambda x: x[1], reverse=True)
            dominant_emotion = emotions_sorted[0]
            secondary_emotion = emotions_sorted[1] if len(emotions_sorted) > 1 else None
            
            emotion_name = dominant_emotion[0]
            emotion_prob = dominant_emotion[1]
            
            # Get color for the dominant emotion
            color = emotion_colors.get(emotion_name, (255, 255, 255))  # White is default
            
            # Draw rectangle around face with thicker line for better visibility
            cv2.rectangle(result_frame, (x, y), (x+w, y+h), color, 3)
            
            # Create a semi-transparent background for text (improves readability)
            overlay = result_frame.copy()
            cv2.rectangle(overlay, (x, y+h), (x+w, y+h+70), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, result_frame, 0.3, 0, result_frame)
            
            # Display dominant emotion name and probability with larger text
            text = f"{emotion_name.capitalize()}: {emotion_prob:.2f}"
            cv2.putText(result_frame, text, (x+5, y+h+25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Display secondary emotion if available
            if secondary_emotion:
                sec_name = secondary_emotion[0]
                sec_prob = secondary_emotion[1]
                sec_text = f"{sec_name.capitalize()}: {sec_prob:.2f}"
                cv2.putText(result_frame, sec_text, (x+5, y+h+55), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, emotion_colors.get(sec_name, (255, 255, 255)), 2)
        
        return result_frame