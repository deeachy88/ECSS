import re
import json
import zlib
import secrets
import random
import logging
import threading
import requests
import traceback

from datetime import date, datetime, timedelta, timezone as dt_timezone

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.db import connection, transaction
from django.db.models import Count, Subquery, OuterRef, Exists, Max
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.conf import settings

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

import os

from django.contrib.staticfiles import finders

from ecs_admin.models import (
    payment_details_master, t_bsic_code, t_competant_authority_master,
    t_dzongkhag_master, t_fees_schedule, t_file_attachment, t_gewog_master,
    t_role_master, t_security_question_master, t_service_master, t_thromde_master,
    t_user_master, t_village_master, t_other_details
)
from ecs_main.models import t_application_history
from ecs_main.views import get_birms_token, get_random_tax_no, insert_app_payment_details, make_payment_request
from proponent.models import (
    t_ec_application_t2, t_ec_application_t1, t_ec_compliance, t_payment_details,
    t_report_submission_t1, t_report_submission_t2, t_workflow_dtls, t_ec_t1,
    t_ec_t2, t_ec_t1_history
)

logger = logging.getLogger(__name__)

MAIN_SERVICE_TYPES = ['Main Activity', 'NC', 'OC', 'TC', 'PC', 'LC', 'CC', 'AC']

def new_application(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    #bsic_details = t_bsic_code.objects.all()
    bsic_details = t_bsic_code.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    response = render(request, 'new_application.html',{'bsic_details':bsic_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'tor_application_count':tor_application_count,'draft_count':draft_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_application_service_id(request):
    data = {}
    activity = request.GET.get('activity')
    activity_details = t_bsic_code.objects.filter(activity=activity)
    for activity_details in activity_details:
        service_id = activity_details.service_id
        service_master = t_service_master.objects.filter(
            service_id=service_id
        ).first()
        attachments = service_master.attachments if service_master else ''
        # Store everything in session
        request.session['service_id'] = service_id
        request.session['ca_auth'] = activity_details.competent_authority
        request.session['colour_code'] = activity_details.colour_code
        request.session['has_tor'] = activity_details.has_tor
        request.session['mas_integration'] = activity_details.mas_integration
        request.session['activity'] = activity_details.activity
        request.session['attachments'] = attachments   #
        data = {
            'colour_code': activity_details.colour_code,
            'has_tor': activity_details.has_tor,
            'mas_integration': activity_details.mas_integration
        }
    return JsonResponse(data)

def application_form(request):
    # Get session data
    login_id = request.session.get('login_id')
    applicant_id = request.session.get('email')

    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    service_id = str(request.session.get('service_id'))

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
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

    # 5. TOR application count (optimized)
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR',
        applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()
    return render(request, 'new_application_form.html',{'service_id': service_id,'thromde':thromde,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'draft_count':draft_count,'tor_application_count':tor_application_count, 'ec_renewal_count':ec_renewal_count})

def get_application_no(request, service_code, service_id):
    if service_code == "TOR":
        application_no= t_ec_application_t1.objects.filter(application_no__contains='TOR').aggregate(Max('application_no'))
    else:
        application_no= t_ec_application_t1.objects.exclude(service_id=service_id, application_no__contains='TOR').filter(application_no__contains=service_code).aggregate(Max('application_no'))
    last_application_no= application_no['application_no__max']
    print(last_application_no)
    if not last_application_no:
        year=timezone.now().year
        new_application_no = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(last_application_no)[9:13]
        substring = int(substring) + 1
        app_num = str(substring).zfill(4)
        print(app_num)
        year =  timezone.now().year
        new_application_no =  service_code + "-" + str(year) + "-" + app_num
    return new_application_no

def get_temp_application_no(login_id, digits=10):
    login_id_str = login_id
    random_number = secrets.randbelow(10**digits)  # 0 .. (10^digits - 1)
    random_part = str(random_number).zfill(digits)
    new_application_no = f"TOR-{login_id_str}-{random_part}"
    print(new_application_no)
    return new_application_no

def save_general_details(request):
    data = {'message': 'failure'}
    
    try:
        post_data = request.POST
        session = request.session

        identifier = request.POST.get('identifier')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        tor_application_no = request.POST.get('tor_application_no')

        # Get the application number from POST data
        application_no = post_data.get('application_no')
        identifier = post_data.get('identifier', '')

        # Check if application already exists
        existing_app = None
        if application_no:
            existing_app = t_ec_application_t1.objects.filter(
                application_no=application_no
            ).first()

        # Get service_id_to_use early for all cases
        service_id_to_use = None
        activity_to_use = None
        color_code_to_use = None
        ca_auth_to_use = None
        
        if identifier not in ['DR', 'NC', 'OC', 'TC', 'PC', 'LC', 'CC']:
            # New application - use session values
            service_id_to_use = request.session['service_id']
            # Get activity from POST data for new applications
            activity_to_use = request.POST.get('activity')
            if not activity_to_use or activity_to_use == '':
                # Fall back to session if POST doesn't have activity
                activity_to_use = request.session.get('activity')
            color_code_to_use = request.session['colour_code']
        else:
            # For modifications, get reference application number
            ref_application_no = None
            if identifier in ['NC', 'OC', 'DR', 'TC', 'PC', 'LC', 'CC']:
                ref_application_no = request.POST.get('application_no')
            
            # Get existing application details
            existing_app = None
            if ref_application_no:
                existing_app = t_ec_application_t1.objects.filter(
                    application_no=ref_application_no
                ).first()
            
            if existing_app:
                service_id_to_use = existing_app.service_id
                activity_to_use = existing_app.activity
                ca_auth_to_use = existing_app.ca_authority
                
                # For DR, keep existing color code; for other modifications, use previous app's color code
                if identifier == 'DR':
                    color_code_to_use = existing_app.colour_code
                else:
                    color_code_to_use = existing_app.colour_code  # Use previous app's color code
            else:
                # If no existing app found, fall back to session values
                service_id_to_use = request.session['service_id']
                activity_to_use = request.session.get('activity')
                color_code_to_use = request.session['colour_code']
        
        # Now determine service_code based on service_id_to_use
        # Service code mapping
        SERVICE_CODE_MAP = {
            '1': 'IEE', '2': 'ENE', '3': 'ROA', '4': 'TRA',
            '5': 'TOU', '6': 'GWA', '7': 'FOR', '8': 'QUA'
        }
        service_code = SERVICE_CODE_MAP.get(str(service_id_to_use), 'GEN')

        # Determine application number based on identifier
        if identifier not in ['DR', 'NC', 'OC', 'TC', 'PC', 'LC', 'CC']:
            # For new applications, use session service_id
            # application_no = get_application_no(request, service_code, request.session['service_id'])
            application_no = get_new_application_no(request, service_code)
        else:
            # For modifications, use the service_id from existing application
            # EXCEPT for DR (draft) - use the same application number
            if identifier == 'DR':
                application_no = ref_application_no  # Use existing application number for draft
            else:
                # application_no = get_application_no(request, service_code, service_id_to_use)
                application_no = get_new_application_no(request, service_code)
        
        # Get prev_ec_reference_no for TC/PC/LC/CC cases
        prev_ec_reference_no = request.POST.get('prev_ec_reference_no') if identifier in ['TC', 'PC', 'LC', 'CC'] else None
        
        if dzongkhag_throm == 'Dzongkhag':
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        else:
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')

        # Determine service_type - For DR always use 'Main Activity'
        if identifier == 'DR':
            service_type_to_use = 'Main Activity'
        else:
            service_type_to_use = request.POST.get('service_type')

        common_data = {
            'application_no': application_no,
            'application_date': timezone.now().date(),
            'application_type': 'New',
            'application_source': 'ECSS',
            'application_status': 'P',
            'applicant_id': request.session['email'],
            'applicant_name': request.POST.get('applicant_name'),
            'address': request.POST.get('address'),
            'cid': request.session['cid'],
            'contact_no': request.POST.get('contact_no'),
            'email': request.POST.get('email'),
            'focal_person': request.POST.get('focal_person'),
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,
            'location_name': request.POST.get('project_site'),
            'cross_dzongkhag_locations': request.POST.get('cross_dzongkhag_locations'),
            'project_name': request.POST.get('project_name'),
            'project_description': request.POST.get('project_description'),
            'dzongkhag_throm': dzongkhag_throm,
            'service_type': service_type_to_use,  # Use determined service_type
            'tor_application_no': tor_application_no,
            'service_id': service_id_to_use,
            'colour_code': color_code_to_use,  # Use determined color code
            'proponent_type': request.session.get('proponent_type'),
            'activity': activity_to_use  # Use determined activity
        }
        
        with transaction.atomic():
            ca_auth = ca_auth_to_use  # Use the ca_auth we already determined
            
            # If ca_auth wasn't determined from existing app, calculate it
            if ca_auth is None:
                # For modifications (NC, OC, DR, TC, PC, LC, CC), get ca_auth from existing application
                if identifier in ['NC', 'OC', 'DR', 'TC', 'PC', 'LC', 'CC']:
                    activity_details = t_bsic_code.objects.filter(activity=activity_to_use)

                    for cat_details in activity_details:
                        request.session['ca_auth'] = cat_details.competent_authority

                    auth_filter = t_competant_authority_master.objects.filter(
                        competent_authority=request.session['ca_auth'],
                        dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
                    )

                    ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
                else:
                    auth_filter = t_competant_authority_master.objects.filter(
                        competent_authority=request.session['ca_auth'],
                        dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
                    )
                    ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None


            # Handle different identifier cases
            if identifier == 'DR':
                # Data Rectification (Draft) - UPDATE EXISTING ENTRY
                existing_app = t_ec_application_t1.objects.filter(application_no=ref_application_no).first()
                if existing_app:
                    # UPDATE existing entry with new data
                    update_data = {
                        **common_data,
                        #'ca_authority': existing_app.ca_authority,  # Keep existing ca_auth
                        'ca_authority': ca_auth,
                        'service_type': 'Main Activity',  # Force Main Activity for DR
                        'service_id': existing_app.service_id,  # Keep existing service_id
                        'colour_code': existing_app.colour_code,  # Keep existing color code for DR
                        'activity': existing_app.activity  # Keep existing activity
                    }
                    
                    # Remove fields that shouldn't be updated for draft
                    if 'application_no' in update_data:
                        del update_data['application_no']  # Don't update application_no
                    
                    # Update the existing record
                    t_ec_application_t1.objects.filter(
                        application_no=ref_application_no
                    ).update(**update_data)
                    
                    print(f"DR - Updated existing application {ref_application_no}")
                else:
                    # If no existing app, create new one with session color code
                    new_data = {
                        'ca_authority': ca_auth,
                        'prev_ec_reference_no': prev_ec_reference_no if prev_ec_reference_no else None
                    }
                    # Ensure service_type is 'Main Activity' for DR
                    common_data['service_type'] = 'Main Activity'
                    t_ec_application_t1.objects.create(**common_data, **new_data)
                    print(f"DR - Created new application {application_no}")
                    
            elif identifier == 'NC':
                # Name Change - CREATE NEW ENTRY
                existing_app = t_ec_application_t1.objects.filter(application_no=ref_application_no).first()
                if existing_app:
                    new_data = {
                        **common_data,
                        'ca_authority': existing_app.ca_authority,  # Use existing ca_auth
                        'prev_ec_reference_no': None,
                        'service_type': identifier,
                        'service_id': existing_app.service_id,  # Use existing service_id
                        'colour_code': existing_app.colour_code,  # Use previous app's color code
                        'activity': existing_app.activity  # Get activity from existing app
                    }
                    # Update project_name for the new entry
                    new_data['project_name'] = request.POST.get('project_name')
                    t_ec_application_t1.objects.create(**new_data)
                else:
                    raise ValueError(f"Application {ref_application_no} does not exist for NC operation")
                
            elif identifier == 'OC':
                # Ownership Change - CREATE NEW ENTRY
                existing_app = t_ec_application_t1.objects.filter(application_no=ref_application_no).first()
                if existing_app:
                    new_data = {
                        **common_data,
                        'ca_authority': existing_app.ca_authority,  # Use existing ca_auth
                        'prev_ec_reference_no': None,
                        'service_type': identifier,
                        'service_id': existing_app.service_id,  # Use existing service_id
                        'colour_code': existing_app.colour_code,  # Use previous app's color code
                        'activity': existing_app.activity  # Get activity from existing app
                    }
                    # Update applicant_name for the new entry
                    new_data['applicant_name'] = request.POST.get('applicant_name')
                    t_ec_application_t1.objects.create(**new_data)
                else:
                    raise ValueError(f"Application {ref_application_no} does not exist for OC operation")
                
            elif identifier in ['TC', 'PC', 'LC', 'CC']:
                # Transfer/Post-Completion/LC/CC Cases - CREATE NEW ENTRY
                if prev_ec_reference_no:
                    prev_app_details = t_ec_application_t1.objects.filter(application_no=prev_ec_reference_no)
                    for prev_app in prev_app_details:
                        # Create new application with prev_ec_reference_no reference
                        new_app_data = {
                            **common_data,
                            'ca_authority': prev_app.ca_authority,  # Use previous app's ca_auth
                            'prev_ec_reference_no': prev_ec_reference_no,
                            'service_type': identifier,
                            'service_id': prev_app.service_id,  # Use previous app's service_id
                            'colour_code': prev_app.colour_code,  # Use previous app's color code
                            'activity': prev_app.activity  # Get activity from previous app
                        }
                        t_ec_application_t1.objects.create(**new_app_data)
                else:
                    # Create new application without previous reference
                    new_data = {
                        'ca_authority': ca_auth,
                        'prev_ec_reference_no': None,
                        'service_type': identifier
                    }
                    t_ec_application_t1.objects.create(**common_data, **new_data)
                    
            else:
                # Main Activity - New Application - CREATE NEW ENTRY
                new_data = {
                    'ca_authority': ca_auth,
                    'prev_ec_reference_no': prev_ec_reference_no if prev_ec_reference_no else None
                }
                t_ec_application_t1.objects.create(**common_data, **new_data)

            # Create application history (ALWAYS INSERT, NEVER UPDATE)
            t_application_history.objects.create(
                application_no=application_no,
                application_date=timezone.now().date(),
                applicant_id=request.session['email'],
                ca_authority=ca_auth,
                service_id=service_id_to_use,
                application_status='P',
                action_date=timezone.now(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                remarks=None,
                status=None
            )

            # Handle workflow details - Create workflow for all cases
            # For DR (draft), check if workflow already exists before creating
            if identifier not in []:  # Create workflow for all identifiers
                # For DR, only create workflow if it doesn't exist
                if identifier == 'DR':
                    existing_workflow = t_workflow_dtls.objects.filter(
                        application_no=application_no
                    ).exists()
                    if not existing_workflow:
                        # Determine service_type for workflow
                        workflow_service_type = 'Main Activity'  # DR should be 'Main Activity'
                        
                        # Create workflow
                        t_workflow_dtls.objects.create(
                            application_no=application_no,
                            service_id=service_id_to_use,
                            application_status='P',
                            actor_id=request.session['login_id'],
                            actor_name=request.session['name'],
                            assigned_role_id='3',
                            assigned_role_name='Reviewer',
                            ca_authority=ca_auth,
                            application_source='ECSS',
                            service_type=workflow_service_type
                        )
                else:
                    # For other identifiers
                    # Determine service_type for workflow
                    if identifier in ['NC', 'OC', 'TC', 'PC', 'LC', 'CC']:
                        # For modifications
                        workflow_service_type = identifier
                    else:
                        # For new applications
                        workflow_service_type = request.POST.get('service_type')
                    
                    # Create workflow
                    t_workflow_dtls.objects.create(
                        application_no=application_no,
                        service_id=service_id_to_use,
                        application_status='P',
                        actor_id=request.session['login_id'],
                        actor_name=request.session['name'],
                        assigned_role_id='3',
                        assigned_role_name='Reviewer',
                        ca_authority=ca_auth,
                        application_source='ECSS',
                        service_type=workflow_service_type
                    )
            
            data['message'] = 'success'
            data['application_no'] = application_no
            
    except Exception as e:
        print('An error occurred:', e)
        data['error'] = str(e)
        
    return JsonResponse(data)

# Save NEW General Details START
@csrf_exempt
@require_http_methods(["POST"])
def save_new_general_details(request):
    data = {'message': 'failure'}

    try:
        post_data = request.POST
        session = request.session

        # Get the application number from POST data
        application_no = post_data.get('application_no')
        identifier = post_data.get('identifier', '')

        # Check if application already exists
        existing_app = None
        if application_no:
            existing_app = t_ec_application_t1.objects.filter(
                application_no=application_no
            ).first()

        # Service code mapping
        SERVICE_CODE_MAP = {
            '1': 'IEE', '2': 'ENE', '3': 'ROA', '4': 'TRA',
            '5': 'TOU', '6': 'GWA', '7': 'FOR', '8': 'QUA'
        }

        # Get location details
        dzongkhag_throm = post_data.get('dzongkhag_throm')
        if dzongkhag_throm == 'Dzongkhag':
            dzongkhag_code = post_data.get('dzongkhag')
            gewog_code = post_data.get('gewog')
            village_code = post_data.get('vil_chiwog')
            thromde_id = None
        else:
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = post_data.get('thromde_id')

        # Get service details
        if existing_app:
            # Use existing service details
            service_id = existing_app.service_id
            activity = existing_app.activity
            color_code = existing_app.colour_code
        else:
            # Use session/service defaults
            service_id = session.get('service_id')
            activity = post_data.get('activity') or session.get('activity')
            color_code = session.get('colour_code')

        service_code = SERVICE_CODE_MAP.get(str(service_id), 'GEN')

        # Determine competent authority - optimized with single query
        ca_auth = session.get('ca_auth')
        ca_auth_id = ca_auth  # Default value

        if ca_auth == 'DEC' and dzongkhag_code:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                dzongkhag_code_id=dzongkhag_code
            ).values_list('competent_authority_id', flat=True).first()
            ca_auth_id = auth_record if auth_record else ca_auth

        elif ca_auth == 'THROMDE' and thromde_id:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                thromde_id_id=thromde_id
            ).values_list('competent_authority_id', flat=True).first()
            ca_auth_id = auth_record if auth_record else ca_auth

        elif ca_auth:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth
            ).values_list('competent_authority_id', flat=True).first()
            ca_auth_id = auth_record if auth_record else ca_auth

        # Get current time once
        current_date = timezone.now().date()
        current_datetime = timezone.now()

        # Prepare data
        common_data = {
            'application_no': application_no,
            'application_date': current_date,
            'application_type': 'New',
            'application_source': 'ECSS',
            'application_status': 'P',
            'applicant_id': session.get('email'),
            'applicant_name': post_data.get('applicant_name'),
            'address': post_data.get('address'),
            'cid': session.get('cid'),
            'contact_no': post_data.get('contact_no'),
            'email': post_data.get('email'),
            'focal_person': post_data.get('focal_person'),
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,
            'location_name': post_data.get('project_site'),
            'cross_dzongkhag_locations': post_data.get('cross_dzongkhag_locations'),
            'project_name': post_data.get('project_name'),
            'project_description': post_data.get('project_description'),
            'dzongkhag_throm': dzongkhag_throm,
            'service_type': 'Main Activity',
            'service_id': service_id,
            'colour_code': color_code,
            'proponent_type': session.get('proponent_type'),
            'activity': activity,
            'ec_reference_no': post_data.get('ec_reference_no'),
            'ec_approve_date': post_data.get('ec_issue_date'),
            'ec_expiry_date': post_data.get('ec_validity'),
            'ca_authority': ca_auth_id,
            'tor_application_no': post_data.get('tor_no'),
            'mas_integration': post_data.get('mas_integration'),
            'fmfsr_no': post_data.get('fmfsr_no'),
            'app_remarks': post_data.get('app_remarks'),
        }

        with transaction.atomic():
            if existing_app:
                # UPDATE existing application
                update_data = common_data.copy()
                update_data.pop('application_no', None)  # Remove application_no if exists
                t_ec_application_t1.objects.filter(
                    application_no=application_no
                ).update(**update_data)

                # Update workflow if exists
                t_workflow_dtls.objects.filter(
                    application_no=application_no
                ).update(ca_authority=ca_auth_id)

            else:
                # CREATE new application
                if not application_no:
                    application_no = get_new_application_no(request, service_code)
                    common_data['application_no'] = application_no

                t_ec_application_t1.objects.create(**common_data)

                # Create workflow
                t_workflow_dtls.objects.create(
                    application_no=application_no,
                    service_id=service_id,
                    application_status='P',
                    actor_id=session.get('login_id'),
                    actor_name=session.get('name'),
                    assigned_role_id='3',
                    assigned_role_name='Reviewer',
                    ca_authority=ca_auth_id,
                    application_source='ECSS',
                    service_type='Main Activity',
                )

            # Save application number to session for future tabs
            if application_no:
                request.session['current_application_no'] = application_no

            # Create history entry (always create new history record)
            t_application_history.objects.create(
                application_no=application_no,
                application_date=current_date,
                applicant_id=session.get('email'),
                ca_authority=ca_auth_id,
                service_id=service_id,
                application_status='P',
                action_date=current_datetime,
                actor_id=session.get('login_id'),
                actor_name=session.get('name'),
                remarks=None,
                status=None
            )

            data.update({
                'message': 'success',
                'application_no': application_no
            })

    except Exception as e:
        print(f'An error occurred: {e}')
        import traceback
        traceback.print_exc()
        data['error'] = str(e)

    return JsonResponse(data)
# Save NEW General Details END

# Save OTHER MODIFICATION General Details START
def save_other_modification_general_details(request):
    data = {'message': 'failure'}
    try:
        post_data = request.POST
        session = request.session

        # Get the application number from POST data
        new_application_no = post_data.get('new_application_no')
        previous_ec_reference_no = post_data.get('previous_ec_reference_no')
        identifier = post_data.get('identifier')
        service_id = post_data.get('service_id')
        colour_code = post_data.get('colour_code')
        activity = post_data.get('activity')

        #print(f"DEBUG: application_no from POST: {application_no}, identifier: {identifier}")
        #print(f"DEBUG: Final application_no: {application_no}")

        # Check if application already exists
        existing_app = None
        if new_application_no:
            existing_app = t_ec_application_t1.objects.filter(
                application_no=new_application_no
            ).first()

        # Get location details
        if post_data.get('dzongkhag_throm') == 'Dzongkhag':
            dzongkhag_code = post_data.get('dzongkhag')
            gewog_code = post_data.get('gewog')
            village_code = post_data.get('vil_chiwog')
            thromde_id = None
        else:
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = post_data.get('thromde_id')

        # START Fetch Activity, Service, ca_auth from the existing record.
        # These values do not change during the draft application. Its already been selected and saved While saving the New Application
        activity_details = t_ec_t1.objects.filter(ec_reference_no=previous_ec_reference_no).first()
        other_modification_activity = activity_details.activity

        ca_details = t_bsic_code.objects.filter(activity=other_modification_activity).first()
        ca_auth = ca_details.competent_authority

        # Get service details
        if existing_app:
            # Use existing service details
            service_id = existing_app.service_id
            activity = existing_app.activity
            color_code = existing_app.colour_code
        else:
            # Use session/service defaults
            service_id = service_id
            activity = activity
            color_code = colour_code

        service_code = identifier

        if ca_auth =='DEC' and dzongkhag_code:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                dzongkhag_code_id=dzongkhag_code
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth
        elif ca_auth == 'THROMDE' and thromde_id:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                thromde_id_id=thromde_id
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth
        else:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth

        # Prepare data
        common_data = {
            'application_no': new_application_no,
            'application_date': timezone.now().date(),
            'application_type': identifier,
            'application_source': 'ECSS',
            'application_status': 'P',
            'applicant_id': session.get('email'),
            'applicant_name': post_data.get('applicant_name'),
            'address': post_data.get('address'),
            'cid': session.get('cid'),
            'contact_no': post_data.get('contact_no'),
            'email': post_data.get('email'),
            'focal_person': post_data.get('focal_person'),
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,
            'location_name': post_data.get('project_site'),
            'project_name': post_data.get('project_name'),
            'project_description': post_data.get('project_description'),
            'dzongkhag_throm': post_data.get('dzongkhag_throm'),
            'service_type': 'Main Activity',
            'service_id': service_id,
            'colour_code': color_code,
            'proponent_type': session.get('proponent_type'),
            'activity': activity,
            'prev_ec_reference_no': previous_ec_reference_no,
            'ca_authority': ca_auth_id,
            'app_remarks': post_data.get('app_remarks'),
            'cross_dzongkhag_locations': post_data.get('cross_dzongkhag_locations'),
        }

        with transaction.atomic():
            if existing_app:
                # UPDATE existing application
                #print(f"DEBUG: Updating application {application_no}")
                # Remove application_no from update data
                update_data = common_data.copy()
                del update_data['application_no']
                t_ec_application_t1.objects.filter(
                    application_no=new_application_no
                ).update(**update_data)
                t_workflow_dtls.objects.filter(
                    application_no=new_application_no
                ).update(ca_authority=ca_auth_id,)
            else:
                # CREATE new application (only if we don't have application_no)
                if not new_application_no:
                    # Generate new application number
                    # application_no = get_application_no(request, service_code, service_id)
                    new_application_no = get_new_application_no(request, service_code)
                    common_data['application_no'] = new_application_no
                print(f"DEBUG: Creating new application {new_application_no}")
                t_ec_application_t1.objects.create(**common_data)
                # Create workflow
                t_workflow_dtls.objects.create(
                    application_no=new_application_no,
                    service_id=service_id,
                    application_status='P',
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    assigned_role_id='3',
                    assigned_role_name='Reviewer',
                    ca_authority=ca_auth_id,
                    application_source='ECSS',
                    service_type=identifier,
                )
            # Save application number to session for future tabs
            if new_application_no:
                request.session['current_application_no'] = new_application_no
            # Create history
            t_application_history.objects.create(
                application_no=new_application_no,
                application_date=timezone.now().date(),
                applicant_id=session.get('email'),
                ca_authority=ca_auth_id,
                service_id=service_id,
                application_status='P',
                action_date=timezone.now(),
                actor_id=session.get('login_id'),
                actor_name=session.get('name'),
                remarks=None,
                status=None
            )
            data.update({
                'message': 'success',
                'new_application_no': new_application_no
            })
    except Exception as e:
        print(f'An error occurred: {e}')
        import traceback
        traceback.print_exc()
        data['error'] = str(e)
    return JsonResponse(data)
# Save OTHER MODIFICATION General Details END

# Save DRAFT General Details START
def save_draft_general_details(request):
    data = {'message': 'failure'}
    try:
        post_data = request.POST
        session = request.session

        application_no = post_data.get('application_no')
        if not application_no:
            return JsonResponse({'message': 'failure', 'error': 'Application number missing'}, status=400)

        # 1. Get location details efficiently
        dzongkhag_throm = post_data.get('dzongkhag_throm')
        if dzongkhag_throm == 'Dzongkhag':
            dzongkhag_code = post_data.get('dzongkhag')
            gewog_code = post_data.get('gewog')
            village_code = post_data.get('vil_chiwog')
            thromde_id = None
        else:
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = post_data.get('thromde_id')

        # 2. Optimized Fetch Activity & Authority (One step further: check if they exist)
        # Using .values() to avoid overhead of model instances
        app_info = t_ec_application_t1.objects.filter(application_no=application_no).values('activity').first()
        if not app_info:
            return JsonResponse({'message': 'failure', 'error': 'Application not found'}, status=404)

        draft_activity = app_info['activity']

        # Get the ca_auth string from basic code master
        ca_auth = t_bsic_code.objects.filter(activity=draft_activity).values_list('competent_authority',
                                                                                  flat=True).first()

        # 3. Determine competent authority ID (Optimized lookup like Version 1)
        ca_auth_id = ca_auth  # Fallback

        if ca_auth:
            query = t_competant_authority_master.objects.filter(competent_authority=ca_auth)

            if ca_auth == 'DEC' and dzongkhag_code:
                query = query.filter(dzongkhag_code_id=dzongkhag_code)
            elif ca_auth == 'THROMDE' and thromde_id:
                query = query.filter(thromde_id_id=thromde_id)

            auth_id_record = query.values_list('competent_authority_id', flat=True).first()
            if auth_id_record:
                ca_auth_id = auth_id_record

        # 4. Prepare data for update
        update_data = {
            'focal_person': post_data.get('focal_person'),
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,
            'location_name': post_data.get('project_site'),
            'cross_dzongkhag_locations': post_data.get('cross_dzongkhag_locations'),
            'project_name': post_data.get('project_name'),
            'project_description': post_data.get('project_description'),
            'app_remarks': post_data.get('app_remarks'),
            'dzongkhag_throm': dzongkhag_throm,
            'ca_authority': ca_auth_id
        }

        with transaction.atomic():
            # Perform updates
            t_ec_application_t1.objects.filter(application_no=application_no).update(**update_data)

            t_workflow_dtls.objects.filter(application_no=application_no).update(ca_authority=ca_auth_id)

        data.update({
            'message': 'success',
            'application_no': application_no
        })
        return JsonResponse(data, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        data['error'] = str(e)
        return JsonResponse(data, status=500)
# Save DRAFT General Details END

def save_general_attachment(request):
    data = dict()

    if 'general_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    general_attach = request.FILES['general_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    service_code = None
    if request.session['service_id'] == 1:
        service_code = 'IEE'
    elif request.session['service_id'] == 2:
        service_code = 'ENE'
    elif request.session['service_id'] == 3:
        service_code = 'ROA'
    elif request.session['service_id'] == 4:
        service_code = 'TRA'
    elif request.session['service_id'] == 5:
        service_code = 'TOU'
    elif request.session['service_id'] == 6:
        service_code = 'GWA'
    elif request.session['service_id'] == 7:
        service_code = 'FOR'
    elif request.session['service_id'] == 8:
        service_code = 'QUA'
    else:
        service_code = 'GEN'

    file_name = f"{app_no}_{general_attach.name}"
    year = timezone.now().year

    fs = FileSystemStorage(location=f"attachments/{year}/{service_code}")

    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = f"attachments/{year}/{service_code}/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)

def save_general_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
    service_code = None
    if request.session['service_id'] == 1:
        service_code = 'IEE'
    elif request.session['service_id'] == 2:
        service_code = 'ENE'
    elif request.session['service_id'] == 3:
        service_code = 'ROA'
    elif request.session['service_id'] == 4:
        service_code = 'TRA'
    elif request.session['service_id'] == 5:
        service_code = 'TOU'
    elif request.session['service_id'] == 6:
        service_code = 'GWA'
    elif request.session['service_id'] == 7:
        service_code = 'FOR'
    elif request.session['service_id'] == 8:
        service_code = 'QUA'
    else :
        service_code = 'GEN'

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type=service_code)
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type=service_code)

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})


def check_file_attachment(request):
    data = dict()
    application_no = request.GET.get('application_no')
    file_count = t_file_attachment.objects.filter(application_no=application_no).count()
    data['file_count'] = file_count
    return JsonResponse(data)

def delete_application_attachment(request):
    file_id = request.POST.get('file_id')
    identifier = request.POST.get('attachment_type')
    application_no = request.POST.get('application_no')

    if identifier == 'GEN':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            file_n = f"{application_no}_{file_name}"
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GEN/")
            fs.delete(str(file_n))
        file.delete()
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
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TOR/")
            fs.delete(str(file_name))
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
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})


def submit_general_application(request):
    try:
        application_no = request.POST.get('general_disclaimer_application_no')
        if not application_no:
            return JsonResponse({'error': 'Missing application number'}, status=400)

        email = request.session.get('email')
        name = request.session.get('name', '')
        if not email:
            return JsonResponse({'error': 'Missing email in session'}, status=400)

        now = timezone.now()

        with transaction.atomic():
            # Get and update application
            application = t_ec_application_t1.objects.get(application_no=application_no)
            application.action_date = now
            application.save(update_fields=['action_date'])

            # Update workflow
            t_workflow_dtls.objects.filter(
                application_no=application_no
            ).update(action_date=now)

            # Update application history
            t_application_history.objects.filter(
                application_no=application_no
            ).update(remarks='Application Submitted', action_date=now)

            # Send email after successful commit
            transaction.on_commit(lambda: threading.Thread(
                target=_send_submit_email_in_background,
                args=(name, email, application_no),
                daemon=True
            ).start())

        return JsonResponse({'message': 'success'})

    except t_ec_application_t1.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=400)
    except Exception as exc:
        return JsonResponse({'error': str(exc).splitlines()[0]}, status=500)

def _send_submit_email_in_background(name, email_id, application_no):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_submit_application_mail(name, email_id, application_no)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_submit_application_mail(name, email_id, application_no):
    subject = "Application Submitted"
    message = (
        f"Dear {name},\n\n"
        f"Your Environment Clearance application has been submitted successfully.\n"
        f"Your application number is: {application_no}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )

def _send_submit_email_in_background_tor(name, email, application_no):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_submit_tor_mail(name, email, application_no)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_submit_tor_mail(name, email, application_no):
    subject = "Application Submitted"
    message = (
        f"Dear {name},\n\n"
        f"Your TOR application has been submitted successfully.\n"
        f"Your application number is: {application_no}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )

def _send_submit_renewal_email_in_background(name, email_id, application_no):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_submit_renewal_application_mail(name, email_id, application_no)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_submit_renewal_application_mail(name, email_id, application_no):
    subject = "Application Submitted"
    message = (
        f"Dear {name},\n\n"
        f"Your Environment Clearance Renewal Application has been submitted successfully.\n"
        f"Your application number is: {application_no}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )


## NDI IMPLEMENTATION START
# Set up logging
#logger = logging.getLogger(__name__)

def proof_request(request):
    category = request.GET.get('category', '')

    if category == 'Login':
        purpose = 'login'
    else:
        purpose = 'ekyc'

    try:
        # Invalidate existing session and create a new session
        session_id = request.session.session_key
        if session_id:
            request.session.flush()
            request.session.create()

        request.session.create()  # Create a new session
        new_session_id = request.session.session_key

        # Get NDI access token
        ndi_token = get_access_token_ndi()

        # Define verifier API URL and headers
        verifier_api_url = 'https://demo-client.bhutanndi.com/verifier/v1/proof-request'
        headers = {'Authorization': f"Bearer {ndi_token}", 'Content-Type': 'application/json'}

        # Define proof request data
        proof_attributes = [
            {
                'name': "ID Number",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/c7952a0a-e9b5-4a4b-a714-1e5d0a1ae076"
                    }
                ]
            }
        ]
        proof_data = {
            'proofName': 'ECSS Credentials',
            'proofAttributes': proof_attributes
        }

        # Make request to verifier API
        response = requests.post(verifier_api_url, headers=headers, data=json.dumps(proof_data), verify=False)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        logger.debug(f"Proof request response: {response_data}")

        # Get the thread_id from the response
        thread_id = response_data.get('data', {}).get('proofRequestThreadId', '')

        # Insert the new session_id and thread_id into the database
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO proponent_t_ndi_login_temp (session_id, thread_id, category, created_date) VALUES (%s, %s, %s, CURRENT_DATE)",
                [new_session_id, thread_id, category]
            )

        # Include session_id in the response data
        response_data['session_id'] = new_session_id

        return JsonResponse(response_data)
    except requests.RequestException as e:
        logger.error(f"Error making request to verifier API: {e}")
        return JsonResponse({'error': 'Error making request to verifier API'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': 'Unexpected error occurred'}, status=500)


def proof_request_employee(request):
    category = request.GET.get('category', '')

    try:
        # Invalidate existing session and create a new session
        session_id = request.session.session_key
        if session_id:
            request.session.flush()
            request.session.create()

        request.session.create()  # Create a new session
        new_session_id = request.session.session_key

        # Get NDI access token
        ndi_token = get_access_token_ndi()

        # Define verifier API URL and headers
        verifier_api_url = 'https://demo-client.bhutanndi.com/verifier/v1/proof-request'
        headers = {'Authorization': f"Bearer {ndi_token}", 'Content-Type': 'application/json'}

        # Define proof request data
        proof_attributes = [
            {
                'name': "EID",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/2f528ccc-d42f-4760-9758-625580ec2bf8"
                    }
                ]
            }
        ]
        proof_data = {
            'proofName': 'ECSS Credentials',
            'proofAttributes': proof_attributes
        }

        # Make request to verifier API
        response = requests.post(verifier_api_url, headers=headers, data=json.dumps(proof_data), verify=False)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        logger.debug(f"Proof request response: {response_data}")

        # Get the thread_id and revocation_id from the response
        thread_id = response_data.get('data', {}).get('proofRequestThreadId', '')
        revocation_id = response_data.get('data', {}).get('revocationId', '')

        # Insert the new session_id, thread_id, and revocation_id into the database
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO proponent_t_ndi_login_temp (session_id, thread_id, revocation_id, category, created_date) VALUES (%s, %s, %s, %s, CURRENT_DATE)",
                [new_session_id, thread_id, revocation_id, category]
            )

        # Include session_id in the response data
        response_data['session_id'] = new_session_id

        return JsonResponse(response_data)

    except requests.RequestException as e:
        logger.error(f"Error making request to verifier API: {e}")
        return JsonResponse({'error': 'Error making request to verifier API'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': 'Unexpected error occurred'}, status=500)

def fetch_relationship_data(request,thread_id):
    ndi_token = get_access_token_ndi()
    print(f"Received thread_id: {thread_id}")
    
    if not thread_id:
        return JsonResponse({'error': 'thread_id parameter is required'}, status=400)
    
    # Define verifier API URL and headers
    verifier_api_url = f'https://demo-client.bhutanndi.com/verifier/v1/proof-request?threadId={thread_id}'
    print(f"API URL: {verifier_api_url}")
    
    headers = {'Authorization': f"Bearer {ndi_token}", 'Content-Type': 'application/json'}
    
    response = requests.get(verifier_api_url, headers=headers, verify=False)
    print(f"API Response status code: {response.status_code}")
    
    # Check if the request was successful
    if response.status_code == 200:
        try:
            response_data = response.json()
            print(f"Response data: {response_data}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return JsonResponse({'error': 'Invalid JSON response from verifier API'}, status=500)
        
        # Check if 'data' key exists and is a dictionary
        if 'data' in response_data and isinstance(response_data['data'], dict):
            relationship_did = response_data['data'].get('relationshipDid')
            status = response_data['data'].get('status')
            print(f"relationshipDid: {relationship_did}, status: {status}")
            
            if relationship_did:
                request.session['relationship_did'] = relationship_did
                print(f"relationshipDid found: {relationship_did}")
                return JsonResponse({'relationshipDid': relationship_did, 'status': status})
            else:
                print("No 'relationshipDid' found in data")
                return JsonResponse({'error': 'No relationshipDid found in the response data'}, status=500)
        else:
            print("Invalid response structure")
            return JsonResponse({'error': 'Invalid response structure from verifier API'}, status=500)
    else:
        # Handle error response
        print(f"Error fetching data: {response.status_code}")
        return JsonResponse({'error': 'Failed to fetch data from verifier API'}, status=response.status_code)

def proof_request_proponent(request):
    category = request.GET.get('category', '')  # Get the category from query parameters

    try:
        # Invalidate existing session and create a new session
        session_id = request.session.session_key
        if session_id:
            request.session.flush()
            request.session.create()

        request.session.create()  # Create a new session
        new_session_id = request.session.session_key

        # Get NDI access token
        ndi_token = get_access_token_ndi()

        # Define verifier API URL and headers
        verifier_api_url = 'https://demo-client.bhutanndi.com/verifier/v1/proof-request'
        headers = {'Authorization': f"Bearer {ndi_token}", 'Content-Type': 'application/json'}

        # Define proof request data
        proof_attributes = [
            {
                'name': "ID Number",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/c7952a0a-e9b5-4a4b-a714-1e5d0a1ae076"
                    }
                ]
            },
            {
                'name': "Full Name",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/c7952a0a-e9b5-4a4b-a714-1e5d0a1ae076"
                    }
                ]
            },
            {
                'name': "Dzongkhag",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/e3b606d0-e477-4fc2-b5ab-0adc4bd75c54"
                    }
                ]
            },
            {
                'name': "Gewog",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/e3b606d0-e477-4fc2-b5ab-0adc4bd75c54"
                    }
                ]
            },
            {
                'name': "Village",
                'restrictions': [
                    {
                        "schema_name": "https://dev-schema.ngotag.com/schemas/e3b606d0-e477-4fc2-b5ab-0adc4bd75c54"
                    }
                ]
            }
        ]
        proof_data = {
            'proofName': 'ECSS Credentials',
            'proofAttributes': proof_attributes
        }

        # Make request to verifier API with proof data
        response = requests.post(verifier_api_url, headers=headers, data=json.dumps(proof_data), verify=False)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        logger.debug(f"Proof request response: {response_data}")

        # Get the thread_id from the response
        thread_id = response_data.get('data', {}).get('proofRequestThreadId', '')

        # Insert the new session_id, thread_id, and category into the database
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO proponent_t_ndi_login_temp (session_id, thread_id, category, created_date) VALUES (%s, %s, %s, CURRENT_DATE)",
                [new_session_id, thread_id, category]
            )

        # Include session_id in the response data
        response_data['session_id'] = new_session_id

        return JsonResponse(response_data)

    except requests.RequestException as e:
        logger.error(f"Error making request to verifier API: {e}")
        return JsonResponse({'error': 'Error making request to verifier API'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': 'Unexpected error occurred'}, status=500)

from django.views.decorators.http import require_GET

@require_GET
def fetch_verified_user_data(request):
    data = dict()
    thread_id = request.GET.get('thread_id')
    value = request.GET.get('value')
    request.session['thread_id'] = thread_id
    request.session['value'] = value
    print(f"Value in fetch: {value}")
    BASE_URL = 'https://demo-client.bhutanndi.com/webhook/v1/subscribe/'
    token = get_access_token_ndi()
    print(token)
    headers = {
        'Authorization': f"Bearer {token}",
    }
    post_data = {
        "webhookId": "ecsstagingwebhookIdthree",
        "threadId": thread_id
    }

    try:
        res = requests.post(BASE_URL, json=post_data, headers=headers, verify=False, timeout=15)
        res.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
        response_data = res.json()
        print("fetch verified data:", response_data)
        
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "The request timed out. Please try again later."}, status=504)
    except requests.exceptions.HTTPError as e:
        return JsonResponse({"error": f"HTTP error occurred: {str(e)}"}, status=res.status_code)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Request exception: {str(e)}"}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON response from the server."}, status=500)

    return JsonResponse(response_data, safe=False)

@csrf_exempt
def webhook(request):

    print("Inside Webhook")

    try:

        cleaned_body = request.body.decode('utf-8')
        data = json.loads(cleaned_body)

        requested_presentation = data.get('requested_presentation', {})
        revealed_attrs = requested_presentation.get('revealed_attrs', {})

        id_number = revealed_attrs.get('ID Number', [{}])[0].get('value', '1111')

        eid = revealed_attrs.get('EID', [{}])[0].get('value', None)

        full_name = revealed_attrs.get('Full Name', [{}])[0].get('value', None)

        relationshipDid = data.get('relationship_did')

        thid = data.get('thid')

        holder_did = data.get('holder_did')

        proof_type = data.get('type')

        if not thid:
            return JsonResponse(
                {
                    "statusCode": "400",
                    "statusDescription": "Missing thread id"
                },
                status=400
            )

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT category, session_id, is_used
                FROM proponent_t_ndi_login_temp
                WHERE thread_id = %s
            """, [thid])

            row = cursor.fetchone()

            if not row:

                return JsonResponse(
                    {
                        "statusCode": "400",
                        "statusDescription": "Session not found"
                    },
                    status=400
                )

            category, session_id, is_used = row

            if is_used == 'Y':

                return JsonResponse(
                    {
                        "statusCode": "403",
                        "statusDescription": "Request already consumed"
                    },
                    status=403
                )

            payload = {
                'type': 'send_id_number',
                'id_number': id_number,
                'eid': eid,
                'full_name': full_name,
                'relationshipDid': relationshipDid,
                'thid': thid,
                'holder_did': holder_did,
                'category': category,
                'session_id': session_id,
                'proof_type': proof_type
            }

            # Add optional fields
            dzongkhag = revealed_attrs.get('Dzongkhag', [{}])[0].get('value')

            gewog = revealed_attrs.get('Gewog', [{}])[0].get('value')

            village = revealed_attrs.get('Village', [{}])[0].get('value')

            if dzongkhag:
                payload['dzongkhag'] = dzongkhag

            if gewog:
                payload['gewog'] = gewog

            if village:
                payload['village'] = village

            # Remove None values
            payload = {
                k: v for k, v in payload.items()
                if v is not None
            }

            print("Payload to WebSocket:", payload)

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f'ndi_{thid}',
                payload
            )

            """
            Mark request consumed
            """

            cursor.execute("""
                UPDATE proponent_t_ndi_login_temp
                SET is_used = 'Y'
                WHERE thread_id = %s
            """, [thid])

        return JsonResponse(
            {
                "statusCode": "202",
                "statusDescription": "Accepted"
            },
            status=202
        )

    except KeyError as e:

        print(f"KeyError: {e}")

        return JsonResponse(
            {
                "statusCode": "400",
                "statusDescription": "Invalid request payload"
            },
            status=400
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "statusCode": "400",
                "statusDescription": "Invalid JSON"
            },
            status=400
        )

    except Exception as e:

        print(f"Unexpected Error: {e}")

        return JsonResponse(
            {
                "statusCode": "500",
                "statusDescription": "Internal Server Error"
            },
            status=500
        )

def ndi_dash(request):
    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        print(f"ID Number received: {id_number}")

        check_user = t_user_master.objects.filter(cid=id_number, is_active='Y', logical_delete='N').first()

        if check_user is not None:
            print(f"User found: {check_user.login_id}")
            request.session['login_id'] = check_user.login_id
            request.session['email'] = check_user.email_id
            request.session['login_type'] = check_user.login_type

            if check_user.login_type == 'I':
                role_details = t_role_master.objects.filter(role_id=check_user.role_id_id).first()
                if role_details:
                    request.session['name'] = check_user.name
                    request.session['role'] = role_details.role_name
                    request.session['ca_authority'] = check_user.agency_code
                    request.session['dzongkhag_code'] = check_user.dzongkhag_code
                    return JsonResponse({'redirect': 'dashboard'})
            else:
                request.session['name'] = check_user.proponent_name
                request.session['address'] = check_user.address
                request.session['contact_number'] = check_user.contact_number
                if check_user.proponent_type == 4:
                    request.session['cid'] = check_user.cid
                else:
                    request.session['cid'] = None
                return JsonResponse({'redirect': 'dashboard'})
        else:
            _message = 'ID Not Found'
            print(_message)
            context = {'message': _message}
            return JsonResponse({'redirect': 'index', 'message': _message})
    else:
        _message = 'Please sign in'
        print(_message)
        context = {'message': _message}
        return JsonResponse({'redirect': 'index', 'message': _message})

def ndi_dash_eid(request):
    if request.method == 'POST':
        eid = request.POST.get('eid')
        print(f"EID Number received: {eid}")

        check_user = t_user_master.objects.filter(employee_id=eid, is_active='Y', logical_delete='N').first()

        if check_user is not None:
            print(f"User found: {check_user.login_id}")

            request.session['login_id'] = check_user.login_id
            request.session['email'] = check_user.email_id
            request.session['login_type'] = check_user.login_type

            if check_user.login_type == 'I':
                role_details = t_role_master.objects.filter(role_id=check_user.role_id_id).first()
                if role_details:
                    request.session['name'] = check_user.name
                    request.session['role'] = role_details.role_name
                    request.session['ca_authority'] = check_user.agency_code
                    request.session['dzongkhag_code'] = check_user.dzongkhag_code
                    return JsonResponse({'redirect': 'dashboard'})
            else:
                request.session['name'] = check_user.proponent_name
                request.session['address'] = check_user.address
                request.session['contact_number'] = check_user.contact_number
                return JsonResponse({'redirect': 'dashboard'})
        else:
            _message = 'ID Not Found'
            print(_message)
            context = {'message': _message}
            return JsonResponse({'redirect': 'index', 'message': _message})
    else:
        _message = 'Please sign in'
        print(_message)
        context = {'message': _message}
        return JsonResponse({'redirect': 'index', 'message': _message})


def update_password_ndi(request):
    # Fetch security questions for the form
    #print('inside update_password def')
    security_questions = t_security_question_master.objects.all()
    context = {'security': security_questions}
    return render(request, 'update_password.html', context)

@csrf_exempt
def issuance_call(request):
    try:
        # Extract parameters from the request
        id_number = request.POST.get('id_number')
        print(id_number)
        holder_did = request.POST.get('holder_did')
        relationshipDid = request.POST.get('relationshipDid')

        if not id_number or not holder_did or not relationshipDid:
            return JsonResponse({'error': 'Missing required parameters: id_number, holder_did, or relationshipDid'}, status=400)

        # Log the inputs
        print(f"id_number: {id_number}, holder_did: {holder_did}, relationshipDid: {relationshipDid}")

        # Get NDI access token
        ndi_token = get_access_token_ndi()
        if not ndi_token:
            return JsonResponse({'error': 'Failed to retrieve NDI access token'}, status=500)

        # Fetch application details in a single query
        application_details = t_ec_application_t1.objects.filter(cid=id_number, application_status='A')

        if not application_details.exists():
            return JsonResponse({'error': 'No application details found for the provided ID number'}, status=404)

        # Check if revocation is required
        requires_revocation = application_details.filter(revocation_id__isnull=False, is_revoked__isnull=True).exists()

        if requires_revocation:
            revocation_response = revoke_vc(request, id_number)
            if revocation_response.status_code != 201:
                return JsonResponse({
                    'error': 'Failed to revoke existing credential. Issuance aborted.',
                    'details': revocation_response.json()
                }, status=revocation_response.status_code)

        credentials_issued = []

        # Prepare headers for issuing credentials
        issue_url = "https://demo-client.bhutanndi.com/issuer/v1/issue-credential"
        headers = {
            'Authorization': f"Bearer {ndi_token}",
            'Content-Type': 'application/json'
        }

        with transaction.atomic():
            for application_detail in application_details:
                try:
                    # Prepare credential data
                    credential_data = {
                        "EC Reference Number": application_detail.ec_reference_no,
                        "EC Approve Date": application_detail.ec_approve_date.isoformat(),
                        "EC Expiry Date": application_detail.ec_expiry_date.isoformat(),
                        "EC Status": "A",
                        "Applicant Name": str(application_detail.applicant_name),
                        "Project Name": str(application_detail.project_name),
                        "Address": str(application_detail.address),
                        "Location Name": str(application_detail.location_name),
                        "Total Area Acre": str(application_detail.total_area_acre)
                    }

                    proof_data = {
                        "schemaId": "https://dev-schema.ngotag.com/schemas/33f8b16a-303e-4e49-b3b2-2b5256336029",
                        "credentialData": credential_data,
                        "holderDID": holder_did,
                        "forRelationship": relationshipDid
                    }

                    # Issue credential via API
                    response = requests.post(issue_url, headers=headers, data=json.dumps(proof_data))

                    if response.status_code == 201:
                        response_data = response.json()
                        revocation_id = response_data['data'].get('revocationId')

                        if revocation_id:
                            application_detail.revocation_id = revocation_id
                            application_detail.save()

                        credentials_issued.append(
                            f"Credential for EC Reference Number {application_detail.ec_reference_no} issued successfully"
                        )
                    else:
                        # Rollback transaction on failure
                        raise Exception(f"Failed to issue credential: {response.json()}")

                except Exception as e:
                    print(f"Error issuing credential for {application_detail.ec_reference_no}: {e}")
                    return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'message': 'Credentials issued successfully', 'details': credentials_issued}, status=201)

    except Exception as e:
        print(f"Exception occurred: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.', 'details': str(e)}, status=500)


def revoke_vc(request, id_number):
    issuance_detail = t_ec_application_t1.objects.filter(
        cid=id_number, application_status='A', revocation_id__isnull=False
    ).first()

    if not issuance_detail:
        return JsonResponse({'error': 'No credential found to revoke.'}, status=404)

    revocation_id = issuance_detail.revocation_id
    ndi_token = get_access_token_ndi()
    url = 'https://demo-client.bhutanndi.com/issuer/v1/revoke_suspend'
    params = {
        'status': 'REVOKED',
        'revocationId': revocation_id
    }
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {ndi_token}',
    }

    response = requests.post(url, headers=headers, params=params)

    return response

def revoke_ec(request):
    revocation_id = request.POST.get('revocation_id')
    print(f"REVOCATION ID: {revocation_id}")
    
    if not revocation_id:
        return JsonResponse({'error': 'Revocation ID is required'}, status=400)

    ndi_token = get_access_token_ndi()

    url = 'https://demo-client.bhutanndi.com/issuer/v1/revoke_suspend'
    params = {
        'status': 'REVOKED',
        'revocationId': revocation_id
    }
    headers = {
        'accept': '*/*',
        'Authorization': f'Bearer {ndi_token}',
    }
    app_details = t_ec_application_t1.objects.filter(revocation_id=revocation_id)
    app_details.update(is_revoked='Y')
    response = requests.post(url, headers=headers, params=params)

    if response.status_code == 201:
        return JsonResponse({'message': 'Revocation successful', 'data': response.json()})
    elif response.status_code == 403:
        return JsonResponse({'error': 'Forbidden', 'details': response.text}, status=403)
    else:
        return JsonResponse({'error': 'Failed to revoke credential', 'details': response.json()}, status=response.status_code)
    
def get_access_token_ndi():
    authApiUrl = 'https://staging.bhutanndi.com/authentication/v1/authenticate';
    clientId = '3tq7ho23g5risndd90a76jre5f';
    clientSecret = '111rvn964mucumr6c3qq3n2poilvq5v92bkjh58p121nmoverquh';

    credentials = {
        'client_id': clientId,
        'client_secret': clientSecret,
        'grant_type': 'client_credentials'
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post(authApiUrl, data=credentials, headers=headers, verify=False)

    json_response = res.json()
    #print(json_response)
    return json_response['access_token']



# Draft Application Details
def draft_application_list(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    identifier = request.GET.get('identifier')

    #application_details = t_ec_application_t1.objects.filter(applicant_id=applicant_id,application_status='P',service_type='Main Activity',action_date__isnull=True)
    # -----------------------------
    # Application details based on identifier
    # -----------------------------
    if identifier == 'OLD':
        application_details = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id,
            #application_status='R',
            application_status__in=['P', 'RS'],
            application_type='Old_EC',
            #action_date__isnull=True
        ).order_by('-record_id')
        template_name = 'pending_old_ec_list.html'
    else:  # NEW
        application_details = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id,
            application_status='P',
            application_type__in=["New", "TC", "PC", "CC", "AC", "LC"],
            action_date__isnull=True
        ).order_by('-record_id')
        template_name = 'draft_application_list.html'

    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()
    
    response = render(request, template_name,{'application_details':application_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'service_details':service_details, 'tor_application_count':tor_application_count, 'draft_count':draft_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_draft_application_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    applicant_id = request.session.get('email', None)
    assigned_user_id = request.session.get('login_id', None)
    service_id = request.GET.get('service_id')

    request.session['service_id'] = service_id

    service_master = t_service_master.objects.filter(
        service_id=service_id
    ).first()

    attachments = service_master.attachments if service_master else ''
    request.session['attachments'] = attachments

    # Fetch common data
    application_details = t_ec_application_t1.objects.filter(application_no=application_no, service_type='Main Activity')
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    # Badge COUNT START
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=applicant_id
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()
    # Badge COUNT END
    context = {
        'thromde': thromde,
        'application_details': application_details,
        'application_no': application_no,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'service_id': service_id,
        'file_attach':file_attach,
        'ec_renewal_count': ec_renewal_count,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'tor_application_count': tor_application_count,
        'draft_count': draft_count,
        'attachment_type':file_attach.first().attachment_type if file_attach.exists() else 'GEN'

    }

    return render(request, 'draft_application_details.html', context)

    #DELETE DRAFT APPLICATION start
def delete_draft_application(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    service_id = request.GET.get('service_id')

    try:
        # Delete related file attachments
        t_file_attachment.objects.filter(application_no=application_no).delete()

        # Delete the main application records
        t_ec_application_t1.objects.filter(
            application_no=application_no
        ).delete()

        # Clear session data
        if request.session.get('application_no') == application_no:
            del request.session['application_no']
        if request.session.get('service_id') == service_id:
            del request.session['service_id']
        if 'attachments' in request.session:
            del request.session['attachments']

        # ✅ CORRECT: Build URL first, then redirect
        url = reverse('draft_application_list') + '?identifier=NEW'
        return redirect(url)

    except Exception as e:
        print(f"Error deleting application: {e}")
        url = reverse('draft_application_list') + '?identifier=NEW'
        return redirect(url)
    #OLD EC APPLICATION LIST start

def old_ec_application_list(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    identifier = request.GET.get('identifier')

    # application_details = t_ec_application_t1.objects.filter(applicant_id=applicant_id,application_status='SM',service_type='Main Activity')
    # -----------------------------SM- Submitted
    # Application details based on identifier
    # -----------------------------

    application_details = t_ec_application_t1.objects.filter(
        ca_authority=request.session['ca_authority'],
        application_status='SM',
        application_type='Old_EC'
    ).order_by('-record_id')
    template_name = 'verifier_old_ec_list.html'

    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=applicant_id
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    )

    non_updated_renewals = t_ec_t1.objects.filter(
        applicant_id=request.session['email'],
        service_type__in=["Main Activity", "Old EC"],
        ec_expiry_date__lt=expiry_date_threshold,
    ).filter(
        Exists(renewal_exists)
    )

    ec_renewal_count = non_updated_renewals.count()
    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    response = render(request, template_name,
                      {'application_details': application_details, 'ec_renewal_count': ec_renewal_count,
                       'app_hist_count': app_hist_count, 'cl_application_count': cl_application_count,
                       'service_details': service_details, 'tor_application_count': tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def view_old_ec_application_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    service_id = request.GET.get('service_id') or request.session.get('service_id')
    request.session['service_id'] = service_id

    # Fetch common data
    application_details = t_ec_application_t1.objects.filter(application_no=application_no,
                                                                    service_type='Main Activity')
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()

    context = {
        'thromde': thromde,
        'application_details': application_details,
        'application_no': application_no,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'service_id': service_id,
        'file_attach': file_attach
    }

    return render(request, 'draft_application_details.html', context)


def view_verifier_pending_old_ec_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    service_id = request.GET.get('service_id') or request.session.get('service_id')
    request.session['service_id'] = service_id

    # Fetch common data
    application_details = t_ec_application_t1.objects.filter(application_no=application_no,
                                                                    service_type='Main Activity')
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()

    context = {
        'thromde': thromde,
        'application_details': application_details,
        'application_no': application_no,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'service_id': service_id,
        'file_attach': file_attach
    }

    return render(request, 'verifier_old_ec_details.html', context)

#OLD EC APPLICATION LIST end

def view_pending_old_ec_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    service_id = request.GET.get('service_id') or request.session.get('service_id')
    request.session['service_id'] = service_id

    # Fetch common data
    application_details = t_ec_application_t1.objects.filter(application_no=application_no,
                                                                    service_type='Main Activity')
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()

    context = {
        'thromde': thromde,
        'application_details': application_details,
        'application_no': application_no,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'service_id': service_id,
        'file_attach': file_attach
    }

    return render(request, 'pending_old_ec_details.html', context)

def ec_renewal(request):
    applicant_id = request.session.get('email')
    login_id = request.session.get('login_id')
    if not applicant_id:
        return redirect('login')

    threshold_date = date.today() + timedelta(days=60)
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # -----------------------------------
    # Subquery: renewal exists AND is NOT approved
    # -----------------------------------
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(application_status='A')

    # -----------------------------------
    # ECs expiring soon & NOT pending renewal
    # -----------------------------------
    application_details = (
        t_ec_t1.objects
        .filter(
            applicant_id=applicant_id,
            service_type__in=["Main Activity", "Old EC"],
            ec_reference_no__isnull=False,
            ec_reference_no__gt='',          # covers empty string
            ec_expiry_date__isnull=False,
            ec_expiry_date__lt=threshold_date,
            status='A',
        )
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
        .order_by('ec_expiry_date')
    )

    # -----------------------------------
    # Renewal details (pending only)
    # -----------------------------------
    renewal_details = t_ec_compliance.objects.filter(
        application_status__isnull=True
    )

    # -----------------------------------
    # Service master (static data)
    # -----------------------------------
    service_details = t_service_master.objects.all()

    # -----------------------------------
    # Application history count
    # -----------------------------------
    app_hist_count = (
        t_application_history.objects
        .filter(applicant_id=applicant_id)
        .values('application_no')
        .distinct()
        .count()
    )

    # -----------------------------------
    # TOR applications not yet converted
    # -----------------------------------
    tor_converted_exists = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    )

    tor_application_count = (
        t_ec_application_t1.objects
        .filter(
            applicant_id=applicant_id,
            application_status='A',
            application_no__contains='TOR',
        )
        .annotate(is_converted=Exists(tor_converted_exists))
        .filter(is_converted=False)
        .count()
    )

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    # Client application count
    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=login_id
    ).count()

    # -----------------------------------
    # Context
    # -----------------------------------
    context = {
        'application_details': application_details,
        'app_hist_count': app_hist_count,
        'renewal_details': renewal_details,
        'ec_renewal_count': ec_renewal_count,
        'cl_application_count': cl_application_count,
        'service_details': service_details,
        'draft_count': draft_count,
        'tor_application_count': tor_application_count,
        'threshold_date': threshold_date,
    }

    response = render(request, 'renewal.html', context)

    # Prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


def ec_renewal_details(request):
    applicant_id = request.session.get('email')
    ec_reference_no = request.GET.get('ec_reference_no')
    service_code = 'REN'
    temp_application_no = get_ren_temp_application_no(request, service_code, '10')

    # Parent EC applications (as you had)
    application_details = t_ec_t1.objects.filter(
        ec_reference_no=ec_reference_no, service_type="Main Activity"
    )

    # Fetch ALL EC terms for display (no DB writes here)
    ec_terms = t_ec_t2.objects.filter(
        ec_reference_no=ec_reference_no, ec_type='Terms'
    ).order_by('order')  # adjust ordering if needed (e.g., seq_no)

    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()

    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=request.session['login_id']
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    ec_renewal_count = non_updated_renewals.count()

    # Note: Do NOT create t_ec_compliance rows here.
    # Just pass ec_terms to the template for temporary display.
    return render(
        request,
        'renewal_details.html',
        {
            'application_details': application_details,
            'temp_application_no': temp_application_no,
            'ec_terms': ec_terms,  # pass terms for display
            'dzongkhag': dzongkhag,
            'gewog': gewog,
            'village': village,
            'thromde': thromde,
            'draft_count': draft_count,
            'app_hist_count': app_hist_count,
            'cl_application_count': cl_application_count,
            'ec_renewal_count': ec_renewal_count,
        }
    )

def submit_renew_application(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = {"message": "failure"}

    try:
        # Basic fields
        ec_reference_no = request.POST.get('ec_reference_no')
        temp_application_no = request.POST.get('temp_application_no')
        initiatives_undertaken = request.POST.get('initiatives_undertaken')
        initiatives_remarks = request.POST.get('initiatives_undertaken_remarks')
        name = request.session.get('name')
        email_id = request.session.get('email')
        service_code = 'REN'
        print(ec_reference_no, temp_application_no, initiatives_undertaken, initiatives_remarks, name, email_id, service_code, email_id, service_code)

        # Per-term arrays (may be empty if no EC terms exist)
        t2_record_ids = request.POST.getlist('t2_record_id[]')        # hidden record_id from t_ec_t2
        actions_list = request.POST.getlist('action_undertaken[]')    # action per term
        remarks_list = request.POST.getlist('remarks[]')              # remarks per term

        # Validate essentials (but NOT the presence of EC terms)
        #application_no = get_ren_application_no(request, service_code, '10')
        application_no = get_new_application_no(request, service_code)
        if not ec_reference_no or not application_no:
            return JsonResponse({"message": "Missing required fields"}, status=400)

        # Source application (copy static fields)
        application_details = (
            t_ec_t1.objects
            .filter(ec_reference_no=ec_reference_no)
            .first()
        )

        if not application_details:
            return JsonResponse({"message": "Invalid EC reference number"}, status=404)

        # ===== OPTIONAL VALIDATION: Only if terms were posted =====
        terms_map = {}
        if t2_record_ids:  # Only validate IF user posted term rows
            if not (len(t2_record_ids) == len(actions_list) == len(remarks_list)):
                return JsonResponse({"message": "Mismatched EC details arrays"}, status=400)

            # Fetch referenced t_ec_t2 rows by record_id (and ensure they belong to this EC)
            terms_qs = (
                t_ec_t2.objects
                .filter(record_id__in=t2_record_ids, ec_reference_no=ec_reference_no)  # , ec_type='Terms'
                .order_by('record_id')
            )
            terms_map = {str(t.record_id): t for t in terms_qs}
            if len(terms_map) != len(set(t2_record_ids)):
                return JsonResponse({"message": "Some EC term identifiers are invalid or do not match the EC reference"}, status=400)

        # If you still need to copy all terms into t_ec_application_t2
        ec_details_qs = (
            t_ec_t2.objects
            .filter(ec_reference_no=ec_reference_no)
            .order_by('record_id')
        )

        with transaction.atomic():
            # A) Create renewal record (parent) - ALWAYS HAPPENS
            t_ec_application_t1.objects.create(
                application_no=application_no,
                ec_reference_no=ec_reference_no,
                applicant_name=application_details.applicant_name,
                address=application_details.address,
                initiatives_undertaken=initiatives_undertaken,
                initiatives_remarks=initiatives_remarks,  # ensure field name matches your model
                applicant_id=application_details.applicant_id,
                service_id=application_details.service_id,
                application_date=timezone.now(),
                action_date=timezone.now(),
                application_status='P',
                application_type='Renewal',
                ca_authority=application_details.ca_authority,
                colour_code=application_details.colour_code,
                contact_no=application_details.contact_no,
                email=application_details.email,
                focal_person=application_details.focal_person,
                thromde_id=application_details.thromde_id,
                dzongkhag_code=application_details.dzongkhag_code,
                gewog_code=application_details.gewog_code,
                village_code=application_details.village_code,
                location_name=application_details.location_name,
                application_source=application_details.application_source,
                dzongkhag_throm=application_details.dzongkhag_throm,
                activity=application_details.activity,
                project_description=application_details.project_description,
                project_name=application_details.project_name,
                service_type=application_details.service_type,
                proponent_type=application_details.proponent_type,
                cid=application_details.cid
            )

            # B) Create workflow record - ALWAYS HAPPENS
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id='10',
                application_status='P',
                action_date=timezone.now(),
                actor_id=request.session.get('login_id'),
                actor_name=request.session.get('name'),
                assigned_role_id='3',
                assigned_role_name='Reviewer',
                ca_authority=application_details.ca_authority,
                application_source='ECSS',
                service_type="Renewal"
            )

            # C) (Optional) Copy ALL EC terms into application-specific table
            if ec_details_qs.exists():
                app_t2_rows = [
                    t_ec_application_t2(
                        application_no=application_no,
                        ec_type=ed.ec_type,
                        ec_heading=ed.ec_heading,
                        ec_terms=ed.ec_terms,
                        ec_reference_no=ec_reference_no,
                        order=ed.order,
                        # If t_ec_application_t2 has a record_id/seq_no, copy it too:
                        # record_id=ed.record_id,
                        # seq_no=ed.seq_no,
                    )
                    for ed in ec_details_qs
                ]
                t_ec_application_t2.objects.bulk_create(app_t2_rows, batch_size=1000)

            # D) Build compliance rows from posted arrays + server-fetched terms - ONLY IF POSTED
            if t2_record_ids:  # Only save compliance data if user posted any terms
                compliance_rows = []
                for rid, action_txt, remark_txt in zip(t2_record_ids, actions_list, remarks_list):
                    term = terms_map.get(str(rid))
                    if not term:
                        raise ValueError(f"Invalid EC term identifier: {rid}")

                    compliance_rows.append(
                        t_ec_compliance(
                            application_no=application_no,
                            ec_reference_no=ec_reference_no,
                            ec_heading=term.ec_heading,
                            ec_terms=term.ec_terms,
                            order=term.order,
                            # Ensure these names match your t_ec_compliance model:
                            action_undertaken=(action_txt or '').strip(),
                            remarks=(remark_txt or '').strip(),
                        )
                    )
                if compliance_rows:
                    t_ec_compliance.objects.bulk_create(compliance_rows, batch_size=1000)

            # E) Remap attachments from temp to final application_no - ALWAYS HAPPENS
            t_file_attachment.objects.filter(application_no=temp_application_no).update(
                application_no=application_no
            )

            # F) Send email after commit - ALWAYS HAPPENS
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_submit_renewal_email_in_background,
                    args=(name, email_id, application_no),
                    daemon=True
                ).start()
            )

        data["message"] = "success"
        return JsonResponse(data)

    except Exception as e:
        print("Submit renewal application error:", e)
        return JsonResponse({"message": "failure", "error": str(e)}, status=500)

def save_renew_attachment(request):
    data = dict()
    ea_attach = request.FILES['renewal_attach']
    file_name = ea_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECR/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ea_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/ECR" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_renew_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('temp_application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='ECR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECR')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def submit_oc_application(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = {"message": "failure"}

    try:
        # Basic fields
        ec_reference_no = request.POST.get('ec_reference_no')
        temp_application_no = request.POST.get('temp_application_no')
        applicant_focal_person = request.POST.get('applicant_focal_person')
        app_remarks = request.POST.get('app_remarks')
        name = request.session.get('name')
        email_id = request.session.get('email')
        service_code = 'OC'

        # Validate essentials
        #application_no = get_oc_application_no(request, service_code, '12')
        application_no = get_new_application_no(request, service_code)
        if not ec_reference_no or not application_no:
            return JsonResponse({"message": "Missing required fields"}, status=400)

        # Source application (copy static fields)
        application_details = (
            t_ec_t1.objects
            .filter(ec_reference_no=ec_reference_no)
            .first()
        )
        if not application_details:
            return JsonResponse({"message": "Invalid EC reference number"}, status=404)

        # Source applicant details
        applicant_details = (
            t_user_master.objects
            .filter(email_id=email_id)
            .first()
        )

        # Get all EC terms from original application
        ec_details_qs = (
            t_ec_t2.objects
            .filter(ec_reference_no=ec_reference_no)
            .order_by('record_id')
        )

        with transaction.atomic():
            # A) Create ownership change record (parent)
            t_ec_application_t1.objects.create(
                application_no=application_no,
                ec_reference_no=ec_reference_no,
                applicant_name=application_details.applicant_name,
                address=application_details.address,
                applicant_id=application_details.applicant_id,
                service_id=application_details.service_id,
                application_date=timezone.now(),
                action_date=timezone.now(),
                application_status='OC',
                application_type='OC',
                ca_authority=application_details.ca_authority,
                colour_code=application_details.colour_code,
                contact_no=application_details.contact_no,
                email=application_details.email,
                focal_person=application_details.focal_person,
                thromde_id=application_details.thromde_id,
                dzongkhag_code=application_details.dzongkhag_code,
                gewog_code=application_details.gewog_code,
                village_code=application_details.village_code,
                location_name=application_details.location_name,
                application_source=application_details.application_source,
                dzongkhag_throm=application_details.dzongkhag_throm,
                activity=application_details.activity,
                project_description=application_details.project_description,
                project_name=application_details.project_name,
                service_type=application_details.service_type,
                proponent_type=application_details.proponent_type,
                cid=application_details.cid,
                buyer_applicant_name=applicant_details.proponent_name,
                buyer_address=applicant_details.address,
                buyer_cid=applicant_details.cid,
                buyer_email=applicant_details.email_id,
                buyer_contact_no=applicant_details.contact_number,
                buyer_proponent_type=applicant_details.proponent_type,
                buyer_project_name=application_details.project_name,
                buyer_focal_person=applicant_focal_person,
                app_remarks=app_remarks,
                cross_dzongkhag_locations=application_details.cross_dzongkhag_locations,
            )

            # B) Create workflow record
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id='12',
                application_status='P',
                action_date=timezone.now(),
                actor_id=request.session.get('login_id'),
                actor_name=request.session.get('name'),
                assigned_role_id='3',
                assigned_role_name='Reviewer',
                ca_authority=application_details.ca_authority,
                application_source='ECSS',
                service_type="OC"
            )

            # C) Copy ALL EC terms into application-specific table
            if ec_details_qs.exists():
                app_t2_rows = [
                    t_ec_application_t2(
                        application_no=application_no,
                        ec_type=ed.ec_type,
                        ec_heading=ed.ec_heading,
                        ec_terms=ed.ec_terms,
                        ec_reference_no=ec_reference_no,
                        order=ed.order
                    )
                    for ed in ec_details_qs
                ]
                t_ec_application_t2.objects.bulk_create(app_t2_rows, batch_size=1000)

            # D) Remap attachments from temp to final application_no
            t_file_attachment.objects.filter(application_no=temp_application_no).update(
                application_no=application_no
            )

            # E) Send email after commit
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_submit_renewal_email_in_background,
                    args=(name, email_id, application_no),
                    daemon=True
                ).start()
            )

        data["message"] = "success"
        return JsonResponse(data)

    except Exception as e:
        print("Submit OC application error:", e)
        return JsonResponse({"message": "failure", "error": str(e)}, status=500)

def save_oc_attachment(request):
    data = dict()
    ea_attach = request.FILES['oc_attach']
    file_name = ea_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECOC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ea_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/ECOC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_oc_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('temp_application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='ECOC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECOC')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})


def oc_application(request):
    applicant_id = request.session.get('email', None)
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    oc_details = t_ec_application_t1.objects.filter(
        application_status='OC', application_type='OC', applicant_id=applicant_id
    )
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    service_details = t_service_master.objects.all()

    app_hist_count = t_application_history.objects.filter(
        applicant_id=applicant_id
    ).distinct('application_no').count()
    response = render(request, 'oc_request_list.html',
                      {'tor_application_count': tor_application_count, 'ec_renewal_count': ec_renewal_count,
                       'oc_details': oc_details, 'service_details': service_details, 'app_hist_count': app_hist_count,
                       'draft_count': draft_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_oc_application_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    applicant_id = request.session.get('email', None)
    assigned_user_id = request.session.get('login_id', None)
    service_id = request.GET.get('service_id')

    request.session['service_id'] = service_id

    service_master = t_service_master.objects.filter(
        service_id=service_id
    ).first()

    attachments = service_master.attachments if service_master else ''
    request.session['attachments'] = attachments

    # Fetch common data
    application_details = t_ec_application_t1.objects.filter(application_no=application_no)
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    # Badge COUNT START
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=applicant_id
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()
    # Badge COUNT END
    context = {
        'thromde': thromde,
        'application_details': application_details,
        'application_no': application_no,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'service_id': service_id,
        'file_attach':file_attach,
        'ec_renewal_count': ec_renewal_count,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'tor_application_count': tor_application_count,
        'draft_count': draft_count

    }

    return render(request, 'oc_application_details.html', context)



def oc_decide_application(request):
    try:
        application_no = request.POST.get('application_no')
        decision = request.POST.get('decision')

        if not application_no or decision not in ('accept', 'reject'):
            return JsonResponse(
                {'message': 'failure', 'error': 'Invalid payload'},
                status=400
            )

        status_map = {
            'accept': 'P',
            'reject': 'RJ'
        }
        new_status = status_map[decision]

        now = timezone.now()

        with transaction.atomic():
            updated_app = t_ec_application_t1.objects.filter(
                application_no=application_no
            ).update(application_status=new_status, action_date=now)

            updated_workflow = t_workflow_dtls.objects.filter(
                application_no=application_no
            ).update(application_status=new_status, action_date=now)

            if not updated_app and not updated_workflow:
                return JsonResponse(
                    {'message': 'failure', 'error': 'Application not found'},
                    status=404
                )

        return JsonResponse({'message': 'success', 'status': new_status})

    except Exception as e:
        return JsonResponse({'message': 'failure', 'error': str(e)}, status=500)

def submit_nc_application(request):
    if request.method != "POST":
        return JsonResponse({"message": "Method not allowed"}, status=405)

    data = {"message": "failure"}

    try:
        # Basic fields
        ec_reference_no = request.POST.get('ec_reference_no')
        temp_application_no = request.POST.get('temp_application_no')
        new_project_name = request.POST.get('new_project_name')
        app_remarks = request.POST.get('app_remarks')
        name = request.session.get('name')
        email_id = request.session.get('email')
        service_code = 'NC'

        # Validate essentials
        application_no = get_new_application_no(request, service_code)
        if not ec_reference_no or not application_no:
            return JsonResponse({"message": "Missing required fields"}, status=400)

        # Source application (copy static fields)
        application_details = (
            t_ec_t1.objects
            .filter(ec_reference_no=ec_reference_no)
            .first()
        )
        if not application_details:
            return JsonResponse({"message": "Invalid EC reference number"}, status=404)

        # Source applicant details
        applicant_details = (
            t_user_master.objects
            .filter(email_id=email_id)
            .first()
        )

        # Get all EC terms from original application
        ec_details_qs = (
            t_ec_t2.objects
            .filter(ec_reference_no=ec_reference_no)
            .order_by('record_id')
        )

        with transaction.atomic():
            # A) Create ownership change record (parent)
            t_ec_application_t1.objects.create(
                application_no=application_no,
                ec_reference_no=ec_reference_no,
                applicant_name=application_details.applicant_name,
                address=application_details.address,
                applicant_id=application_details.applicant_id,
                service_id=application_details.service_id,
                application_date=timezone.now(),
                action_date=timezone.now(),
                application_status='P',
                application_type='NC',
                ca_authority=application_details.ca_authority,
                colour_code=application_details.colour_code,
                contact_no=application_details.contact_no,
                email=application_details.email,
                focal_person=application_details.focal_person,
                thromde_id=application_details.thromde_id,
                dzongkhag_code=application_details.dzongkhag_code,
                gewog_code=application_details.gewog_code,
                village_code=application_details.village_code,
                location_name=application_details.location_name,
                cross_dzongkhag_locations=application_details.cross_dzongkhag_locations,
                application_source=application_details.application_source,
                dzongkhag_throm=application_details.dzongkhag_throm,
                activity=application_details.activity,
                project_description=application_details.project_description,
                project_name=application_details.project_name,
                service_type=application_details.service_type,
                proponent_type=application_details.proponent_type,
                cid=application_details.cid,
                new_project_name=new_project_name,
                app_remarks=app_remarks

            )

            # B) Create workflow record
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id='11',
                application_status='P',
                action_date=timezone.now(),
                actor_id=request.session.get('login_id'),
                actor_name=request.session.get('name'),
                assigned_role_id='3',
                assigned_role_name='Reviewer',
                ca_authority=application_details.ca_authority,
                application_source='ECSS',
                service_type="NC"
            )

            # C) Copy ALL EC terms into application-specific table
            if ec_details_qs.exists():
                app_t2_rows = [
                    t_ec_application_t2(
                        application_no=application_no,
                        ec_type=ed.ec_type,
                        ec_heading=ed.ec_heading,
                        ec_terms=ed.ec_terms,
                        ec_reference_no=ec_reference_no,
                        order=ed.order
                    )
                    for ed in ec_details_qs
                ]
                t_ec_application_t2.objects.bulk_create(app_t2_rows, batch_size=1000)

            # D) Remap attachments from temp to final application_no
            t_file_attachment.objects.filter(application_no=temp_application_no).update(
                application_no=application_no
            )

            # E) Send email after commit
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_submit_renewal_email_in_background,
                    args=(name, email_id, application_no),
                    daemon=True
                ).start()
            )

        data["message"] = "success"
        return JsonResponse(data)

    except Exception as e:
        print("Submit NC application error:", e)
        return JsonResponse({"message": "failure", "error": str(e)}, status=500)

def save_nc_attachment(request):
    data = dict()
    ea_attach = request.FILES['nc_attach']
    file_name = ea_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECNC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ea_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/ECNC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_nc_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('temp_application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='ECNC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECNC')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def view_nc_application_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    applicant_id = request.session.get('email', None)
    assigned_user_id = request.session.get('login_id', None)
    service_id = request.GET.get('service_id')

    request.session['service_id'] = service_id

    service_master = t_service_master.objects.filter(
        service_id=service_id
    ).first()

    attachments = service_master.attachments if service_master else ''
    request.session['attachments'] = attachments

    # Fetch common data
    application_details = t_ec_application_t1.objects.filter(application_no=application_no)
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    # Badge COUNT START
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
        applicant_id=applicant_id
    ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()
    # Badge COUNT END
    context = {
        'thromde': thromde,
        'application_details': application_details,
        'application_no': application_no,
        'dzongkhag': dzongkhag,
        'gewog': gewog,
        'village': village,
        'service_id': service_id,
        'file_attach':file_attach,
        'ec_renewal_count': ec_renewal_count,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'tor_application_count': tor_application_count,
        'draft_count': draft_count

    }

    return render(request, 'nc_application_details.html', context)


def save_compliance_details(request):
    ec_terms_id = request.POST.get('ec_terms_id')
    action_undertaken = request.POST.get('action_undertaken')
    remarks = request.POST.get('remarks')
    

    app_details = t_ec_compliance.objects.filter(record_id=ec_terms_id)
    app_details.update(action_undertaken=action_undertaken,remarks=remarks)

    ec_details = t_ec_compliance.objects.filter(record_id=ec_terms_id)
    return render(request, 'ec_details.html', {'ec_details': ec_details})

def send_renew_payment_mail(name, email_id, amount):
    subject = 'Application Submitted'
    message = "Dear " + name + " Your Application for Renewal OF Environment Clearance Is Submitted. Please Make A Payment of " \
              + str(amount) + ""
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    

def get_ren_temp_application_no(request, service_code, service_id):
    """
    Generates a unique application number using a random 4-digit sequence.
    No DB query or thread locking needed.
    """
    year = timezone.now().year
    rand_num = str(random.randint(1000, 9999))  # Always 4 digits
    temp_application_no = f"{service_code}-{year}-{rand_num}"

    return temp_application_no

def get_ren_application_no(request, service_code, service_id):
    last_application_no = t_ec_application_t1.objects.aggregate(max_app=Max('application_no'))['max_app']
    if not last_application_no:
        year=timezone.now().year
        new_application_no = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(last_application_no)[9:13]
        substring = int(substring) + 1
        app_num = str(substring).zfill(4)
        print(app_num)
        year =  timezone.now().year
        new_application_no =  service_code + "-" + str(year) + "-" + app_num
    return new_application_no

def get_oc_application_no(request, service_code, service_id):
    last_application_no = t_ec_application_t1.objects.aggregate(max_app=Max('application_no'))['max_app']
    if not last_application_no:
        year=timezone.now().year
        new_application_no = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(last_application_no)[9:13]
        substring = int(substring) + 1
        app_num = str(substring).zfill(4)
        print(app_num)
        year =  timezone.now().year
        new_application_no =  service_code + "-" + str(year) + "-" + app_num
    return new_application_no

def get_nc_application_no(request, service_code, service_id):
    last_application_no = t_ec_application_t1.objects.aggregate(max_app=Max('application_no'))['max_app']
    if not last_application_no:
        year=timezone.now().year
        new_application_no = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(last_application_no)[9:13]
        substring = int(substring) + 1
        app_num = str(substring).zfill(4)
        print(app_num)
        year =  timezone.now().year
        new_application_no =  service_code + "-" + str(year) + "-" + app_num
    return new_application_no

DIGITS = 5  # number of digits for sequence part, change to 5 if you want 00001

def _to_int32_signed(x: int) -> int:
    """
    Convert an unsigned 32-bit value to signed 32-bit range [-2^31, 2^31-1].
    """
    if x > 0x7FFFFFFF:
        return x - 0x100000000
    return x

def _advisory_lock(service_code: str, year: int) -> None:
    """
    Acquire a transaction-scoped advisory lock for (service_code, year)
    using the two-int32 variant of pg_advisory_xact_lock.
    """
    sc_crc32 = zlib.crc32(service_code.upper().encode("utf-8")) & 0xFFFFFFFF
    key1 = _to_int32_signed(sc_crc32)  # must be signed 32-bit
    key2 = int(year)                   # year fits comfortably in int4

    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(%s, %s);", [key1, key2])

def _next_number_unlocked(service_code: str, year: int, digits: int = DIGITS) -> str:
    """
    Compute the next application_no for the given service_code and year.
    MUST be called only while holding the advisory lock.
    """
    prefix = f"{service_code.upper()}-{year}-"
    last_app = (
        t_ec_application_t1.objects
        .filter(application_no__startswith=prefix)
        .aggregate(max_val=Max("application_no"))
        .get("max_val")
    )

    if last_app:
        try:
            last_num = int(last_app.split("-")[-1])
        except (ValueError, IndexError):
            last_num = 0
        next_num = last_num + 1
    else:
        next_num = 1

    return f"{prefix}{next_num:0{digits}d}"

def get_new_application_no(request, service_code, service_id=None) -> str:
    """
    Concurrency-safe number generator.
    IMPORTANT: Call this INSIDE the same transaction where you also INSERT the row.
    """
    if not service_code:
        raise ValueError("service_code is required")

    current_year = timezone.now().year
    _advisory_lock(service_code, current_year)
    return _next_number_unlocked(service_code, current_year, digits=DIGITS)


# TOR DETAILS
def tor_form(request):
    service_code = 'TOR'
    login_id = request.session.get('login_id')
    applicant_id = request.session.get('email')

    #application_no = get_application_no(request, service_code, None)
    temp_application_no = get_temp_application_no(login_id)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
    print(temp_application_no)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
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

    # 5. TOR application count (optimized)
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A',
        application_no__contains='TOR',
        applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    return render(request, 'tor_form.html', {'app_hist_count':app_hist_count,'temp_application_no':temp_application_no,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'draft_count': draft_count, 'tor_application_count': tor_application_count,
                   'ec_renewal_count': ec_renewal_count})


def save_tor_form(request):
    data = {}
    try:
        temp_application_no = request.POST.get('temp_application_no')
        project_name = request.POST.get('project_name')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        project_description = request.POST.get('project_description')
        app_remarks = request.POST.get('app_remarks')
        focal_person = request.POST.get('focal_person')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        proponent_type = request.session['proponent_type']
        project_site = request.POST.get('project_site')
        cross_dzongkhag_locations = request.POST.get('cross_dzongkhag_locations')
        mas_integration = request.POST.get('mas_integration')
        print(mas_integration)

        # Get location details
        if dzongkhag_throm == 'Dzongkhag':
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        else:
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')

        location_name = request.POST.get('location_name')

        activity = request.session['activity']
        service_id = request.session['service_id']
        login_id = request.session['login_id']
        name = request.session['name']
        colour_code = request.session['colour_code']

        application_date = timezone.now().date()
        action_date = application_date
        ca_auth = None
        account_head = None
        
        #auth_filter = t_competant_authority_master.objects.filter(
        #        competent_authority=request.session['ca_auth'],
        #        dzongkhag_code_id=dzongkhag if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
        #    )
        #ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None

        # Determine competent authority
        ca_auth = request.session.get('ca_auth')
        if ca_auth == 'DEC' and dzongkhag_code:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                dzongkhag_code_id=dzongkhag_code
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth
        elif ca_auth == 'THROMDE' and thromde_id:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                thromde_id_id=thromde_id
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth
        else:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth

        # Generate Application Number
        service_code = 'TOR'
        #application_no = get_application_no(request, service_code, service_id)
        application_no = get_new_application_no(request, service_code)

        # Insert record in t_ec_application_t1 table
        t_ec_application_t1.objects.create(
            application_no=application_no,
            project_name=project_name,
            applicant_name=applicant_name,
            application_date=application_date,
            address=address,
            contact_no=contact_no,
            email=email,
            focal_person=focal_person,
            dzongkhag_throm=dzongkhag_throm,
            thromde_id=thromde_id,
            dzongkhag_code=dzongkhag_code,
            gewog_code=gewog_code,
            village_code=village_code,
            location_name=project_site,
            cross_dzongkhag_locations=cross_dzongkhag_locations,
            activity=activity,
            applicant_id=request.session['email'],
            ca_authority=ca_auth_id,
            application_status='P',
            action_date=action_date,
            service_id=service_id,
            application_source='ECSS',
            colour_code=colour_code,
            proponent_type=proponent_type,
            service_type='TOR',
            application_type='New',
            project_description=project_description,
            app_remarks=app_remarks,
            mas_integration=mas_integration
        )

        # Insert record in t_application_history table
        t_application_history.objects.create(
            application_no=application_no,
            application_date=application_date,
            applicant_id=request.session['email'],
            ca_authority=ca_auth_id,
            service_id=service_id,
            application_status='P',
            action_date=action_date,
            actor_id=login_id,
            actor_name=name,
            remarks='TOR Application Submitted',
            status='P',
            service_type='TOR'
        )

        # Insert record in t_workflow_dtls table
        t_workflow_dtls.objects.create(
            application_no=application_no,
            service_id=service_id,
            application_status='P',
            action_date=action_date,
            actor_id=login_id,
            actor_name=name,
            assigned_user_id=None,
            assigned_role_id='3',
            assigned_role_name='Reviewer',
            result=None,
            ca_authority=ca_auth_id,
            application_source='ECSS',
            service_type='TOR'
        )

        t_file_attachment.objects.filter(application_no=temp_application_no).update(application_no=application_no)

        #payment_details = payment_details_master.objects.filter(payment_type='TOR')
        #for pay_dets in payment_details:
        #    account_head = pay_dets.account_head_code
        #make_payment_request(request,temp_application_no,"500",'NEW TOR APPLICATION',request.session['email'],account_head,"TOR")
        #send_tor_payment_mail(request.session['name'], request.session['email'], 500)

        # Start the thread ONLY after successful DB commit

        transaction.on_commit(lambda: threading.Thread(
            target=_send_submit_email_in_background_tor,
            args=(name, email, application_no),
            daemon=True
        ).start())

        data['message'] = 'success'
    except Exception as e:
        data['error'] = str(e).split("\n")[0]
    return JsonResponse(data)

def send_tor_payment_mail(name, email_id, amount):
    subject = 'Application Submitted'
    message = "Dear " + name + " Your TOR Application for ECS System Is Submitted. Please Make A Payment of " \
              + str(amount) + ""
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)

def save_tor_attachment(request):
    data = dict()
    tor_attach = request.FILES['tor_attach']
    file_name = tor_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TOR/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, tor_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/TOR" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_tor_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url') 
    application_no = request.POST.get('temp_application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='TOR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOR')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def tor_list(request):
    applicant_id = request.session.get('email', None)
    login_id = request.session.get('login_id')
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no') 
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_details = t_ec_application_t1.objects.filter(
        application_status='A',application_no__contains='TOR',applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    )
    tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    #Client application count
    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=login_id
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()
    
    service_details = t_service_master.objects.all()
    
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    response = render(request, 'tor/tor_list.html', {'tor_application_count':tor_application_count,
                                             'ec_renewal_count':ec_renewal_count,'tor_details':tor_details,
                                             'service_details':service_details, 'app_hist_count':app_hist_count,
                                             'cl_application_count':cl_application_count, 'draft_count':draft_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_tor_application_details(request):
    applicant_id = request.session.get('email', None)
    tor_application_no = request.GET.get('application_no')
    service_id = request.GET.get('service_id')
    app_det = t_ec_application_t1.objects.filter(application_no=tor_application_no)
    t1_general_subquery = t_ec_application_t1.objects.filter(
    tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    project_name = None
    focal_person = None
    project_description = None
    location_name = None
    service_code = None

    # Service code mapping
    SERVICE_CODES = {
        '1': 'IEE', '2': 'ENE', '3': 'ROA', '4': 'TRA',
        '5': 'TOU', '6': 'GWA', '7': 'FOR', '8': 'QUA'
    }
    service_code = SERVICE_CODES.get(service_id, 'GEN')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    for app_det in app_det:
        request.session['ca_auth'] = app_det.ca_authority
        request.session['colour_code'] = app_det.colour_code
        request.session['service_id'] = app_det.service_id
        request.session['activity'] = app_det.activity
        project_name = app_det.project_name
        focal_person = app_det.focal_person
        project_description = app_det.project_description
        location_name = app_det.location_name
        dzongkhag_throm = app_det.dzongkhag_throm
        thromde_id = app_det.thromde_id
        dzongkhag_code = app_det.dzongkhag_code
        gewog_code = app_det.gewog_code
        village_code = app_det.village_code
        mas_integration = app_det.mas_integration
        service_id = app_det.service_id
        #application_no = get_application_no(request, service_code, service_id)
        #application_no = get_new_application_no(request, service_code)
        #request.session['application_no'] = application_no
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()

    return render(request, 'new_application_form_tor.html',{'thromde':thromde,
                                                'ec_renewal_count':ec_renewal_count,
                                                'tor_application_count':tor_application_count,
                                                'tor_application_no':tor_application_no,
                                                'dzongkhag':dzongkhag,
                                                'gewog':gewog,
                                                'village':village,
                                                'thromde':thromde,
                                                'project_name':project_name,
                                                'project_description':project_description,
                                                'location_name':location_name,
                                                'focal_person':focal_person,
                                                'dzongkhag_throm':dzongkhag_throm,
                                                'thromde_id':thromde_id,
                                                'dzongkhag_code':dzongkhag_code,
                                                'gewog_code':gewog_code,
                                                'service_id': service_id,
                                                'village_code':village_code,
                                                'mas_integration':mas_integration
                                                })

# Validate FMFSR_N0 from MAS API start

def validate_fmfsr(request):
    fmfs_id = request.GET.get('fmfsr_no')
    print(fmfs_id)

    try:
        # Step 1: Get token
        token_response = requests.post(
            "https://stg-sso.tech.gov.bt/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=("wz_hmjRfUWx4ZGyUfL1KfQrAReka", "qIAoW01LGvU7XW5tHF_ZuuSNSGUa")
        )

        access_token = token_response.json().get("access_token")

        # Step 2: Call API
        api_url = f"https://staging-datahub-apim.tech.gov.bt/mas_ecss_quarryleaseserviceapi/1.0.0/getFmfsDetails/{fmfs_id}"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(api_url, headers=headers)
        data = response.json()
        print("API RESPONSE:", data)

        if response.status_code == 200:

            response_data = data.get("getFmfsDetailsResponse", {})
            fmfs_list = response_data.get("fmfsDetail", [])

            if fmfs_list and len(fmfs_list) > 0:

                fmfs = fmfs_list[0]  # take first record

                company_name = fmfs.get("companyName", "")
                applicant_name = fmfs.get("applicantName", "")

                return JsonResponse({
                    "status": "success",
                    "project_name": company_name,
                    "project_description": company_name
                    #"project_description": f"Applicant: {company_name}"
                })

            else:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid FMFSR Number"
                })

        else:
            return JsonResponse({
                "status": "error",
                "message": f"API Error: {response.status_code}"
            })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        })

# Validate FMFSR_No fro MAS APT end



# ReportSubmission
def report_list(request):
    login_type = request.session.get('login_type', None)
    login_id = request.session['login_id']
    email_id = request.session['email']

    print(login_type, login_id, email_id)

    user_list = t_user_master.objects.all()
    ec_details = t_ec_application_t1.objects.all()

    common_context = {
        'app_hist_count': t_application_history.objects.filter(applicant_id=login_id).count(),
        'user_list': user_list,
        'ec_details': ec_details,
    }

    context = {}

    if login_type == 'C':
        report_list = t_report_submission_t1.objects.filter(created_by=email_id).order_by('submission_date')

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

        context.update({
            'report_list': report_list,
            'oc_application_count':oc_application_count,
            'app_hist_count': app_hist_count,
            'cl_application_count': cl_application_count,
            'payment_count': payment_count,
            'tor_application_count': tor_application_count,
            'draft_count': draft_count,
            'ec_renewal_count': ec_renewal_count,
            'download_forms': download_forms,
            'old_ec_draft_count': old_ec_draft_count
        })

    elif login_type == 'I':
        ca_authority = request.session['ca_authority']

        report_list = t_report_submission_t1.objects.filter(ca_authority=ca_authority).exclude(report_status='Pending').values().order_by('submission_date')

        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2',
            assigned_role_name='Verifier',
            action_date__isnull=False,
            application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
            ca_authority=ca_authority
        ).count()

        # Renewal exists AND is NOT approved
        pending_renewal_exists = t_ec_application_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(
            application_status='A'
        )
        # EC Renewal List ( Due for renewal)
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        ec_renewal_count = t_ec_t1.objects.filter(
            ca_authority=ca_authority,
            status='A',
            ec_expiry_date__lt=expiry_date_threshold
        ).count()


        context.update({
            'report_list': report_list,
            'ec_renewal_count': ec_renewal_count,
            'v_application_count': v_application_count,
        })

    context.update(common_context)

    response = render(request, 'report_submission/report_list.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def view_report_details(request):
    report_reference_no = request.GET.get('report_reference_no')
    report_details = t_report_submission_t1.objects.filter(report_reference_no=report_reference_no)
    details = t_report_submission_t2.objects.filter(report_reference_no=report_reference_no)
    file_attach = t_file_attachment.objects.filter(application_no=report_reference_no)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    
    v_application_count = 0  # Provide default value for v_application_count
    ec_renewal_count = 0  # Provide default value for ec_renewal_count

    if request.session.get('ca_authority') is not None:
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                    status='A',
                                                                                    ec_expiry_date__lt=expiry_date_threshold).count()
        
    return render(request, 'report_submission/report_details.html',
                  {'report_details': report_details, 'app_hist_count': app_hist_count, 'ec_renewal_count': ec_renewal_count, 'cl_application_count': cl_application_count, 'v_application_count': v_application_count, 'details': details, 'file_attach': file_attach})


def viewDraftReport(request, report_reference_no):
    applicant = request.session['email']
    print(report_reference_no)
    ec_details = t_ec_application_t1.objects.filter(ec_reference_no__isnull=False, applicant_id=applicant)
    report_details = t_report_submission_t1.objects.filter(report_reference_no=report_reference_no)
    report_submission = t_report_submission_t2.objects.filter(report_reference_no=report_reference_no)
    file_attach = t_file_attachment.objects.filter(application_no=report_reference_no)
    return render(request, 'report_submission/report_submission_draft.html',
                  {'report_details':report_details, 'report_submission':report_submission, 'ec_details':ec_details, 'file_attach':file_attach})

def report_submission_form(request):
    applicant = request.session['email']
    ec_details = t_ec_t1.objects.filter(ec_reference_no__isnull=False,applicant_id=applicant).order_by('ec_reference_no')
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
    return render(request, 'report_submission/report_submission.html', {'ec_details': ec_details, 'app_hist_count':app_hist_count})

def save_report_submission(request):
    data = dict()
    service_code = 'rpt'
    print('inside save_report_submission')
    reference_no = get_report_submission_ref_no(request, service_code)
    submission_year = request.POST.get('submission_year')
    submission_date = request.POST.get('submission_date')
    ec_clearance_no = request.POST.get('ec_clearance_no')
    ca_authority = request.POST.get('ca_authority')
    proponent_name = request.POST.get('proponent_name')
    address = request.POST.get('address')
    remarks = request.POST.get('remarks')
    report_type = request.POST.get('report_type')
    created_on = datetime.now()
    login_id = request.session['email']

    t_report_submission_t1.objects.create(
        report_type=report_type,
        report_reference_no=reference_no,
        submission_year=submission_year,
        submission_date=submission_date,
        ec_clearance_no=ec_clearance_no,
        ca_authority=ca_authority,
        proponent_name=proponent_name,
        address=address,
        remarks=remarks,
        created_by=login_id,
        created_date=created_on,
        report_status='Pending',
    )
    data['refNo'] = reference_no
    return JsonResponse(data)

def get_report_submission_ref_no(request, service_code):
    last_reference_no = t_report_submission_t1.objects.aggregate(Max('report_reference_no'))
    lastRefNo = last_reference_no['report_reference_no__max']
    if not lastRefNo:
        year = timezone.now().year
        newRefNo = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastRefNo)[9:13]
        substring = int(substring) + 1
        RefNo = str(substring).zfill(4)
        year = timezone.now().year
        newRefNo = service_code + "-" + str(year) + "-" + RefNo
    return newRefNo

def update_report_submission(request):
    data = dict()
    reference_no = request.POST.get('report_reference_no')
    submission_year = request.POST.get('submission_year')
    submission_date = request.POST.get('submission_date')
    ec_clearance_no = request.POST.get('ec_clearance_no')
    ca_authority = request.POST.get('ca_authority')
    proponent_name = request.POST.get('proponent_name')
    address = request.POST.get('address')
    remarks = request.POST.get('remarks')
    report_type = request.POST.get('report_type')
    login_id = request.session['email']

    application_details = t_report_submission_t1.objects.filter(report_reference_no=reference_no)

    application_details.update(submission_year=submission_year, submission_date=submission_date,
                               ec_clearance_no=ec_clearance_no, ca_authority=ca_authority,
                               proponent_name=proponent_name, address=address,
                               remarks=remarks, report_type=report_type, created_by=login_id)

    data['refNo'] = reference_no
    return JsonResponse(data)

def load_report_submission_details(request):
    reference_no = request.GET.get('report_reference_no')
    print(reference_no)
    report_submission = t_report_submission_t2.objects.filter(report_reference_no=reference_no)
    return render(request, 'report_submission/report_submitted_details.html',
                  {'report_submission': report_submission})

def save_report_details(request):
    reference_no = request.POST.get('refNo')
    ec_terms = request.POST.get('ec_terms')
    action_taken = request.POST.get('action_taken')
    remarks = request.POST.get('detail_remarks')
    t_report_submission_t2.objects.create(
        report_reference_no=reference_no,
        ec_terms=ec_terms,
        action_taken=action_taken,
        remarks=remarks)

    report_submission = t_report_submission_t2.objects.filter(report_reference_no=reference_no)
    return render(request, 'report_submission/report_submitted_details.html',
                  {'report_submission': report_submission})

def delete_report_details(request):
    record_id = request.GET.get('record_id')
    reference_no = request.GET.get('refNo')
    print(record_id)
    print(reference_no)
    record = t_report_submission_t2.objects.filter(record_id=record_id)
    record.delete()
    report_submission = t_report_submission_t2.objects.filter(report_reference_no=reference_no)
    return render(request, 'report_submission/report_submitted_details.html',
                  {'report_submission': report_submission})

def load_report_attachment_details(request):
    referenceNo = request.GET.get('refNo')
    attachment_details = t_file_attachment.objects.filter(application_no=referenceNo)
    return render(request, 'report_submission/report_file_attachment.html',
                  {'file_attach': attachment_details})

def add_report_file(request):
    data = dict()
    myFile = request.FILES['document']
    app_no = request.POST.get('appNo')
    file_name = app_no + "_" + myFile.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/REPORT")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, myFile)
        file_url = "attachments" + "/" + str(
            timezone.now().year) + "/REPORT" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def add_report_file_name(request):
    app_no = request.POST.get('refNo')
    fileName = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    
    t_file_attachment.objects.create(application_no=app_no,
                                     file_path=file_url, attachment=fileName)
    file_attach = t_file_attachment.objects.filter(application_no=app_no)
    return render(request, 'report_submission/report_file_attachment.html', {'file_attach': file_attach})

def delete_report_file(request):
    file_id = request.GET.get('file_id')
    referenceNo = request.GET.get('refNo')

    file = t_file_attachment.objects.filter(file_id=file_id)

    for file in file:
        file_name = file.attachment
        file_n = f"{referenceNo}_{file_name}"
        print(file_n)
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/REPORT")
        fs.delete(str(file_n))
    file.delete()

    file_attach = t_file_attachment.objects.filter(application_no=referenceNo)
    return render(request, 'report_submission/report_file_attachment.html', {'file_attach':file_attach})



def submit_report_form(request):
    reference_no = request.POST.get('record_id')
    created_on = datetime.now()
    details = t_report_submission_t1.objects.filter(report_reference_no=reference_no)
    details.update(created_date=created_on, report_status='Submitted')

    return redirect(report_list)

def acknowledge_report(request):
    report_reference_no = request.GET.get('report_reference_no')
    details = t_report_submission_t1.objects.filter(report_reference_no=report_reference_no)
    details.update(report_status='Acknowledged')

    return redirect(report_list)

#EndReportSubmission


# EC PRINT DETAILS
def ec_print_list(request):
    applicant_id = request.session.get('email', None)
    login_id = request.session.get('login_id')
    assigned_user_id = request.session.get('login_id', None)
    ca_authority = request.session.get('ca_authority', None)
    role_id=request.session.get('role_id', None)

    # Calculate expiry date threshold ONCE - Fixed duplicate calculations
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    oc_application_count = 0
    payment_count = 0
    draft_count = 0
    old_ec_draft_count = 0
    v_application_count = 0
    r_application_count = 0
    p_application_count = 0
    # Count the number of t_application_history objects related to the logged-in user
    app_hist_count = 0
    if applicant_id:
        app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    # Count the number of t_workflow_dtls objects with assigned_user_id equal to the logged-in user
    cl_application_count = 0
    if assigned_user_id:
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()

    # TOR application count calculation
    tor_application_count = 0
    if applicant_id:
        t1_general_subquery = t_ec_application_t1.objects.filter(
            tor_application_no=OuterRef('application_no')
        ).values('tor_application_no')
        # Query to count approved applications that are not in t1_general
        tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',
            applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

    service_details = t_service_master.objects.all()
    # Fixed: Role-based logic with proper conditions
    if ca_authority:
        # Retrieve t_ec_application_t1 objects with application_status='A' and service_type="Main Activity"
        #application_details = t_ec_t1.objects.filter(status='A',service_type="Main Activity", ca_authority=ca_authority)

        if role_id == 1:
            application_details = t_ec_t1.objects.filter(
                status='A',
                ec_reference_no__in=t_ec_t2.objects.values_list('ec_reference_no', flat=True)
            ).order_by('ca_authority', 'ec_approve_date')
        else:
            application_details = t_ec_t1.objects.filter(
                status='A',
                ca_authority=ca_authority,
                ec_reference_no__in=t_ec_t2.objects.values_list('ec_reference_no', flat=True)
            ).order_by('ec_approve_date')



        # Count the number of t_workflow_dtls objects with assigned_role_id='2',
        # assigned_role_name='Verifier', and ca_authority matching the logged-in user's 'ca_authority'
        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2',
            assigned_role_name='Verifier',
            action_date__isnull=False,
            application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
            ca_authority=request.session['ca_authority']
        ).count()
        # Count the number of t_workflow_dtls objects with assigned_role_id='3',
        # assigned_role_name='Reviewer', and ca_authority matching the logged-in user's 'ca_authority'
        # Reviewer application count
        r_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_user_id=login_id,
            assigned_role_name='Reviewer',
            ca_authority=ca_authority
        ).count()
        # Reviewer application count Payment List
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
        # Fixed: EC renewals due within 60 days - ONLY calculated ONCE
        ec_renewal_count = t_ec_t1.objects.filter(
            ca_authority=ca_authority,
            status='A',
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False  # Added safety check
        ).count()
    else:
        # Retrieve t_ec_application_t1 objects with application_status='A' and service_type="Main Activity"
        application_details = t_ec_t1.objects.filter(
            status='A',
            applicant_id=applicant_id,
            ec_reference_no__in=t_ec_t2.objects.values_list('ec_reference_no', flat=True)
        ).order_by('ec_approve_date')

        # If 'ca_authority' is not found or empty, set the variables to appropriate default values
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

    # Pass the retrieved data to the 'ec_print_list.html' template for rendering
    response = render(request, 'EC/ec_print_list.html', {
        'application_details': application_details,
        'service_details' : service_details,
        'oc_application_count': oc_application_count,
        'app_hist_count': app_hist_count,
        'v_application_count': v_application_count,
        'r_application_count': r_application_count,
        'p_application_count': p_application_count,
        'cl_application_count': cl_application_count,
        'payment_count': payment_count,
        'tor_application_count': tor_application_count,
        'draft_count': draft_count,
        'ec_renewal_count': ec_renewal_count,
        'old_ec_draft_count': old_ec_draft_count
    })
    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_print_details(request):
    # Retrieve the 'ec_reference_no' parameter from the GET request
    ec_reference_no = request.GET.get('ec_reference_no')
    ca_authority = request.GET.get('ca_authority')

    #Retrieve competent_authority
    competent_authority = t_competant_authority_master.objects.filter(
        competent_authority_id=ca_authority
    ).first()
    ca_name = competent_authority.remarks if competent_authority else None
    print(ca_name)
    # Retrieve t_ec_application_t1 objects with ec_reference_no=ec_reference_no and service_type="Main Activity"
    application_details = t_ec_t1.objects.filter(ec_reference_no=ec_reference_no, service_type="Main Activity")
    
    # Retrieve t_ec_application_t2 objects with ec_reference_no=ec_reference_no
    ec_details = t_ec_t2.objects.filter(ec_reference_no=ec_reference_no).order_by('order')
    
    # Count the number of t_application_history objects related to the logged-in user
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
    
    # Count the number of t_workflow_dtls objects with assigned_user_id equal to the logged-in user
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    
    # Check if the 'ca_authority' exists in the session and has a non-empty value
    if 'ca_authority' in request.session and request.session['ca_authority']:
        # Count the number of t_workflow_dtls objects with assigned_role_id='2',
        # assigned_role_name='Verifier', and ca_authority matching the logged-in user's 'ca_authority'
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier',
                                                              ca_authority=request.session['ca_authority']).count()
        
        # Count the number of t_workflow_dtls objects with assigned_role_id='3',
        # assigned_role_name='Reviewer', and ca_authority matching the logged-in user's 'ca_authority'
        r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer',
                                                              ca_authority=request.session['ca_authority']).count()
    else:
        # If 'ca_authority' is not found or empty, set the variables to appropriate default values
        v_application_count = 0
        r_application_count = 0
    
    # Pass the retrieved data to the 'print_ec.html' template for rendering
    return render(request, 'EC/print_ec.html', {'application_details': application_details,
                                                 'ec_details': ec_details,
                                                 'app_hist_count': app_hist_count,
                                                 'cl_application_count': cl_application_count,
                                                 'v_application_count': v_application_count,
                                                 'r_application_count': r_application_count,
                                                'competent_authority': ca_name}
                                                )

#VIEW DRAFT EC START
def view_draft_ec_details(request):
    # Retrieve the 'ec_reference_no' parameter from the GET request
    app_no = request.GET.get('application_no')

    # Retrieve competent_authority
    competent_authority = t_competant_authority_master.objects.filter(
        competent_authority_id=request.session['ca_authority']
    ).first()
    ca_name = competent_authority.remarks if competent_authority else None
    print(ca_name)
    # Retrieve t_ec_application_t1 objects with ec_reference_no=ec_reference_no and service_type="Main Activity"
    application_details = t_ec_application_t1.objects.filter(application_no=app_no, service_type="Main Activity")

    # Retrieve t_ec_application_t2 objects with ec_reference_no=ec_reference_no
    ec_details = t_ec_application_t2.objects.filter(application_no=app_no).order_by('order')

    # Count the number of t_application_history objects related to the logged-in user
    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()

    # Count the number of t_workflow_dtls objects with assigned_user_id equal to the logged-in user
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()

    # Check if the 'ca_authority' exists in the session and has a non-empty value
    if 'ca_authority' in request.session and request.session['ca_authority']:
        # Count the number of t_workflow_dtls objects with assigned_role_id='2',
        # assigned_role_name='Verifier', and ca_authority matching the logged-in user's 'ca_authority'
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier',
                                                             ca_authority=request.session['ca_authority']).count()

        # Count the number of t_workflow_dtls objects with assigned_role_id='3',
        # assigned_role_name='Reviewer', and ca_authority matching the logged-in user's 'ca_authority'
        r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer',
                                                             ca_authority=request.session['ca_authority']).count()
    else:
        # If 'ca_authority' is not found or empty, set the variables to appropriate default values
        v_application_count = 0
        r_application_count = 0

    # Pass the retrieved data to the 'print_ec.html' template for rendering
    return render(request, 'EC/draft_ec.html', {'application_details': application_details,
                                                'ec_details': ec_details,
                                                'app_hist_count': app_hist_count,
                                                'cl_application_count': cl_application_count,
                                                'v_application_count': v_application_count,
                                                'r_application_count': r_application_count,
                                                'competent_authority': ca_name}
                  )


#VIEW EC from OUTSIDE START

def view_ec(request, ec_reference_no):
    token = request.GET.get('token')

    if not ec_reference_no:
        return HttpResponse("EC Reference Number is required", status=400)

    if token != settings.EC_PUBLIC_TOKEN:
        return HttpResponse("Unauthorized", status=403)

    application_details = t_ec_t1.objects.filter(ec_reference_no=ec_reference_no)
    app = application_details.first()

    if not app:
        return HttpResponse("EC not found", status=404)

    ec_details = t_ec_t2.objects.filter(ec_reference_no=ec_reference_no).order_by('order')

    competent_authority = t_competant_authority_master.objects.filter(
        competent_authority_id=app.ca_authority
    ).first()

    ca_name = competent_authority.remarks if competent_authority else None

    return render(request, 'EC/print_ec.html', {
        'application_details': application_details,
        'ec_details': ec_details,
        'competent_authority': ca_name
    })
#VIEW EC from OUTSIDE START


# DOWNLOAD EC START
def download_ec_details(request):
    ec_reference_no = request.GET.get('ec_reference_no')
    ca_authority = request.GET.get('ca_authority')

    # Retrieve competent_authority
    competent_authority = t_competant_authority_master.objects.filter(
        competent_authority_id=ca_authority
    ).first()
    ca_name = competent_authority.remarks if competent_authority else None

    # Retrieve t_ec_application_t1 objects with ec_reference_no=ec_reference_no and service_type="Main Activity"
    application_details = t_ec_t1.objects.filter(ec_reference_no=ec_reference_no, service_type="Main Activity")

    # Retrieve t_ec_application_t2 objects with ec_reference_no=ec_reference_no
    ec_details = t_ec_t2.objects.filter(ec_reference_no=ec_reference_no).order_by('order')

    context = {
        'application_details': application_details,
        'ec_details': ec_details,
        'competent_authority': ca_name}

    template = get_template('EC/pdf_ec.html')
    html = template.render(context)

    result = BytesIO()

    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        link_callback=link_callback
    )

    if pdf.err:
        return HttpResponse("PDF Error", status=500)

    response = HttpResponse(
        result.getvalue(),
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="EC_{ec_reference_no}.pdf"'
    )

    return response


# DOWNLOAD EC END

def link_callback(uri, rel):

    # Convert HTML URIs to absolute system paths

    path = finders.find(uri.replace(settings.STATIC_URL, ""))

    if path:
        return path

    path = os.path.join(
        settings.MEDIA_ROOT,
        uri.replace(settings.MEDIA_URL, "")
    )

    return path


# OTHER MODIFICATION DETAILS
# Name CHANGE
def name_change(request):
    applicant_id = request.session.get('email')
    ec_reference_no = request.GET.get('ec_reference_no')
    service_code = 'NC'
    temp_application_no = get_ren_temp_application_no(request, service_code, '11')
    print(ec_reference_no)
    print(applicant_id)
    # Parent EC applications (as you had)
    application_details = t_ec_t1.objects.filter(
        ec_reference_no=ec_reference_no
    )
    # Applicant 's Details

    applicant_details = t_user_master.objects.filter(
        email_id=applicant_id
    )
    # Fetch ALL EC terms for display (no DB writes here)
    ec_terms = t_ec_t2.objects.filter(
        ec_reference_no=ec_reference_no, ec_type='Terms'
    ).order_by('record_id')  # adjust ordering if needed (e.g., seq_no)

    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()

    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=request.session['login_id']
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    ec_renewal_count = non_updated_renewals.count()

    # Note: Do NOT create t_ec_compliance rows here.
    # Just pass ec_terms to the template for temporary display.
    return render(
        request,
        'nc_change_details.html',
        {
            'application_details': application_details,
            'applicant_details': applicant_details,
            'temp_application_no': temp_application_no,
            'ec_terms': ec_terms,  # pass terms for display
            'dzongkhag': dzongkhag,
            'gewog': gewog,
            'village': village,
            'thromde':thromde,
            'draft_count': draft_count,
            'app_hist_count': app_hist_count,
            'cl_application_count': cl_application_count,
            'ec_renewal_count': ec_renewal_count,
        }
    )

# Ownership CHANGE
def ownership_change(request):
    applicant_id = request.session.get('email')
    ec_reference_no = request.GET.get('ec_reference_no')
    service_code = 'OC'
    temp_application_no = get_ren_temp_application_no(request, service_code, '12')
    # print(ec_reference_no)
    # print(applicant_id)
    # Parent EC applications (as you had)
    application_details = t_ec_t1.objects.filter(
        ec_reference_no=ec_reference_no
    )
    #Applicant 's Details

    applicant_details = t_user_master.objects.filter(
        email_id=applicant_id
    )
    # Fetch ALL EC terms for display (no DB writes here)
    ec_terms = t_ec_t2.objects.filter(
        ec_reference_no=ec_reference_no, ec_type='Terms'
    ).order_by('record_id')  # adjust ordering if needed (e.g., seq_no)

    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()

    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=request.session['login_id']
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    ec_renewal_count = non_updated_renewals.count()

    # Note: Do NOT create t_ec_compliance rows here.
    # Just pass ec_terms to the template for temporary display.
    return render(
        request,
        'ownership_change_details.html',
        {
            'application_details': application_details,
            'applicant_details': applicant_details,
            'temp_application_no': temp_application_no,
            'ec_terms': ec_terms,  # pass terms for display
            'dzongkhag': dzongkhag,
            'gewog': gewog,
            'village': village,
            'thromde': thromde,
            'draft_count': draft_count,
            'app_hist_count': app_hist_count,
            'cl_application_count': cl_application_count,
            'ec_renewal_count': ec_renewal_count,
        }
    )

#Other CHANGE
def other_change(request):
    applicant_id = request.session.get('email')
    ec_reference_no = request.GET.get('ec_reference_no')
    identifier = (request.GET.get('identifier') or '').upper().strip()

    # Map identifiers to display names
    IDENTIFIER_LABELS = {
        'TC': 'Technology Change',
        'PC': 'Product Change',
        'CC': 'Capacity Change',
        'AC': 'Area Change',
        'LC': 'Location Change',
    }
    identifier_name = IDENTIFIER_LABELS.get(identifier, 'Other Modification')

    # Parent EC applications (as you had)
    application_details = t_ec_t1.objects.filter(
        ec_reference_no=ec_reference_no
    )
    # Applicant 's Details

    applicant_details = t_user_master.objects.filter(
        email_id=applicant_id
    )

    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['email']
    ).distinct('application_no').count()

    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=request.session['login_id']
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
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

    draft_count = t_ec_application_t1.objects.filter(
        applicant_id=applicant_id,
        application_status='P',
        service_type__in=["Main Activity", "TC", "PC", "CC", "AC", "LC"],
        action_date__isnull=True
    ).count()

    ec_renewal_count = non_updated_renewals.count()

    # Note: Do NOT create t_ec_compliance rows here.
    # Just pass ec_terms to the template for temporary display.
    return render(
        request,
        'other_modification_application_details.html',
        {
            'application_details': application_details,
            'applicant_details': applicant_details,
            'dzongkhag': dzongkhag,
            'gewog': gewog,
            'village': village,
            'thromde': thromde,
            'draft_count': draft_count,
            'app_hist_count': app_hist_count,
            'cl_application_count': cl_application_count,
            'ec_renewal_count': ec_renewal_count,
            'identifier': identifier,
            'identifier_name': identifier_name,
        }
    )

def other_modifications(request):
    # Get identifier from URL parameter, default to 'NC' if not provided
    identifier = request.GET.get('identifier')
    # print(identifier)
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A')
    application_details = t_ec_t1.objects.filter(status='A', applicant_id=email)
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
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()

    # Pass the dynamic identifier instead of hardcoded 'NC'
    response = render(request, 'other_modification_details.html',
                      {
                          'workflow_details': workflow_details,
                          'ec_renewal_count': ec_renewal_count,
                          'app_hist_count': app_hist_count,
                          'cl_application_count': cl_application_count,
                          'application_details': application_details,
                          'dzongkhag': dzongkhag,
                          'gewog': gewog,
                          'village': village,
                          'thromde': thromde,
                          'identifier': identifier,  # Dynamic identifier passed here
                          'tor_application_count': tor_application_count,
                          'draft_count': draft_count,
                      })

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# PAYMENT DETAILS
@csrf_exempt
def ecss_payment_update(request):
    # Check if the request method is POST
    if request.method == "POST":
        try:
            # Decode and strip raw body
            raw_body = request.body.decode('utf-8').strip()

            # Remove unwanted characters and prefix using regex
            cleaned_body = re.sub(r'^Payload :', '', raw_body).strip()

            # Remove invisible or non-printable characters
            cleaned_body = ''.join(char for char in cleaned_body if char.isprintable())

            # Check for empty body
            if not cleaned_body:
                return JsonResponse({"statusCode": "400", "statusDescription": "Empty request body"}, status=400)

            # Attempt to parse the JSON from cleaned_body
            data = json.loads(cleaned_body)

            # Extract required fields with better error handling
            required_fields = ['refNo', 'receiptList', 'paymentMethod', 'paymentMode', 'instrumentDate', 'responseDate']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        "statusCode": "400",
                        "statusDescription": f"Missing required field: {field}"
                    }, status=400)

            ref_no = data['refNo']
            receipt_list = data['receiptList']

            if not receipt_list:
                return JsonResponse({
                    "statusCode": "400",
                    "statusDescription": "receiptList cannot be empty"
                }, status=400)

            payment_method = data['paymentMethod']
            payment_mode = data['paymentMode']
            instrument_date = data['instrumentDate']

            # Extracting values from receipt list
            receipt = receipt_list[0]  # Assuming there's only one receipt in the list

            # Validate receipt fields
            receipt_required = ['receiptNo', 'receiptDate', 'paymentAdviceStatus', 'paymentAdviceAmountPaid']
            for field in receipt_required:
                if field not in receipt:
                    return JsonResponse({
                        "statusCode": "400",
                        "statusDescription": f"Missing required field in receipt: {field}"
                    }, status=400)

            receipt_no = receipt['receiptNo']
            receipt_date = receipt['receiptDate']
            payment_advice_status = receipt['paymentAdviceStatus']
            responseDate = data['responseDate']
            payment_advice_amount_paid = receipt['paymentAdviceAmountPaid']

            # Convert dates with proper error handling
            try:
                # Handle instrument_date
                instrument_date_clean = instrument_date.replace('Z', '+00:00')
                instrument_date_datetime = datetime.fromisoformat(instrument_date_clean)
                #instrument_date_datetime_utc = instrument_date_datetime.astimezone(timezone.utc).strftime(
                #    "%Y-%m-%d %H:%M:%S")
                instrument_date_datetime_utc = instrument_date_datetime.astimezone(dt_timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                return JsonResponse({
                    "statusCode": "400",
                    "statusDescription": f"Invalid instrument_date format: {str(e)}"
                }, status=400)

            try:
                original_receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d %H:%M:%S")
                formatted_receipt_date = original_receipt_date.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                return JsonResponse({
                    "statusCode": "400",
                    "statusDescription": f"Invalid receipt_date format: {str(e)}"
                }, status=400)

            try:
                # Handle different date formats for responseDate
                try:
                    original_responseDate = datetime.strptime(responseDate, "%a %b %d %H:%M:%S BTT %Y")
                except ValueError:
                    original_responseDate = datetime.strptime(responseDate, "%Y-%m-%d %H:%M:%S")
                formatted_responseDate = original_responseDate.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                return JsonResponse({
                    "statusCode": "400",
                    "statusDescription": f"Invalid responseDate format: {str(e)}"
                }, status=400)

            # Check if payment record exists before updating
            payment_details = t_payment_details.objects.filter(application_no=ref_no)

            if not payment_details.exists():
                return JsonResponse({
                    "statusCode": "404",
                    "statusDescription": f"No payment record found for application_no: {ref_no}"
                }, status=404)

            # Perform the update
            updated_count = payment_details.update(
                payment_method=payment_method,
                payment_mode=payment_mode,
                instrument_date=instrument_date_datetime_utc,
                receipt_no=receipt_no,
                receipt_date=formatted_receipt_date,
                payment_advice_status=payment_advice_status,
                response_date=formatted_responseDate,
                payment_advice_amount_paid=payment_advice_amount_paid
            )

            # Log successful update (optional)
            print(f"Payment details updated for application_no: {ref_no}, rows updated: {updated_count}")

            response_data = {
                "statusCode": "200",
                "statusDescription": "Payment Details received successfully",
            }

            return JsonResponse(response_data)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", str(e))
            return JsonResponse({
                "statusCode": "400",
                "statusDescription": f"Invalid JSON payload: {str(e)}"
            }, status=400)

        except Exception as e:
            print("Error:", str(e))
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "statusCode": "500",
                "statusDescription": f"Server Error: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            "statusCode": "405",
            "statusDescription": "Method not allowed. Only POST requests are accepted."
        }, status=405)


@csrf_exempt
def ecss_payment_reversal(request):
    if request.method == "POST":
        try:
            # Decode and strip raw body
            raw_body = request.body.decode('utf-8').strip()
            
            # Remove unwanted characters and prefix using regex
            cleaned_body = re.sub(r'^Payload :', '', raw_body).strip()
            
            # Remove invisible or non-printable characters
            cleaned_body = ''.join(char for char in cleaned_body if char.isprintable())
            
            # Check for empty body
            if not cleaned_body:
                return JsonResponse({"statusCode": "400", "statusDescription": "Empty request body"}, status=400)
            
            # Attempt to parse the JSON from cleaned_body
            data = json.loads(cleaned_body)
            receiptNo = data['receiptNo']
            payment_details = t_payment_details.objects.filter(receipt_no=receiptNo)
            cancelledDate=data['cancelledDate']
            original_cancelledDate = datetime.strptime(cancelledDate, "%a %b %d %H:%M:%S BTT %Y")
            formatted_cancelledDate = original_cancelledDate.strftime("%Y-%m-%d %H:%M:%S")
            payment_details.update(
                cancelled_date=formatted_cancelledDate,
                cancelled_reason=data['cancelledReason'],
                remarks=data['remarks']
            )

            response_data = {
                "statusCode": "200",
                "statusDescription": "Payment Details Cancelled Successfully",
            }
            
            return JsonResponse(response_data)
        
        except json.JSONDecodeError as e:
            # Handle JSON parse error
            print("JSONDecodeError:", str(e))
            return JsonResponse({"statusCode": "400", "statusDescription": "Invalid JSON payload"}, status=400)
        
        except Exception as e:
            # Handle other exceptions
            print("Error:", str(e))
            return JsonResponse({"statusCode": "400", "statusDescription": "Bad Request"}, status=400)
    else:
        # Handle non-POST requests
        return JsonResponse({"statusCode": "405", "statusDescription": "Method not allowed"}, status=405)


# OLD EC UPDATE START

def check_old_ec(request):
    old_ec = request.GET.get('ec_reference_no')
    old_ec_count = (
        t_ec_application_t1.objects
        .filter(ec_reference_no=old_ec)
        .count()
    )
    return JsonResponse({"old_ec_count": old_ec_count})

def old_ec_application(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    bsic_details = t_bsic_code.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A', application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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
    response = render(request, 'old_ec_application.html', {'bsic_details': bsic_details,'ec_renewal_count':ec_renewal_count, 'app_hist_count': app_hist_count,
                                                        'cl_application_count': cl_application_count,
                                                        'tor_application_count': tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response



def old_ec_application_form(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    service_code = None
    if request.session['service_id'] == '1':
        service_code = 'IEE'
    elif request.session['service_id'] == '2':
        service_code = 'ENE'
    elif request.session['service_id'] == '3':
        service_code = 'ROA'
    elif request.session['service_id'] == '4':
        service_code = 'TRA'
    elif request.session['service_id'] == '5':
        service_code = 'TOU'
    elif request.session['service_id'] == '6':
        service_code = 'GWA'
    elif request.session['service_id'] == '7':
        service_code = 'FOR'
    elif request.session['service_id'] == '8':
        service_code = 'QUA'
    else:
        service_code = 'GEN'
    #application_no = get_application_no(request, service_code, request.session['service_id'])
    #request.session['application_no'] = application_no
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_application_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

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

    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
        application_status='A', application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    return render(request, 'old_ec_application_form.html', {'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'tor_application_count':tor_application_count, 'thromde': thromde,'ec_renewal_count':ec_renewal_count,
                                                         'dzongkhag': dzongkhag, 'gewog': gewog, 'village': village})


def save_old_ec_general_details(request):
    data = {'message': 'failure'}

    try:
        # Get basic form data
        identifier = request.POST.get('identifier')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        application_type = "Old_EC"
        ec_reference_no = request.POST.get('ec_reference_no')
        ec_issue_date = request.POST.get('ec_issue_date')
        ec_validity = request.POST.get('ec_validity')
        service_type_to_use = 'Main Activity'

        # CRITICAL FIX: Initialize ALL variables early
        service_id_to_use = None
        activity_to_use = None
        color_code_to_use = None
        service_code = None
        ca_auth = None  # ✅ Initialize ca_auth early to prevent errors
        ref_application_no = None

        if identifier != 'DR':
            # New application - use session values
            service_id_to_use = request.session.get('service_id')
            activity_to_use = request.session.get('activity')
            color_code_to_use = request.session.get('colour_code')

            service_code_map = {
                '1': 'IEE', '2': 'ENE', '3': 'ROA', '4': 'TRA',
                '5': 'TOU', '6': 'GWA', '7': 'FOR', '8': 'QUA'
            }
            service_code = service_code_map.get(str(service_id_to_use), 'GEN')
        else:
            # For Draft/Update, get reference application number
            ref_application_no = request.POST.get('application_no')

            # Get existing application details
            existing_app = None
            if ref_application_no:
                existing_app = t_ec_application_t1.objects.filter(
                    application_no=ref_application_no
                ).first()

            if existing_app:
                service_id_to_use = existing_app.service_id
                activity_to_use = existing_app.activity
                color_code_to_use = existing_app.colour_code
                ca_auth = existing_app.ca_authority  # ✅ Get ca_auth from existing app
            else:
                # Fallback to session values
                service_id_to_use = request.session.get('service_id')
                activity_to_use = request.session.get('activity')
                color_code_to_use = request.session.get('colour_code')

        # Determine application number
        if identifier != 'DR':
           #application_no = get_application_no(request, service_code, service_id_to_use)
            application_no = get_new_application_no(request, service_code)
        else:
            application_no = ref_application_no

        # Handle location data
        if dzongkhag_throm == 'Dzongkhag':
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        else:
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')

        # Prepare common data
        common_data = {
            'application_no': application_no,
            'application_date': timezone.now().date(),
            'application_type': application_type,
            'application_source': 'ECSS',
            'application_status': 'P',
            'applicant_id': request.session.get('email'),
            'applicant_name': request.POST.get('applicant_name'),
            'address': request.POST.get('address'),
            'cid': request.session.get('cid'),
            'contact_no': request.POST.get('contact_no'),
            'email': request.POST.get('email'),
            'focal_person': request.POST.get('focal_person'),
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,
            'location_name': request.POST.get('project_site'),
            'cross_dzongkhag_locations': request.POST.get('cross_dzongkhag_locations'),
            'project_name': request.POST.get('project_name'),
            'project_description': request.POST.get('project_description'),
            'dzongkhag_throm': dzongkhag_throm,
            'service_type': service_type_to_use,
            'service_id': service_id_to_use,
            'colour_code': color_code_to_use,
            'proponent_type': request.session.get('proponent_type'),
            'activity': activity_to_use,
            'ec_reference_no': ec_reference_no,
            'ec_approve_date': ec_issue_date,
            'ec_expiry_date': ec_validity
        }

        with transaction.atomic():
            #  CRITICAL FIX: Determine ca_auth with proper error handling
            if ca_auth is None:
                try:
                    # Method 1: Get from activity
                    if activity_to_use:
                        activity_details = t_bsic_code.objects.filter(activity=activity_to_use).first()
                        if activity_details:
                            ca_authority_code = activity_details.competent_authority
                            request.session['ca_auth'] = ca_authority_code

                            # Get the actual ca_authority_id
                            auth_filter = t_competant_authority_master.objects.filter(
                                competent_authority=ca_authority_code,
                                dzongkhag_code_id=dzongkhag_code if ca_authority_code in ['DEC', 'THROMDE'] else None
                            )

                            if auth_filter.exists():
                                ca_auth = auth_filter.first().competent_authority_id
                            else:
                                print(f"Warning: No competent authority found for {ca_authority_code}")
                                # Try without dzongkhag filter as fallback
                                fallback_auth = t_competant_authority_master.objects.filter(
                                    competent_authority=ca_authority_code
                                ).first()
                                ca_auth = fallback_auth.competent_authority_id if fallback_auth else None
                        else:
                            print(f"Warning: No activity details found for {activity_to_use}")

                    # Method 2: Fallback to session ca_auth
                    if ca_auth is None and request.session.get('ca_auth'):
                        auth_filter = t_competant_authority_master.objects.filter(
                            competent_authority=request.session['ca_auth'],
                            dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC',
                                                                                               'THROMDE'] else None
                        )
                        if auth_filter.exists():
                            ca_auth = auth_filter.first().competent_authority_id
                        else:
                            # Try without dzongkhag filter
                            fallback_auth = t_competant_authority_master.objects.filter(
                                competent_authority=request.session['ca_auth']
                            ).first()
                            ca_auth = fallback_auth.competent_authority_id if fallback_auth else None

                except Exception as ca_error:
                    print(f"Error determining ca_auth: {ca_error}")
                    ca_auth = None

            #  CRITICAL VALIDATION: Ensure ca_auth is not None
            if ca_auth is None:
                error_msg = "Unable to determine competent authority (ca_auth). Please check activity and location data."
                print(f"ERROR: {error_msg}")
                data['error'] = error_msg
                return JsonResponse(data)

            print(f"✅ Final ca_auth value: {ca_auth}")

            # Handle different identifier cases
            if identifier == 'DR':
                # Data Rectification (Draft) - UPDATE EXISTING ENTRY
                existing_app = t_ec_application_t1.objects.filter(
                    application_no=ref_application_no
                ).first()

                if existing_app:
                    # UPDATE existing entry
                    update_data = {
                        **common_data,
                        'ca_authority': ca_auth,
                        'service_type': 'Main Activity',
                        'service_id': existing_app.service_id,
                        'colour_code': existing_app.colour_code,
                        'activity': existing_app.activity
                    }

                    # Remove application_no from update (shouldn't be updated)
                    if 'application_no' in update_data:
                        del update_data['application_no']

                    t_ec_application_t1.objects.filter(
                        application_no=ref_application_no
                    ).update(**update_data)

                    print(f"✅ DR - Updated existing application {ref_application_no}")
                else:
                    # Create new if existing not found
                    new_data = {'ca_authority': ca_auth}
                    common_data['service_type'] = 'Main Activity'
                    t_ec_application_t1.objects.create(**common_data, **new_data)
                    print(f"✅ DR - Created new application {application_no}")
            else:
                # Create new application
                new_data = {'ca_authority': ca_auth}
                t_ec_application_t1.objects.create(**common_data, **new_data)
                print(f"✅ Created new application {application_no}")

            # Create application history
            t_application_history.objects.create(
                application_no=application_no,
                application_date=timezone.now().date(),
                applicant_id=request.session.get('email'),
                ca_authority=ca_auth,
                service_id=service_id_to_use,
                application_status='P',
                action_date=timezone.now(),
                actor_id=request.session.get('login_id'),
                actor_name=request.session.get('name'),
                remarks=None,
                status=None
            )

            data['message'] = 'success'
            data['application_no'] = application_no

    except Exception as e:
        print(f'An error occurred: {e}')
        import traceback
        print(f'📊 Traceback: {traceback.format_exc()}')
        data['error'] = str(e)

    return JsonResponse(data)

def submit_old_ec_general_application(request):
    data = {}
    try:
        application_no = request.POST.get('general_disclaimer_application_no')
        ec_reference_no = request.POST.get('ec_reference_no')
        reject_reason   = request.POST.get('reject_reason')
        identifier      = request.GET.get('identifier')

        print(application_no, ec_reference_no, reject_reason, identifier)

        # Get application details
        application_details = t_ec_application_t1.objects.filter(application_no=application_no)
        main_application    = application_details.filter(service_type='Main Activity').first()

        if not main_application:
            data['error'] = "No main application found"
            return JsonResponse(data, status=400)

        applicant_name = main_application.applicant_name
        email          = main_application.applicant_id

        if identifier in ['A', 'R']:
            main_application.application_status = identifier
            main_application.assigned_by        = request.session['login_id']
            main_application.assigned_date      = timezone.now()
            main_application.save()

            # Push to main/history tables ONLY when approved
            _handle_old_application_ec_tables(ec_reference_no, application_no)

            remarks = 'OLD EC Approved'

            # ✅ Send approval email after DB commit
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_approval_mail_in_background,
                    args=(applicant_name, email, application_no),
                    daemon=True
                ).start()
            )

        else:
            main_application.action_date         = timezone.now()
            main_application.application_status  = identifier
            main_application.reject_remarks      = reject_reason
            main_application.save()

            remarks = 'OLD EC Sent back for Resubmission'

            # ✅ Send rejection email after DB commit
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_rejection_mail_in_background,
                    args=(applicant_name, email, application_no, reject_reason),
                    daemon=True
                ).start()
            )

        # Update existing history row(s) for the main activity
        t_application_history.objects.filter(
            application_no=application_no,
            service_type='Main Activity'
        ).update(
            remarks=remarks,
            action_date=timezone.now(),
            application_status=identifier
        )

        data['message'] = "success"

    except Exception as e:
        data['error'] = str(e).split("\n")[0]

    return JsonResponse(data)

# OLD EC UPDATE END

#SEND EMAIL on APPROVE AND REJECT start
# ──────────────────────────────────────────────
# Background thread targets
# ──────────────────────────────────────────────

def _send_approval_mail_in_background(name, email, application_no):
    try:
        _send_approval_mail(name, email, application_no)
    except Exception:
        logger.exception(
            "Failed to send approval email for application_no=%s", application_no
        )


def _send_rejection_mail_in_background(name, email, application_no, reject_reason):
    try:
        _send_rejection_mail(name, email, application_no, reject_reason)
    except Exception:
        logger.exception(
            "Failed to send rejection email for application_no=%s", application_no
        )


# ──────────────────────────────────────────────
# Actual mail senders
# ──────────────────────────────────────────────

def _send_approval_mail(name, email, application_no):
    subject = "EC Application Approved"
    message = (
        f"Dear {name},\n\n"
        f"Your application registered under the application number: {application_no} "
        f"has been approved.\n\n"
        f"Please log in to the portal for further steps.\n\n"
        f"Regards,\n"
        f"Environment Clearance Services"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )


def _send_rejection_mail(name, email, application_no, reject_reason):
    subject = "EC Application Rejected / Sent for Resubmission"
    message = (
        f"Dear {name},\n\n"
        f"Your application registered under the application number: {application_no} "
        f"has been rejected / sent back for resubmission.\n\n"
        f"Remarks: {reject_reason}\n\n"
        f"Please log in to the portal to resubmit your application.\n\n"
        f"Regards,\n"
        f"Environment Clearance Services"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )

#SEND EMAIL on APPROVE AND REJECT start


def _handle_old_application_ec_tables(ec_reference_no, application_no):
    source_t1_records = t_ec_application_t1.objects.filter(
        ec_reference_no=ec_reference_no.strip(),
        application_no=application_no.strip()
    )
    print(ec_reference_no)
    print(application_no)
    t1_objects_to_create = []
    t1_history_objects = []

    for source in source_t1_records:
        t1_record = t_ec_t1(
            application_source=source.application_source,
            activity=source.activity,
            project_description=source.project_description,
            service_id=source.service_id,
            colour_code=source.colour_code,
            service_type=source.service_type,
            ca_authority=source.ca_authority,
            proponent_type=source.proponent_type,
            applicant_id=source.applicant_id,
            applicant_name=source.applicant_name,
            address=source.address,
            cid=source.cid,
            contact_no=source.contact_no,
            email=source.email,
            project_name=source.project_name,
            focal_person=source.focal_person,
            dzongkhag_throm=source.dzongkhag_throm,
            thromde_id=source.thromde_id,
            dzongkhag_code=source.dzongkhag_code,
            gewog_code=source.gewog_code,
            village_code=source.village_code,
            location_name=source.location_name,
            ec_reference_no=source.ec_reference_no,
            prev_ec_reference_no=source.prev_ec_reference_no,
            ec_approve_date=source.ec_approve_date,
            ec_expiry_date=source.ec_expiry_date,
            tor_approve_date=source.tor_approve_date,
            tor_remarks=source.tor_remarks,
            tor_clearance_no=source.tor_clearance_no,
            status='A',
            application_no=application_no
        )
        t1_objects_to_create.append(t1_record)

        t1_history_objects.append(t_ec_t1_history(
            application_source=source.application_source,
            activity=source.activity,
            project_description=source.project_description,
            service_id=source.service_id,
            colour_code=source.colour_code,
            service_type=source.service_type,
            ca_authority=source.ca_authority,
            proponent_type=source.proponent_type,
            applicant_id=source.applicant_id,
            applicant_name=source.applicant_name,
            address=source.address,
            cid=source.cid,
            contact_no=source.contact_no,
            email=source.email,
            project_name=source.project_name,
            focal_person=source.focal_person,
            dzongkhag_throm=source.dzongkhag_throm,
            thromde_id=source.thromde_id,
            dzongkhag_code=source.dzongkhag_code,
            gewog_code=source.gewog_code,
            village_code=source.village_code,
            location_name=source.location_name,
            ec_reference_no=source.ec_reference_no,
            prev_ec_reference_no=source.prev_ec_reference_no,
            ec_approve_date=source.ec_approve_date,
            ec_expiry_date=source.ec_expiry_date,
            tor_approve_date=source.tor_approve_date,
            tor_remarks=source.tor_remarks,
            tor_clearance_no=source.tor_clearance_no,
            status='A',
            history_date=timezone.now(),
            history_action='OLD_EC',
            application_no=application_no
        ))

    if t1_objects_to_create:
        t_ec_t1.objects.bulk_create(t1_objects_to_create)
        t_ec_t1_history.objects.bulk_create(t1_history_objects)


