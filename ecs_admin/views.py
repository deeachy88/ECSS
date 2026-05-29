import asyncio
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.utils import timezone
import requests,json
from django.db.models import Count, Subquery, OuterRef, Exists

from ecs_admin.models import t_competant_authority_master, t_user_master, t_security_question_master, t_role_master, t_service_master, \
    t_fees_schedule, t_bsic_code, t_forgot_password, \
    t_file_attachment, t_menu_master, t_agency_master, t_proponent_type_master, t_dzongkhag_master, t_village_master,\
    t_gewog_master,t_submenu_master, t_other_details, t_about_us, t_notification_details, t_homepage_master
from ecs_admin.forms import UserForm, RoleForm
from proponent.models import t_ec_application_t1, t_payment_details, t_ec_t1, t_ec_t2
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
import string
import random
import logging
import threading
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, render
from datetime import date
from ecs_main.models import t_application_history
from datetime import datetime, timedelta
from django.db import transaction
from django.core.mail import send_mail
from django.views.decorators.cache import cache_control
from proponent.models import t_workflow_dtls
from django.db.models import Case, When, Value, CharField, Count

#from proponent.views import oc_application
from django.conf import settings
logger = logging.getLogger(__name__)

# Create your views here.
def home(request):
    proponent_type = t_proponent_type_master.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    security = t_security_question_master.objects.all()
    menu_details = t_menu_master.objects.filter(is_active='Y',is_deleted='N').order_by('order')
    submenu_details = t_submenu_master.objects.filter(is_active='Y',is_deleted='N').order_by('order')
    other_details = t_other_details.objects.filter(is_active='Y',is_deleted='N')
    homepage_details = t_homepage_master.objects.filter(homepage_id='1')
    pub_file_attachment = t_file_attachment.objects.filter(attachment_type='P',document_id__in=t_other_details.objects.filter(
        is_active='Y',
        is_deleted='N'
    ).values('document_id'))
    down_file_attachment = t_file_attachment.objects.filter(attachment_type='D',document_id__in=t_other_details.objects.filter(
        is_active='Y',
        is_deleted='N'
    ).values('document_id'))
    form_file_attachment = t_file_attachment.objects.filter(attachment_type='C',document_id__in=t_other_details.objects.filter(
        is_active='Y',
        is_deleted='N'
    ).values('document_id'))
    home_attachment = t_file_attachment.objects.filter(attachment_type='H')
    
    # Get login error message from session if it exists (no default message)
    login_error_message = request.session.pop('login_error_message', None)
    
    context = {
        'proponent_type': proponent_type,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'security': security,
        'menu_details': menu_details,
        'submenu_details': submenu_details,
        'other_details': other_details,
        'pub_file_attachment': pub_file_attachment,
        'homepage_details': homepage_details,
        'home_attachment': home_attachment,
        'download_forms': down_file_attachment,
        'form_file_attachment': form_file_attachment,
        'message': login_error_message  # This will be None if no error
    }
    
    response = render(request, 'index.html', context)
    
    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def proponent_registration(request):
    proponent_type = t_proponent_type_master.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'proponent_registration.html',{'proponent_type':proponent_type,'dzongkhag':dzongkhag,
                                         'gewog':gewog,'village':village})

def user_login(request):
    return render(request, 'login.html')

def contact_us(request):
    menu_details = t_menu_master.objects.all()
    return render(request,'contact_us.html',{'menu_details':menu_details})

def get_content_details(request):
    menu_id = request.GET.get('menu_id')
    identifier = request.GET.get('identifier')
    file_attachment = t_file_attachment.objects.all()
    if identifier == 'M':
        menu_details = t_menu_master.objects.filter(menu_id=menu_id)
    else:
        menu_details = t_submenu_master.objects.filter(sub_menu_id=menu_id)
    return render(request,'content_details.html',{'menu_details':menu_details,'identifier':identifier,
                                                  'file_attachment':file_attachment})

def login(request):
    if request.method == 'POST':
        _username = request.POST['username']
        _password = request.POST['password']
        _loginType = request.POST['loginType']
        if _loginType == 'proponent':
            check_user = t_user_master.objects.filter(email_id=_username, is_active='Y', logical_delete='N',employee_id__isnull=True)
        else:
            check_user = t_user_master.objects.filter(email_id=_username, is_active='Y', logical_delete='N',employee_id__isnull=False)
        
        if check_user.exists():
            user_found = False
            for check_user in check_user:
                check_pass = check_password(_password, check_user.password)
                if check_pass:
                    user_found = True
                    if not check_user.last_login_date:
                        request.session['login_id'] = check_user.login_id
                        request.session['email'] = check_user.email_id
                        
                        security = t_security_question_master.objects.all()
                        response = render(request, 'update_password.html', {'security': security})

                        # Set cache-control headers to prevent caching
                        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                        response['Pragma'] = 'no-cache'
                        response['Expires'] = '0'
                        return response
                    else:
                        if check_user.login_type == 'I':
                            role_details = t_role_master.objects.filter(role_id=check_user.role_id_id)
                            for roles in role_details:
                                request.session['name'] = check_user.name
                                request.session['both_role_id'] = roles.role_id

                                # ============ ASSIGN ROLE_ID WITH CONDITION ============
                                if request.session['both_role_id'] == 5:
                                    request.session['role_id'] = 2  # Assign Verifier role
                                    request.session['role'] = 'Verifier'
                                else:
                                    request.session['role_id'] = roles.role_id
                                    request.session['role'] = roles.role_name

                                request.session['email'] = check_user.email_id
                                request.session['login_type'] = check_user.login_type
                                request.session['login_id'] = check_user.login_id
                                request.session['ca_authority'] = check_user.agency_code
                                request.session['dzongkhag_code'] = check_user.dzongkhag_code

                                return redirect(dashboard)
                        else:
                            request.session['name'] = check_user.proponent_name
                            request.session['email'] = check_user.email_id
                            request.session['login_type'] = check_user.login_type
                            request.session['login_id'] = check_user.login_id
                            request.session['address'] = check_user.address
                            request.session['contact_number'] = check_user.contact_number
                            request.session['proponent_type'] = check_user.proponent_type
                            if check_user.proponent_type == 4:
                                request.session['cid'] = check_user.cid
                            else:
                                request.session['cid'] = None
                            return redirect(dashboard)
            
            if not user_found:
                # Store only actual error messages
                request.session['login_error_message'] = 'User ID or Password Not Matching.'
                return redirect(home)
        else:
            # Store only actual error messages
            request.session['login_error_message'] = 'Invalid Credentials, Please Try Again.'
            return redirect(home)
    
    # For GET requests, redirect to home without any error message
    return redirect(home)

def dashboard(request):
    """Dashboard view displaying user-specific counts and applications"""

    # ============ AUTHENTICATION CHECK ============
    if 'email' not in request.session:
        return redirect('home')  # Replace with your actual home URL name

    # ============ INITIALIZE ALL COUNTERS ============
    v_application_count = 0
    v_old_ec_count = 0
    r_application_count = 0
    p_application_count = 0
    ec_renewal_count = 0
    payment_count = 0
    cl_application_count = 0
    client_application_count = 0
    ibls_application_count = 0
    p_a_application_count = 0
    reviewer_application_count = {}
    reviewer_applications = {}
    applications_by_reviewer = {}
    reviewer_counts = {}
    reviewer_names = {}
    applications_list = {}

    try:
        login_type = request.session['login_type']
    except KeyError:
        login_type = None

    # ============ INTERNAL USER (Verifier/Reviewer) ============
    if login_type == 'I':
        role = request.session.get('role')
        ca_authority = request.session.get('ca_authority')
        login_id = request.session.get('login_id')

        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        # Check for pending renewals
        pending_renewal_exists = t_ec_application_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(application_status='A')
        non_updated_renewals = (
            t_ec_t1.objects
            .filter(
                # applicant_id=request.session['email'],
                service_type__in=["Main Activity", "Old EC"],
                ec_expiry_date__lt=expiry_date_threshold,
                ec_expiry_date__isnull=False,
                ec_reference_no__isnull=False,
                status='A',

            )
            .exclude(ec_reference_no='')
            .annotate(has_pending_renewal=Exists(pending_renewal_exists))
            .filter(has_pending_renewal=False)
        )
        ec_renewal_count = non_updated_renewals.count()

        # ============ VERIFIER ROLE ============
        if role == 'Verifier':
            v_application_count = t_workflow_dtls.objects.filter(
                assigned_role_id='2',
                assigned_role_name='Verifier',
                application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
                ca_authority=ca_authority,
                action_date__isnull=False
            ).count()

            v_old_ec_count = t_ec_application_t1.objects.filter(
                ca_authority=ca_authority,
                application_status = 'SM',
                application_type = 'Old_EC'
            ).count()

            expiry_date_threshold = datetime.now().date() + timedelta(days=60)
            ec_renewal_count = t_ec_t1.objects.filter(
                ca_authority=ca_authority,
                status='A',
                ec_expiry_date__lt=expiry_date_threshold
            ).count()

            # Get applications grouped by reviewer with names from t_user_master
            applications_by_reviewer_qs = (
                t_ec_application_t1.objects
                .filter(ca_authority=ca_authority)
                .values(
                    'record_id',
                    'project_name',
                    'applicant_name',
                    'application_status',
                    'application_date',
                    'application_no',
                    'location_name',
                    'service_id',
                    'assigned_to',
                    'application_source'
                )
                .order_by('-assigned_to', 'application_date')
            )
            # Convert QuerySet to list
            applications_list = list(applications_by_reviewer_qs)
            # Extract unique reviewer IDs (skip None/NULL values)
            unique_reviewer_ids = set(
                app['assigned_to'] for app in applications_list
                if app['assigned_to']
            )
            #print(f"DEBUG 1 - Unique reviewer IDs: {unique_reviewer_ids}")
            # Fetch reviewer names from t_user_master in ONE query
            reviewer_name_map = {}
            if unique_reviewer_ids:
                reviewers_from_db = t_user_master.objects.filter(
                    login_id__in=unique_reviewer_ids
                ).values('login_id', 'name')

                #print(f"DEBUG 2 - Reviewers found: {list(reviewers_from_db)}")

                # Build mapping dictionary: login_id → name
                reviewer_name_map = {
                    reviewer['login_id']: reviewer['name']
                    for reviewer in reviewers_from_db
                }
            #print(f"DEBUG 3 - Reviewer name map: {reviewer_name_map}")
            # Initialize result dictionaries
            applications_by_reviewer = {}
            reviewer_counts = {}
            reviewer_names = {}
            # Group applications and map reviewer names
            for application in applications_list:
                reviewer_id = application['assigned_to']

                # Skip unassigned applications
                if not reviewer_id:
                    continue

                # Get reviewer name from mapping (default to 'Unknown Reviewer' if not found)
                reviewer_name = reviewer_name_map.get(reviewer_id, 'Unknown Reviewer')

                #print(f"DEBUG 4 - Reviewer ID: {reviewer_id}, Reviewer Name: {reviewer_name}")

                # Store reviewer name (only once per reviewer)
                if reviewer_id not in reviewer_names:
                    reviewer_names[reviewer_id] = reviewer_name

                # Count applications by reviewer
                if reviewer_id not in reviewer_counts:
                    reviewer_counts[reviewer_id] = 0
                reviewer_counts[reviewer_id] += 1

                # Group applications by reviewer
                if reviewer_id not in applications_by_reviewer:
                    applications_by_reviewer[reviewer_id] = []
                applications_by_reviewer[reviewer_id].append(application)

                #print(applications_by_reviewer)
            #print(f"DEBUG 5 - Final reviewer_names: {reviewer_names}")
            #print(f"DEBUG 6 - Final reviewer_counts: {reviewer_counts}")


        # ============ REVIEWER ROLE ============
        elif role == 'Reviewer':

            # Reviewer application count
            r_application_count = t_workflow_dtls.objects.filter(
                assigned_role_id='3',
                assigned_user_id=login_id,
                assigned_role_name='Reviewer',
                ca_authority=ca_authority
            ).count()

            # Reviewer application count for Payment update
            p_application_count = t_workflow_dtls.objects.filter(
                assigned_role_id='3',
                assigned_role_name='Reviewer',
                ca_authority=ca_authority,
                assigned_user_id__isnull=True,  # assigned_user_id is null
                action_date__isnull=False  # action_date is not null
            ).exclude(
                ca_authority=1  # Exclude ca_authority = 1
            ).count()

            # print(p_application_count)
            # Get reviewer applications grouped by status
            reviewer_applications_qs = (
                t_ec_application_t1.objects
                .filter(assigned_to=login_id)
                .values(
                    'record_id',
                    'project_name',
                    'applicant_name',
                    'application_status',
                    'application_date',
                    'application_no',
                    'location_name',
                    'service_id',
                    'application_source'
                )
                .order_by('-application_date')
            )

            # Create count dictionary and group applications by status
            reviewer_application_count = {}
            reviewer_applications = {}

            for application in reviewer_applications_qs:
                # Determine status group
                if application['application_status'] == 'A':
                    status_group = 'Approved'
                #elif application['application_status'] == 'P':
                #    status_group = 'Pending'
                else:
                    #status_group = application.get('application_status', 'Other')
                    status_group = 'Pending'

                # Count applications by status
                if status_group not in reviewer_application_count:
                    reviewer_application_count[status_group] = 0
                reviewer_application_count[status_group] += 1

                # Group applications by status
                if status_group not in reviewer_applications:
                    reviewer_applications[status_group] = []
                reviewer_applications[status_group].append(application)


        elif role in ['Admin', 'NECS Head']:
            client_application_count = t_user_master.objects.filter(
                accept_reject__isnull=True,
                login_type='C'
            ).count()
            p_a_application_count = t_workflow_dtls.objects.filter(
                assigned_role_id='3',
                ca_authority=1,
                assigned_user_id__isnull=True,  # assigned_user_id is null
                action_date__isnull=False,  # action_date is not null
                application_status= 'P'
            ).count()
            ibls_application_count = t_workflow_dtls.objects.filter(application_status='P',
                                                                    assigned_role_id=request.session['role_id'],
                                                                    action_date__isnull=False).count()
            # Get applications grouped by reviewer with names from t_user_master
            applications_by_reviewer_qs = (
                t_ec_application_t1.objects
                .filter(ca_authority='1')
                .values(
                    'record_id',
                    'project_name',
                    'applicant_name',
                    'application_status',
                    'application_date',
                    'application_no',
                    'location_name',
                    'service_id',
                    'assigned_to',
                    'application_source'
                )
                .order_by('-assigned_to', 'application_date')
            )
            # Convert QuerySet to list
            applications_list = list(applications_by_reviewer_qs)
            # Extract unique reviewer IDs (skip None/NULL values)
            unique_reviewer_ids = set(
                app['assigned_to'] for app in applications_list
                if app['assigned_to']
            )
            # Fetch reviewer names from t_user_master in ONE query
            reviewer_name_map = {}
            if unique_reviewer_ids:
                reviewers_from_db = t_user_master.objects.filter(
                    login_id__in=unique_reviewer_ids
                ).values('login_id', 'name')

                # Build mapping dictionary: login_id → name
                reviewer_name_map = {
                    reviewer['login_id']: reviewer['name']
                    for reviewer in reviewers_from_db
                }
            # Initialize result dictionaries
            applications_by_reviewer = {}
            reviewer_counts = {}
            reviewer_names = {}
            # Group applications and map reviewer names
            for application in applications_list:
                reviewer_id = application['assigned_to']

                # Skip unassigned applications
                if not reviewer_id:
                    continue

                # Get reviewer name from mapping (default to 'Unknown Reviewer' if not found)
                reviewer_name = reviewer_name_map.get(reviewer_id, 'Unknown Reviewer')

                # Store reviewer name (only once per reviewer)
                if reviewer_id not in reviewer_names:
                    reviewer_names[reviewer_id] = reviewer_name

                # Count applications by reviewer
                if reviewer_id not in reviewer_counts:
                    reviewer_counts[reviewer_id] = 0
                reviewer_counts[reviewer_id] += 1

                # Group applications by reviewer
                if reviewer_id not in applications_by_reviewer:
                    applications_by_reviewer[reviewer_id] = []
                applications_by_reviewer[reviewer_id].append(application)

        # ============ CONTEXT FOR INTERNAL USERS ============
        context = {
            'v_application_count': v_application_count,
            'v_old_ec_count':v_old_ec_count,
            'r_application_count': r_application_count,
            'p_application_count': p_application_count,
            'p_a_application_count': p_a_application_count,
            'ec_renewal_count': ec_renewal_count,
            'client_application_count': client_application_count,
            'ibls_application_count': ibls_application_count,
            'reviewer_application_count': reviewer_application_count,
            'reviewer_applications': reviewer_applications,
            'applications_by_reviewer': applications_by_reviewer,
            'reviewer_counts': reviewer_counts,
            'reviewer_names': reviewer_names,  # ← MAKE SURE THIS IS HERE
            'total_applications': len(applications_list),
            'total_reviewers': len(reviewer_names)
        }
        response = render(request, 'dashboard.html', context)
    # ============ EXTERNAL USER (Client) ============
    else:
        email_id = request.session['email']
        login_id = request.session['login_id']

        # Get application history count
        oc_application_count = t_ec_application_t1.objects.filter(
            applicant_id=email_id, application_type='OC', application_status='OC'
        ).distinct('application_no').count()

        # Get application history count
        app_hist_count = t_application_history.objects.filter(
            applicant_id=email_id
        ).distinct('application_no').count()

        # Get assigned applications count
        cl_application_count = t_workflow_dtls.objects.filter(
            assigned_user_id=login_id
        ).count()

        # Get pending payments
        payment_count = t_payment_details.objects.filter(
            payment_advice_amount_paid__isnull=True
        ).count()

        # Get draft applications
        draft_count = t_ec_application_t1.objects.filter(
            applicant_id=email_id,
            application_status='P',
            service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
            action_date__isnull=True
        ).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        # Check for pending renewals
        pending_renewal_exists = t_ec_application_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(application_status='A')
        non_updated_renewals = (
            t_ec_t1.objects
            .filter(
                applicant_id=request.session['email'],
                service_type__in=["Main Activity", "Old EC"],
                ec_expiry_date__lt=expiry_date_threshold,
                ec_expiry_date__isnull=False,
                ec_reference_no__isnull=False,
                status='A',

            )
            .exclude(ec_reference_no='')
            .annotate(has_pending_renewal=Exists(pending_renewal_exists))
            .filter(has_pending_renewal=False)
        )
        ec_renewal_count = non_updated_renewals.count()
        # Get old EC draft count
        old_ec_draft_count = t_ec_application_t1.objects.filter(
            applicant_id=request.session['email'],
            application_type='Old_EC',
            application_status__in=['P', 'RS']
        ).count()
        # Get TOR applications count
        t1_general_subquery = t_ec_application_t1.objects.filter(
            tor_application_no=OuterRef('application_no')
        ).values('tor_application_no')
        tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',
            applicant_id=email_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
        # Get download forms
        download_forms = t_file_attachment.objects.filter(
            attachment_type='F',
            document_id__in=t_other_details.objects.filter(
                is_active='Y',
                is_deleted='N'
            ).values('document_id')
        )
        # ============ CONTEXT FOR EXTERNAL USERS ============
        context = {
            'oc_application_count':oc_application_count,
            'app_hist_count': app_hist_count,
            'cl_application_count': cl_application_count,
            'payment_count': payment_count,
            'tor_application_count': tor_application_count,
            'draft_count': draft_count,
            'ec_renewal_count': ec_renewal_count,
            'ibls_application_count': ibls_application_count,
            'download_forms': download_forms,
            'old_ec_draft_count': old_ec_draft_count
        }
        response = render(request, 'dashboard.html', context)
    # ============ CACHE CONTROL HEADERS ============
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

def add_user(request):
    try:
        employee_id    = request.POST.get('employee_id')
        name           = request.POST.get('name')
        gender         = request.POST.get('gender')
        email          = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        role           = request.POST.get('role')
        agency         = request.POST.get('agency')

        # ── Duplicate Email Check ──────────────────────────────
        if t_user_master.objects.filter(email_id=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email is already in use.'})

        # ── Create User ────────────────────────────────────────
        password       = get_random_password_string(8)
        password_value = make_password(password)

        common_fields = dict(
            login_type      = "I",
            employee_id     = employee_id,
            name            = name,
            gender          = gender,
            contact_number  = contact_number,
            email_id        = email,
            password        = password_value,
            is_active       = "Y",
            logical_delete  = "N",
            last_login_date = date.today(),
            created_on      = date.today(),
            modified_by     = None,
            modified_on     = None,
            role_id_id      = role,
        )

        with transaction.atomic():
            if role == '1':
                t_user_master.objects.create(
                    **common_fields,
                    agency_code = None,
                    created_by  = None,
                )
            else:
                t_user_master.objects.create(
                    **common_fields,
                    agency_code = agency,
                    created_by  = request.session['login_id'],
                )

            # ── Send Email After Successful Commit ─────────────
            transaction.on_commit(lambda: threading.Thread(
                target=_send_add_user_mail_in_background,
                args=(name, email, password),
                daemon=True
            ).start())

        return JsonResponse({'status': 'success', 'message': 'User successfully added.'})

    except Exception as exc:
        logger.exception("add_user failed for email=%s", email)
        return JsonResponse({'status': 'error', 'message': str(exc).splitlines()[0]}, status=500)


def _send_add_user_mail_in_background(name, email, password):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_add_user_mail(name, email, password)
    except Exception:
        logger.exception("Failed to send add user email to=%s", email)


def send_add_user_mail(name, email, password):
    subject = "User Account Created - ECS System"
    message = (
        f"Dear {name},\n\n"
        f"Your account has been created for the ECS System.\n"
        f"Your login credentials are as follows:\n\n"
        f"  Login ID : {email}\n"
        f"  Password : {password}\n\n"
        f"Please log in and change your password after your first login.\n\n"
        f"Regards,\nECS System Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )


def update_user(request):
    login_id = request.POST.get('editLoginId')
    employee_id = request.POST.get('edit_employee_id')
    name = request.POST.get('edit_name')
    gender = request.POST.get('edit_gender')
    email = request.POST.get('edit_email')
    contact_number = request.POST.get('edit_contact_number')
    role = request.POST.get('edit_role')
    agency = request.POST.get('edit_agency')

    print(role)
    
    user_details = t_user_master.objects.filter(login_id=login_id)
    if role != '1':
        user_details.update(employee_id=employee_id, name=name, gender=gender,
                            contact_number=contact_number, email_id=email,
                            agency_code=agency, modified_by=request.session['login_id'],
                            modified_on=date.today(), role_id_id=role)
    else:
        user_details.update(employee_id=employee_id, name=name, gender=gender,
                            contact_number=contact_number, email_id=email,
                            modified_by=request.session['login_id'],
                            modified_on=date.today(), role_id_id=role)
    return redirect(user_master)

def get_random_password_string(length):
    password_characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(password_characters) for i in range(length))
    return password

def get_random_document_id_string(length):
    doc_id_characters = string.digits
    document_id = ''.join(random.choice(doc_id_characters) for i in range(length))
    return document_id

def load_gewog(request):
    dzongkhag_id = request.GET.get('dzongkhag_id')

    if not dzongkhag_id or dzongkhag_id.strip() == '':
        gewog_list = t_gewog_master.objects.none()
    else:
        try:
            gewog_list = t_gewog_master.objects.filter(
                dzongkhag_code_id=int(dzongkhag_id)
            ).order_by('gewog_name')
        except (ValueError, TypeError):
            gewog_list = t_gewog_master.objects.none()

    return render(request, 'gewog_list.html', {'gewog': gewog_list})

def load_village(request):
    gewog_id = request.GET.get('gewog_id')

    # Handle empty or invalid gewog_id
    if not gewog_id or gewog_id.strip() == '':
        village_list = t_village_master.objects.none()  # Return empty queryset
    else:
        try:
            village_list = t_village_master.objects.filter(
                gewog_code_id=int(gewog_id)
            ).order_by('village_name')
        except (ValueError, TypeError):
            # Handle non-numeric gewog_id
            village_list = t_village_master.objects.none()

    return render(request, 'village_list.html', {'village': village_list})

def check_email_id(request):
    email = request.POST.get('email', '').strip()

    if not email:
        return JsonResponse({'error': 'No email provided'}, status=400)

    try:
        file_count = t_user_master.objects.filter(email_id__iexact=email).count()
        return JsonResponse({'file_count': file_count})
    except Exception as e:
        return JsonResponse({'error': 'Database error'}, status=500)


def check_cid(request):
    data = dict()
    cid = request.POST.get('cid')
    message_count = t_user_master.objects.filter(cid=cid).count()
    data['count'] = message_count
    return JsonResponse(data)

def check_emp_id(request):
    data = dict()
    employee_id = request.POST.get('employee_id')
    message_count = t_user_master.objects.filter(employee_id=employee_id).count()
    data['count'] = message_count
    return JsonResponse(data)


def manage_menu(request):
    menu_details = t_menu_master.objects.all().order_by('order')
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'manage_menu.html',{'menu_details':menu_details,'document_id':document_id,
                                               'file_attachment':file_attachment,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def manage_submenu(request):
    menu_details = t_menu_master.objects.filter(has_sub_menu="Yes",is_active="Y").order_by('order')
    sub_menu_details = t_submenu_master.objects.all()
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'manage_sub_menu.html',{'menu_details':menu_details,'sub_menu_details':sub_menu_details,
                                                   'document_id':document_id, 'file_attachment':file_attachment,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def add_menu_master(request):
    menu_name = request.POST.get('menu_name')
    has_submenu = request.POST.get('has_submenu')
    has_image = request.POST.get('has_image')
    menu_content = request.POST.get('content')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    document_id = request.POST.get('document_id')
    if has_submenu == 'Yes' and has_image == 'No':
        t_menu_master.objects.create(menu_name=menu_name,menu_content=menu_content,has_sub_menu=has_submenu,is_active='Y')
    else:
        t_menu_master.objects.create(menu_name=menu_name, menu_content=menu_content, has_sub_menu=has_submenu,
                                     is_active='Y',document_id=document_id)
        t_file_attachment.objects.create(document_id=document_id, file_path=file_url,
                                         attachment=file_name)
    return redirect(manage_menu)

def add_submenu_master(request):
    menu_id = request.POST.get('menu_name')
    sub_menu_order = request.POST.get('sub_menu_order')
    sub_menu_name = request.POST.get('sub_menu_name')
    sub_menu_content = request.POST.get('content')
    document_id = request.POST.get('document_id')

    t_submenu_master.objects.create(menu_id=menu_id,order=sub_menu_order,sub_menu_name=sub_menu_name,sub_menu_content=sub_menu_content,
                                    document_id=document_id,is_active='Y', is_deleted='N')
    return redirect(manage_submenu)

def user_master(request):
    users = t_user_master.objects.filter(login_type='I')
    roles = t_role_master.objects.all().order_by('role_name')
    agency = t_competant_authority_master.objects.all().order_by('remarks')
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'user_master.html', {'users': users, 'role': roles, 'agency':agency,'client_application_count':client_application_count})
    
    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def agency_master(request):
    agency_list = t_competant_authority_master.objects.all().order_by('competent_authority_id')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'agency_master.html', {'agency_list': agency_list, 'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def proponent_master(request):
    proponent_list = t_proponent_type_master.objects.all()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'proponent_master.html', {'proponent_list':proponent_list,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def role_master(request):
    role_list = t_role_master.objects.all()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'role_master.html', {'role':role_list,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def service_master(request):
    service_list = t_service_master.objects.all().order_by('service_name')
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'service_master.html', {'service':service_list,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_service_details(request, service_id):
    service_details = t_service_master.objects.filter(service_id=service_id)
    service_list = t_service_master.objects.all()
    competant_authority = t_competant_authority_master.objects.values('competent_authority').order_by('competent_authority').distinct()
    return render(request, 'edit_service.html', {'competant_authority':competant_authority,'service_details': service_details, 'service_list':service_list})

def edit_service_master(request):
    service_id = request.POST.get('service_id')
    attachments = request.POST.get('attachments')

    t_service_master.objects.filter(service_id=service_id).update(
        attachments=attachments
    )

    return JsonResponse({"status": "success"})

def fee_schedule_master(request):
    fees_schedule_list = t_fees_schedule.objects.all().order_by('service_name')
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'fees_schedule.html', {'fees_schedule':fees_schedule_list,'client_application_count':client_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def edit_fee_schedule_master(request):
    edit_service_name = request.POST.get('service_name')
    edit_parameter = request.POST.get('parameter')
    edit_rate = request.POST.get('rate')
    edit_application_fee = request.POST.get('application_fee')
    edit_fees_id = request.POST.get('fees_id')
    fees_details = t_fees_schedule.objects.filter(fees_id=edit_fees_id)
    fees_details.update(rate=edit_rate, application_fee=edit_application_fee)
    return redirect(fee_schedule_master)

def delete_fee_schedule_master(request):
    fees_schedule_list = t_fees_schedule.objects.all()
    return render(request, 'fees_schedule.html', {'fees_schedule':fees_schedule_list})

def bsic_master(request):
    bsic_code_list = t_bsic_code.objects.exclude(status='Deleted').order_by('activity').distinct()
    service_list = t_service_master.objects.all()
    competant_authority = t_competant_authority_master.objects.values('competent_authority').order_by('competent_authority').distinct()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'bsic_code_master.html', {'client_application_count':client_application_count,'bsic_code_list':bsic_code_list, 'service_list':service_list, 'competant_authority':competant_authority})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def add_bsic_code_master(request):
    activity = request.GET.get('activity')
    colour_code = request.GET.get('colour_code')
    competent_authority = request.GET.get('competent_authority')
    entry_point = 'ECSS'
    service_id = request.GET.get('service_id')
    has_tor = request.GET.get('has_tor')
    mas_integration = request.GET.get('mas_integration')
    t_bsic_code.objects.create(activity=activity,
                               colour_code=colour_code,
                               competent_authority=competent_authority,
                               entry_point=entry_point,
                               service_id=service_id,
                               has_tor=has_tor,
                               mas_integration=mas_integration)
    return redirect(bsic_master)

def get_bsic_code_details(request, bsic_id):
    bsic_code_details = t_bsic_code.objects.filter(bsic_id=bsic_id)
    service_list = t_service_master.objects.all()
    competant_authority = t_competant_authority_master.objects.values('competent_authority').order_by('competent_authority').distinct()
    return render(request, 'edit_bsic_code.html', {'competant_authority':competant_authority,'bsic_code_details': bsic_code_details, 'service_list':service_list})

def edit_bsic_code_master(request):
    edit_bsic_id = request.POST.get('bsic_id')
    edit_activity = request.POST.get('activity')
    edit_colour_code = request.POST.get('colour_code')
    edit_competent_authority = request.POST.get('competent_authority')
    edit_service_id = request.POST.get('service_id')
    has_tor = request.POST.get('has_tor')
    mas_integration = request.POST.get('mas_integration')
    bsic_code_details = t_bsic_code.objects.filter(bsic_id=edit_bsic_id)
    bsic_code_details.update(activity=edit_activity,
                             colour_code=edit_colour_code,
                             competent_authority=edit_competent_authority,
                             service_id=edit_service_id,
                             has_tor=has_tor,
                             mas_integration=mas_integration)
    return redirect(bsic_master)

def delete_bsic_code_master(request):
    delete_bsic_id = request.POST.get('bsic_id')
    bsic_details = t_bsic_code.objects.filter(bsic_id=delete_bsic_id)
    bsic_details.update(status="Deleted")
    #bsic_details.delete()
    return redirect(bsic_master)

def add_agency_master(request):
    agency_name = request.POST.get('agency_name')
    remarks = request.POST.get('remarks')
    dzongkhag = request.POST.get('dzongkhag')
    t_competant_authority_master.objects.create(competent_authority=agency_name,remarks=remarks,dzongkhag_code=dzongkhag)
    return redirect(agency_master)

def edit_agency_master(request):
    agency_code = request.POST.get('edit_agency_code')
    agency_name = request.POST.get('edit_agency_name')
    remarks = request.POST.get('edit_remarks')
    dzongkhag = request.POST.get('edit_dzongkhag')
    competant_authority_master = t_competant_authority_master.objects.filter(agency_code=agency_code)
    competant_authority_master.update(competent_authority=agency_name,remarks=remarks,dzongkhag_code=dzongkhag)
    return redirect(agency_master)

def delete_agency_master(request):
    agency_code = request.POST.get('delete_agency_code')
    agency_details = t_competant_authority_master.objects.filter(agency_code=agency_code)
    agency_details.delete()
    return redirect(agency_master)

def add_proponent_master(request):
    proponent_name = request.POST.get('proponent_type_name')
    t_proponent_type_master.objects.create(proponent_type_name=proponent_name)
    return redirect(proponent_master)

def edit_proponent_master(request):
    proponent_id = request.POST.get('edit_proponent_type_id')
    proponent_name = request.POST.get('edit_proponent_type_name')
    agency_details = t_proponent_type_master.objects.filter(proponent_type_id=proponent_id)
    agency_details.update(proponent_type_name=proponent_name)
    return redirect(proponent_master)

def delete_proponent_master(request):
    proponent_id = request.POST.get('delete_proponent_type_id')
    proponent_details = t_proponent_type_master.objects.filter(proponent_type_id=proponent_id)
    proponent_details.delete()
    return redirect(proponent_master)

def manage_user(request):
    data = dict()
    login_id = request.GET.get('login_id')
    email_id = request.GET.get('Email_Id')
    name = request.GET.get('Name')
    identifier = request.GET.get('identifier')

    user_list = t_user_master.objects.filter(login_id=login_id)

    if identifier == "Activate":
        user_list.update(is_active="Y")
    elif identifier == "Deactivate":
        user_list.update(is_active="N")
    else:
        password = get_random_password_string(8)
        password_value = make_password(password)
        user_list.update(password=password_value)
        user_list.update(last_login_date=None)
        user_password_reset_mail(name, email_id, password)
    data['identifier'] = identifier
    return JsonResponse(data)


def user_password_reset_mail(Name, Email_Id, password):
    subject = 'PASSWORD RESET'
    message = "Dear " + Name + " Your Password Has Been Reset for ECS System. Your Login Id is " \
              + Email_Id + " And Password is " + password + ""
    recipient_list = [Email_Id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)

def logout_view(request):
    # Use flush() to completely clear the session
    request.session.flush()
    
    # Also logout the user if using Django's auth system
    response = redirect('/')
    
    # Add headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


def account_setting(request):
    email_id = request.session['email']
    application_details = t_user_master.objects.filter(email_id=email_id)
    return render(request, 'account_setting.html', {'application_details': application_details})

def add_submenu_details(request):
    menu_details = t_menu_master.objects.filter(has_sub_menu='Yes', is_active='Y', is_deleted='N')
    document_id = get_random_document_id_string(5)
    return render(request, 'add_submenu.html', {'menu_details': menu_details, 'document_id':document_id})

def add_menu_details(request):
    document_id = get_random_document_id_string(5)
    return render(request, 'add_menu.html', {'document_id':document_id})

def save_menu_attachment(request):
    data = dict()
    menu_attach = request.FILES['menu_attach']
    file_name = menu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/menu/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, menu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/menu" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_menu_attachment_details(request):
    document_id = request.POST.get('document_id')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')

    t_file_attachment.objects.create(document_id=document_id,file_path=file_url,
                                     attachment=file_name,attachment_type='M')

    file_attach = t_file_attachment.objects.filter(document_id=document_id,attachment_type='M')
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def save_submenu_attachment(request):
    data = dict()
    sub_menu_attach = request.FILES['sub_menu_attach']
    file_name = sub_menu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/submenu/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, sub_menu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/submenu" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_submenu_attachment_details(request):
    document_id = request.POST.get('document_id')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')

    t_file_attachment.objects.create(document_id=document_id,file_path=file_url,
                                     attachment=file_name,attachment_type='SM')

    file_attach = t_file_attachment.objects.filter(document_id=document_id,attachment_type='SM')
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})


def delete_attachment(request):
    file_id = request.POST.get('file_id')
    identifier = request.POST.get('attachment_type')
    application_no = request.POST.get('application_no')

    files_to_delete = t_file_attachment.objects.filter(file_id=file_id)  # ✅ Renamed variable

    if identifier == 'M':
        for file_obj in files_to_delete:  # ✅ Different variable name
            file_name = file_obj.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/menu/")
            fs.delete(str(file_name))
        files_to_delete.delete()  # ✅ Delete QuerySet, not iteration variable

    elif identifier == 'SM':
        for file_obj in files_to_delete:
            file_name = file_obj.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/submenu/")
            fs.delete(str(file_name))
        files_to_delete.delete()

    elif identifier == 'H':
        for file_obj in files_to_delete:
            file_name = file_obj.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/homepage/")
            fs.delete(str(file_name))
        files_to_delete.delete()

    elif identifier == 'GEN':
        for file_obj in files_to_delete:
            file_name = file_obj.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GEN/")
            fs.delete(str(file_n))
        files_to_delete.delete()
    elif identifier == 'ECR':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECR/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'ECOC':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECOC/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'ECNC':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECNC/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'TOR':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TOR/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'FO':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/FO/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'IEE':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/IEE/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'TRA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TRA/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'ROA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ROA/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'ENE':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ENE/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'EA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EA/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'TOU':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TOU/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'QUA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/QUA/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'GW':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GW/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'EATC':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            print(file_n)
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EATC/")
            fs.delete(str(file_n))
        file.delete()
    elif identifier == 'RRJ':
        for file_obj in files_to_delete:
            file_name = file_obj.attachment
            new_file_name = f"{application_no}-{file_name}"
            print(new_file_name)
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RRJ/")
            fs.delete(str(new_file_name))
        files_to_delete.delete()

        # ✅ Fixed template name for RRJ
        reject_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RRJ')
        return render(request, 'reject_attachment_page.html', {'reject_attach': reject_attach})

    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type=identifier)
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})


def save_menu_details(request):
    menu_order = request.POST.get('menu_order')
    menu_name = request.POST.get('menu_name')
    has_sub_menu = request.POST.get('has_submenu')
    menu_content = request.POST.get('content')
    document_id = request.POST.get('document_id')

    if has_sub_menu == 'Yes':
        t_menu_master.objects.create(menu_name=menu_name, order=menu_order, has_sub_menu=has_sub_menu,is_active='Y',is_deleted='N')
    else:
        t_menu_master.objects.create(menu_name=menu_name, order=menu_order, has_sub_menu=has_sub_menu,menu_content=menu_content,
                                     document_id=document_id,is_active='Y',is_deleted='N')
    return redirect(manage_menu)

def update_menu_details(request):
    menu_id = request.POST.get('menu_id')
    menu_order = request.POST.get('menu_order')
    menu_name = request.POST.get('menu_name')
    has_sub_menu = request.POST.get('has_submenu')
    menu_content = request.POST.get('content')
    document_id = request.POST.get('document_id')

    menu_details = t_menu_master.objects.filter(menu_id=menu_id)
    if has_sub_menu == 'Yes':
        menu_details.update(menu_name=menu_name, order=menu_order, has_sub_menu=has_sub_menu)
    else:
        menu_details.update(menu_name=menu_name, order=menu_order, has_sub_menu=has_sub_menu,menu_content=menu_content,
                                     document_id=document_id)
    return redirect(manage_menu)

def manage_menu_details(request):
    menu_id = request.POST.get('menu_id')
    identifier = request.POST.get('identifier')
    menu_details = t_menu_master.objects.filter(menu_id=menu_id)

    if identifier == 'Activate':
        menu_details.update(is_active='Y')
    elif identifier == 'Delete':
        menu_details.update(is_deleted='Y')
    else:
        menu_details.update(is_active='N')
    return redirect(manage_menu)

def update_submenu_details(request):
    sub_menu_id = request.POST.get('sub_menu_id')
    menu_id = request.POST.get('menu_name')
    sub_menu_order = request.POST.get('sub_menu_order')
    sub_menu_name = request.POST.get('sub_menu_name')
    sub_menu_content = request.POST.get('content')

    menu_details = t_submenu_master.objects.filter(sub_menu_id=sub_menu_id)
    menu_details.update(menu_id=menu_id, order=sub_menu_order,sub_menu_name=sub_menu_name,sub_menu_content=sub_menu_content)
    return redirect(manage_submenu)

def manage_submenu_details(request):
    sub_menu_id = request.POST.get('sub_menu_id')
    identifier = request.POST.get('identifier')
    sub_menu_details = t_submenu_master.objects.filter(sub_menu_id=sub_menu_id)

    if identifier == 'Activate':
        sub_menu_details.update(is_active='Y')
    elif identifier == 'Delete':
        sub_menu_details.update(is_deleted='Y')
    else:
        sub_menu_details.update(is_active='N')
    return redirect(manage_submenu)

def manage_about_us(request):
    about_us_details = t_about_us.objects.filter(is_deleted='N')
    return render(request, 'manage_about_us.html', {'about_us_details': about_us_details })


def about_us(request):
    about_us_details = t_about_us.objects.filter(is_active='Y',is_deleted='N').order_by('about_us_id')
    return render(request, 'about_us.html', {'about_us_details': about_us_details })

def add_about_us(request):
    return render(request, 'add_about_us.html')

def save_about_us(request):
    about_us_title = request.POST.get('about_us_title')
    about_us_content = request.POST.get('about_us_content')
    t_about_us.objects.create(about_us_title=about_us_title,about_us_content=about_us_content,is_active='Y',is_deleted='N')
    return redirect(about_us)

def edit_about_us(request,about_us_id):
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)
    return render(request, 'edit_about_us.html', {'about_us_details': about_us_details})

def update_about_us(request):
    about_us_id = request.POST.get('about_us_id')
    about_us_title = request.POST.get('about_us_title')
    about_us_content = request.POST.get('about_us_content')
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)
    about_us_details.update(about_us_title=about_us_title,about_us_content=about_us_content)
    return redirect(about_us)

def manage_about_us_details(request):
    about_us_id = request.POST.get('about_us_id')
    identifier = request.POST.get('identifier')
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)

    if identifier == 'Activate':
        about_us_details.update(is_active='Y')
    elif identifier == 'Delete':
        about_us_details.update(is_deleted='Y')
    else:
        about_us_details.update(is_active='N')
    return redirect(about_us)

def show_about_us(request):
    about_us_id = request.GET.get('about_us_id')
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)
    return render(request, 'view_about_us.html', {'about_us_details': about_us_details})

def track_application(request):
    return render(request, 'track_application.html')

def manage_notification_circulars(request):
    notification_details = t_notification_details.objects.filter(is_deleted='N')
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    return render(request,'manage_notifications_circulars.html', {'notification_details': notification_details,
                                                      'file_attachment':file_attachment,'document_id':document_id})

def notification_circulars(request):
    notification_details = t_notification_details.objects.filter(is_active='Y', is_deleted='N')
    file_attachment = t_file_attachment.objects.all()
    return render(request, 'notification_circulars.html', {'file_attachment': file_attachment,
                                                 'notification_details': notification_details})

def get_notification_details(request):
    notification_id = request.GET.get('notification_id')
    document_id = request.GET.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    notification_details = t_notification_details.objects.filter(notification_id=notification_id)
    return render(request, 'edit_notification_details.html',{'file_attachment':file_attachment,'notification_details':notification_details})


def manage_notification_details(request):
    notification_id = request.POST.get('notification_id')
    identifier = request.POST.get('identifier')
    notification_details = t_notification_details.objects.filter(notification_id=notification_id)

    if identifier == 'Activate':
        notification_details.update(is_active='Y')
    elif identifier == 'Delete':
        notification_details.update(is_deleted='Y')
    else:
        notification_details.update(is_active='N')
    return redirect(manage_notification_circulars)

def add_notification_file(request):
    data = dict()
    attachment_name = request.FILES['notification_document']

    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/notifications")
    if fs.exists(attachment_name.name):
        data['form_is_valid'] = False
    else:
        fs.save(attachment_name.name, attachment_name)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/notifications" + "/" + attachment_name.name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = attachment_name.name
    return JsonResponse(data)

def add_notification_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    notification_title = request.POST.get('notification_title')

    t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id,attachment_type='NC')

    t_notification_details.objects.create(notification_title=notification_title,document_id=document_id,is_active='Y',
                                         is_deleted='N')

    return redirect(manage_notification_circulars)

def delete_notification_attachment(request):
    document_id = request.POST.get('document_id')
    file = t_file_attachment.objects.filter(document_id=document_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/notifications")
        fs.delete(str(file_name))
    file.delete()

    file_attach = t_file_attachment.objects.filter(document_id=document_id)
    notification_details = t_notification_details.objects.filter(document_id=document_id)
    return render(request, 'edit_notification_details.html', {'file_attachment':file_attach,
                                                             'notification_details':notification_details})

def update_notification_file(request):
    data = dict()
    attachment_name = request.FILES['edit_notification_document']
    document_id = request.POST.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)

    if file_attachment.exists():
        data['file_url'] = file_attachment.file_url
        data['file_name'] = file_attachment.attachment
        return JsonResponse(data)
    else:
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/notifications")
        if fs.exists(attachment_name.name):
            data['form_is_valid'] = False
        else:
            fs.save(attachment_name.name, attachment_name)
            file_url = "attachments" + "/" + str(timezone.now().year) + "/notifications" + "/" + attachment_name.name
            data['form_is_valid'] = True
            data['file_url'] = file_url
            data['file_name'] = attachment_name.name
        return JsonResponse(data)

def update_notification_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    notification_title = request.POST.get('notification_title')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    notification_details = t_notification_details.objects.filter(document_id=document_id)
    if file_attachment.exists():
        notification_details.update(notification_title=notification_title)
    else:
        t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id,attachment_type='NC')
        notification_details.update(notification_title=notification_title)
    return redirect(manage_notification_circulars)

def manage_committee_schedule(request):
    return render(request, 'manage_committee_schedule.html')

def manage_eia_related(request):
    return render(request, 'manage_eia_related.html')

def manage_live_statistics(request):
    return render(request, 'manage_live_statistics.html')

def manage_home_page(request):
    home_page_details = t_homepage_master.objects.filter(homepage_id='1')
    file_attachment = t_file_attachment.objects.filter(attachment_type='H')
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request, 'manage_home_page.html', {'client_application_count':client_application_count,'home_page_details': home_page_details,
                                                'file_attach': file_attachment})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
    

def update_homepage_details(request):
    homepage_title = request.POST.get('homepage_title')
    content = request.POST.get('content')
    home_page = t_homepage_master.objects.filter(homepage_id=1)
    home_page.update(homepage_title=homepage_title,homepage_content=content)
    home_page_details = t_homepage_master.objects.filter(homepage_id=1)
    file_attach = t_file_attachment.objects.filter(attachment_type='H')
    return render(request, 'manage_home_page.html', {'home_page_details': home_page_details, 'file_attach': file_attach})

def save_homepage_attachment(request):
    data = dict()
    menu_attach = request.FILES['homepage_attach']
    file_name = menu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/homepage/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, menu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/homepage" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_homepage_attachment_details(request):
    document_id = request.POST.get('document_id')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    print(document_id)
    t_file_attachment.objects.create(document_id=document_id,file_path=file_url,
                                     attachment=file_name,attachment_type='H')

    file_attach = t_file_attachment.objects.filter(document_id=document_id,attachment_type='H')
    home_page_details = t_homepage_master.objects.filter(homepage_id=1)
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def download_forms(request):
    file_attach = t_file_attachment.objects.filter(attachment_type='F')
    return render(request, 'download_forms.html', {'download_forms': file_attach})

def change_password(request):
    data = dict()
    email_id = request.session['email']
    password_value = make_password(request.POST.get('confirm_password'))
    application_details = t_user_master.objects.filter(email_id=email_id)
    application_details.update(password=password_value)
    data['message'] = "update_successful"
    return JsonResponse(data)


def check_user_password(request):
    data = dict()
    _username = request.session['email']
    _password = request.GET.get('current_password')
    user_details = t_user_master.objects.filter(email_id=_username)
    for user_data in user_details:
        check_pass = check_password(_password, user_data.password)
        if check_pass:
            data['form_is_valid'] = True
        else:
            data['form_is_valid'] = False
        return JsonResponse(data)


def change_mobile_number(request):
    data = dict()
    email_id = request.session['email']
    new_contact_number = request.POST.get('new_contact_number')
    application_details = t_user_master.objects.filter(email_id=email_id)
    application_details.update(contact_number=new_contact_number)
    data['message'] = "update_successful"
    return JsonResponse(data)


def client_registration(request):
    data = dict()
    proponent_type = request.POST.get('proponent_type')
    print(proponent_type)
    cid = request.POST.get('cid')
    proponent_name = request.POST.get('proponent_name')
    address = request.POST.get('proponent_address')
    contact_person = request.POST.get('contact_person')
    email = request.POST.get('email')
    contact_number = request.POST.get('contact_number')
    dzongkhag = request.POST.get('dzongkhag')
    gewog = request.POST.get('gewog')
    village = request.POST.get('village')
    i_dzongkhag = request.POST.get('i_dzongkhag')
    i_gewog = request.POST.get('i_gewog')
    i_village = request.POST.get('i_village')

    if proponent_type == '4':
        t_user_master.objects.create(login_type='C', proponent_type=proponent_type,cid=cid, proponent_name=proponent_name,
                                 address=address, contact_person=contact_person, email_id=email,
                                 contact_number=contact_number, i_dzongkhag=i_dzongkhag, i_gewog=i_gewog,
                                 i_village=i_village,is_active="N", logical_delete="N")
        data['message'] = "registration successful"
    else:
        t_user_master.objects.create(login_type='C', proponent_type=proponent_type, proponent_name=proponent_name,
                                 address=address, contact_person=contact_person, email_id=email,
                                 contact_number=contact_number, dzongkhag_code=dzongkhag, gewog_code=gewog,
                                 village_code=village,is_active="N", logical_delete="N")
        data['message'] = "registration successful"
    return JsonResponse(data)

def new_client_registration(request):
    reg_clients = t_user_master.objects.filter(login_type="C")
    clients = reg_clients.filter(accept_reject=None)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    proponent_type = t_proponent_type_master.objects.all()
    response = render(request, 'new_client_registration.html', {'new_clients': clients,'dzongkhag':dzongkhag,
                                                            'gewog':gewog, 'village':village,
                                                            'proponent_type':proponent_type})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def registered_client(request):
    reg_clients = t_user_master.objects.filter(login_type='C')
    clients = reg_clients.filter(accept_reject='A')
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    proponent_type = t_proponent_type_master.objects.all()
    response = render(request, 'registered_clients.html', {'new_clients': clients,'dzongkhag':dzongkhag,
                                                            'gewog':gewog, 'village':village,
                                                            'proponent_type':proponent_type})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def manage_client(request):
    try:
        login_id   = request.POST.get('login_id')
        email_id   = request.POST.get('email')
        name       = request.POST.get('name')
        identifier = request.POST.get('identifier')

        reg_clients = t_user_master.objects.filter(login_id=login_id)

        if identifier == 'Accept':
            password = get_random_password_string(8)
            with transaction.atomic():
                reg_clients.update(
                    accept_reject='A',
                    is_active='Y',
                    password=make_password(password),
                    last_login_date=date.today()
                )
                transaction.on_commit(lambda: threading.Thread(
                    target=_send_accept_mail_in_background,
                    args=(name, email_id, password),
                    daemon=True
                ).start())

        elif identifier == 'Reject':
            with transaction.atomic():
                reg_clients.update(accept_reject='R')
                transaction.on_commit(lambda: threading.Thread(
                    target=_send_reject_mail_in_background,
                    args=(name, email_id),
                    daemon=True
                ).start())

        elif identifier == 'Reset':
            password = get_random_password_string(8)
            with transaction.atomic():
                reg_clients.update(password=make_password(password))
                transaction.on_commit(lambda: threading.Thread(
                    target=_send_reset_pass_mail_in_background,
                    args=(name, email_id, password),
                    daemon=True
                ).start())

        elif identifier == 'Activate':
            reg_clients.update(is_active='Y')

        elif identifier == 'Deactivate':
            reg_clients.update(is_active='N')

        return redirect(new_client_registration)

    except Exception as exc:
        logger.exception("manage_client failed for login_id=%s", login_id)
        return redirect(new_client_registration)  # or return an error page/message



# ────────────────────────────────────────────────
# ACCEPT
# ────────────────────────────────────────────────

def _send_accept_mail_in_background(name, email_id, password):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_accept_mail(name, email_id, password)
    except Exception:
        logger.exception("Failed to send accept email to=%s", email_id)


def send_accept_mail(name, email_id, password):
    subject = "Registration Accepted - ECS System"
    message = (
        f"Dear {name},\n\n"
        f"Your registration for the ECS System has been accepted.\n"
        f"Your login credentials are as follows:\n\n"
        f"  Login ID : {email_id}\n"
        f"  Password : {password}\n\n"
        f"Please log in and change your password after your first login.\n\n"
        f"Regards,\nECS System Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )


# ────────────────────────────────────────────────
# REJECT
# ────────────────────────────────────────────────

def _send_reject_mail_in_background(name, email_id):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_reject_mail(name, email_id)
    except Exception:
        logger.exception("Failed to send reject email to=%s", email_id)


def send_reject_mail(name, email_id):
    subject = "Registration Status - ECS System"
    message = (
        f"Dear {name},\n\n"
        f"We regret to inform you that your registration for the ECS System "
        f"has been rejected.\n\n"
        f"If you believe this is a mistake, please contact our support team.\n\n"
        f"Regards,\nECS System Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )


# ────────────────────────────────────────────────
# RESET PASSWORD
# ────────────────────────────────────────────────

def _send_reset_pass_mail_in_background(name, email_id, password):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_reset_pass_mail(name, email_id, password)
    except Exception:
        logger.exception("Failed to send password reset email to=%s", email_id)


def send_reset_pass_mail(name, email_id, password):
    subject = "Password Reset - ECS System"
    message = (
        f"Dear {name},\n\n"
        f"Your password for the ECS System has been reset.\n"
        f"Your updated login credentials are as follows:\n\n"
        f"  Login ID : {email_id}\n"
        f"  Password : {password}\n\n"
        f"Please log in and change your password at your earliest convenience.\n\n"
        f"Regards,\nECS System Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )

def update_first_login_details(request):
    login_id = request.POST['login_id']
    confirm_password = request.POST['password']
    security_question = request.POST['security_question']
    security_answer = request.POST['answer']
    today = date.today()

    password = make_password(confirm_password)
    reg_users = t_user_master.objects.filter(pk=login_id)
    reg_users.update(password=password)
    reg_users.update(last_login_date=today)
    t_forgot_password.objects.create(login_id=login_id, security_question_id=security_question, answer=security_answer)
    return redirect(login)

def get_security_answer(request):
    data = dict()
    email_id = request.GET.get('email_id')
    question_id = request.GET.get('questionId')
    details = t_user_master.objects.filter(email_id=email_id)
    for app_details in details:
        login_id = app_details.login_id
        application_details = t_forgot_password.objects.filter(login_id=login_id, security_question_id=question_id)
        for application in application_details:
            data["answer"] = application.answer
    return JsonResponse(data)

def update_password(request):
    data = dict()
    email_id = request.POST.get('email_id')
    password = get_random_password_string(8)
    password_value = make_password(password)
    application_details = t_user_master.objects.filter(email_id=email_id)
    application_details.update(password=password_value)
    data['message'] = "update_successful"
    for details in application_details:
        if details.login_type == 'I':
            send_reset_pass_mail(details.name, email_id, password)
        else:
            send_reset_pass_mail(details.proponent_name, email_id, password)
    return JsonResponse(data)


def load_security_question(request):
    email_id = request.GET.get('email')
    login_details = t_user_master.objects.filter(email_id=email_id)
    for id_details in login_details:
        login_id = id_details.login_id
        details = t_forgot_password.objects.filter(login_id=login_id)
        for security_details in details:
            question_id = security_details.security_question_id
            security = t_security_question_master.objects.filter(question_id=question_id)
    return render(request, 'forgot_pass_list.html', {'security': security})


def manage_others(request):
    other_details = t_other_details.objects.filter(is_deleted='N')
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    response = render(request,'others_master.html', {'other_details': other_details,'client_application_count':client_application_count,
                                                      'file_attachment':file_attachment,'document_id':document_id})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def add_publication_file(request):
    data = dict()
    myFile = request.FILES['others_document']  # Use get to avoid MultiValueDictKeyError

    if myFile:
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/others")
        if fs.exists(myFile.name):
            data['form_is_valid'] = False
        else:
            fs.save(myFile.name, myFile)
            file_url = "attachments" + "/" + str(timezone.now().year) + "/others" + "/" + myFile.name
            data['form_is_valid'] = True
            data['file_url'] = file_url
            data['file_name'] = myFile.name
    else:
        data['form_is_valid'] = False
        data['error'] = 'No file uploaded'

    return JsonResponse(data)

def add_publication_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    title = request.POST.get('title')
    type = request.POST.get('type')

    
    t_file_attachment.objects.create(file_path=file_url, attachment=attachment_name, document_id=document_id,
                                         attachment_type='F')

    t_other_details.objects.create(title=title, type=type, document_id=document_id,is_active='Y',
                                         is_deleted='N')

    return redirect(manage_others)


def get_other_details(request):
    others_id = request.GET.get('others_id')
    document_id = request.GET.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    others_details = t_other_details.objects.filter(others_id=others_id)
    return render(request, 'edit_other_details.html',{'file_attachment':file_attachment,'others_details':others_details})

def get_menu_details(request,menu_id):
    menu_details = t_menu_master.objects.filter(menu_id=menu_id)
    for menu_det in menu_details:
        doc_id = menu_det.document_id
        file_attach = t_file_attachment.objects.filter(document_id=doc_id)
        return render(request, 'edit_menu_details.html',{'menu_details':menu_details,'file_attach':file_attach })

def get_submenu_details(request, sub_menu_id):
    sub_menu_details = t_submenu_master.objects.filter(sub_menu_id=sub_menu_id)
    for sub_menu_det in sub_menu_details:
        doc_id = sub_menu_det.document_id
        file_attach = t_file_attachment.objects.filter(document_id=doc_id)
        menu_list = t_menu_master.objects.all()
        return render(request, 'edit_submenu_details.html', {'sub_menu_details': sub_menu_details, 'file_attach': file_attach,
                                                             'menu_list':menu_list})

def delete_publication_attachment(request):
    document_id = request.POST.get('document_id')
    file = t_file_attachment.objects.filter(document_id=document_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/publications")
        fs.delete(str(file_name))
    file.delete()

    file_attach = t_file_attachment.objects.filter(document_id=document_id)
    publication_details = t_other_details.objects.filter(document_id=document_id)
    return render(request, 'edit_other_details.html', {'file_attachment':file_attach,
                                                             'publication_details':publication_details})

def update_publication_file(request):
    data = dict()
    attachment_name = request.FILES['edit_others_document']
    document_id = request.POST.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)

    if file_attachment.exists():
        data['file_url'] = file_attachment.file_url
        data['file_name'] = file_attachment.attachment
        return JsonResponse(data)
    else:
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/others")
        if fs.exists(attachment_name.name):
            data['form_is_valid'] = False
        else:
            fs.save(attachment_name.name, attachment_name)
            file_url = "attachments" + "/" + str(timezone.now().year) + "/others" + "/" + attachment_name.name
            data['form_is_valid'] = True
            data['file_url'] = file_url
            data['file_name'] = attachment_name.name
        return JsonResponse(data)

def update_publication_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    title = request.POST.get('title')
    type = request.POST.get('type')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    publication_details = t_other_details.objects.filter(document_id=document_id)
    if file_attachment.exists():
        publication_details.update(title=title)
        publication_details.update(type=type)
    else:

        t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id)
        publication_details.update(title=title)
        publication_details.update(type=type)
    return redirect(manage_others)

def manage_publication_details(request):
    others_id = request.POST.get('publication_id')
    identifier = request.POST.get('identifier')
    publication_details = t_other_details.objects.filter(others_id=others_id)

    if identifier == 'Activate':
        publication_details.update(is_active='Y')
    elif identifier == 'Delete':
        publication_details.update(is_deleted='Y')
    else:
        publication_details.update(is_active='N')
    return redirect(manage_others)

def publications(request):
    publication_details = t_other_details.objects.filter(is_active='Y',is_deleted='N')
    file_attachment = t_file_attachment.objects.all()
    return render(request, 'publications.html', {'file_attachment': file_attachment,
                                                 'publication_details': publication_details})

# CITIZEN DETAILS
def check_cid_exists(request):
    data = dict()
    cid = request.GET.get('cid')
    message_count = t_user_master.objects.filter(cid=cid, login_type='C').count()
    if message_count > 0:
        data['count'] = message_count
    else:
        BASE_URL = 'https://staging-datahub-apim.dit.gov.bt/dcrc_individualcitizendetailapi/1.0.0/citizendata/' + cid
        token = get_auth_token()
        headers = {'Authorization': "Bearer {}".format(token)}
        response = requests.get(BASE_URL, headers=headers, verify=False)
        print(response.json())
        data['response'] = response.json()
    return JsonResponse(data)


def get_auth_token():
    """
    get an auth token
    """
    credentials = {'client_id': 'oKvI_XucoWSSNGmfpvRIIlwE4yAa',
                   'client_secret': 'Ux3nnEgJWYhn4BiBBNlTE9LANFYa',
                   'grant_type': 'client_credentials'}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post('https://sso.tech.gov.bt/oauth2/token', params=credentials,
                        headers=headers,verify=False)

    json = res.json()
    return json["access_token"]


def change_role(request):
    """
    Handle role switching for users with dual roles
    Updates session and prepares dashboard context for new role
    """
    try:
        data = json.loads(request.body)
        new_role_id = int(data.get('role_id'))

        # ============ VALIDATE USER HAS DUAL ROLES ============
        if request.session.get('both_role_id') != 5:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to switch roles.'
            }, status=403)

        # ============ VALIDATE ROLE_ID ============
        valid_roles = {
            2: {'role': 'Verifier', 'role_id': 2},
            3: {'role': 'Reviewer', 'role_id': 3}
        }

        if new_role_id not in valid_roles:
            return JsonResponse({
                'success': False,
                'message': 'Invalid role selected.'
            }, status=400)

        # ============ UPDATE SESSION WITH NEW ROLE ============
        role_data = valid_roles[new_role_id]
        request.session['role'] = role_data['role']
        request.session['role_id'] = role_data['role_id']
        request.session.modified = True

        # ============ PREPARE DASHBOARD CONTEXT ============
        context = prepare_dashboard_context(request, role_data['role'])

        # ============ REDIRECT TO DASHBOARD ============
        redirect_url = reverse('dashboard')

        return JsonResponse({
            'success': True,
            'message': f'Role switched to {role_data["role"]} successfully!',
            'redirect_url': redirect_url
        })

    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid request format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)


def prepare_dashboard_context(request, role):
    """
    Prepare dashboard context based on the role
    Mirrors the logic from the dashboard view
    """

    # ============ INITIALIZE ALL COUNTERS ============
    context = {
        'v_application_count': 0,
        'r_application_count': 0,
        'ec_renewal_count': 0,
        'client_application_count': 0,
        'ibls_application_count': 0,
        'reviewer_application_count': {},
        'reviewer_applications': {},
        'applications_by_reviewer': {},
        'reviewer_counts': {},
        'reviewer_names': {},
        'total_applications': 0,
        'total_reviewers': 0
    }

    try:
        login_type = request.session.get('login_type')
        login_id = request.session.get('login_id')
        email = request.session.get('email')
        ca_authority = request.session.get('ca_authority')

        # ============ EC RENEWAL COUNT (Common for Verifier/Reviewer) ============
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        pending_renewal_exists = t_ec_application_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(application_status='A')

        non_updated_renewals = (
            t_ec_t1.objects
            .filter(
                applicant_id=email,
                service_type__in=["Main Activity", "Old EC"],
                ec_expiry_date__lt=expiry_date_threshold,
                ec_expiry_date__isnull=False,
                ec_reference_no__isnull=False,
            )
            .exclude(ec_reference_no='')
            .annotate(has_pending_renewal=Exists(pending_renewal_exists))
            .filter(has_pending_renewal=False)
        )
        context['ec_renewal_count'] = non_updated_renewals.count()

        # ============ VERIFIER ROLE ============
        if role == 'Verifier':
            # Get verifier application count
            context['v_application_count'] = t_workflow_dtls.objects.filter(
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_authority,
                action_date__isnull=False
            ).count()

            # Get applications grouped by reviewer
            applications_by_reviewer_qs = (
                t_ec_application_t1.objects
                .filter(ca_authority=ca_authority)
                .values(
                    'record_id',
                    'project_name',
                    'applicant_name',
                    'application_status',
                    'application_date',
                    'application_no',
                    'location_name',
                    'service_id',
                    'assigned_to',
                    'application_source'
                )
                .order_by('-assigned_to', 'application_date')
            )

            applications_list = list(applications_by_reviewer_qs)

            # Extract unique reviewer IDs
            unique_reviewer_ids = set(
                app['assigned_to'] for app in applications_list
                if app['assigned_to']
            )

            # Fetch reviewer names
            reviewer_name_map = {}
            if unique_reviewer_ids:
                reviewers_from_db = t_user_master.objects.filter(
                    login_id__in=unique_reviewer_ids
                ).values('login_id', 'name')

                reviewer_name_map = {
                    reviewer['login_id']: reviewer['name']
                    for reviewer in reviewers_from_db
                }

            # Initialize result dictionaries
            applications_by_reviewer = {}
            reviewer_counts = {}
            reviewer_names = {}

            # Group applications by reviewer
            for application in applications_list:
                reviewer_id = application['assigned_to']

                if not reviewer_id:
                    continue

                reviewer_name = reviewer_name_map.get(reviewer_id, 'Unknown Reviewer')

                if reviewer_id not in reviewer_names:
                    reviewer_names[reviewer_id] = reviewer_name

                if reviewer_id not in reviewer_counts:
                    reviewer_counts[reviewer_id] = 0
                reviewer_counts[reviewer_id] += 1

                if reviewer_id not in applications_by_reviewer:
                    applications_by_reviewer[reviewer_id] = []
                applications_by_reviewer[reviewer_id].append(application)

            context.update({
                'applications_by_reviewer': applications_by_reviewer,
                'reviewer_counts': reviewer_counts,
                'reviewer_names': reviewer_names,
                'total_applications': len(applications_list),
                'total_reviewers': len(reviewer_names)
            })

        # ============ REVIEWER ROLE ============
        elif role == 'Reviewer':
            # Get reviewer application count
            context['r_application_count'] = t_workflow_dtls.objects.filter(
                assigned_role_id='3',
                assigned_user_id=login_id,
                assigned_role_name='Reviewer',
                ca_authority=ca_authority,
                service_type__in=['Main Activity', 'Renewal']
            ).count()

            # Get reviewer applications grouped by status
            reviewer_applications_qs = (
                t_ec_application_t1.objects
                .filter(assigned_to=login_id)
                .values(
                    'record_id',
                    'project_name',
                    'applicant_name',
                    'application_status',
                    'application_date',
                    'application_no',
                    'location_name',
                    'service_id',
                    'application_source'
                )
                .order_by('-application_date')
            )

            reviewer_application_count = {}
            reviewer_applications = {}

            for application in reviewer_applications_qs:
                # Determine status group
                if application['application_status'] == 'A':
                    status_group = 'Approved'
                else:
                    status_group = 'Pending'

                # Count applications by status
                if status_group not in reviewer_application_count:
                    reviewer_application_count[status_group] = 0
                reviewer_application_count[status_group] += 1

                # Group applications by status
                if status_group not in reviewer_applications:
                    reviewer_applications[status_group] = []
                reviewer_applications[status_group].append(application)

            context.update({
                'reviewer_application_count': reviewer_application_count,
                'reviewer_applications': reviewer_applications
            })

        return context

    except Exception as e:
        print(f"Error preparing dashboard context: {str(e)}")
        return context


import bleach

