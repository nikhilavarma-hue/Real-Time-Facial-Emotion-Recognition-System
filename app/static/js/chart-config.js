// Chart.js global configuration
document.addEventListener('DOMContentLoaded', function() {
    // Set default Chart.js options to match the app theme
    if (window.Chart) {
        Chart.defaults.font.family = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif";
        
        // Check if dark theme is active
        const isDarkTheme = document.body.classList.contains('dark-theme') || 
                           !document.body.classList.contains('light-theme');
        
        // Set chart defaults based on theme
        if (isDarkTheme) {
            Chart.defaults.color = '#A0A0A0';
            Chart.defaults.borderColor = '#333333';
            Chart.defaults.backgroundColor = '#252525';
        } else {
            Chart.defaults.color = '#666666';
            Chart.defaults.borderColor = '#e0e0e0';
            Chart.defaults.backgroundColor = '#ffffff';
        }
        
        // Create a function to apply emotion colors consistently
        window.getEmotionColor = function(emotion, opacity = 1) {
            const colors = {
                'angry': 'rgba(244, 67, 54, ' + opacity + ')',
                'disgust': 'rgba(255, 152, 0, ' + opacity + ')',
                'fear': 'rgba(255, 235, 59, ' + opacity + ')',
                'happy': 'rgba(76, 175, 80, ' + opacity + ')',
                'neutral': 'rgba(158, 158, 158, ' + opacity + ')',
                'sad': 'rgba(33, 150, 243, ' + opacity + ')',
                'surprise': 'rgba(156, 39, 176, ' + opacity + ')'
            };
            
            return colors[emotion.toLowerCase()] || 'rgba(100, 216, 134, ' + opacity + ')';
        };
    }
});