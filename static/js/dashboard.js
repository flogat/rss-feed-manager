// Function to format timestamps
function formatTimestamp(isoString, useRelative = false) {
    if (!isoString) return 'Never';
    
    // Parse the UTC ISO string and convert to local time
    const utcDate = new Date(isoString);
    const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000);
    
    if (useRelative) {
        const now = new Date();
        // Convert now to UTC for comparison
        const nowUTC = new Date(now.getTime() + now.getTimezoneOffset() * 60000);
        const diffMs = nowUTC - utcDate;
        const diffSeconds = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSeconds / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'just now';
        if (diffMins < 10) {
            // Show minutes and seconds when less than 10 minutes
            const secs = Math.floor(diffSeconds % 60);
            return `${diffMins} minute${diffMins === 1 ? '' : 's'} ${secs} second${secs === 1 ? '' : 's'} ago`;
        }
        if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
        if (diffHours < 10) {
            // Show hours and minutes when less than 10 hours
            const mins = Math.floor(diffMins % 60);
            return `${diffHours} hour${diffHours === 1 ? '' : 's'} ${mins} minute${mins === 1 ? '' : 's'} ago`;
        }
        if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
        if (diffDays < 10) {
            // Show days and hours when less than 10 days
            const hrs = Math.floor(diffHours % 24);
            return `${diffDays} day${diffDays === 1 ? '' : 's'} ${hrs} hour${hrs === 1 ? '' : 's'} ago`;
        }
        if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
        return localDate.toLocaleDateString();
    }
    
    return localDate.toLocaleString();
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
            // Show progress bar for both manual and automatic scans
            if (scanProgress && scanProgress.is_scanning) {
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
                Total Articles: ${totalArticles} (${recentArticles} in last 7 days)
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
                        <td>${formatTimestamp(feed.last_article_date, true)}</td>
                        <td>${formatTimestamp(feed.last_scan_time, true)}</td>
                        <td>${feed.last_scan_trigger}</td>
                        <td>${feed.status}</td>
                        <td>
                            <a href="/feeds/${feed.id}/articles" class="btn btn-sm btn-primary">
                                <i class="bi bi-list-ul"></i>
                            </a>
                            <button class="btn btn-sm btn-secondary refresh-feed" data-feed-id="${feed.id}">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                            <button class="btn btn-sm btn-info download-feed" data-feed-id="${feed.id}">
                                <i class="bi bi-download"></i>
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
        const row = button.closest('tr');
        button.prop('disabled', true);
        
        // Update status immediately to show scanning
        const statusCell = row.find('td:nth-child(8)');
        const originalStatus = statusCell.text();
        statusCell.text('scanning...');
        
        $.post(`/api/feeds/${feedId}/refresh`)
            .done(function(response) {
                // Update status immediately
                statusCell.text('scan complete');
                
                // Update last scan time
                const lastScanCell = row.find('td:nth-child(6)');
                lastScanCell.text(formatTimestamp(new Date().toISOString(), true));
                
                // If response contains updated feed data, update last article date
                if (response.feed && response.feed.last_article_date) {
                    const lastArticleCell = row.find('td:nth-child(5)');
                    lastArticleCell.text(formatTimestamp(response.feed.last_article_date, true));
                }
                
                // Full reload after a delay to get all updated stats
                setTimeout(() => loadFeeds(currentSort), 500);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                statusCell.text(originalStatus);
                showError('Error refreshing feed: ' + error);
            })
            .always(function() {
                button.prop('disabled', false);
            });
    });
    
    // Handle feed article download
    $('#feedsList').on('click', '.download-feed', function() {
        const feedId = $(this).data('feed-id');
        window.location.href = `/api/feeds/${feedId}/articles/download`;
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
    // Initialize download modal dates when shown
    $('#downloadModal').on('show.bs.modal', function() {
        const today = new Date();
        const sevenDaysAgo = new Date(today);
        sevenDaysAgo.setDate(today.getDate() - 7);
        
        // Format dates as YYYY-MM-DD
        $('#startDate').val(sevenDaysAgo.toISOString().split('T')[0]);
        $('#endDate').val(today.toISOString().split('T')[0]);
    });

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