function nats_call(proofRequestThreadId,value) {
    $.ajax({
        url: '/fetch_verified_user_data/',
        method: 'GET',
        data: {
            thread_id: proofRequestThreadId,
            value:value
        },
        success: function(response) {
           
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
                    //alert(response.message); // Or handle the message display appropriately
                }
            }
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
        }
    });
}

function makeNdiDashCallEID(eid) {
    $.ajax({
        url: '/ndi_dash_eid/',
        method: 'POST',
        data: {
            eid: eid
        },
        headers: {
            'X-CSRFToken': csrftoken  // Ensure csrftoken is defined
        },
        success: function(response) {
            //alert(response.redirect);
            if (response.redirect === 'update_password') {
                if (response.security_questions) {
                    // Store security questions in sessionStorage if they exist
                    sessionStorage.setItem('security_questions', JSON.stringify(response.security_questions));
                }
                window.location.href = '/update_password_ndi'; // Redirect to update_password page
            } else if (response.redirect === 'dashboard') {
                window.location.href = '/dashboard'; // Redirect to dashboard
            } else if (response.redirect === 'index') {
                window.location.href = '/';
                if (response.message) {
                    // Optionally display the message
                    alert(response.message); // Or handle the message display appropriately
                }
            }
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
            alert("An error occurred while processing your request. Please try again.");
        }
    });
}


function nats_proponent_call(proofRequestThreadId,value) {
    //alert('inside nats_proponent_call');
    $.ajax({
        url: '/fetch_verified_user_data/',
        method: 'GET',
        data: {
            thread_id: proofRequestThreadId,
            value:value
        },
        success: function(response) {
            // Do nothing here
        },
        error: function(xhr, status, error) {
            console.error("Error fetching user data:", error);
        }
    });
}

function makeIssuanceCall(relationshipDid,thid,id_number,holder_did) {
    $.ajax({
        url: '/issuance_call/',
        method: 'POST',
        data: {
            relationshipDid: relationshipDid,
            thread_id:thid,
            id_number:id_number,
            holder_did:holder_did
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            if (response.message) {
                alert(response.message);
            } else if (response.error) {
                alert(response.error);
            }
        },
        error: function(xhr, status, error) {
            console.error("Error response received:", xhr.responseText); // Debug statement
            try {
                var response = JSON.parse(xhr.responseText);
                if (response.details) {
                    console.error("Details:", response.details);
                }
            } catch (e) {
                console.error("Unexpected error:", e); // Debug statement
            }
        }
    });
}
