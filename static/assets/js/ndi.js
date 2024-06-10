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
            //alert(response.redirect);
            if (response.redirect === 'update_password') {
                //alert('inside update_password');
                // Store security questions in sessionStorage or pass as needed
                sessionStorage.setItem('security_questions', JSON.stringify(response.security_questions));
                window.location.href = '/update_password_ndi'; // Redirect to update_password page
            } else if (response.redirect === 'dashboard') {
                window.location.href = '/dashboard'; // Redirect to dashboard
            } else if (response.redirect === 'index') {
                // Handle index redirect, possibly display the message
                window.location.href = '/';
                if (response.message) {
                    alert(response.message); // Or handle the message display appropriately
                }
            }
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
        }
    });
}


function nats_proponent_call(proofRequestThreadId) {
    //alert('inside nats_proponent_call');
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
