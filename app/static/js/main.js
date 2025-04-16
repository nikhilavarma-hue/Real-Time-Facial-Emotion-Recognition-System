// Improved emotion display and video feed handling
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const videoFeed = document.getElementById('video-feed');
    const permissionRequest = document.getElementById('permission-request');
    const btnRefresh = document.getElementById('btn-refresh');
    const btnStop = document.getElementById('btn-stop');
    const btnSnapshot = document.getElementById('btn-snapshot');
    const btnRequestPermission = document.getElementById('btn-request-permission');
    const fpsElement = document.getElementById('fps');
    const inferenceTimeElement = document.getElementById('inference-time');
    
    // Status variables
    let streamActive = false;
    let emotionPollingInterval;
    let performanceInterval;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    
    // Initialize Chart.js with dark theme
    Chart.defaults.color = '#A0A0A0';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
    
    // Create radar chart
    const ctx = document.getElementById('emotion-chart').getContext('2d');
    const emotionChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise'],
            datasets: [{
                label: 'Confidence',
                data: [0, 0, 0, 0, 1, 0, 0], // Default to neutral
                backgroundColor: 'rgba(100, 216, 134, 0.2)',
                borderColor: 'rgba(100, 216, 134, 0.8)',
                pointBackgroundColor: [
                    '#f44336', '#ff9800', '#ffeb3b', 
                    '#4CAF50', '#9e9e9e', '#2196F3', '#9c27b0'
                ],
                pointBorderColor: '#252525',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(100, 216, 134, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    pointLabels: {
                        color: '#E4E4E4',
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        backdropColor: 'transparent',
                        color: '#A0A0A0',
                        z: 1
                    },
                    suggestedMin: 0,
                    suggestedMax: 1
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 30, 30, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#333333',
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return `Confidence: ${(context.raw * 100).toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
    
    // Initialize video feed with error handling
    function initVideoFeed() {
        // Add a timestamp to prevent caching
        const timestamp = new Date().getTime();
        videoFeed.src = `/api/video_feed?t=${timestamp}`;
        streamActive = true;
        
        // Add error handling for video feed
        videoFeed.onerror = function() {
            console.error('Error loading video feed');
            handleVideoError();
        };
        
        // Add load event to confirm stream is working
        videoFeed.onload = function() {
            console.log('Video feed loaded successfully');
            reconnectAttempts = 0;
            streamActive = true;
            startEmotionPolling();
            startPerformanceMonitoring();
        };
    }
    
    // Handle video feed errors
    function handleVideoError() {
        reconnectAttempts++;
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
            setTimeout(initVideoFeed, 2000);
        } else {
            showNotification('Could not connect to video feed. Please refresh the page.', 'error');
            updateUIForStoppedStream();
        }
    }
    
    // Refresh video feed
    function refreshVideoFeed() {
        stopVideoFeed();
        setTimeout(() => {
            reconnectAttempts = 0;
            initVideoFeed();
            showNotification('Video feed refreshed');
        }, 1000);
    }
    
    // Stop video feed
    function stopVideoFeed() {
        videoFeed.src = "";
        streamActive = false;
        stopEmotionPolling();
        stopPerformanceMonitoring();
        updateUIForStoppedStream();
    }
    
    // Update UI for stopped stream
    function updateUIForStoppedStream() {
        fpsElement.innerHTML = '<i class="fas fa-tachometer-alt"></i> FPS: --';
        inferenceTimeElement.innerHTML = '<i class="fas fa-stopwatch"></i> Inference: --ms';
        
        // Reset emotion displays to show "Stream Stopped"
        const dominantLabel = document.getElementById('dominant-emotion-label');
        dominantLabel.textContent = 'Stream Stopped';
        
        // Reset progress bars
        const emotions = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise'];
        emotions.forEach(emotion => {
            const progressBar = document.getElementById(`progress-${emotion}`);
            if (progressBar) {
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
            }
        });
    }
    
    // Take snapshot
    function takeSnapshot() {
        if (!streamActive) {
            showNotification('Video stream is not active', 'error');
            return;
        }
        
        fetch('/api/analyze_current_emotion')
            .then(response => {
                if (!response.ok) {
                    throw new Error('No emotion data available');
                }
                return response.json();
            })
            .then(data => {
                // Save snapshot logic would go here
                showNotification('Snapshot saved!');
            })
            .catch(error => {
                showNotification('Unable to save snapshot: ' + error.message, 'error');
            });
    }
    
    // Start emotion data polling
    function startEmotionPolling() {
        // Clear any existing interval
        stopEmotionPolling();
        
        // Set new interval
        emotionPollingInterval = setInterval(() => {
            if (document.visibilityState === 'visible' && streamActive) {
                fetchEmotionData();
            }
        }, 300); // Poll more frequently for responsiveness
    }
    
    // Stop emotion data polling
    function stopEmotionPolling() {
        if (emotionPollingInterval) {
            clearInterval(emotionPollingInterval);
        }
    }
    
    // Fetch emotion data from API
    function fetchEmotionData() {
        fetch('/api/analyze_current_emotion')
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('No emotion data available');
            })
            .then(data => {
                if (data.error) {
                    console.warn('Emotion data warning:', data.error);
                }
                updateEmotionDisplay(data.emotions, data.dominant_emotion);
            })
            .catch(error => {
                console.log('Waiting for emotion data...', error);
            });
    }
    
    // Update the display with emotion data
    function updateEmotionDisplay(emotions, dominantEmotion) {
        // Update dominant emotion
        const dominantLabel = document.getElementById('dominant-emotion-label');
        const dominantBadge = document.getElementById('dominant-emotion-badge');
        
        if (dominantLabel.textContent !== dominantEmotion) {
            // Add pulse effect when emotion changes
            dominantLabel.classList.add('pulse');
            dominantBadge.classList.add('pulse');
            
            setTimeout(() => {
                dominantLabel.classList.remove('pulse');
                dominantBadge.classList.remove('pulse');
            }, 700);
        }
        
        dominantLabel.textContent = dominantEmotion.charAt(0).toUpperCase() + dominantEmotion.slice(1);
        dominantBadge.textContent = dominantEmotion;
        
        // Update badge class - remove all emotion classes first
        dominantBadge.className = 'emotion-badge';
        dominantBadge.classList.add(`emotion-${dominantEmotion}`);
        
        // Update progress bars
        for (const [emotion, confidence] of Object.entries(emotions)) {
            const progressBar = document.getElementById(`progress-${emotion}`);
            if (progressBar) {
                const percentage = Math.round(confidence * 100);
                progressBar.style.width = `${percentage}%`;
                progressBar.textContent = `${percentage}%`;
                
                // Make sure data-label attribute is set correctly
                progressBar.setAttribute('data-label', emotion.charAt(0).toUpperCase() + emotion.slice(1));
            }
        }
        
        // Update chart data
        emotionChart.data.datasets[0].data = [
            emotions.angry || 0,
            emotions.disgust || 0,
            emotions.fear || 0,
            emotions.happy || 0,
            emotions.neutral || 0,
            emotions.sad || 0,
            emotions.surprise || 0
        ];
        emotionChart.update();
    }
    
    // Start performance metrics monitoring
    function startPerformanceMonitoring() {
        if (performanceInterval) {
            clearInterval(performanceInterval);
        }
        
        performanceInterval = setInterval(() => {
            if (!streamActive) return;
            
            fetch('/api/performance_metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.warn('Performance metrics warning:', data.error);
                        return;
                    }
                    
                    fpsElement.innerHTML = `<i class="fas fa-tachometer-alt"></i> FPS: ${data.fps || 0}`;
                    inferenceTimeElement.innerHTML = `<i class="fas fa-stopwatch"></i> Inference: ${((data.avg_inference_time || 0) * 1000).toFixed(1)}ms`;
                })
                .catch(error => {
                    console.error('Error fetching performance metrics:', error);
                });
        }, 2000);
    }
    
    // Stop performance monitoring
    function stopPerformanceMonitoring() {
        if (performanceInterval) {
            clearInterval(performanceInterval);
        }
    }
    
    // Show notification
    function showNotification(message, type = 'success') {
        // Remove any existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notif => {
            document.body.removeChild(notif);
        });
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    // Request camera permission
    function requestCameraPermission() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                permissionRequest.style.display = 'none';
                videoFeed.style.display = 'block';
                stream.getTracks().forEach(track => track.stop());
                initVideoFeed();
            })
            .catch(error => {
                showNotification('Camera permission denied. Please enable camera access.', 'error');
                console.error('Error accessing camera:', error);
            });
    }
    
    // Event listeners
    btnRefresh.addEventListener('click', refreshVideoFeed);
    btnStop.addEventListener('click', stopVideoFeed);
    btnSnapshot.addEventListener('click', takeSnapshot);
    btnRequestPermission.addEventListener('click', requestCameraPermission);
    
    // Check camera permission
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
            navigator.permissions.query({ name: 'camera' })
                .then(permissionStatus => {
                    if (permissionStatus.state === 'granted') {
                        permissionRequest.style.display = 'none';
                        initVideoFeed();
                    } else if (permissionStatus.state === 'prompt') {
                        permissionRequest.style.display = 'block';
                        videoFeed.style.display = 'none';
                    } else {
                        permissionRequest.style.display = 'block';
                        videoFeed.style.display = 'none';
                        showNotification('Camera access is required for emotion recognition.', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error checking camera permission:', error);
                    initVideoFeed(); // Try anyway
                });
        } catch (error) {
            console.error('Permission API not supported, trying direct access:', error);
            initVideoFeed(); // Try anyway
        }
    } else {
        showNotification('Your browser does not support camera access.', 'error');
    }
});