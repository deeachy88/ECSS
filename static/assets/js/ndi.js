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
                if (typeof window.hideNdiLoader === 'function') {
                    window.hideNdiLoader();
                }
                //alert('inside update_password');
                // Store security questions in sessionStorage or pass as needed
                sessionStorage.setItem('security_questions', JSON.stringify(response.security_questions));
                window.location.href = '/update_password_ndi'; // Redirect to update_password page
            } else if (response.redirect === 'dashboard') {
                if (typeof window.hideNdiLoader === 'function') {
                    window.hideNdiLoader();
                }
                window.location.href = '/dashboard'; // Redirect to dashboard
            } else if (response.redirect === 'index') {
                // Handle index redirect, possibly display the message
                if(response.message === 'ID Not Found')
                {
                    if (typeof window.hideNdiLoader === 'function') {
                        window.hideNdiLoader();
                    }
                    $("#loginModalForm").modal('show');
                    $("#ndi_div").hide();
                    $("#loginBox").show();
                    $('#ndi_login_error').html("CID Not Found. Please Register First To Login");
                    $('#ndi_login_error').show();
                    $('#ndi_login_error').delay(10000).fadeOut('slow');
                }
            }
        },
        error: function(xhr, status, error) {
            if (typeof window.hideNdiLoader === 'function') {
                window.hideNdiLoader();
            }
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
                if (typeof window.hideNdiLoader === 'function') {
                    window.hideNdiLoader();
                }
                if (response.security_questions) {
                    // Store security questions in sessionStorage if they exist
                    sessionStorage.setItem('security_questions', JSON.stringify(response.security_questions));
                }
                window.location.href = '/update_password_ndi'; // Redirect to update_password page
            } else if (response.redirect === 'dashboard') {
                if (typeof window.hideNdiLoader === 'function') {
                    window.hideNdiLoader();
                }
                window.location.href = '/dashboard'; // Redirect to dashboard
            } else if (response.redirect === 'index') {
                // Handle index redirect, possibly display the message
                if(response.message === 'ID Not Found')
                {
                    if (typeof window.hideNdiLoader === 'function') {
                        window.hideNdiLoader();
                    }
                    $("#loginModalForm").modal('show');
                    $("#ndi_div").hide();
                    $("#loginBox").show();
                    $('#ndi_login_error').html("EID Not Found. Please Register First To Login");
                    $('#ndi_login_error').show();
                    $('#ndi_login_error').delay(10000).fadeOut('slow');
                }
            }
        },
        error: function(xhr, status, error) {
            if (typeof window.hideNdiLoader === 'function') {
                window.hideNdiLoader();
            }
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

function makeIssuanceCall(relationshipDid, thid, id_number, holder_did) {
    $.ajax({
        url: '/issuance_call/',
        method: 'POST',
        data: {
            relationshipDid: relationshipDid,
            thread_id: thid,
            id_number: id_number,
            holder_did: holder_did
        },
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            if (typeof window.hideNdiLoader === 'function') {
                window.hideNdiLoader();
            }
            if (response.success) {
                $('#ndi_div').hide();
                $('#issuanceMessageDiv').show();
            } else {
                $('#loginBox').hide();
                $('#issuanceMessageError').show();
                // Display the error message from the response
                $('#issuanceMessageError').text(response.error || 'An error occurred');
            }
        },
        error: function(xhr, status, error) {
            if (typeof window.hideNdiLoader === 'function') {
                window.hideNdiLoader();
            }
            // Handle HTTP errors (like 500, 404, etc.)
            let errorMessage = 'Request failed';
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    errorMessage = response.error;
                }
            } catch (e) {
                errorMessage = `${xhr.statusText}: ${error}`;
            }
            
            $('#loginBox').hide();
            $('#issuanceMessageError').show().text(errorMessage);
            $('#issuanceMessageError').delay(10000).fadeOut('slow');
            location.reload
        }
    });
}

// NDI waiting loader (shown after QR scan while proof is being verified)
(function() {
    let ndiWaitingTimer = null;

    window.showNdiWaitingLoader = function() {
        const $overlay = $('#ndiLoaderOverlay');
        if (!$overlay.length) return;

        const $main = $('#ndiLoaderMainText');
        const $sub = $('#ndiLoaderSubText');

        if ($main.length) $main.text('Waiting for response');
        if ($sub.length) $sub.text('Please wait');

        $overlay.css('display', 'flex');

        let dots = 0;
        if (ndiWaitingTimer) {
            clearInterval(ndiWaitingTimer);
        }
        ndiWaitingTimer = setInterval(function() {
            dots = (dots + 1) % 4;
            const suffix = '.'.repeat(dots);
            if ($sub.length) $sub.text('Please wait' + suffix);
        }, 500);
    };

    window.hideNdiLoader = function() {
        const $overlay = $('#ndiLoaderOverlay');
        if ($overlay.length) $overlay.hide();
        if (ndiWaitingTimer) {
            clearInterval(ndiWaitingTimer);
            ndiWaitingTimer = null;
        }
    };
})();
