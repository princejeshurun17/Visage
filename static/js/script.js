
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
    
    // Update emotion
    function updateEmotion() {
        fetch('/get_emotion')
            .then(response => response.json())
            .then(data => {
                const emotionBadge = document.getElementById('emotion-badge');
                emotionBadge.textContent = data.emotion;
                
                // Update badge color based on emotion
                emotionBadge.className = 'badge';
                
                // Add appropriate class based on emotion
                switch(data.emotion.toLowerCase()) {
                    case 'happy':
                        emotionBadge.classList.add('badge-success');
                        break;
                    case 'sad':
                        emotionBadge.classList.add('badge-info');
                        break;
                    case 'angry':
                        emotionBadge.classList.add('badge-danger');
                        break;
                    case 'neutral':
                        emotionBadge.classList.add('badge-secondary');
                        break;
                    default:
                        emotionBadge.classList.add('badge-primary');
                }
            })
            .catch(error => {
                console.error('Error fetching emotion:', error);
            });
    }
    
    // Update emotion every 5 seconds
    setInterval(updateEmotion, 2000);
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
});