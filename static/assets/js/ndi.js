function nats_call(proofRequestThreadId) {
    $.ajax({
        url: '/fetch_verified_user_data/',
        method: 'GET',
        data: {
            thread_id: proofRequestThreadId
        },
        success: function(response) {
            // Do nothing here
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
        }
    });
}


// Function to make the second AJAX call to /ndi_dash/
function makeNdiDashCall(id_number) {
    $.ajax({
        url: '/ndi_dash/',
        method: 'POST',
        data: {
            id_number: id_number
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            // Do nothing here or perform any additional logic
            // The redirection is handled separately
            window.location.href = '/dashboard'; // Redirect to the test_dashboard page
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
        }
    });
}
