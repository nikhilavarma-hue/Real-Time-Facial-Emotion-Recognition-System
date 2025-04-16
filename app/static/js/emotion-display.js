/**
 * Emotion display functionality for the emotion recognition application.
 * This script handles updating the UI based on emotion recognition results.
 */

// Emotion display elements
const dominantEmotionLabel = document.getElementById('dominant-emotion-label');
const dominantEmotionBadge = document.getElementById('dominant-emotion-badge');
const emotionChart = document.getElementById('emotion-chart');

// Progress bars for each emotion
const progressBars = {
    angry: document.getElementById('progress-angry'),
    disgust: document.getElementById('progress-disgust'),
    fear: document.getElementById('progress-fear'),
    happy: document.getElementById('progress-happy'),
    neutral: document.getElementById('progress-neutral'),
    sad: document.getElementById('progress-sad'),
    surprise: document.getElementById('progress-surprise')
};

// Emotion color mapping
const emotionColors = {
    angry: '#f44336',
    disgust: '#ff9800',
    fear: '#ffeb3b',
    happy: '#4CAF50',
    neutral: '#9e9e9e',
    sad: '#2196F3',
    surprise: '#9c27b0'
};

// Chart instance
let emotionChartInstance = null;

/**
 * Initialize the emotion display
 */
function initEmotionDisplay() {
    // Create initial emotion chart
    createEmotionChart();
    
    // Start polling for emotion data
    startEmotionPolling();
}

/**
 * Create the emotion radar chart
 */
function createEmotionChart() {
    const ctx = emotionChart.getContext('2d');
    
    emotionChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise'],
            datasets: [{
                label: 'Emotion Confidence',
                data: [0, 0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                pointBackgroundColor: Object.values(emotionColors),
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(75, 192, 192, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 1
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Start polling for emotion data
 */
function startEmotionPolling() {
    // Poll for emotion data every 500ms
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            fetchEmotionData();
        }
    }, 500);
}

/**
 * Fetch the current emotion data from the API
 */
function fetchEmotionData() {
    fetch('/api/analyze_current_emotion')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('No emotion data available');
        })
        .then(data => {
            updateEmotionDisplay(data.emotions, data.dominant_emotion);
        })
        .catch(error => {
            // Silent error handling - user might not have started the video feed yet
            console.log('Waiting for emotion data...');
        });
}

/**
 * Update the emotion display with new data
 * @param {Object} emotions - Object containing emotion confidence values
 * @param {string} dominantEmotion - The dominant emotion
 */
function updateEmotionDisplay(emotions, dominantEmotion) {
    // Update dominant emotion
    dominantEmotionLabel.textContent = dominantEmotion.charAt(0).toUpperCase() + dominantEmotion.slice(1);
    dominantEmotionBadge.textContent = dominantEmotion;
    dominantEmotionBadge.className = `emotion-badge emotion-${dominantEmotion}`;
    
    // Update progress bars
    for (const [emotion, confidence] of Object.entries(emotions)) {
        if (progressBars[emotion]) {
            const percentage = Math.round(confidence * 100);
            progressBars[emotion].style.width = `${percentage}%`;
            progressBars[emotion].textContent = `${percentage}%`;
        }
    }
    
    // Update chart data
    if (emotionChartInstance) {
        emotionChartInstance.data.datasets[0].data = [
            emotions.angry || 0,
            emotions.disgust || 0,
            emotions.fear || 0,
            emotions.happy || 0,
            emotions.neutral || 0,
            emotions.sad || 0,
            emotions.surprise || 0
        ];
        emotionChartInstance.update();
    }
}

/**
 * Add a pulsing effect to the dominant emotion
 */
function pulseEffect(element) {
    element.classList.add('pulse');
    setTimeout(() => {
        element.classList.remove('pulse');
    }, 700);
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', initEmotionDisplay);