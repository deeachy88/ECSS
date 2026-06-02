/**
 * NDI page integration (WebSocket + QR / deep link UI).
 * Requires: jQuery, ndi.js (handleNdiProofData, setNdiSession, nats_call, etc.)
 */
(function() {
    window.RegistrationHandler = window.RegistrationHandler || {
        init: function() {}
    };
    window.selectedLoginType = null;

    let socket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000;
    let ndiLoaderTimer = null;

    window.sessionId = null;

    function connectWebSocket() {
        const host = window.location.hostname;
        const isLocalHost = host === 'localhost' || host === '127.0.0.1';
        const wsProtocol = isLocalHost ? 'ws:' : (window.location.protocol === 'https:' ? 'wss:' : 'ws:');
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/socketserver/`;

        try {
            socket = new WebSocket(wsUrl);

            socket.onopen = function() {
                console.log('WebSocket connected');
                $('#wsStatus').removeClass('ws-disconnected').addClass('ws-connected');
                reconnectAttempts = 0;
            };

            socket.onmessage = function(e) {
                try {
                    const data = JSON.parse(e.data);
                    console.log('Data received:', data);
                    if (isRelevantNdiMessage(data)) {
                        window.showNdiWaitingLoader();
                    }
                    if (typeof handleNdiProofData === 'function') {
                        handleNdiProofData(data);
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };

            socket.onerror = function(error) {
                console.error('WebSocket error:', error);
                $('#wsStatus').removeClass('ws-connected').addClass('ws-disconnected');
            };

            socket.onclose = function() {
                console.log('WebSocket closed');
                $('#wsStatus').removeClass('ws-connected').addClass('ws-disconnected');
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connectWebSocket, reconnectDelay);
                }
            };
        } catch (error) {
            console.error('WebSocket creation error:', error);
        }
    }

    window.hideAllSpinners = function() {
        $('#progressIndicator').hide();
        $('#progressIndicator1').hide();
        $('#progressLoader').hide();
        $('#ndiLoaderOverlay').hide();
    };

    function showNdiLoader(mainText, subText) {
        const defaultMain = 'Generating QR code';
        const defaultSub = 'Please wait';
        const $main = $('#ndiLoaderMainText');
        const $sub = $('#ndiLoaderSubText');
        $main.text(mainText || defaultMain);
        $sub.text(subText || defaultSub);
        $('#ndiLoaderOverlay').css('display', 'flex');

        let dots = 0;
        if (ndiLoaderTimer) {
            clearInterval(ndiLoaderTimer);
        }
        ndiLoaderTimer = setInterval(function() {
            dots = (dots + 1) % 4;
            const suffix = '.'.repeat(dots);
            $sub.text('Please wait' + suffix);
        }, 500);
    }

    function hideNdiLoader() {
        $('#ndiLoaderOverlay').hide();
        if (ndiLoaderTimer) {
            clearInterval(ndiLoaderTimer);
            ndiLoaderTimer = null;
        }
    }

    window.hideNdiLoader = hideNdiLoader;

    window.showNdiWaitingLoader = function() {
        showNdiLoader('Waiting for response', 'Please wait');
    };

    function isNdiAwaitingProof() {
        return !!sessionStorage.getItem('ndi_thread_id');
    }

    function ndiPanelIsVisible() {
        if ($('#ndi_div').is(':visible')) {
            return true;
        }
        const $proPanel = typeof getProponentNdiPanel === 'function'
            ? getProponentNdiPanel()
            : $('#ndi_div_proponent');
        return $proPanel.length && $proPanel.is(':visible');
    }

    function isRelevantNdiMessage(data) {
        if (!data || data.type === 'connection-established') {
            return false;
        }
        const pendingThread = sessionStorage.getItem('ndi_thread_id');
        const activeSession = window.sessionId || sessionStorage.getItem('ndi_session_id');
        if (data.thid && pendingThread && data.thid !== pendingThread) {
            return false;
        }
        if (data.session_id && activeSession && data.session_id !== activeSession) {
            return false;
        }
        return !!(pendingThread || activeSession);
    }

    window.showLoginForm = function(type) {
        window.selectedLoginType = type;
        if (type === 'proponent') {
            $('#proponentLoginForm').show();
            $('#agencyLoginForm').hide();
            $('#btnProponent').addClass('active-login-btn');
            $('#btnAgency').removeClass('active-login-btn');
        } else {
            $('#proponentLoginForm').hide();
            $('#agencyLoginForm').show();
            $('#btnAgency').addClass('active-login-btn');
            $('#btnProponent').removeClass('active-login-btn');
        }
        $('#ndi_login_error').hide();
    };

    function requireLoginTypeSelection() {
        if (window.selectedLoginType === 'proponent' || window.selectedLoginType === 'agency') {
            return true;
        }
        $('#ndi_login_error')
            .html('Please choose Proponent Login or Agency Login first.')
            .show()
            .delay(4000)
            .fadeOut('slow');
        return false;
    }

    window.startNdiLogin = function(value) {
        if (!requireLoginTypeSelection()) {
            return;
        }
        if (window.selectedLoginType !== 'proponent') {
            $('#ndi_login_error')
                .html('Please choose Proponent Login to continue with this Bhutan NDI option.')
                .show()
                .delay(4000)
                .fadeOut('slow');
            return;
        }
        window.authenticate_ndi(value);
    };

    window.startNdiEmployeeLogin = function(value) {
        if (!requireLoginTypeSelection()) {
            return;
        }
        if (window.selectedLoginType !== 'agency') {
            $('#ndi_login_error')
                .html('Please choose Agency Login to continue with this Bhutan NDI option.')
                .show()
                .delay(4000)
                .fadeOut('slow');
            return;
        }
        window.authenticate_ndi_empid(value);
    };

    window.forgotPassword = function() {
        $('#loginBox').hide();
        $('#ForgotBox').show();
    };

    window.back = function() {
        $('#loginBox').show();
        $('#ForgotBox').hide();
        $('#ndi_div').hide();
        $('#issuanceMessageDiv').hide();
    };

    function getProponentNdiPanel() {
        const $modalPanel = $('#registrationModalForm #ndi_div_proponent');
        if ($modalPanel.length && $('#registrationModalForm').hasClass('show')) {
            return $modalPanel;
        }
        // Standalone /proponent_registration/ page: panel is inside #registration_div (not .closest('form'))
        const $pagePanel = $('#registration_div').find('#ndi_div_proponent');
        if ($pagePanel.length) {
            return $pagePanel.first();
        }
        const $visible = $('#ndi_div_proponent:visible');
        if ($visible.length) {
            return $visible.first();
        }
        return $('#ndi_div_proponent').last();
    }
    window.getProponentNdiPanel = getProponentNdiPanel;

    window.backToRegistration = function() {
        getProponentNdiPanel().hide();
        $('#registration_div').show();
        $('.modal-footer').show();
    };

    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    function isCustomAppScheme(url) {
        return /^[a-z][a-z0-9+.-]*:/i.test(url) && !/^https?:/i.test(url);
    }

    // Force demo wallet scheme so mobile opens Bhutan NDI Demo app.
    function normalizeToDemoDeepLink(url) {
        if (!url) {
            return '';
        }
        const raw = String(url);
        const lower = raw.toLowerCase();
        if (lower.indexOf('bhutanndidemo://') === 0) {
            return raw;
        }
        if (lower.indexOf('bhutanndi://') === 0) {
            return 'bhutanndidemo://' + raw.slice('bhutanndi://'.length);
        }
        if (lower.indexOf('bhutandemo://') === 0) {
            return 'bhutanndidemo://' + raw.slice('bhutandemo://'.length);
        }
        return raw;
    }

    /** bhutanndi://data?url=https://stage-demo-shortening-url... */
    function parseNdiDeepLink(deepLinkURL) {
        if (!deepLinkURL) {
            return { appUrl: '', proofUrl: '' };
        }
        const match = deepLinkURL.match(/[?&]url=([^&]+)/i);
        let proofUrl = '';
        if (match && match[1]) {
            try {
                proofUrl = decodeURIComponent(match[1]);
            } catch (e) {
                proofUrl = match[1];
            }
        }
        return { appUrl: deepLinkURL, proofUrl: proofUrl };
    }

    function isDemoProofUrl(url) {
        return !!url && /stage-demo-shortening-url/i.test(url);
    }

    /** URLs from /proof_request/ — same shape as NDI API (data.deepLinkURL, data.proofRequestURL). */
    function extractProofRequestData(apiResponse) {
        const payload = apiResponse || {};
        const data = payload.data || {};
        return {
            proofRequestURL: data.proofRequestURL || data.proofRequestUrl || payload.proofRequestURL,
            deepLinkURL: data.deepLinkURL || data.deepLinkUrl || data.deeplinkURL || payload.deepLinkURL,
            proofRequestThreadId: data.proofRequestThreadId || payload.proofRequestThreadId,
            sessionId: payload.session_id,
            ndiEnvironment: payload.ndi_environment,
            mobileShowQrAlso: payload.ndi_mobile_show_qr_also,
        };
    }

    function applyNdiSessionFromProofResponse(proof) {
        const ndiSessionId = proof && (proof.sessionId || proof.session_id);
        if (ndiSessionId && typeof setNdiSession === 'function') {
            setNdiSession(ndiSessionId);
        }
        if (proof.ndiEnvironment) {
            window.NDI_CONFIG = window.NDI_CONFIG || {};
            window.NDI_CONFIG.environment = proof.ndiEnvironment;
        }
        if (typeof proof.mobileShowQrAlso === 'boolean') {
            window.NDI_CONFIG = window.NDI_CONFIG || {};
            window.NDI_CONFIG.mobileShowQrAlso = proof.mobileShowQrAlso;
        }
    }

    function renderQrCode($container, proofRequestURL, logoElementId) {
        const logoEl = document.getElementById(logoElementId || 'logo');
        $container.empty().qrcode({
            render: 'canvas',
            minVersion: 1,
            maxVersion: 40,
            ecLevel: 'L',
            left: 0,
            top: 0,
            size: 200,
            fill: '#000',
            background: '#fff',
            text: proofRequestURL,
            radius: 0,
            quiet: 0,
            mode: 4,
            mSize: 0.15,
            mPosX: 0.5,
            mPosY: 0.5,
            label: '',
            fontcolor: '#000',
            fontname: 'sans',
            image: logoEl,
        });
        $container.show();
    }

    /**
     * Mobile browsers open custom schemes reliably only from a real <a href="bhutanndi://...">,
     * not from button + JavaScript. HTTP pages may also block app schemes (use HTTPS/ngrok).
     */
    function bindDeepLinkButton($wrap, $btn, deepLinkURL, proofRequestURL) {
        $wrap.find('.ndi-open-fallback, .ndi-http-warning').remove();

        if (!deepLinkURL) {
            $wrap.hide();
            return;
        }

        const parsed = parseNdiDeepLink(deepLinkURL);
        const proofUrl = proofRequestURL || parsed.proofUrl;
        const deepLinkHref = normalizeToDemoDeepLink(deepLinkURL);
        $wrap.show();

        // Hard reset wrapper so mobile shows exactly one Open Wallet control.
        const btnHtml = '<span>Open Bhutan NDI wallet</span>';
        const btnClass = $btn.length ? ($btn.attr('class') || '') : '';
        $wrap.find('a.ndi-app-open-link, button').remove();

        const $link = $('<a>', {
            class: 'ndi-app-open-link ' + btnClass,
            role: 'button',
        });
        $link.css({
            display: 'inline-block',
            textDecoration: 'none',
            color: '#fff',
        });
        $wrap.prepend($link);

        $link.attr('href', deepLinkHref);
        $link.html(btnHtml);
        $link.off('click.ndiWaiting').on('click.ndiWaiting', function() {
            window.showNdiWaitingLoader();
        });

        // Intentionally no HTTPS/ngrok helper line in UI copy.

        // Keep popup copy strictly aligned to Bhutan NDI UI copy.
    }

    function shouldShowQrAlso() {
        const cfg = window.NDI_CONFIG || {};
        return cfg.mobileShowQrAlso !== false;
    }

    function updateLoginNdiDisplay(proofRequestURL, deepLinkURL) {
        $('#ndi_div').show();
        if (isMobileDevice()) {
            $('#ndi_div .ndi-flow-title').html('Login with <span style="color:#5AC994">Bhutan NDI</span> Wallet');
        } else {
            $('#ndi_div .ndi-flow-title').html('Scan with <span style="color:#5AC994">Bhutan NDI</span> wallet');
        }
        if (isMobileDevice()) {
            bindDeepLinkButton($('#deepLink'), $('#deepLinkBtn'), deepLinkURL, proofRequestURL);
            if (shouldShowQrAlso() && proofRequestURL) {
                renderQrCode($('#qrcode'), proofRequestURL, 'logo');
            } else {
                $('#qrcode').hide();
            }
        } else {
            $('#deepLink').hide();
            $('#ndiOrDivider').hide();
            renderQrCode($('#qrcode'), proofRequestURL, 'logo');
        }
        if (isMobileDevice() && $('#deepLink').is(':visible') && $('#qrcode').is(':visible')) {
            $('#ndiOrDivider').show();
        } else {
            $('#ndiOrDivider').hide();
        }
    }

    function updateProponentNdiDisplay($panel, proofRequestURL, deepLinkURL) {
        // Registration flow title must stay "Scan with Bhutan NDI wallet" on all devices.
        $panel.find('.ndi-flow-title').html('Scan with <span style="color:#5AC994">Bhutan NDI</span> wallet');
        const $deepLink = $panel.find('#deepLinkPro');
        const $deepLinkBtn = $panel.find('#deepLinkBtnPro');
        const $qr = $panel.find('#qrcodeproponent');

        if (isMobileDevice()) {
            bindDeepLinkButton($deepLink, $deepLinkBtn, deepLinkURL, proofRequestURL);
        } else {
            $deepLink.hide();
            $('#ndiOrDividerPro').hide();
        }
        if (shouldShowQrAlso() && proofRequestURL) {
            renderQrCode($qr, proofRequestURL, 'logoPro');
        } else if ($qr.length) {
            $qr.hide();
        }
        if (isMobileDevice() && $deepLink.is(':visible') && $qr.is(':visible')) {
            $('#ndiOrDividerPro').show();
        } else {
            $('#ndiOrDividerPro').hide();
        }
    }

    window.authenticate_ndi = function(value) {
        if (value === 'Issuance') {
            $('#loginModalForm').modal('show');
            $('#progressLoader').show();
            $('#loginBox').hide();
            $('#cls_but').show();
            setTimeout(function() { $('#progressLoader').hide(); }, 5000);
        } else {
            $('#back_but').show();
        }

        $('#progressIndicator').show();
        showNdiLoader('Generating QR code', 'Please wait');
        $.ajax({
            type: 'GET',
            url: `/proof_request/?category=${value}`,
            success: function(data) {
                const proof = extractProofRequestData(data);
                applyNdiSessionFromProofResponse(proof);
                $('.modal-footer').hide();
                updateDisplay(
                    proof.proofRequestURL,
                    proof.deepLinkURL,
                    proof.proofRequestThreadId,
                    value
                );
                $('#progressIndicator').hide();
                hideNdiLoader();
            },
            error: function() {
                $('#progressIndicator').hide();
                hideNdiLoader();
                $('#ndi_login_error').html('Failed to connect. Please try again.').show().delay(4000).fadeOut('slow');
            }
        });
    };

    window.updateDisplay = function(proofRequestURL, deepLinkURL, proofRequestThreadId, value) {
        $('#loginBox').hide();
        updateLoginNdiDisplay(proofRequestURL, deepLinkURL);
        if (typeof nats_call === 'function') {
            nats_call(proofRequestThreadId, value);
        }
    };

    window.authenticate_ndi_empid = function(value) {
        $('#progressIndicator').show();
        showNdiLoader('Generating QR code', 'Please wait');
        $.ajax({
            type: 'GET',
            url: `/proof_request_employee/?category=${value}`,
            success: function(data) {
                const proof = extractProofRequestData(data);
                applyNdiSessionFromProofResponse(proof);
                $('.modal-footer').hide();
                updateDisplayEmp(
                    proof.proofRequestURL,
                    proof.deepLinkURL,
                    proof.proofRequestThreadId,
                    value
                );
                $('#progressIndicator').hide();
                hideNdiLoader();
            },
            error: function() {
                $('#progressIndicator').hide();
                hideNdiLoader();
                $('#ndi_login_error').html('Failed to connect. Please try again.').show().delay(4000).fadeOut('slow');
            }
        });
    };

    window.updateDisplayEmp = function(proofRequestURL, deepLinkURL, proofRequestThreadId, value) {
        $('#loginBox').hide();
        updateLoginNdiDisplay(proofRequestURL, deepLinkURL);
        if (typeof nats_call === 'function') {
            nats_call(proofRequestThreadId, value);
        }
    };

    window.registerauthenticateWithAPI = function(value) {
        $('#progressIndicator1').show();
        showNdiLoader('Generating QR code', 'Please wait');
        $.ajax({
            type: 'GET',
            url: `/proof_request_proponent/?category=${value}`,
            success: function(data) {
                try {
                    const proof = extractProofRequestData(data);
                    applyNdiSessionFromProofResponse(proof);
                    updateDisplayProponent(
                        proof.proofRequestURL,
                        proof.deepLinkURL,
                        proof.proofRequestThreadId,
                        value
                    );
                } catch (err) {
                    console.error('NDI registration display failed:', err);
                    $('#proponent_ErrorMsg')
                        .html('Failed to show NDI screen. Check browser console.')
                        .show()
                        .delay(6000)
                        .fadeOut('slow');
                }
                $('#progressIndicator1').hide();
                hideNdiLoader();
            },
            error: function(xhr) {
                console.error('proof_request_proponent failed', xhr.status, xhr.responseText);
                $('#progressIndicator1').hide();
                hideNdiLoader();
                $('#proponent_ErrorMsg').html('Failed to connect. Please try again.').show().delay(4000).fadeOut('slow');
            }
        });
    };

    window.updateDisplayProponent = function(proofRequestURL, deepLinkURL, proofRequestThreadId, value) {
        const $ndiPanel = getProponentNdiPanel();
        const inModal = $ndiPanel.closest('#registrationModalForm').length > 0;

        if (inModal) {
            const $registrationModal = $('#registrationModalForm');
            if ($registrationModal.length && !$registrationModal.hasClass('show')) {
                if (typeof $registrationModal.modal === 'function') {
                    $registrationModal.modal('show');
                } else if (window.bootstrap && bootstrap.Modal) {
                    bootstrap.Modal.getOrCreateInstance($registrationModal[0]).show();
                }
            }
            $('#registrationModalForm .modal-footer').hide();
        }

        $('#registration_div').hide();
        $ndiPanel.show();
        updateProponentNdiDisplay($ndiPanel, proofRequestURL, deepLinkURL);
        if (typeof nats_proponent_call === 'function') {
            nats_proponent_call(proofRequestThreadId, value);
        }
    };

    window.showRegistrationForm = function() {
        if ($('#registrationModalForm').length && !$('#registrationModalForm').hasClass('show')) {
            $('#registrationModalForm').modal('show');
        }
        getProponentNdiPanel().hide();
        $('#registration_div').show();
        $('.modal-footer').show();
    };

    window.fillInputFields = function(id_number, full_name, dzongkhag, gewog, village) {
        document.getElementById('cid').value = id_number;
        document.getElementById('proponent_name').value = full_name;
        document.getElementById('i_dzongkhag').value = dzongkhag;
        document.getElementById('i_gewog').value = gewog;
        document.getElementById('i_village').value = village;
    };

    $(document).ready(function() {
        // Keep Proponent as the default selected login type.
        if (typeof window.showLoginForm === 'function') {
            window.showLoginForm('proponent');
        }
        connectWebSocket();
        // Do not auto-resume NDI modals after page refresh.
        if (typeof clearNdiSession === 'function') {
            clearNdiSession();
        } else {
            sessionStorage.removeItem('ndi_session_id');
            sessionStorage.removeItem('ndi_category');
            sessionStorage.removeItem('ndi_thread_id');
        }
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState !== 'visible') {
                return;
            }
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            }
            if (isNdiAwaitingProof() && ndiPanelIsVisible()) {
                window.showNdiWaitingLoader();
            }
        });
        $('.modal').on('hidden.bs.modal', function() {
            sessionStorage.removeItem('modalShown');
            if (typeof stopProofPolling === 'function') {
                stopProofPolling();
            }
            if (typeof clearNdiSession === 'function') {
                clearNdiSession();
            }
            hideNdiLoader();
            $('#registration_div').show();
            $('#ndi_div_proponent').hide();
            $('#ndi_div').hide();
            $('#loginBox').show();
            $('#ForgotBox').hide();
        });
    });
})();
