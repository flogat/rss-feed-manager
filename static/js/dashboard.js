// Function to format timestamps
function formatTimestamp(isoString) {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    return date.toLocaleString();
}

// Function to show error messages
function showError(message) {
    const toast = document.getElementById('errorToast');
    toast.querySelector('.toast-body').textContent = message;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Function to start countdown timer
function startCountdownTimer(initialNextScanTime) {
    window.nextScanTime = initialNextScanTime;
    
    // Clear existing interval if any
    if (window.countdownInterval) {
        clearInterval(window.countdownInterval);
    }
    
    function updateCountdown() {
        const now = new Date();
        const diffMs = window.nextScanTime - now;
        
        if (diffMs <= 0) {
            clearInterval(window.countdownInterval);
            window.countdownInterval = null;
            return;
        }
        
        const diffMins = Math.floor(diffMs / 60000);
        const diffSecs = Math.floor((diffMs % 60000) / 1000);
        
        let timeStr = '';
        if (diffMins > 0) {
            timeStr += `${diffMins} minute${diffMins === 1 ? '' : 's'}`;
            if (diffSecs > 0) {
                timeStr += ` ${diffSecs} second${diffSecs === 1 ? '' : 's'}`;
            }
        } else {
            timeStr = `${diffSecs} second${diffSecs === 1 ? '' : 's'}`;
        }
        
        // Update all instances of next scan time display
        $('.next-scan-time').text(`in ${timeStr}`);
    }
    
    // Update immediately and then every second
    updateCountdown();
    window.countdownInterval = setInterval(updateCountdown, 1000);
}

let currentSort = {
    column: 'title',
    direction: 'asc'
};

function loadFeeds(sort = currentSort) {
    $.get('/api/feeds')
        .done(function(response) {
            const feeds = response.feeds;
            // Update document title and progress bar
            const scanProgress = response.scan_progress;
            if (scanProgress && scanProgress.is_scanning && !scanProgress.completed) {
                // Update title
                document.title = `Scanning... (${scanProgress.current_index}/${scanProgress.total_feeds}) - RSS Downloader`;
                
                // Show and update progress bar
                const progressPercent = (scanProgress.current_index / scanProgress.total_feeds) * 100;
                $('#scanProgress').show();
                $('#scanProgress .progress-bar')
                    .css('width', `${progressPercent}%`)
                    .attr('aria-valuenow', progressPercent);
            } else {
                document.title = 'RSS Downloader';
                $('#scanProgress').hide();
            }

            // Update summary
            let activeFeeds = feeds.filter(f => f.status === 'active').length;
            let totalArticles = feeds.reduce((sum, feed) => sum + feed.num_articles, 0);
            let recentArticles = feeds.reduce((sum, feed) => sum + feed.recent_articles, 0);
            
            $('#feedSummary').html(`
                Total Feeds: ${feeds.length} (${activeFeeds} active)<br>
                Total Articles: ${totalArticles} (${recentArticles} in last 7 days)<br>
                Next automatic scan: <span class="next-scan-time">calculating...</span>
            `);
            
            // Update next scan time without resetting the timer if it's already running
            if (response.next_scan) {
                const nextScanTime = new Date(response.next_scan);
                if (!window.countdownInterval) {
                    startCountdownTimer(nextScanTime);
                } else {
                    window.nextScanTime = nextScanTime; // Update the time without restarting timer
                }
            }

            // Sort feeds based on current sort settings
            feeds.sort((a, b) => {
                let aVal = a[sort.column];
                let bVal = b[sort.column];
                
                // Handle null values
                if (aVal === null && bVal === null) return 0;
                if (aVal === null) return 1;
                if (bVal === null) return -1;
                
                // Compare based on type
                if (typeof aVal === 'string') {
                    return sort.direction === 'asc' ? 
                        aVal.localeCompare(bVal) : 
                        bVal.localeCompare(aVal);
                }
                return sort.direction === 'asc' ? aVal - bVal : bVal - aVal;
            });

            // Render feeds
            const tbody = $('#feedsList');
            tbody.empty();
            feeds.forEach(feed => {
                tbody.append(`
                    <tr>
                        <td>${feed.title || feed.url}</td>
                        <td>${feed.url}</td>
                        <td>${feed.num_articles}</td>
                        <td>${feed.recent_articles}</td>
                        <td>${formatTimestamp(feed.last_article_date)}</td>
                        <td>${formatTimestamp(feed.last_scan_time)}</td>
                        <td>${feed.last_scan_trigger}</td>
                        <td>${feed.status}</td>
                        <td>
                            <button class="btn btn-sm btn-primary refresh-feed" data-feed-id="${feed.id}">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-feed" data-feed-id="${feed.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                `);
            });
        })
        .fail(function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Failed to load feeds';
            showError(error);
        });
}

$(document).ready(function() {
    // Initial load
    loadFeeds();
    
    // Refresh feeds periodically
    setInterval(loadFeeds, 5000);
    
    // Handle sorting
    $('.sortable').click(function() {
        const column = $(this).data('sort');
        if (currentSort.column === column) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort = {
                column: column,
                direction: 'asc'
            };
        }
        
        // Update sort indicators
        $('.sortable').removeClass('active');
        $(this).addClass('active');
        
        // Update icon
        const icon = $(this).find('i');
        if (currentSort.direction === 'asc') {
            icon.removeClass('bi-sort-down').addClass('bi-sort-up');
        } else {
            icon.removeClass('bi-sort-up').addClass('bi-sort-down');
        }
        
        loadFeeds(currentSort);
    });
    
    // Handle individual feed refresh
    $('#feedsList').on('click', '.refresh-feed', function() {
        const feedId = $(this).data('feed-id');
        const button = $(this);
        button.prop('disabled', true);
        
        $.post(`/api/feeds/${feedId}/refresh`)
            .done(function(response) {
                loadFeeds(currentSort);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error refreshing feed: ' + error);
            })
            .always(function() {
                button.prop('disabled', false);
            });
    });
    
    // Handle feed deletion
    $('#feedsList').on('click', '.delete-feed', function() {
        if (!confirm('Are you sure you want to delete this feed?')) return;
        
        const feedId = $(this).data('feed-id');
        $.ajax({
            url: `/api/feeds/${feedId}`,
            method: 'DELETE'
        })
            .done(function(response) {
                loadFeeds(currentSort);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error deleting feed: ' + error);
            });
    });
    
    // Handle refresh all feeds
    $('#refreshFeeds').click(function() {
        $(this).prop('disabled', true);
        
        $.post('/api/feeds/refresh')
            .done(function(response) {
                loadFeeds(currentSort);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error refreshing feeds: ' + error);
            })
            .always(function() {
                $(this).prop('disabled', false);
            });
    });
    
    // Handle add feed form submission
    $('#addFeedForm').submit(function(e) {
        e.preventDefault();
        const urls = $('#feedUrls').val().split('\n').map(url => url.trim()).filter(url => url);
        
        if (urls.length === 0) {
            showError('Please enter at least one URL');
            return;
        }
        
        $.post('/api/feeds/bulk', {
            urls: urls
        })
            .done(function(response) {
                if (response.errors && response.errors.length > 0) {
                    showError('Some feeds could not be added:\n' + response.errors.join('\n'));
                }
                $('#addFeedModal').modal('hide');
                $('#feedUrls').val('');
                loadFeeds(currentSort);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error adding feeds: ' + error);
            });
    });
    
    // Handle article download form submission
    $('#downloadForm').submit(function(e) {
        e.preventDefault();
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        if (!startDate || !endDate) {
            showError('Please select both start and end dates');
            return;
        }
        
        window.location.href = `/api/articles/download?start_date=${startDate}&end_date=${endDate}`;
        $('#downloadModal').modal('hide');
    });
});

// Initialize sort state globally
//var currentSort = {
//    column: 'title',
//    direction: 'asc'
//};