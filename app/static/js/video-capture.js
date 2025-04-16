/**
 * Video capture and processing functionality for the emotion recognition application.
 * This script handles the webcam feed, camera permissions, and UI updates.
 */

// Variables for video elements
let videoFeed = document.getElementById('video-feed');
let permissionRequest = document.getElementById('permission-request');
let btnRefresh = document.getElementById('btn-refresh');
let btnStop = document.getElementById('btn-stop');
let btnSnapshot = document.getElementById('btn-snapshot');
let btnRequestPermission = document.getElementById('btn-request-permission');

// Performance monitoring elements
let fpsElement = document.getElementById('fps');
let inferenceTimeElement = document.getElementById('inference-time');

// Stream status
let streamActive = true;

/**
 * Initialize the video feed
 */
function initVideoFeed() {
    // Initial setup
    videoFeed.src = "/api/video_feed?" + new Date().getTime(); // Add timestamp to prevent caching
    streamActive = true;

    // Update performance metrics
    startPerformanceMonitoring();
}

/**
 * Refresh the video feed
 */
function refreshVideoFeed() {
    if (!streamActive) {
        videoFeed.src = "/api/video_feed?" + new Date().getTime();
        streamActive = true;
        // Update performance metrics
        startPerformanceMonitoring();
    } else {
        // Just refresh the current feed
        videoFeed.src = "/api/video_feed?" + new Date().getTime();
    }
}

/**
 * Stop the video feed
 */
function stopVideoFeed() {
    videoFeed.src = "";
    streamActive = false;
    // Stop performance monitoring
    stopPerformanceMonitoring();
}

/**
 * Take a snapshot of the current emotion state
 */
function takeSnapshot() {
    // Call API to analyze current emotion
    fetch('/api/analyze_current_emotion')
        .then(response => {
            if (!response.ok) {
                throw new Error('No emotion data available');
            }
            return response.json();
        })
        .then(data => {
            // Show confirmation to user
            showNotification('Snapshot saved!');

            // Update emotion display
            updateEmotionDisplay(data.emotions, data.dominant_emotion);
        })
        .catch(error => {
            showNotification('Unable to save snapshot: ' + error.message, 'error');
        });
}

/**
 * Show a notification message
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error)
 */
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to document
    document.body.appendChild(notification);

    // Show animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

/**
 * Start performance monitoring
 */
function startPerformanceMonitoring() {
    // Update performance metrics every 2 seconds
    performanceInterval = setInterval(() => {
        fetch('/api/performance_metrics')
            .then(response => response.json())
            .then(data => {
                // Update UI with performance metrics
                fpsElement.textContent = `FPS: ${data.fps}`;
                inferenceTimeElement.textContent = `Inference: ${(data.avg_inference_time * 1000).toFixed(1)}ms`;
            })
            .catch(error => {
                console.error('Error fetching performance metrics:', error);
            });
    }, 2000);
}

/**
 * Stop performance monitoring
 */
function stopPerformanceMonitoring() {
    clearInterval(performanceInterval);
    fpsElement.textContent = 'FPS: --';
    inferenceTimeElement.textContent = 'Inference: --ms';
}

/**
 * Handle camera permission request
 */
function requestCameraPermission() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            // Permission granted, close the request dialog
            permissionRequest.style.display = 'none';
            
            // Stop the stream (we don't need it, the server handles video)
            stream.getTracks().forEach(track => track.stop());
            
            // Start the video feed
            initVideoFeed();
        })
        .catch(error => {
            // Show an error message
            showNotification('Camera permission denied. Please enable camera access.', 'error');
            console.error('Error accessing camera:', error);
        });
}

// Event listeners
btnRefresh.addEventListener('click', refreshVideoFeed);
btnStop.addEventListener('click', stopVideoFeed);
btnSnapshot.addEventListener('click', takeSnapshot);
btnRequestPermission.addEventListener('click', requestCameraPermission);

// Check if the browser supports getUserMedia
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    // Check if camera permission has been granted
    navigator.permissions.query({ name: 'camera' })
        .then(permissionStatus => {
            if (permissionStatus.state === 'granted') {
                // Camera permission already granted
                initVideoFeed();
            } else if (permissionStatus.state === 'prompt') {
                // Show permission request dialog
                permissionRequest.style.display = 'block';
                videoFeed.style.display = 'none';
            } else {
                // Permission denied
                permissionRequest.style.display = 'block';
                videoFeed.style.display = 'none';
                showNotification('Camera access is required for emotion recognition.', 'error');
            }
        })
        .catch(error => {
            // Can't check permission status, just try to initialize
            console.error('Error checking camera permission:', error);
            initVideoFeed();
        });
} else {
    // Browser doesn't support getUserMedia
    showNotification('Your browser does not support camera access.', 'error');
}

// Initialize video feed if the page loads with an existing feed URL
if (videoFeed.src && videoFeed.src.includes('/api/video_feed')) {
    startPerformanceMonitoring();
}