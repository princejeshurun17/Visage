document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    themeToggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        document.body.classList.toggle('light-mode');
        
        // Update toggle button text
        if (document.body.classList.contains('dark-mode')) {
            themeToggleBtn.textContent = '☀️';
        } else {
            themeToggleBtn.textContent = '🌙';
        }
    });
    
    // Update time every second
    function updateTime() {
        fetch('/get_current_time')
            .then(response => response.json())
            .then(data => {
                document.getElementById('current-time').textContent = data.time;
                document.getElementById('current-date').textContent = data.date;
            });
    }
    
    setInterval(updateTime, 1000);
    
    function updateEmotion() {
        fetch('/get_emotion')
            .then(response => response.json())
            .then(data => {
                const emotionBadge = document.getElementById('emotion-badge');
                emotionBadge.textContent = data.emotion;
                
                // Update badge color based on emotion
                switch(data.emotion.toLowerCase()) {
                    case 'happy':
                        emotionBadge.style.backgroundColor = 'var(--dark-success)';
                        break;
                    case 'sad':
                        emotionBadge.style.backgroundColor = 'var(--dark-text-secondary)';
                        break;
                    case 'angry':
                        emotionBadge.style.backgroundColor = 'var(--dark-danger)';
                        break;
                    case 'neutral':
                        emotionBadge.style.backgroundColor = 'var(--dark-accent)';
                        break;
                    case 'surprised':
                        emotionBadge.style.backgroundColor = 'var(--dark-warning)';
                        break;
                    default:
                        emotionBadge.style.backgroundColor = '#2196F3'; // Default blue
                }
            })
            .catch(error => {
                console.error('Error fetching emotion:', error);
            });
    }
    
    // Update emotion every 3 seconds
    setInterval(updateEmotion, 3000);
    updateEmotion(); // Initial update
    
    // Form submission
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            
            if (message !== '') {
                fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Clear input and update messages
                        messageInput.value = '';
                        loadMessages();
                    }
                })
                .catch(error => {
                    console.error('Error sending message:', error);
                });
            }
        });
    }
    
    // Load messages
    function loadMessages() {
        fetch('/get_messages')
            .then(response => response.json())
            .then(data => {
                const messagesContainer = document.getElementById('messages-container');
                messagesContainer.innerHTML = '';
                
                data.messages.forEach(msg => {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message';
                    messageElement.innerHTML = `
                        <span class="message-time">${msg.time}</span>
                        <span class="message-content">${msg.content}</span>
                    `;
                    messagesContainer.appendChild(messageElement);
                });
                
                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading messages:', error);
            });
    }
    
    // Initial load
    updateTime();
    if (document.getElementById('messages-container')) {
        loadMessages();
        // Refresh messages every 3 seconds
        setInterval(loadMessages, 3000);
    }

    // Add event listener for the refresh emotions button
    const refreshButton = document.getElementById('refresh-emotions');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshButton.disabled = true;
            refreshButton.textContent = '🔄 Refreshing...';
            
            fetch('/refresh_emotions')
                .then(response => response.json())
                .then(data => {
                    if (data.emotion_stats) {
                        updateEmotionChart(data.emotion_stats);
                    }
                })
                .catch(error => {
                    console.error('Error refreshing emotions:', error);
                })
                .finally(() => {
                    setTimeout(() => {
                        refreshButton.disabled = false;
                        refreshButton.textContent = '🔄 Refresh Data';
                    }, 500);
                });
        });
    }
    
    // Function to update the emotion chart
    function updateEmotionChart(stats) {
        const container = document.querySelector('.emotion-chart');
        if (!container) return;
        
        // Clear existing content
        container.innerHTML = '';
        
        // Add new emotion rows
        stats.forEach(emotion => {
            const row = document.createElement('div');
            row.className = 'emotion-row';
            row.innerHTML = `
                <span class="emotion-name">${emotion.emotion}</span>
                <div class="emotion-bar-container">
                    <div class="emotion-bar" style="width: ${emotion.percentage}%;" data-emotion="${emotion.emotion.toLowerCase()}"></div>
                </div>
                <span class="emotion-percentage">${emotion.percentage}%</span>
            `;
            container.appendChild(row);
        });
    }
});