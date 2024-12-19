$(document).ready(function() {
    // Load feeds on page load
    loadFeeds();
    
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

function loadFeeds() {
    $.get('/api/feeds')
        .done(function(feeds) {
            const tbody = $('#feedsList');
            tbody.empty();
            
            let totalArticles = 0;
            let totalRecentArticles = 0;
            
            feeds.forEach(function(feed) {
                totalArticles += feed.num_articles;
                totalRecentArticles += feed.recent_articles || 0;
                
                const row = $('<tr>');
                row.append($('<td>').text(feed.title || 'Untitled'));
                row.append($('<td>').text(feed.url));
                row.append($('<td>').text(feed.num_articles));
                row.append($('<td>').text(feed.recent_articles || 0));
                row.append($('<td>').text(feed.last_article_date ? formatRelativeTime(feed.last_article_date) : 'No articles'));
                row.append($('<td>').html(getStatusBadge(feed.status)));
                
                const actions = $('<td>');
                const deleteBtn = $('<button>')
                    .addClass('btn btn-sm btn-danger')
                    .html('<i class="bi bi-trash"></i>')
                    .click(function() {
                        deleteFeed(feed.id);
                    });
                actions.append(deleteBtn);
                
                row.append(actions);
                tbody.append(row);
            });
            
            // Update summary
            $('#feedSummary').html(
                `<strong>Feed Statistics:</strong> ${feeds.length} feeds tracked, ` +
                `${totalArticles} total articles, ` +
                `${totalRecentArticles} articles in the last 7 days`
            );
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
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    const diffMonths = Math.floor(diffDays / 30);
    
    if (diffSecs < 60) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
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
        'error': 'bg-danger'
    };
    return `<span class="badge ${classes[status] || 'bg-secondary'}">${status}</span>`;
}

function showError(message) {
    const toast = document.getElementById('errorToast');
    toast.querySelector('.toast-body').textContent = message;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}