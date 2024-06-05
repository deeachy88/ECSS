function nats_call(proofRequestThreadId) {
    // Make AJAX call to fetch_verified_user_data
    $.ajax({
        url: '/fetch_verified_user_data/',
        method: 'GET',
        data: {
            thread_id: proofRequestThreadId
        },
        success: function(response) {
            setTimeout(function() {
                $.ajax({
                    url: '/ndi_dash/',
                    method: 'GET',
                    success: function(response) {
                        // Redirect to the test_dashboard page after the ndi_dash AJAX call
                        window.location.href = '/ndi_dash/';
                    },
                    error: function(xhr, status, error) {
                        console.error("Error fetching user data:", error);
                    }
                });
            }, 20000); // 20 seconds delay
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
        }
    });
}