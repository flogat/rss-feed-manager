$(document).ready(function() {
    // Initialize sort state
    let currentSort = {
        column: 'title',
        direction: 'asc'
    };

    // Add click handlers for sortable columns
    $('.sortable').click(function() {
        const column = $(this).data('sort');
        if (currentSort.column === column) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.column = column;
            currentSort.direction = 'asc';
        }
        
        // Update sort indicators
        $('.sortable').removeClass('active');
        $(this).addClass('active');
        $('.sortable i').attr('class', 'bi bi-sort-alpha-down');
        const iconClass = currentSort.direction === 'asc' ? 'down' : 'up';
        $(this).find('i').attr('class', `bi bi-sort-${column === 'num_articles' || column === 'recent_articles' ? 'numeric' : 'alpha'}-${iconClass}`);
        
        loadFeeds(currentSort);
    });
    
    // Load feeds on page load
    loadFeeds(currentSort);
    
    // Set default dates for download form
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);
    
    $('#startDate').val(sevenDaysAgo.toISOString().split('T')[0]);
    $('#endDate').val(today.toISOString().split('T')[0]);

    // Refresh feeds
    $('#refreshFeeds').click(function() {
        $.post('/api/feeds/refresh')
            .done(function() {
                loadFeeds();
            })
            .fail(function(xhr) {
                const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
                showError('Error refreshing feeds: ' + error);
            });
    });

    // Add feeds
    $('#addFeedForm').submit(function(e) {
        e.preventDefault();
        const urls = $('#feedUrls').val().split('\n').filter(url => url.trim());
        
        if (urls.length === 0) {
            showError('Please enter at least one URL');
            return;
        }
        
        $.ajax({
            url: '/api/feeds/bulk',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                urls: urls
            })
        })
        .done(function(response) {
            $('#addFeedModal').modal('hide');
            $('#feedUrls').val('');
            loadFeeds();
            
            if (response.errors && response.errors.length > 0) {
                showError('Some feeds could not be added: ' + response.errors.join(', '));
            }
        })
        .fail(function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
            showError('Error adding feeds: ' + error);
        });
    });

    // Download articles
    $('#downloadForm').submit(function(e) {
        e.preventDefault();
        const startDate = $('#startDate').val();
        const endDate = $('#endDate').val();
        
        window.location.href = `/api/articles/download?start_date=${startDate}&end_date=${endDate}`;
    });
});

function loadFeeds(sort = { column: 'title', direction: 'asc' }) {
    $.get('/api/feeds')
        .done(function(feeds) {
            // Sort feeds based on current sort settings
            feeds.sort((a, b) => {
                let aVal = a[sort.column];
                let bVal = b[sort.column];
                
                // Handle special cases
                if (sort.column === 'last_article_date') {
                    aVal = aVal ? new Date(aVal).getTime() : 0;
                    bVal = bVal ? new Date(bVal).getTime() : 0;
                } else if (sort.column === 'num_articles' || sort.column === 'recent_articles') {
                    aVal = aVal || 0;
                    bVal = bVal || 0;
                } else {
                    aVal = (aVal || '').toString().toLowerCase();
                    bVal = (bVal || '').toString().toLowerCase();
                }
                
                if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
                return 0;
            });
            
            const tbody = $('#feedsList');
            tbody.empty();
            
            let totalArticles = 0;
            let totalRecentArticles = 0;
            let mostRecentFeed = null;
            let mostRecentDate = null;
            
            feeds.forEach(function(feed) {
                totalArticles += feed.num_articles;
                totalRecentArticles += feed.recent_articles || 0;
                
                // Track most recent article
                if (feed.last_article_date) {
                    const articleDate = new Date(feed.last_article_date);
                    if (!mostRecentDate || articleDate > mostRecentDate) {
                        mostRecentDate = articleDate;
                        mostRecentFeed = feed;
                    }
                }
                
                const row = $('<tr>').attr('id', `feed-${feed.id}`);
                row.append($('<td>').text(feed.title || 'Untitled'));
                row.append($('<td>').text(feed.url));
                row.append($('<td>').text(feed.num_articles));
                row.append($('<td>').text(feed.recent_articles || 0));
                row.append($('<td>').text(feed.last_article_date ? formatRelativeTime(feed.last_article_date) : 'No articles'));
                row.append($('<td>').text(feed.last_updated ? formatRelativeTime(feed.last_updated) : 'Never'));
                row.append($('<td>').html(getStatusBadge(feed.status)));
                
                const actions = $('<td>');
                // Add refresh button
                const refreshBtn = $('<button>')
                    .addClass('btn btn-sm btn-secondary me-2')
                    .html('<i class="bi bi-arrow-clockwise"></i>')
                    .click(function() {
                        refreshSingleFeed(feed.id);
                    });
                // Add delete button
                const deleteBtn = $('<button>')
                    .addClass('btn btn-sm btn-danger')
                    .html('<i class="bi bi-trash"></i>')
                    .click(function() {
                        deleteFeed(feed.id);
                    });
                actions.append(refreshBtn, deleteBtn);
                
                row.append(actions);
                tbody.append(row);
            });
            
            // Update summary with most recent article info
            let summaryHtml = `<strong>Feed Statistics:</strong> ${feeds.length} feeds tracked, ` +
                `${totalArticles} total articles, ` +
                `${totalRecentArticles} articles in the last 7 days`;
            
            if (mostRecentFeed && mostRecentDate) {
                summaryHtml += `<br><strong>Latest Article:</strong> ${formatRelativeTime(mostRecentDate)} from "${mostRecentFeed.title || 'Untitled'}"`;
            }
            
            $('#feedSummary').html(summaryHtml);
        })
        .fail(function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
            showError('Error loading feeds: ' + error);
        });
}

function deleteFeed(feedId) {
    if (confirm('Are you sure you want to delete this feed?')) {
        $.ajax({
            url: `/api/feeds/${feedId}`,
            method: 'DELETE'
        })
        .done(function() {
            loadFeeds();
        })
        .fail(function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
            showError('Error deleting feed: ' + error);
        });
    }
}

function formatRelativeTime(dateStr) {
    if (!dateStr) return 'Never';
    
    const date = new Date(dateStr);
    const now = new Date();
    // Convert both to UTC milliseconds for comparison
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    const diffMonths = Math.floor(diffDays / 30);
    
    if (diffSecs < 60) return `${diffSecs} second${diffSecs === 1 ? '' : 's'} ago`;
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    if (diffHours < 10) {
        const remainingMins = diffMins % 60;
        return remainingMins ? 
            `${diffHours} hour${diffHours === 1 ? '' : 's'} ${remainingMins} minute${remainingMins === 1 ? '' : 's'} ago` :
            `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    }
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    if (diffMonths < 12) {
        const remainingDays = diffDays % 30;
        return remainingDays ? 
            `${diffMonths} month${diffMonths === 1 ? '' : 's'}, ${remainingDays} day${remainingDays === 1 ? '' : 's'} ago` :
            `${diffMonths} month${diffMonths === 1 ? '' : 's'} ago`;
    }
    return date.toLocaleDateString();
}

function getStatusBadge(status) {
    const classes = {
        'active': 'bg-success',
        'error': 'bg-danger',
        'refreshing': 'bg-warning'
    };
    return `<span class="badge ${classes[status] || 'bg-secondary'}">${status}</span>`;
}

function refreshSingleFeed(feedId) {
    // Find the feed's status cell and update it
    const row = $(`#feed-${feedId}`);
    const statusCell = row.find('td').eq(6); // Status is the 7th column
    statusCell.html(getStatusBadge('refreshing'));
    
    $.post(`/api/feeds/${feedId}/refresh`)
        .done(function(response) {
            loadFeeds();
        })
        .fail(function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Unknown error occurred';
            showError('Error refreshing feed: ' + error);
            loadFeeds();
        });
}

function showError(message) {
    const toast = document.getElementById('errorToast');
    toast.querySelector('.toast-body').textContent = message;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
