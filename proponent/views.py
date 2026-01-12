from datetime import date, datetime, timedelta, timezone
import json
import logging
import re
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import connection
from django.contrib.sessions.models import Session

from django.http import JsonResponse
from django.shortcuts import redirect, render
import requests
from django.db.models import Count, Subquery, OuterRef,Exists
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from pyasn1.codec.ber.eoo import endOfOctets

from ecs_admin.models import payment_details_master, t_bsic_code, t_competant_authority_master, t_dzongkhag_master, t_fees_schedule, t_file_attachment, t_gewog_master, t_role_master, t_security_question_master, t_service_master, t_thromde_master, t_user_master, t_village_master
from ecs_main.models import t_application_history
from ecs_main.views import get_birms_token, get_random_tax_no, insert_app_payment_details, make_payment_request
from proponent.models import t_ec_industries_t11_ec_details, t_ec_industries_t1_general, t_ec_renewal_t1, t_ec_renewal_t2, t_payment_details, t_report_submission_t1, t_report_submission_t2, t_workflow_dtls

def new_application(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    #bsic_details = t_bsic_code.objects.all()
    bsic_details = t_bsic_code.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    response = render(request, 'new_application.html',{'bsic_details':bsic_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_application_service_id(request):
    data = {}
    activity = request.GET.get('activity')

    activity_details = t_bsic_code.objects.filter(activity=activity)

    for cat_details in activity_details:
        service_id = cat_details.service_id

        service_master = t_service_master.objects.filter(
            service_id=service_id
        ).first()

        attachments = service_master.attachments if service_master else ''

        # Store everything in session
        request.session['service_id'] = service_id
        request.session['ca_auth'] = cat_details.competent_authority
        request.session['colour_code'] = cat_details.colour_code
        request.session['has_tor'] = cat_details.has_tor
        request.session['activity'] = cat_details.activity
        request.session['attachments'] = attachments   #

        data = {
            'colour_code': cat_details.colour_code,
            'has_tor': cat_details.has_tor
        }

    return JsonResponse(data)


def application_form(request):
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    service_id = str(request.session.get('service_id'))

    print(service_id)
    return render(request, 'new_application_form.html',{'service_id': service_id,'thromde':thromde,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def get_application_no(request, service_code, service_id):
    if service_code == "TOR":
        application_no= t_ec_industries_t1_general.objects.filter(application_no__contains='TOR').aggregate(Max('application_no'))
    else:
        application_no= t_ec_industries_t1_general.objects.exclude(service_id=service_id, application_no__contains='TOR').filter(application_no__contains=service_code).aggregate(Max('application_no'))
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
            existing_app = t_ec_industries_t1_general.objects.filter(
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
                existing_app = t_ec_industries_t1_general.objects.filter(
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
            application_no = get_application_no(request, service_code, request.session['service_id'])
        else:
            # For modifications, use the service_id from existing application
            # EXCEPT for DR (draft) - use the same application number
            if identifier == 'DR':
                application_no = ref_application_no  # Use existing application number for draft
            else:
                application_no = get_application_no(request, service_code, service_id_to_use)
        
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
                existing_app = t_ec_industries_t1_general.objects.filter(application_no=ref_application_no).first()
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
                    t_ec_industries_t1_general.objects.filter(
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
                    t_ec_industries_t1_general.objects.create(**common_data, **new_data)
                    print(f"DR - Created new application {application_no}")
                    
            elif identifier == 'NC':
                # Name Change - CREATE NEW ENTRY
                existing_app = t_ec_industries_t1_general.objects.filter(application_no=ref_application_no).first()
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
                    t_ec_industries_t1_general.objects.create(**new_data)
                else:
                    raise ValueError(f"Application {ref_application_no} does not exist for NC operation")
                
            elif identifier == 'OC':
                # Ownership Change - CREATE NEW ENTRY
                existing_app = t_ec_industries_t1_general.objects.filter(application_no=ref_application_no).first()
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
                    t_ec_industries_t1_general.objects.create(**new_data)
                else:
                    raise ValueError(f"Application {ref_application_no} does not exist for OC operation")
                
            elif identifier in ['TC', 'PC', 'LC', 'CC']:
                # Transfer/Post-Completion/LC/CC Cases - CREATE NEW ENTRY
                if prev_ec_reference_no:
                    prev_app_details = t_ec_industries_t1_general.objects.filter(application_no=prev_ec_reference_no)
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
                        t_ec_industries_t1_general.objects.create(**new_app_data)
                else:
                    # Create new application without previous reference
                    new_data = {
                        'ca_authority': ca_auth,
                        'prev_ec_reference_no': None,
                        'service_type': identifier
                    }
                    t_ec_industries_t1_general.objects.create(**common_data, **new_data)
                    
            else:
                # Main Activity - New Application - CREATE NEW ENTRY
                new_data = {
                    'ca_authority': ca_auth,
                    'prev_ec_reference_no': prev_ec_reference_no if prev_ec_reference_no else None
                }
                t_ec_industries_t1_general.objects.create(**common_data, **new_data)

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

def save_new_general_details(request):
    data = {'message': 'failure'}

    try:
        post_data = request.POST
        session = request.session

        # Get the application number from POST data
        application_no = post_data.get('application_no')
        identifier = post_data.get('identifier', '')

        print(f"DEBUG: application_no from POST: {application_no}, identifier: {identifier}")

        print(f"DEBUG: Final application_no: {application_no}")

        # Check if application already exists
        existing_app = None
        if application_no:
            existing_app = t_ec_industries_t1_general.objects.filter(
                application_no=application_no
            ).first()

        # Service code mapping
        SERVICE_CODE_MAP = {
            '1': 'IEE', '2': 'ENE', '3': 'ROA', '4': 'TRA',
            '5': 'TOU', '6': 'GWA', '7': 'FOR', '8': 'QUA'
        }

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

        # Determine competent authority
        ca_auth = session.get('ca_auth')
        if ca_auth in ['DEC', 'THROMDE'] and dzongkhag_code:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth,
                dzongkhag_code_id=dzongkhag_code
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth
        else:
            auth_record = t_competant_authority_master.objects.filter(
                competent_authority=ca_auth
            ).first()
            ca_auth_id = auth_record.competent_authority_id if auth_record else ca_auth

        # Prepare data
        common_data = {
            'application_no': application_no,
            'application_date': timezone.now().date(),
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
            'project_name': post_data.get('project_name'),
            'project_description': post_data.get('project_description'),
            'dzongkhag_throm': post_data.get('dzongkhag_throm'),
            'service_type': 'Main Activity',
            'service_id': service_id,
            'colour_code': color_code,
            'proponent_type': session.get('proponent_type'),
            'activity': activity,
            'ec_reference_no': post_data.get('ec_reference_no'),
            'ec_approve_date': post_data.get('ec_issue_date'),
            'ec_expiry_date': post_data.get('ec_validity'),
            'ca_authority': ca_auth_id
        }

        with transaction.atomic():
            if existing_app:
                # UPDATE existing application
                print(f"DEBUG: Updating application {application_no}")
                # Remove application_no from update data
                update_data = common_data.copy()
                del update_data['application_no']
                t_ec_industries_t1_general.objects.filter(
                    application_no=application_no
                ).update(**update_data)
                t_workflow_dtls.objects.filter(
                    application_no=application_no
                ).update(ca_authority=ca_auth_id,)
            else:
                # CREATE new application (only if we don't have application_no)
                if not application_no:
                    # Generate new application number
                    application_no = get_application_no(request, service_code, service_id)
                    common_data['application_no'] = application_no
                print(f"DEBUG: Creating new application {application_no}")
                t_ec_industries_t1_general.objects.create(**common_data)
                # Create workflow
                t_workflow_dtls.objects.create(
                    application_no=application_no,
                    service_id=service_id,
                    application_status='P',
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    assigned_role_id='3',
                    assigned_role_name='Reviewer',
                    ca_authority=ca_auth_id,
                    application_source='ECSS',
                    service_type='Main Activity',
                )
            # Save application number to session for future tabs
            if application_no:
                request.session['current_application_no'] = application_no
            # Create history
            t_application_history.objects.create(
                application_no=application_no,
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
                'application_no': application_no
            })
    except Exception as e:
        print(f'An error occurred: {e}')
        import traceback
        traceback.print_exc()
        data['error'] = str(e)
    return JsonResponse(data)
# Save NEW General Details END

def save_general_attachment(request):
    data = dict()
    general_attach = request.FILES['general_attach']
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
    else :
        service_code = 'GEN'
    file_name = general_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + service_code)
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + service_code + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def check_file_attachment(request):
    data = dict()
    application_no = request.GET.get('application_no')
    print(application_no)
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
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GEN/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'ECR':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECR/")
            fs.delete(str(file_name))
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
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/FO/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'IEE':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/IEE/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'TRA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TRA/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'ROA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ROA/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'ENE':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ENE/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'EA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EA/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'TOU':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TOU/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'QUA':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/QUA/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'GW':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GW/")
            fs.delete(str(file_name))
        file.delete()
    file_attach = t_file_attachment.objects.filter(application_no=application_no)
    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_general_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
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
    else :
        service_code = 'GEN'

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type=service_code)
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type=service_code)

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def submit_general_application(request):
    data = {}
    try:
        application_no = request.POST.get('general_disclaimer_application_no')
        
        # Get application details
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        main_application = application_details.filter(service_type__in=['Main Activity','NC', 'OC', 'TC', 'PC', 'LC', 'CC']).first()

        if not main_application:
            data['error'] = "No main application found"
            return JsonResponse(data, status=400)
        
        main_application.action_date = timezone.now()
        main_application.save()

        # Update workflow
        workflow_update = {'action_date': timezone.now()}
        t_workflow_dtls.objects.filter(application_no=application_no,service_type__in=['Main Activity','NC', 'OC', 'TC', 'PC', 'LC', 'CC']).update(**workflow_update)
        t_application_history.objects.filter(application_no=application_no,service_type__in=['Main Activity','NC', 'OC', 'TC', 'PC', 'LC', 'CC']).update(
            remarks='Application Submitted',
            action_date=timezone.now()
        )
        data['message'] = "success"
    except Exception as e:
        data['error'] = str(e).split("\n")[0]
    return JsonResponse(data)

## NDI IMPLEMENTATION START
# Set up logging
logger = logging.getLogger(__name__)

def proof_request(request):
    category = request.GET.get('category', '')

    try:
        # Invalidate existing session and create a new session
        session_id = request.session.session_key
        if session_id:
            Session.objects.filter(session_key=session_id).delete()  # Delete the old session

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
            Session.objects.filter(session_key=session_id).delete()  # Delete the old session

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
            Session.objects.filter(session_key=session_id).delete()  # Delete the old session

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
    request.session.clear()
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

        # Fetch category and session_id from database based on thid
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT category, session_id FROM proponent_t_ndi_login_temp WHERE thread_id = %s",
                [thid]
            )
            row = cursor.fetchone()
            if row:
                category, session_id = row
            else:
                category = None
                session_id = None

        if session_id is None:
            return JsonResponse({"statusCode": "400", "statusDescription": "Session not found"}, status=400)

        if eid is not None and id_number == '1111' and full_name is None:
            payload = {
                'type': 'send_id_number',
                'id_number': id_number,
                'eid': eid,
                'relationshipDid': relationshipDid,
                'thid': thid,
                'holder_did': holder_did,
                'category': category,
                'session_id': session_id,  # Include session_id in payload
                'proof_type': data.get('type')
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            print("Payload to be sent to WebSocket:", payload)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'id_number_group',
                payload
            )
            return JsonResponse({"statusCode": "202", "statusDescription": "Accepted"}, status=202)
        elif eid is None and id_number is not None and full_name is None:
            payload = {
                'type': 'send_id_number',
                'id_number': id_number,
                'relationshipDid': relationshipDid,
                'thid': thid,
                'holder_did': holder_did,
                'category': category,
                'session_id': session_id,  # Include session_id in payload
                'proof_type': data.get('type')
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            print("Payload to be sent to WebSocket:", payload)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'id_number_group',
                payload
            )
            return JsonResponse({"statusCode": "202", "statusDescription": "Accepted"}, status=202)
        elif eid is None and id_number is not None and full_name is not None:
            print('inside proponent')
            dzongkhag = revealed_attrs.get('Dzongkhag', [{}])[0].get('value', None)
            gewog = revealed_attrs.get('Gewog', [{}])[0].get('value', None)
            village = revealed_attrs.get('Village', [{}])[0].get('value', None)
            payload = {
                'type': 'send_id_number',
                'id_number': id_number,
                'full_name': full_name,
                'dzongkhag': dzongkhag,
                'gewog': gewog,
                'village': village,
                'thid': thid,
                'category': category,
                'session_id': session_id , # Include session_id in payload
                'proof_type': data.get('type')
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            print("Payload to be sent to WebSocket:", payload)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'id_number_group',
                payload
            )
            return JsonResponse({"statusCode": "202", "statusDescription": "Accepted"}, status=202)
        elif data.get('type') == 'present-proof/rejected':
            payload = {
                'type': 'send_id_number',
                'id_number': None,
                'category': category,
                'session_id': session_id , # Include session_id in payload
                'proof_type': data.get('type')
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            print("Payload to be sent to WebSocket:", payload)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'id_number_group',
                payload
            )
            return JsonResponse({"statusCode": "202", "statusDescription": "Accepted"}, status=202)
    except KeyError as e:
        print(f"KeyError: {e}")
        return JsonResponse({"statusCode": "400", "statusDescription": "Invalid request payload"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"statusCode": "400", "statusDescription": "Invalid JSON"}, status=400)

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
        application_details = t_ec_industries_t1_general.objects.filter(cid=id_number, application_status='A')

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
    issuance_detail = t_ec_industries_t1_general.objects.filter(
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
    app_details = t_ec_industries_t1_general.objects.filter(revocation_id=revocation_id)
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

    #application_details = t_ec_industries_t1_general.objects.filter(applicant_id=applicant_id,application_status='P',service_type='Main Activity',action_date__isnull=True)
    # -----------------------------
    # Application details based on identifier
    # -----------------------------
    if identifier == 'OLD':
        application_details = t_ec_industries_t1_general.objects.filter(
            applicant_id=applicant_id,
            #application_status='R',
            application_status__in=['P', 'R'],
            application_type='Old_EC',
            #action_date__isnull=True
        ).order_by('-record_id')
        template_name = 'pending_old_ec_list.html'
    else:  # NEW
        application_details = t_ec_industries_t1_general.objects.filter(
            applicant_id=applicant_id,
            application_status='P',
            application_type='New',
            action_date__isnull=True
        ).order_by('-record_id')
        template_name = 'draft_application_list.html'

    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()


    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    
    response = render(request, template_name,{'application_details':application_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'service_details':service_details, 'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_draft_application_details(request):
    application_no = request.GET.get('application_no') or request.session.get('application_no')
    request.session['application_no'] = application_no
    service_id = request.GET.get('service_id')

    request.session['service_id'] = service_id

    service_master = t_service_master.objects.filter(
        service_id=service_id
    ).first()

    attachments = service_master.attachments if service_master else ''
    request.session['attachments'] = attachments

    # Fetch common data
    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity')
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
        'file_attach':file_attach
    }
    
    return render(request, 'draft_application_details.html', context)


#OLD EC APPLICATION LIST start
def old_ec_application_list(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    identifier = request.GET.get('identifier')

    # application_details = t_ec_industries_t1_general.objects.filter(applicant_id=applicant_id,application_status='SM',service_type='Main Activity')
    # -----------------------------SM- Submitted
    # Application details based on identifier
    # -----------------------------

    application_details = t_ec_industries_t1_general.objects.filter(
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
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    )

    non_updated_renewals = t_ec_industries_t1_general.objects.filter(
        applicant_id=request.session['email'],
        service_type__in=["Main Activity", "Old EC"],
        ec_expiry_date__lt=expiry_date_threshold,
    ).filter(
        Exists(renewal_exists)
    )

    ec_renewal_count = non_updated_renewals.count()
    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
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
    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,
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
    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,
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
    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,
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
    if not applicant_id:
        return redirect('login')

    threshold_date = date.today() + timedelta(days=60)

    # -----------------------------------
    # Subquery: renewal exists AND is NOT approved
    # -----------------------------------
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(application_status='A')

    # -----------------------------------
    # ECs expiring soon & NOT pending renewal
    # -----------------------------------
    application_details = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=applicant_id,
            service_type__in=["Main Activity", "Old EC"],
            ec_reference_no__isnull=False,
            ec_reference_no__gt='',          # covers empty string
            ec_expiry_date__isnull=False,
            ec_expiry_date__lt=threshold_date,
        )
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
        .order_by('ec_expiry_date')
    )

    # -----------------------------------
    # Renewal details (pending only)
    # -----------------------------------
    renewal_details = t_ec_renewal_t2.objects.filter(
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
    tor_converted_exists = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    )

    tor_application_count = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=applicant_id,
            application_status='A',
            application_no__contains='TOR',
        )
        .annotate(is_converted=Exists(tor_converted_exists))
        .filter(is_converted=False)
        .count()
    )

    # -----------------------------------
    # Context
    # -----------------------------------
    context = {
        'application_details': application_details,
        'app_hist_count': app_hist_count,
        'renewal_details': renewal_details,
        'service_details': service_details,
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
    ec_reference_no = request.GET.get('ec_reference_no')
    service_code = 'REN'
    application_no = get_ren_application_no(request, service_code, '10')
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no,service_type="Main Activity")
    for app_details in application_details:
        ec_data = t_ec_industries_t11_ec_details.objects.filter(application_no=app_details.application_no,ec_type='Terms')
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    ec_application_details = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()
    if ec_application_details.exists():
        ec_details = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)    
        return render(request, 'renewal_details.html',{'application_details':application_details,'application_no':application_no, 'ec_details':ec_details,
                                                        'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})
    else:
        for ec_data in ec_data:
            t_ec_renewal_t2.objects.create(application_no=application_no, ec_reference_no=ec_reference_no,ec_heading=ec_data.ec_heading,ec_terms=ec_data.ec_terms)
        ec_details = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)    
        return render(request, 'renewal_details.html',{'application_details':application_details,'application_no':application_no, 'ec_details':ec_details,'ec_renewal_count':ec_renewal_count,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})

def submit_renew_application(request):
    data = {"message": "failure"}

    try:
        ec_reference_no = request.POST.get('ec_reference_no')
        application_no = request.POST.get('application_no')
        initiatives_undertaken = request.POST.get('initiatives_undertaken')
        remarks = request.POST.get('initiatives_undertaken_remarks')

        if not ec_reference_no or not application_no:
            return JsonResponse(
                {"message": "Missing required fields"},
                status=400
            )

        # Fetch single record safely
        application_details = (
            t_ec_industries_t1_general.objects
            .filter(ec_reference_no=ec_reference_no)
            .first()
        )

        if not application_details:
            return JsonResponse(
                {"message": "Invalid EC reference number"},
                status=404
            )

        with transaction.atomic():
            # Create renewal record
            t_ec_renewal_t1.objects.create(
                application_no=application_no,
                ec_reference_no=ec_reference_no,
                proponent_name=application_details.applicant_name,
                address=application_details.address,
                initiatives_undertaken=initiatives_undertaken,
                remarks=remarks,
                submission_date=timezone.now(),
                action_date=timezone.now(),
                application_status='P'
            )

            # Create workflow record
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

        data["message"] = "success"

    except Exception as e:
        print("Submit renewal application error:", e)

    return JsonResponse(data)

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
    application_no = request.POST.get('application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='ECR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECR')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})


def save_compliance_details(request):
    ec_terms_id = request.POST.get('ec_terms_id')
    action_undertaken = request.POST.get('action_undertaken')
    remarks = request.POST.get('remarks')
    

    app_details = t_ec_renewal_t2.objects.filter(record_id=ec_terms_id)
    app_details.update(action_undertaken=action_undertaken,remarks=remarks)

    ec_details = t_ec_renewal_t2.objects.filter(record_id=ec_terms_id)
    return render(request, 'ec_details.html', {'ec_details': ec_details})

def send_renew_payment_mail(name, email_id, amount):
    subject = 'Application Submitted'
    message = "Dear " + name + " Your Application for Renewal OF Environment Clearance Is Submitted. Please Make A Payment of " \
              + str(amount) + ""
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    
def get_ren_application_no(request, service_code, service_id):
    last_application_no = t_ec_renewal_t1.objects.aggregate(max_app=Max('application_no'))['max_app']
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

# TOR DETAILS
def tor_form(request):
    service_code = 'TOR'
    application_no = get_application_no(request, service_code, None)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()

    return render(request, 'tor_form.html', {'app_hist_count':app_hist_count,'application_no':application_no,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde})


def save_tor_form(request):
    data = {}
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        focal_person = request.POST.get('focal_person')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        if dzongkhag_throm == 'Thromde':
            dzongkhag = None
            gewog = None
            vil_chiwog = None
            thromde = request.POST.get('thromde_id')
        else:
            dzongkhag = request.POST.get('dzongkhag')
            gewog = request.POST.get('gewog')
            vil_chiwog = request.POST.get('vil_chiwog')
            thromde = None
        location_name = request.POST.get('location_name')

        broad_activity_code = request.session['broad_activity_code']
        specific_activity_code = request.session['specific_activity_code']
        category = request.session['category']
        service_id = request.session['service_id']
        login_id = request.session['login_id']
        name = request.session['name']
        colour_code = request.session['colour_code']

        application_date = timezone.now().date()
        action_date = application_date
        ca_auth = None
        account_head = None
        
        auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=dzongkhag if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
        ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        # Insert record in t_ec_industries_t1_general table
        t_ec_industries_t1_general.objects.create(
            application_no=application_no,
            project_name=project_name,
            applicant_name=applicant_name,
            application_date=application_date,
            address=address,
            contact_no=contact_no,
            email=email,
            focal_person=focal_person,
            dzongkhag_throm=dzongkhag_throm,
            thromde_id=thromde,
            dzongkhag_code=dzongkhag,
            gewog_code=gewog,
            village_code=vil_chiwog,
            location_name=location_name,
            broad_activity_code=broad_activity_code,
            specific_activity_code=specific_activity_code,
            category=category,
            applicant_id=request.session['email'],
            ca_authority=ca_auth,
            application_status='P',
            action_date=action_date,
            service_id=service_id,
            application_source='ECSS',
            colour_code=colour_code
        )

        # Insert record in t_application_history table
        t_application_history.objects.create(
            application_no=application_no,
            application_date=application_date,
            applicant_id=request.session['email'],
            ca_authority=ca_auth,
            service_id=service_id,
            application_status='P',
            action_date=action_date,
            actor_id=login_id,
            actor_name=name,
            remarks='TOR Application Submitted',
            status='P'
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
            assigned_role_id='2',
            assigned_role_name='Verifier',
            result=None,
            ca_authority=ca_auth,
            application_source='ECSS'
        )
        payment_details = payment_details_master.objects.filter(payment_type='TOR')
        for pay_dets in payment_details:
            account_head = pay_dets.account_head_code
        make_payment_request(request,application_no,"500",'NEW TOR APPLICATION',request.session['email'],account_head,"TOR")
        send_tor_payment_mail(request.session['name'], request.session['email'], 500)
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
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='TOR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOR')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def tor_list(request):
    applicant_id = request.session.get('email', None)
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no') 
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_details = t_ec_industries_t1_general.objects.filter(
        application_status='A',application_no__contains='TOR',applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    )
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()
    
    service_details = t_service_master.objects.all()
    
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    response = render(request, 'tor/tor_list.html', {'tor_application_count':tor_application_count,'ec_renewal_count':ec_renewal_count,'tor_details':tor_details,'service_details':service_details, 'app_hist_count':app_hist_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_tor_application_details(request):
    applicant_id = request.session.get('email', None)
    tor_application_no = request.GET.get('application_no')
    service_id = request.GET.get('service_id')
    app_det = t_ec_industries_t1_general.objects.filter(application_no=tor_application_no)
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
    tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    service_code = None
    if service_id == '1':
        service_code = 'IEE'
    elif service_id == '2':
        service_code = 'ENE'
    elif service_id == '3':
        service_code = 'ROA'
    elif service_id == '4':
        service_code = 'TRA'
    elif service_id == '5':
        service_code = 'TOU'
    elif service_id == '6':
        service_code = 'GWA'
    elif service_id == '7':
        service_code = 'FOR'
    elif service_id == '8':
        service_code = 'QUA'
    else :
        service_code = 'GEN'

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
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

        application_no = get_application_no(request, service_code, service_id)
        request.session['application_no'] = application_no
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        return render(request, 'tor/tor.html',{'thromde':thromde,'ec_renewal_count':ec_renewal_count,'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,
                                                'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde})



# ReportSubmission
def report_list(request):
    login_type = request.session.get('login_type', None)
    login_id = request.session.get('email', None)

    user_list = t_user_master.objects.all()
    ec_details = t_ec_industries_t1_general.objects.all()

    common_context = {
        'app_hist_count': t_application_history.objects.filter(applicant_id=login_id).count(),
        'user_list': user_list,
        'ec_details': ec_details,
    }

    context = {}

    if login_type == 'C':
        report_list = t_report_submission_t1.objects.filter(created_by=login_id).order_by('submission_date')

        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()

        t1_general_subquery = t_ec_industries_t1_general.objects.filter(
            tor_application_no=OuterRef('application_no')
        ).values('tor_application_no')

        tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=login_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

        expiry_date_threshold = datetime.now().date() + timedelta(days=60)

        # Renewal exists AND is NOT approved
        pending_renewal_exists = t_ec_renewal_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(
            application_status='A'
        )

        non_updated_renewals = (
            t_ec_industries_t1_general.objects
            .filter(
                applicant_id=request.session['email'],
                service_type__in=["Main Activity", "Old EC"],
                ec_expiry_date__lt=expiry_date_threshold,
                ec_expiry_date__isnull=False,
                ec_reference_no__isnull=False,
            )
            .exclude(ec_reference_no='')
            .annotate(has_pending_renewal=Exists(pending_renewal_exists))
            .filter(has_pending_renewal=False)
        )

        ec_renewal_count = non_updated_renewals.count()

        context.update({
            'report_list': report_list,
            'cl_application_count': cl_application_count,
            'tor_application_count': tor_application_count,
            'ec_renewal_count': ec_renewal_count
        })

    elif login_type == 'I':
        ca_authority = request.session['ca_authority']

        report_list = t_report_submission_t1.objects.filter(ca_authority=ca_authority).exclude(report_status='Pending').values().order_by('submission_date')

        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2', assigned_role_name='Verifier', ca_authority=ca_authority
        ).count()

        expiry_date_threshold = datetime.now().date() + timedelta(days=60)

        # Renewal exists AND is NOT approved
        pending_renewal_exists = t_ec_renewal_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(
            application_status='A'
        )

        non_updated_renewals = (
            t_ec_industries_t1_general.objects
            .filter(
                applicant_id=request.session['email'],
                service_type__in=["Main Activity", "Old EC"],
                ec_expiry_date__lt=expiry_date_threshold,
                ec_expiry_date__isnull=False,
                ec_reference_no__isnull=False,
            )
            .exclude(ec_reference_no='')
            .annotate(has_pending_renewal=Exists(pending_renewal_exists))
            .filter(has_pending_renewal=False)
        )

        ec_renewal_count = non_updated_renewals.count()

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
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                    application_status='A',
                                                                                    ec_expiry_date__lt=expiry_date_threshold).count()
        
    return render(request, 'report_submission/report_details.html',
                  {'report_details': report_details, 'app_hist_count': app_hist_count, 'ec_renewal_count': ec_renewal_count, 'cl_application_count': cl_application_count, 'v_application_count': v_application_count, 'details': details, 'file_attach': file_attach})


def viewDraftReport(request, report_reference_no):
    applicant = request.session['email']
    ec_details = t_ec_industries_t1_general.objects.filter(ec_reference_no__isnull=False, applicant_id=applicant)
    report_details = t_report_submission_t1.objects.filter(report_reference_no=report_reference_no)
    details = t_report_submission_t2.objects.filter(report_reference_no=report_reference_no)
    file_attach = t_file_attachment.objects.filter(application_no=report_reference_no)
    return render(request, 'report_submission/report_submission_draft.html',
                  {'report_details':report_details, 'details':details, 'ec_details':ec_details, 'file_attach':file_attach})

def report_submission_form(request):
    applicant = request.session['email']
    ec_details = t_ec_industries_t1_general.objects.filter(ec_reference_no__isnull=False,applicant_id=applicant)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
    return render(request, 'report_submission/report_submission.html', {'ec_details': ec_details, 'app_hist_count':app_hist_count})

def save_report_submission(request):
    data = dict()
    service_code = 'rpt'
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
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + myFile.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ecs_main")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, myFile)
        file_url = "attachments" + "/" + str(
            timezone.now().year) + "/ecs_main" + "/" + file_name
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
    file = t_file_attachment.objects.filter(pk=file_id)
    for file in file:
        fileName = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ecs_main")
        fs.delete(str(fileName))
    file.delete()
    file_attach = t_file_attachment.objects.filter(application_no=referenceNo)
    return render(request, 'report_submission/report_file_attachment.html', {'file_attach': file_attach})


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
    assigned_user_id= request.session.get('login_id', None)
    
    # Retrieve t_ec_industries_t1_general objects with application_status='A' and service_type="Main Activity"
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A', service_type="Main Activity")
    
    # Count the number of t_application_history objects related to the logged-in user
    app_hist_count = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).distinct('application_no').count()
    
    # Count the number of t_workflow_dtls objects with assigned_user_id equal to the logged-in user
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
    tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
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
        
        # Calculate the expiry date threshold as today's date plus 30 days
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        
        # Count the number of t_ec_industries_t1_general objects with ca_authority matching the logged-in user's 'ca_authority',
        # application_status='A', and ec_expiry_date less than the expiry date threshold
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                     application_status='A',
                                                                     ec_expiry_date__lt=expiry_date_threshold).count()

        
    else:
        # If 'ca_authority' is not found or empty, set the variables to appropriate default values
        v_application_count = 0
        r_application_count = 0
        ec_renewal_count = 0
    
    # Pass the retrieved data to the 'ec_print_list.html' template for rendering
    payment_details = t_payment_details.objects.all()
    service_details = t_service_master.objects.all()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    response = render(request, 'EC/ec_print_list.html', {'application_details': application_details,
                                                     'ec_renewal_count': ec_renewal_count,
                                                     'app_hist_count': app_hist_count,
                                                     'cl_application_count': cl_application_count,
                                                     'v_application_count': v_application_count,
                                                     'r_application_count': r_application_count,
                                                     'tor_application_count':tor_application_count,
                                                     'service_details':service_details,
                                                     'payment_details':payment_details})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_print_details(request):
    # Retrieve the 'ec_reference_no' parameter from the GET request
    ec_reference_no = request.GET.get('ec_reference_no')
    
    # Retrieve t_ec_industries_t1_general objects with ec_reference_no=ec_reference_no and service_type="Main Activity"
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no, service_type="Main Activity")
    
    # Retrieve t_ec_industries_t11_ec_details objects with ec_reference_no=ec_reference_no
    ec_details = t_ec_industries_t11_ec_details.objects.filter(ec_reference_no=ec_reference_no)
    
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
                                                 'r_application_count': r_application_count})


# OTHER MODIFICATION DETAILS
def name_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'NC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def ownership_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'OC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def technology_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A', service_id__in=['1', '2', '6'])
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'TC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def product_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A', service_id='1')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()
    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'OC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def capacity_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.exclude(application_status='A', service_id='3')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'CC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def area_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'AC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def location_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(
            applicant_id=email
        ).distinct('application_no').count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
        )
        .exclude(ec_reference_no='')
        .annotate(has_pending_renewal=Exists(pending_renewal_exists))
        .filter(has_pending_renewal=False)
    )

    ec_renewal_count = non_updated_renewals.count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'LC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_other_modification_details(request):
    ec_reference_no = request.GET.get('ec_reference_no')
    identifier = request.GET.get('identifier')
    app_no = None
    service_id = None
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
    for app_details in application_details:
        service_id = app_details.service_id
        app_no = app_details.application_no
        request.session['service_id'] = service_id
    if identifier == 'NC' or 'OC':
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)

        # Renewal exists AND is NOT approved
        pending_renewal_exists = t_ec_renewal_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).exclude(
            application_status='A'
        )

        non_updated_renewals = (
            t_ec_industries_t1_general.objects
            .filter(
                applicant_id=request.session['email'],
                service_type__in=["Main Activity", "Old EC"],
                ec_expiry_date__lt=expiry_date_threshold,
                ec_expiry_date__isnull=False,
                ec_reference_no__isnull=False,
            )
            .exclude(ec_reference_no='')
            .annotate(has_pending_renewal=Exists(pending_renewal_exists))
            .filter(has_pending_renewal=False)
        )

        ec_renewal_count = non_updated_renewals.count()
        return render(request, 'other_modifications/other_modification.html',{'application_details':application_details,'dzongkhag':dzongkhag, 'gewog':gewog,
                                                    'village':village,'ec_renewal_count':ec_renewal_count,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_no':app_no,'identifier':identifier})
    else:
        return redirect(application_form)
    


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
            ref_no = data['refNo']
            
            receipt_list = data['receiptList']
            payment_method = data['paymentMethod']
            payment_mode = data['paymentMode']
            instrument_date = data['instrumentDate']
            # Extracting values from receipt list
            receipt = receipt_list[0]  # Assuming there's only one receipt in the list
            receipt_no = receipt['receiptNo']
            receipt_date = receipt['receiptDate']
            payment_advice_status = receipt['paymentAdviceStatus']
            responseDate = data['responseDate']
            payment_advice_amount_paid = receipt['paymentAdviceAmountPaid']
            
            instrument_date_datetime = datetime.fromisoformat(instrument_date.replace('Z', '+00:00'))
            instrument_date_datetime_utc = instrument_date_datetime.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            original_receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d %H:%M:%S")
            formatted_receipt_date = original_receipt_date.strftime("%Y-%m-%d %H:%M:%S")
            
            original_responseDate = datetime.strptime(responseDate, "%a %b %d %H:%M:%S BTT %Y")
            formatted_responseDate = original_responseDate.strftime("%Y-%m-%d %H:%M:%S")

            payment_details = t_payment_details.objects.filter(ref_no=ref_no)
            payment_details.update(
                payment_method = payment_method,
                payment_mode = payment_mode,
                instrument_date = instrument_date_datetime_utc,
                receipt_no = receipt_no,
                receipt_date = formatted_receipt_date,
                payment_advice_status = payment_advice_status,
                response_date = formatted_responseDate,
                payment_advice_amount_paid = payment_advice_amount_paid
            )

            response_data = {
                "statusCode": "200",
                "statusDescription": "Payment Details received successfully",
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
        t_ec_industries_t1_general.objects
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
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
        application_status='A', application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    # Renewal exists AND is NOT approved
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
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
    pending_renewal_exists = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).exclude(
        application_status='A'
    )

    non_updated_renewals = (
        t_ec_industries_t1_general.objects
        .filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
            ec_expiry_date__isnull=False,
            ec_reference_no__isnull=False,
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
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
        application_status='A', application_no__contains='TOR', applicant_id=applicant_id
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()

    return render(request, 'old_ec_application_form.html', {'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'tor_application_count':tor_application_count, 'thromde': thromde,'ec_renewal_count':ec_renewal_count,
                                                         'dzongkhag': dzongkhag, 'gewog': gewog, 'village': village})

def save_old_ec_general_details(request):
    data = {'message': 'failure'}

    try:
        # identifier is for Old Pending/Draft Application. identifier = 'DR'
        # dzongkhag_throm, application_type, ec_reference_no, ec_issue_date, ec_validity are pulled from the form
        # (old_ec_application_form.html AND pending_old_ec_details.html)
        identifier = request.POST.get('identifier')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        application_type = "Old_EC"
        ec_reference_no = request.POST.get('ec_reference_no')
        ec_issue_date = request.POST.get('ec_issue_date')
        ec_validity = request.POST.get('ec_validity')
        service_type_to_use = 'Main Activity'

        # Get service_id_to_use early for all cases
        service_id_to_use = None
        activity_to_use = None
        color_code_to_use = None
        service_code = None
        ca_auth_to_use = None

        if identifier !='DR':
            # New application - use session values.
            # Get service_id_to_use,  activity_to_use, color_code_to_use from POST data for new applications
            service_id_to_use = request.session['service_id']
            activity_to_use = request.POST.get('activity')
            color_code_to_use = request.session['colour_code']
            # Determine service_code based on service_id_to_use
            service_code_map = {
                '1': 'IEE', '2': 'ENE', '3': 'ROA', '4': 'TRA',
                '5': 'TOU', '6': 'GWA', '7': 'FOR', '8': 'QUA'
            }
            service_code = service_code_map.get(request.session.get('service_id'), 'GEN')
        else:
            # For Update, get reference application number
            ref_application_no = None
            if identifier == 'DR':
                ref_application_no = request.POST.get('application_no')
            # Get existing application details
            existing_app = None
            if ref_application_no:
                existing_app = t_ec_industries_t1_general.objects.filter(
                    application_no=ref_application_no
                ).first()

            if existing_app:
                service_id_to_use = existing_app.service_id
                activity_to_use = existing_app.activity
                color_code_to_use = existing_app.colour_code
            else:
                # If no existing app found, fall back to session values
                service_id_to_use = request.session['service_id']
                activity_to_use = request.session.get('activity')
                color_code_to_use = request.session['colour_code']

        # Determine application number based on identifier
        if identifier !='DR':
            # For new applications, use session service_id
            application_no = get_application_no(request, service_code, service_id_to_use)
        else:
            # For modifications, use the service_id from existing application
            application_no = ref_application_no  # Use existing application number for draft

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

        common_data = {
            'application_no': application_no,
            'application_date': timezone.now().date(),
            'application_type': application_type,
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
            'project_name': request.POST.get('project_name'),
            'project_description': request.POST.get('project_description'),
            'dzongkhag_throm': dzongkhag_throm,
            'service_type': service_type_to_use,  # Use determined service_type
            'service_id': service_id_to_use,
            'colour_code': color_code_to_use,  # Use determined color code
            'proponent_type': request.session.get('proponent_type'),
            'activity': activity_to_use,  # Use determined activity,
            'ec_reference_no': ec_reference_no,
            'ec_approve_date': ec_issue_date,
            'ec_expiry_date': ec_validity
        }

        with transaction.atomic():
            ca_auth = ca_auth_to_use  # Use the ca_auth we already determined

            # If ca_auth wasn't determined from existing app, calculate it
            if ca_auth is None:
                # Determine ca_auth from the POST data.
                #IN CASE of DEC and THROMDE, based on the selection of Dzo and thromde,
                # The ca_auth will change EVEN in DRAFT application
                if identifier =='DR':
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
                existing_app = None
                existing_app = t_ec_industries_t1_general.objects.filter(application_no=ref_application_no).first()
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
                    t_ec_industries_t1_general.objects.filter(
                        application_no=ref_application_no
                    ).update(**update_data)

                    print(f"DR - Updated existing application {ref_application_no}")
                else:
                    # If no existing app, create new one with session color code
                    new_data = {
                        'ca_authority': ca_auth,
                        #'prev_ec_reference_no': prev_ec_reference_no if prev_ec_reference_no else None
                    }
                    # Ensure service_type is 'Main Activity' for DR
                    common_data['service_type'] = 'Main Activity'
                    t_ec_industries_t1_general.objects.create(**common_data, **new_data)
                    print(f"DR - Created new application {application_no}")
            else:
                new_data = {
                    'ca_authority': ca_auth,
                    # 'prev_ec_reference_no': prev_ec_reference_no if prev_ec_reference_no else None
                }
                t_ec_industries_t1_general.objects.create(**common_data, **new_data)

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

            data['message'] = 'success'
            data['application_no'] = application_no

    except Exception as e:
        print('An error occurred:', e)
        data['error'] = str(e)

    return JsonResponse(data)

def submit_old_ec_general_application(request):
    data = {}
    try:
        application_no = request.POST.get('general_disclaimer_application_no')
        identifier = request.GET.get('identifier')

        # Get application details
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        main_application = application_details.filter(service_type='Main Activity').first()

        if not main_application:
            data['error'] = "No main application found"
            return JsonResponse(data, status=400)

        if identifier in ['A', 'R']:
            main_application.application_status = identifier
            main_application.assigned_by = request.session['login_id']
            main_application.assigned_date = timezone.now()
            main_application.save()
        else:
            main_application.action_date = timezone.now()
            main_application.application_status = identifier
            main_application.save()

        # Update HISTORY

        t_application_history.objects.filter(application_no=application_no, service_type='Main Activity').update(
            remarks='OLD EC Submitted',
            action_date=timezone.now(),
            application_status= identifier

        )
        data['message'] = "success"
    except Exception as e:
        data['error'] = str(e).split("\n")[0]
    return JsonResponse(data)

# OLD EC UPDATE END