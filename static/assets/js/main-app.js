// assets/js/main-app.js
(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        wsUrl: `wss://${window.location.host}/ws/socketserver/`,
        ndiAuthUrl: '/api/ndi/authenticate/',
        csrfCookieName: 'csrftoken'
    };

    // State Management
    const AppState = {
        sessionId: null,
        socket: null,
        currentQRData: null
    };

    // DOM Elements Cache
    const DOM = {
        ndiDiv: () => document.getElementById('ndi_div'),
        ndiDivProponent: () => document.getElementById('ndi_div_proponent'),
        loginBox: () => document.getElementById('loginBox'),
        registrationDiv: () => document.getElementById('registration_div'),
        qrcode: () => document.getElementById('qrcode'),
        qrcodeProp: () => document.getElementById('qrcodeproponent')
    };

    // Utility Functions
    const Utils = {
        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        isMobile() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        },

        showLoading(show, elementId = 'progressLoader') {
            const loader = document.getElementById(elementId);
            if (loader) loader.style.display = show ? 'flex' : 'none';
        },

        showAlert(type, message, containerId) {
            const alertDiv = document.getElementById(containerId);
            if (alertDiv) {
                alertDiv.textContent = message;
                alertDiv.style.display = 'block';
                setTimeout(() => alertDiv.style.display = 'none', 4000);
            }
        }
    };

    // WebSocket Management
    class WebSocketManager {
        constructor(url, onMessage) {
            this.url = url;
            this.onMessage = onMessage;
            this.socket = null;
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = 5;
            this.connect();
        }

        connect() {
            try {
                this.socket = new WebSocket(this.url);
                this.socket.onmessage = this.onMessage.bind(this);
                this.socket.onclose = () => this.handleDisconnect();
                this.socket.onerror = (error) => console.error('WebSocket error:', error);
                this.reconnectAttempts = 0;
            } catch (error) {
                console.error('WebSocket connection failed:', error);
            }
        }

        handleDisconnect() {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => this.connect(), 3000 * this.reconnectAttempts);
            }
        }
    }

    // NDI Authentication Handler
    class NDIHandler {
        static handleMessage(data) {
            const { eid, id_number, category, full_name, proof_type, relationshipDid, thid, holder_did, dzongkhag, gewog, village } = data;

            if (proof_type === 'present-proof/rejected') {
                this.handleRejection(category);
                return;
            }

            switch(category) {
                case 'Employee':
                    if (eid && id_number === '1111') window.makeNdiDashCallEID(eid);
                    break;
                case 'Login':
                    if (id_number) window.makeNdiDashCall(id_number);
                    break;
                case 'Issuance':
                    if (id_number) window.makeIssuanceCall(relationshipDid, thid, id_number, holder_did);
                    break;
                case 'Registration':
                    if (full_name) this.fillRegistrationForm(id_number, full_name, dzongkhag, gewog, village);
                    break;
            }
        }

        static handleRejection(category) {
            const errorMessages = {
                'Login': 'ndi_login_error',
                'Employee': 'ndi_login_error',
                'Issuance': 'issuanceMessageError',
                'Registration': 'proponent_ErrorMsg'
            };
            const containerId = errorMessages[category];
            if (containerId) Utils.showAlert('danger', 'Proof Not Shared From Wallet', containerId);
        }

        static fillRegistrationForm(id_number, full_name, dzongkhag, gewog, village) {
            const isMobile = Utils.isMobile();

            if (isMobile) {
                const modal = new bootstrap.Modal(document.getElementById('registrationModalForm'));
                if (!document.getElementById('registrationModalForm').classList.contains('show')) modal.show();

                document.getElementById('proponent_type').value = "4";
                document.querySelector('.cid_details').style.display = 'block';
                document.getElementById('cid').value = id_number;
                document.getElementById('proponent_name').value = full_name;

                ['dzongkhag', 'gewog', 'village'].forEach(id => document.getElementById(id).style.display = 'none');
                ['i_dzongkhag', 'i_gewog', 'i_village'].forEach(id => {
                    const element = document.getElementById(id);
                    element.style.display = 'block';
                    if (id === 'i_dzongkhag') element.value = dzongkhag;
                    if (id === 'i_gewog') element.value = gewog;
                    if (id === 'i_village') element.value = village;
                });
            } else {
                document.getElementById('ndi_div_proponent').style.display = 'none';
                document.getElementById('registration_div').style.display = 'block';
                document.getElementById('cid').value = id_number;
                document.getElementById('proponent_name').value = full_name;
                ['i_dzongkhag', 'i_gewog', 'i_village'].forEach(id => {
                    const element = document.getElementById(id);
                    element.style.display = 'block';
                    if (id === 'i_dzongkhag') element.value = dzongkhag;
                    if (id === 'i_gewog') element.value = gewog;
                    if (id === 'i_village') element.value = village;
                });
            }
            document.querySelector('.modal-footer').style.display = 'block';
        }
    }

    // UI Components
    class ModalManager {
        static init() {
            // Login modal triggers
            document.querySelectorAll('[data-bs-toggle="modal"]').forEach(trigger => {
                trigger.addEventListener('click', (e) => {
                    const target = e.currentTarget.getAttribute('data-bs-target');
                    if (target === '#loginModalForm') this.resetLoginModal();
                });
            });
        }

        static resetLoginModal() {
            document.getElementById('loginBox').style.display = 'block';
            document.getElementById('ForgotBox').style.display = 'none';
            document.getElementById('ndi_div').style.display = 'none';
            document.getElementById('proponentLoginForm').style.display = 'block';
            document.getElementById('agencyLoginForm').style.display = 'none';
        }

        static showLoginForm(type) {
            document.getElementById('proponentLoginForm').style.display = type === 'proponent' ? 'block' : 'none';
            document.getElementById('agencyLoginForm').style.display = type === 'agency' ? 'block' : 'none';

            const proponentBtn = document.getElementById('btnProponent');
            const agencyBtn = document.getElementById('btnAgency');

            if (type === 'proponent') {
                proponentBtn.classList.add('active-login-btn');
                agencyBtn.classList.remove('active-login-btn');
            } else {
                agencyBtn.classList.add('active-login-btn');
                proponentBtn.classList.remove('active-login-btn');
            }
        }

        static forgotPassword() {
            document.getElementById('loginBox').style.display = 'none';
            document.getElementById('ForgotBox').style.display = 'block';
        }

        static back() {
            document.getElementById('loginBox').style.display = 'block';
            document.getElementById('ForgotBox').style.display = 'none';
            document.getElementById('ndi_div').style.display = 'none';
        }
    }

    // Attachment Accordions
    class AttachmentManager {
        static init() {
            document.querySelectorAll('.load-more-btn, .form-load-more-btn, .down-load-more-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetId = btn.getAttribute('data-target');
                    const targetCard = document.getElementById(targetId);
                    const hiddenContent = targetCard.querySelector('.more-attachments, .form-more-attachments, .down-more-attachments');

                    if (hiddenContent) {
                        const isVisible = hiddenContent.style.display === 'block';
                        hiddenContent.style.display = isVisible ? 'none' : 'block';
                        const icon = btn.querySelector('i');
                        if (icon) icon.classList.toggle('mdi-chevron-down', isVisible);
                        if (icon) icon.classList.toggle('mdi-chevron-up', !isVisible);
                    }
                });
            });
        }
    }

    // Registration Handler
    class RegistrationHandler {
        static registerClient() {
            // Validation logic here
            const requiredFields = ['proponent_type', 'cid', 'proponent_name', 'proponent_address', 'contact_person', 'email', 'contact_number'];
            let isValid = true;

            requiredFields.forEach(field => {
                const value = document.getElementById(field)?.value;
                if (!value) {
                    Utils.showAlert('danger', `${field.replace('_', ' ')} is required`, `${field}ErrorMsg`);
                    isValid = false;
                }
            });

            if (isValid) {
                document.getElementById('client_registration_form').submit();
            }
        }

        static checkCID(cid) {
            if (cid.length === 11) {
                fetch(`/api/check-cid/${cid}/`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            Utils.showAlert('danger', 'CID already registered', 'cidErrorMsg');
                        }
                    });
            }
        }
    }

    // Initialize Application
    function init() {
        // Setup WebSocket
        const wsManager = new WebSocketManager(CONFIG.wsUrl, (e) => {
            const data = JSON.parse(e.data);
            console.log('WebSocket message:', data);
            NDIHandler.handleMessage(data);
        });

        // Initialize UI Components
        ModalManager.init();
        AttachmentManager.init();

        // Make functions globally available (for inline onclick handlers)
        window.showLoginForm = ModalManager.showLoginForm.bind(ModalManager);
        window.forgotPassword = ModalManager.forgotPassword.bind(ModalManager);
        window.back = ModalManager.back.bind(ModalManager);
        window.register_client = RegistrationHandler.registerClient.bind(RegistrationHandler);
        window.check_cid = RegistrationHandler.checkCID.bind(RegistrationHandler);
        window.authenticate_ndi = (type) => {
            Utils.showLoading(true);
            // Your NDI authentication logic
        };

        // Add more global function assignments as needed
    }

    // Start app when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();