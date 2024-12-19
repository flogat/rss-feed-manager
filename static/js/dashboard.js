$(document).ready(function() {
    // Load feeds on page load
    loadFeeds();

    // Refresh feeds
    $('#refreshFeeds').click(function() {
        $.post('/api/feeds/refresh')
            .done(function() {
                loadFeeds();
            })
            .fail(function(xhr) {
                alert('Error refreshing feeds: ' + xhr.responseJSON.error);
            });
    });

    // Add feed
    $('#addFeedForm').submit(function(e) {
        e.preventDefault();
        $.ajax({
            url: '/api/feeds',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                url: $('#feedUrl').val()
            })
        })
        .done(function() {
            $('#addFeedModal').modal('hide');
            $('#feedUrl').val('');
            loadFeeds();
        })
        .fail(function(xhr) {
            alert('Error adding feed: ' + xhr.responseJSON.error);
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
                row.append($('<td>').text(new Date(feed.last_updated).toLocaleString()));
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
            alert('Error loading feeds: ' + xhr.responseJSON.error);
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
            alert('Error deleting feed: ' + xhr.responseJSON.error);
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
