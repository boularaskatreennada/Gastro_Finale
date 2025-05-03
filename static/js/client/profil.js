        // Function to show different sections
        function showSection(sectionId) {
            // Hide all sections
            document.getElementById('history-section').style.display = 'none';
            document.getElementById('personal-info-section').style.display = 'none';
            document.getElementById('notifications-section').style.display = 'none';
            
            // Show selected section
            document.getElementById(sectionId + '-section').style.display = 'block';
            
            // Update active menu
            document.querySelectorAll('.sidebar-menu a').forEach(link => {
                link.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
        }

        // Function to switch between history tabs
        function showHistoryTab(tabName) {
            // Update active tabs
            document.querySelectorAll('.history-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.currentTarget.classList.add('active');
            
            // Show corresponding content
            document.getElementById('orders-list').style.display = 'none';
            document.getElementById('reservations-list').style.display = 'none';
            
            if (tabName === 'orders') {
                document.getElementById('orders-list').style.display = 'block';
            } else {
                document.getElementById('reservations-list').style.display = 'block';
            }
        }

        // Initialize with History section open
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('history-section').style.display = 'block';
            document.getElementById('orders-list').style.display = 'block';
        });
