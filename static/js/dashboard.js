// Function to format timestamps
function formatTimestamp(isoString, useRelative = false) {
    if (!isoString) return 'Never';

    // Parse the UTC ISO string and convert to local time
    const utcDate = new Date(isoString);
    const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000);

    if (useRelative) {
        const now = new Date();
        const diffMs = now - localDate;
        const diffSeconds = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSeconds / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
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
function startCountdownTimer(nextScanTimeISO) {
    if (!nextScanTimeISO) {
        $('.next-scan-time').text('calculating...');
        return;
    }

    const nextScanTime = new Date(nextScanTimeISO);

    // Clear existing interval if any
    if (window.countdownInterval) {
        clearInterval(window.countdownInterval);
    }

    function updateCountdown() {
        const now = new Date();
        const diffMs = nextScanTime - now;

        if (diffMs <= 0) {
            $('.next-scan-time').text('due now');
            clearInterval(window.countdownInterval);
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

        $('.next-scan-time').text(`in ${timeStr}`);
    }

    // Update immediately and then every second
    updateCountdown();
    window.countdownInterval = setInterval(updateCountdown, 1000);
}

function loadFeeds() {
    $.get('/api/feeds')
        .done(function(response) {
            updateFeedsDisplay(response);
        })
        .fail(function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Failed to load feeds';
            showError(error);
        });
}

function updateFeedsDisplay(response, sortConfig = { column: 'title', direction: 'asc' }) {
    const feeds = response.feeds;
    const scanProgress = response.scan_progress;
    const nextScan = response.next_scan;

    // Start/update countdown timer
    startCountdownTimer(nextScan);

    // Show progress bar for both manual and automatic scans
    if (scanProgress && scanProgress.is_scanning) {
        // Update title
        document.title = `Scanning... (${Math.round(scanProgress.current_index)}/${scanProgress.total_feeds}) - RSS Feed Manager`;

        // Show and update progress bar
        $('#scanProgress').show();
        const progressPercent = (scanProgress.current_index / scanProgress.total_feeds) * 100;
        $('#scanProgress .progress-bar')
            .css('width', `${Math.round(progressPercent)}%`)
            .attr('aria-valuenow', progressPercent);

        // Update summary with scanning information
        let summaryHtml = `Currently scanning: ${scanProgress.current_feed || 'Unknown feed'}<br>
            Progress: ${Math.round(scanProgress.current_index)} of ${scanProgress.total_feeds} feeds<br><br>`;

        // Add regular feed summary after scanning info
        const activeFeeds = feeds.filter(f => f.status === 'active').length;
        const totalArticles = feeds.reduce((sum, feed) => sum + feed.num_articles, 0);
        const recentArticles = feeds.reduce((sum, feed) => sum + feed.recent_articles, 0);

        summaryHtml += `Total Feeds: ${feeds.length} (${activeFeeds} active)<br>
            Total Articles: ${totalArticles} (${recentArticles} in last 7 days)`;

        $('#feedSummary').html(summaryHtml);
    } else {
        // Reset UI when not scanning
        document.title = 'RSS Feed Manager';
        $('#scanProgress').hide();

        // Show regular summary
        const activeFeeds = feeds.filter(f => f.status === 'active').length;
        const totalArticles = feeds.reduce((sum, feed) => sum + feed.num_articles, 0);
        const recentArticles = feeds.reduce((sum, feed) => sum + feed.recent_articles, 0);

        const summaryHtml = `Total Feeds: ${feeds.length} (${activeFeeds} active)<br>
            Total Articles: ${totalArticles} (${recentArticles} in last 7 days)`;

        $('#feedSummary').html(summaryHtml);
    }

    // Sort feeds based on current sort settings
    feeds.sort((a, b) => {
        let aVal = a[sortConfig.column];
        let bVal = b[sortConfig.column];

        // Handle null values
        if (aVal === null && bVal === null) return 0;
        if (aVal === null) return 1;
        if (bVal === null) return -1;

        // Compare based on type
        if (typeof aVal === 'string') {
            return sortConfig.direction === 'asc' ?
                aVal.localeCompare(bVal) :
                bVal.localeCompare(aVal);
        }
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
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
                    <a href="/feeds/${feed.id}/articles" class="btn btn-sm btn-primary" 
                       data-bs-toggle="tooltip" 
                       data-bs-placement="top" 
                       title="View detailed list of all articles from this feed">
                        <i class="bi bi-list-ul"></i>
                    </a>
                    <button class="btn btn-sm btn-secondary refresh-feed" 
                            data-feed-id="${feed.id}"
                            data-bs-toggle="tooltip" 
                            data-bs-placement="top" 
                            title="Manually refresh this feed to check for new articles">
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                    <button class="btn btn-sm btn-info download-feed" 
                            data-feed-id="${feed.id}"
                            data-bs-toggle="tooltip" 
                            data-bs-placement="top" 
                            title="Download all articles from this feed as a CSV file">
                        <i class="bi bi-download"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-feed" 
                            data-feed-id="${feed.id}"
                            data-bs-toggle="tooltip" 
                            data-bs-placement="top" 
                            title="Permanently remove this feed and all its articles">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `);
    });

    // Initialize tooltips after rendering
    $('[data-bs-toggle="tooltip"]').tooltip();
}

$(document).ready(function() {
    // Initialize sort state
    let currentSort = {
        column: 'title',
        direction: 'asc'
    };

    // Initial load
    loadFeeds();

    // Refresh feeds more frequently during scanning
    let pollInterval = 5000;  // Default 5 second interval
    function updatePollInterval(scanProgress) {
        // If scanning, poll every 500ms, otherwise every 5 seconds
        pollInterval = scanProgress && scanProgress.is_scanning ? 500 : 5000;
    }

    function pollFeeds() {
        $.get('/api/feeds')
            .done(function(response) {
                updatePollInterval(response.scan_progress);
                updateFeedsDisplay(response, currentSort);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Failed to load feeds';
                showError(error);
            })
            .always(function() {
                // Schedule next poll based on current interval
                setTimeout(pollFeeds, pollInterval);
            });
    }

    // Start polling
    pollFeeds();

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

        // Reload feeds with new sort
        $.get('/api/feeds')
            .done(function(response) {
                updateFeedsDisplay(response, currentSort);
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Failed to load feeds';
                showError(error);
            });
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
                setTimeout(() => {
                    $.get('/api/feeds')
                        .done(function(response) {
                            updateFeedsDisplay(response, currentSort);
                        });
                }, 500);
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
        const button = $(this);
        button.prop('disabled', true);

        $.ajax({
            url: `/api/feeds/${feedId}`,
            method: 'DELETE'
        })
            .done(function(response) {
                $.get('/api/feeds')
                    .done(function(response) {
                        updateFeedsDisplay(response, currentSort);
                    });
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Failed to delete feed';
                showError(error);
            })
            .always(function() {
                button.prop('disabled', false);
            });
    });

    // Handle refresh all feeds
    $('#refreshFeeds').click(function() {
        const button = $(this);
        button.prop('disabled', true);

        $.post('/api/feeds/refresh')
            .done(function(response) {
                $.get('/api/feeds')
                    .done(function(response) {
                        updateFeedsDisplay(response, currentSort);
                    });
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error refreshing feeds: ' + error);
            })
            .always(function() {
                button.prop('disabled', false);
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

        $.ajax({
            url: '/api/feeds/bulk',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ urls: urls }),
            success: function(response) {
                if (response.errors && response.errors.length > 0) {
                    showError('Some feeds could not be added:\n' + response.errors.join('\n'));
                }
                $('#addFeedModal').modal('hide');
                $('#feedUrls').val('');
                $.get('/api/feeds')
                    .done(function(response) {
                        updateFeedsDisplay(response, currentSort);
                    });
            },
            error: function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error adding feeds: ' + error);
            }
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