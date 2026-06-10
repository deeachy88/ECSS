let proofPollTimer = null;

function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input && input.value) {
        return input.value;
    }
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

function getNdiSession() {
    return window.sessionId || sessionStorage.getItem('ndi_session_id');
}

function setNdiSession(id) {
    window.sessionId = id;
    if (id) {
        sessionStorage.setItem('ndi_session_id', id);
    }
}

function clearNdiSession() {
    window.sessionId = null;
    window.ndiWalletActionStarted = false;
    sessionStorage.removeItem('ndi_session_id');
    sessionStorage.removeItem('ndi_category');
    sessionStorage.removeItem('ndi_thread_id');
}

function stopProofPolling() {
    if (proofPollTimer) {
        clearInterval(proofPollTimer);
        proofPollTimer = null;
    }
}

function hideNdiLoaderIfAvailable() {
    if (typeof window.hideNdiLoader === 'function') {
        window.hideNdiLoader();
    }
}

function showNdiWaitingIfAvailable() {
    if (typeof window.showNdiWaitingLoader === 'function') {
        window.showNdiWaitingLoader();
    }
}

function showNdiProcessingIfAvailable() {
    if (typeof window.showNdiProcessingLoader === 'function') {
        window.showNdiProcessingLoader();
    } else {
        showNdiWaitingIfAvailable();
    }
}

function ndiHasActionableProof(data) {
    if (!data || data.pending || data.error) {
        return false;
    }
    if (data.proof_type === 'present-proof/rejected') {
        return false;
    }
    return !!(data.eid || data.id_number || data.full_name || data.relationshipDid);
}

function handleNdiProofData(data) {
    if (!data || data.type === 'connection-established') {
        return false;
    }

    const session_id = data.session_id;
    const activeSession = getNdiSession();
    const pendingThread = sessionStorage.getItem('ndi_thread_id');
    if (data.thid && pendingThread && data.thid !== pendingThread) {
        console.log('Thread ID does not match. Ignoring message.');
        return false;
    }
    if (session_id && activeSession && session_id !== activeSession) {
        console.log('Session ID does not match. Ignoring message.');
        return false;
    }

    const eid = data.eid;
    const id_number = data.id_number;
    const relationshipDid = data.relationshipDid;
    const thid = data.thid;
    const holder_did = data.holder_did;
    const full_name = data.full_name;
    const dzongkhag = data.dzongkhag;
    const gewog = data.gewog;
    const village = data.village;
    const category = data.category || sessionStorage.getItem('ndi_category');
    const proof_type = data.proof_type;

    if (proof_type === 'present-proof/rejected') {
        hideNdiLoaderIfAvailable();
        if (typeof hideAllSpinners === 'function') {
            hideAllSpinners();
        }
        if (category === 'Login') {
            $("#ndi_div").hide();
            $("#loginBox").show();
            $('#ndi_login_error').html("Proof Not Shared From Wallet").show().delay(4000).fadeOut('slow');
        } else if (category === 'Issuance') {
            $('#issuanceMessageError').html("Proof Not Shared From Wallet").show().delay(4000).fadeOut('slow');
        } else if (category === 'Employee') {
            $("#ndi_div").hide();
            $("#loginBox").show();
            $('#ndi_login_error').html("Proof Not Shared From Wallet").show().delay(4000).fadeOut('slow');
        } else {
            $('#proponent_ErrorMsg').html("Proof Not Shared From Wallet").show().delay(4000).fadeOut('slow');
        }
        stopProofPolling();
        clearNdiSession();
        return true;
    }

    if (ndiHasActionableProof(data)) {
        showNdiProcessingIfAvailable();
    }

    if (eid && category === 'Employee' && String(id_number) === '1111') {
        $('#progressIndicator').hide();
        $('#progressIndicator1').hide();
        $('#progressLoader').hide();
        stopProofPolling();
        clearNdiSession();
        makeNdiDashCallEID(eid);
        return true;
    }

    if (id_number && category === 'Login' && String(id_number) !== '1111') {
        $('#progressIndicator').hide();
        $('#progressIndicator1').hide();
        $('#progressLoader').hide();
        stopProofPolling();
        clearNdiSession();
        makeNdiDashCall(id_number);
        return true;
    }

    if (id_number && category === 'Issuance') {
        $('#progressIndicator').hide();
        $('#progressIndicator1').hide();
        $('#progressLoader').hide();
        stopProofPolling();
        clearNdiSession();
        makeIssuanceCall(relationshipDid, thid, id_number, holder_did);
        return true;
    }

    if (full_name && category === 'Registration') {
        hideNdiLoaderIfAvailable();
        if (typeof hideAllSpinners === 'function') {
            hideAllSpinners();
        }
        stopProofPolling();
        clearNdiSession();
        if (typeof showRegistrationForm === 'function') {
            showRegistrationForm();
        }
        if (typeof fillInputFields === 'function') {
            fillInputFields(id_number, full_name, dzongkhag, gewog, village);
        }
        return true;
    }

    return false;
}

function startProofPolling(proofRequestThreadId, value) {
    stopProofPolling();
    sessionStorage.setItem('ndi_thread_id', proofRequestThreadId);
    sessionStorage.setItem('ndi_category', value);

    const pollOnce = function() {
        $.ajax({
            url: '/fetch_verified_user_data/',
            method: 'GET',
            data: {
                thread_id: proofRequestThreadId,
                value: value
            },
            success: function(response) {
                if (!response || response.error) {
                    return;
                }
                if (response.pending) {
                    return;
                }
                showNdiProcessingIfAvailable();
                handleNdiProofData(response);
            },
            error: function(xhr, status, error) {
                console.error("Error fetching user data:", error);
            }
        });
    };

    pollOnce();
    proofPollTimer = setInterval(pollOnce, 2000);
}

function nats_call(proofRequestThreadId, value) {
    startProofPolling(proofRequestThreadId, value);
}

function makeNdiDashCall(id_number) {
    $.ajax({
        url: '/ndi_dash/',
        method: 'POST',
        data: {
            id_number: id_number
        },
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        success: function(response) {
            if (response.redirect === 'update_password') {
                sessionStorage.setItem('security_questions', JSON.stringify(response.security_questions));
                window.location.href = '/update_password_ndi';
            } else if (response.redirect === 'dashboard') {
                window.location.href = '/dashboard';
            } else if (response.redirect === 'index') {
                hideNdiLoaderIfAvailable();
                if (response.message === 'ID Not Found') {
                    $("#loginModalForm").modal('show');
                    $("#ndi_div").hide();
                    $("#loginBox").show();
                    $('#ndi_login_error').html("CID Not Found. Please Register First To Login").show().delay(10000).fadeOut('slow');
                }
            } else {
                hideNdiLoaderIfAvailable();
            }
        },
        error: function(xhr, status, error) {
            hideNdiLoaderIfAvailable();
            console.error("Error in ndi_dash:", error, xhr.status, xhr.responseText);
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
            'X-CSRFToken': getCsrfToken()
        },
        success: function(response) {
            if (response.redirect === 'update_password') {
                if (response.security_questions) {
                    sessionStorage.setItem('security_questions', JSON.stringify(response.security_questions));
                }
                window.location.href = '/update_password_ndi';
            } else if (response.redirect === 'dashboard') {
                window.location.href = '/dashboard';
            } else if (response.redirect === 'index') {
                hideNdiLoaderIfAvailable();
                if (response.message === 'ID Not Found') {
                    $("#loginModalForm").modal('show');
                    $("#ndi_div").hide();
                    $("#loginBox").show();
                    $('#ndi_login_error').html("EID Not Found. Please Register First To Login").show().delay(10000).fadeOut('slow');
                }
            } else {
                hideNdiLoaderIfAvailable();
            }
        },
        error: function(xhr, status, error) {
            hideNdiLoaderIfAvailable();
            console.error("Error fetching user data:", error);
            alert("An error occurred while processing your request. Please try again.");
        }
    });
}

function nats_proponent_call(proofRequestThreadId, value) {
    startProofPolling(proofRequestThreadId, value);
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
            'X-CSRFToken': getCsrfToken()
        },
        success: function(response) {
            hideNdiLoaderIfAvailable();
            if (response.success) {
                $('#ndi_div').hide();
                $('#issuanceMessageDiv').show();
            } else {
                $('#loginBox').hide();
                $('#issuanceMessageError').show();
                $('#issuanceMessageError').text(response.error || 'An error occurred');
            }
        },
        error: function(xhr, status, error) {
            hideNdiLoaderIfAvailable();
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
            $('#issuanceMessageError').show().text(errorMessage).delay(10000).fadeOut('slow');
        }
    });
}

function resumeNdiFlowIfPending() {
    const threadId = sessionStorage.getItem('ndi_thread_id');
    const category = sessionStorage.getItem('ndi_category');
    if (!threadId || !category) {
        return;
    }

    if (category === 'Registration') {
        if ($('#registrationModalForm').length) {
            $("#registrationModalForm").modal('show');
        }
        $('#registration_div').hide();
        if (typeof window.getProponentNdiPanel === 'function') {
            window.getProponentNdiPanel().show();
        } else {
            $('#ndi_div_proponent').last().show();
        }
    } else {
        $("#loginModalForm").modal('show');
        $('#loginBox').hide();
        $("#ndi_div").show();
    }

    startProofPolling(threadId, category);
}
