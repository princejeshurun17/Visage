
document.addEventListener('DOMContentLoaded', function() {
    // Update time every second
    function updateTime() {
        fetch('/current_time')
            .then(response => response.json())
            .then(data => {
                document.getElementById('current-time').textContent = data.time;
            });
    }
    
    setInterval(updateTime, 1000);
    updateTime(); // Initial call
    
    // Update video feed
    function updateVideoFeed() {
        fetch('/video_feed')
            .then(response => response.json())
            .then(data => {
                if (data.frame) {
                    document.getElementById('video-feed').src = data.frame;
                }
            });
    }
    
    setInterval(updateVideoFeed, 100);
    
    // Screenshot button
    document.getElementById('screenshot-btn').addEventListener('click', function() {
        fetch('/screenshot', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        });
    });
    
    // Performance chart
    const ctx = document.getElementById('performanceChart').getContext('2d');
    const performanceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                data: [
                    document.querySelectorAll('.performance-high').length,
                    document.querySelectorAll('.performance-medium').length,
                    document.querySelectorAll('.performance-low').length
                ],
                backgroundColor: [
                    'rgba(76, 175, 80, 0.7)',
                    'rgba(255, 152, 0, 0.7)',
                    'rgba(244, 67, 54, 0.7)'
                ],
                borderColor: [
                    'rgba(76, 175, 80, 1)',
                    'rgba(255, 152, 0, 1)',
                    'rgba(244, 67, 54, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Employee Performance'
                }
            }
        }
    });
});
