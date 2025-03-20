/**
 * Employee Management JavaScript
 * This file contains enhanced functionality for the employee management page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Employee selection functionality
    setupEmployeeSelection();
    
    // Status update functionality
    setupStatusUpdates();
    
    // Search and filter functionality
    setupSearchAndFilter();
    
    // Sortable table columns
    setupSortableTable();
    
    // Live time updates
    setupTimeUpdates();
});

/**
 * Sets up employee selection functionality
 */
function setupEmployeeSelection() {
    // Select all checkbox
    document.getElementById('checkbox-all').addEventListener('change', function() {
        const isChecked = this.checked;
        document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        updateSelectedCount();
    });

    // Select all button
    document.getElementById('select-all').addEventListener('click', function() {
        document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
        document.getElementById('checkbox-all').checked = true;
        updateSelectedCount();
    });

    // Deselect all button
    document.getElementById('deselect-all').addEventListener('click', function() {
        document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.getElementById('checkbox-all').checked = false;
        updateSelectedCount();
    });
    
    // Individual checkbox change events
    document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });
}

/**
 * Updates the count of selected employees
 */
function updateSelectedCount() {
    const selectedCount = document.querySelectorAll('.employee-checkbox:checked').length;
    const countDisplay = document.getElementById('selected-count');
    
    if (countDisplay) {
        countDisplay.textContent = selectedCount;
        
        // Show/hide bulk actions based on selection
        const bulkActions = document.querySelector('.bulk-actions');
        if (bulkActions) {
            bulkActions.classList.toggle('has-selection', selectedCount > 0);
        }
    }
}

/**
 * Sets up status update functionality
 */
function setupStatusUpdates() {
    document.querySelectorAll('.status-btn').forEach(button => {
        button.addEventListener('click', function() {
            const status = this.getAttribute('data-status');
            const selectedEmployees = [];
            
            document.querySelectorAll('.employee-checkbox:checked').forEach(checkbox => {
                selectedEmployees.push(checkbox.getAttribute('data-id'));
            });
            
            if (selectedEmployees.length === 0) {
                showNotification('Please select at least one employee', 'error');
                return;
            }
            
            // Show loading state
            button.classList.add('loading');
            button.disabled = true;
            
            // Send AJAX request to update employee statuses
            const formData = new FormData();
            selectedEmployees.forEach(id => {
                formData.append('employee_ids', id);
            });
            formData.append('status', status);
            
            fetch('/employees', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI to reflect changes
                    selectedEmployees.forEach(id => {
                        const statusCell = document.querySelector(`tr[data-id="${id}"] td.status`);
                        statusCell.className = `status ${status}`;
                        statusCell.textContent = status.replace('_', ' ');
                    });
                    
                    // Show success notification
                    showNotification(data.message, 'success');
                    
                    // Refresh the page after a short delay to update all information
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showNotification('Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred while updating employee statuses', 'error');
            })
            .finally(() => {
                // Reset button state
                button.classList.remove('loading');
                button.disabled = false;
            });
        });
    });
}

/**
 * Sets up search and filter functionality
 */
function setupSearchAndFilter() {
    // Employee search functionality
    const searchInput = document.getElementById('employee-search');
    if (searchInput) {
        searchInput.addEventListener('input', filterEmployees);
    }
    
    // Status filter functionality
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterEmployees);
    }
    
    // Performance filter functionality
    const performanceFilter = document.getElementById('performance-filter');
    if (performanceFilter) {
        performanceFilter.addEventListener('change', filterEmployees);
    }
}

/**
 * Filters employees based on search input and filters
 */
function filterEmployees() {
    const searchInput = document.getElementById('employee-search');
    const statusFilter = document.getElementById('status-filter');
    const performanceFilter = document.getElementById('performance-filter');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const statusValue = statusFilter ? statusFilter.value : 'all';
    const performanceValue = performanceFilter ? performanceFilter.value : 'all';
    
    document.querySelectorAll('.employee-list tbody tr').forEach(row => {
        const name = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        const position = row.querySelector('td:nth-child(4)').textContent.toLowerCase();
        const status = row.querySelector('.status').textContent.toLowerCase();
        const performance = row.querySelector('.performance').textContent.toLowerCase();
        
        // Check if row matches search term
        const matchesSearch = name.includes(searchTerm) || 
                             position.includes(searchTerm);
        
        // Check if row matches status filter
        const matchesStatus = statusValue === 'all' || status === statusValue;
        
        // Check if row matches performance filter
        const matchesPerformance = performanceValue === 'all' || performance === performanceValue;
        
        // Show/hide row based on combined filters
        if (matchesSearch && matchesStatus && matchesPerformance) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update visible rows count
    updateVisibleRowsCount();
}

/**
 * Updates the count of visible rows after filtering
 */
function updateVisibleRowsCount() {
    const visibleRows = document.querySelectorAll('.employee-list tbody tr:not([style*="display: none"])').length;
    const totalRows = document.querySelectorAll('.employee-list tbody tr').length;
    
    const countDisplay = document.getElementById('visible-count');
    if (countDisplay) {
        countDisplay.textContent = `Showing ${visibleRows} of ${totalRows} employees`;
    }
}

/**
 * Sets up sortable table columns
 */
function setupSortableTable() {
    const sortableHeaders = document.querySelectorAll('.sortable');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const columnIndex = Array.from(header.parentElement.children).indexOf(header);
            const table = header.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction
            const isAscending = header.classList.toggle('sort-asc');
            header.classList.toggle('sort-desc', !isAscending);
            
            // Remove sort class from other headers
            sortableHeaders.forEach(otherHeader => {
                if (otherHeader !== header) {
                    otherHeader.classList.remove('sort-asc', 'sort-desc');
                }
            });
            
            // Sort the rows
            rows.sort((a, b) => {
                const cellA = a.children[columnIndex].textContent.trim();
                const cellB = b.children[columnIndex].textContent.trim();
                
                // Check if content is numeric
                const isNumeric = !isNaN(cellA) && !isNaN(cellB);
                
                if (isNumeric) {
                    return isAscending 
                        ? parseFloat(cellA) - parseFloat(cellB)
                        : parseFloat(cellB) - parseFloat(cellA);
                } else {
                    return isAscending
                        ? cellA.localeCompare(cellB)
                        : cellB.localeCompare(cellA);
                }
            });
            
            // Append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

/**
 * Sets up live time updates
 */
function setupTimeUpdates() {
    function updateTime() {
        const now = new Date();
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString();
        }
    }

    setInterval(updateTime, 1000);
    updateTime();
}

/**
 * Shows a notification message
 * @param {string} message The message to display
 * @param {string} type The notification type (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    // Check if notification container exists, if not create it
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close">×</button>
        </div>
    `;
    
    // Add notification to container
    container.appendChild(notification);
    
    // Add close button functionality
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', () => {
        notification.classList.add('notification-hiding');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
        if (notification.isConnected) {
            notification.classList.add('notification-hiding');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, 5000);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('notification-visible');
    }, 10);
}
