function nats_call(proofRequestThreadId) {
    $.ajax({ 
        url: '/fetch_verified_user_data/', // Update URL to match your Django URL
        method: 'GET',
        data: {
            thread_id: proofRequestThreadId // Pass thread_id as a parameter
        },
        success: function(response) {
            alert(response);
        },
        error: function(xhr, status, error) {
            console.error(error); // Log any errors to the console
        }
    });
}