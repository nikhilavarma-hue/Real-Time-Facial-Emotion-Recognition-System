// Theme helper functions
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved theme preference or default to 'dark'
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    
    // Theme toggle functionality for settings page
    const themeOptions = document.querySelectorAll('.theme-preview');
    if (themeOptions.length > 0) {
        themeOptions.forEach(option => {
            option.addEventListener('click', function() {
                const theme = this.getAttribute('data-theme');
                setTheme(theme);
                localStorage.setItem('theme', theme);
                
                // Update selected theme preview
                themeOptions.forEach(opt => {
                    opt.classList.remove('selected');
                });
                this.classList.add('selected');
                
                // Update radio button
                document.getElementById('theme-' + theme).checked = true;
            });
        });
    }
    
    // Apply theme settings
    function setTheme(theme) {
        const root = document.documentElement;
        
        if (theme === 'light') {
            root.style.setProperty('--background-color', '#f5f5f5');
            root.style.setProperty('--surface-color', '#ffffff');
            root.style.setProperty('--card-color', '#ffffff');
            root.style.setProperty('--text-color', '#333333');
            root.style.setProperty('--text-light', '#666666');
            root.style.setProperty('--border-color', '#e0e0e0');
            root.style.setProperty('--border-color-light', '#eeeeee');
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
        } else {
            // Reset to default dark theme values from CSS
            root.style.setProperty('--background-color', '#121212');
            root.style.setProperty('--surface-color', '#1E1E1E');
            root.style.setProperty('--card-color', '#252525');
            root.style.setProperty('--text-color', '#E4E4E4');
            root.style.setProperty('--text-light', '#A0A0A0');
            root.style.setProperty('--border-color', '#333333');
            root.style.setProperty('--border-color-light', '#444444');
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
        }
    }
});