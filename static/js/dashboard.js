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
            
            feeds.forEach(function(feed) {
                const row = $('<tr>');
                row.append($('<td>').text(feed.title || 'Untitled'));
                row.append($('<td>').text(feed.url));
                row.append($('<td>').text(feed.num_articles));
                row.append($('<td>').text(feed.last_article_date ? new Date(feed.last_article_date).toLocaleString() : 'No articles'));
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