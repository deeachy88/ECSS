from datetime import date, datetime, timedelta, timezone
import json
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import connection
from django.contrib.sessions.models import Session

from django.http import JsonResponse
from django.shortcuts import render
import requests
from django.db.models import Count, Subquery, OuterRef
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from ecs_admin.models import t_bsic_code, t_competant_authority_master, t_dzongkhag_master, t_file_attachment, t_gewog_master, t_role_master, t_security_question_master, t_service_master, t_thromde_master, t_user_master, t_village_master
from ecs_main.models import t_application_history
from proponent.models import t_ec_industries_t1_general, t_ec_renewal_t1, t_ec_renewal_t2, t_payment_details, t_report_submission_t1, t_workflow_dtls

def new_application(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    #bsic_details = t_bsic_code.objects.all()
    bsic_details = t_bsic_code.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
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
    response = render(request, 'new_application.html',{'bsic_details':bsic_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_application_service_id(request):
    data = dict()
    activity = request.GET.get('activity')

    activity_details = t_bsic_code.objects.filter(activity=activity)
    for cat_details in activity_details:
        print(cat_details.competent_authority)
        request.session['ca_auth'] = cat_details.competent_authority
        request.session['colour_code'] = cat_details.colour_code
        request.session['service_id'] = cat_details.service_id
        request.session['has_tor'] = cat_details.has_tor
        request.session['activity'] = cat_details.activity
        data['service_id'] = cat_details.service_id
        data['colour_code'] = cat_details.colour_code
        data['ca_auth'] = cat_details.competent_authority
        data['has_tor'] = cat_details.has_tor
    return JsonResponse(data)

def application_form(request):
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
    application_no = get_application_no(request, service_code, '1')
    request.session['application_no'] = application_no
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    return render(request, 'new_application_form.html',{'application_no':application_no,'thromde':thromde,
                                                     'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

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
    data = {}
    try:
        identifier = request.POST.get('identifier')
        application_no = request.POST.get('application_no')
        tor_application_no = request.POST.get('tor_application_no')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        service_type = request.POST.get('service_type')
        application_type = "New"

        # 2. Handle location data
        dzongkhag_code = gewog_code = village_code = thromde_id = None
        if dzongkhag_throm == 'Thromde':
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')

        common_fields = {
            # Application metadata
            'application_date': timezone.now().date(),
            'application_type': application_type,
            'application_source': 'ECSS',
            'application_status': 'P',

            # Project details
            'project_name': request.POST.get('project_name'),
            'project_category': request.POST.get('project_category'),
            'location_name': request.POST.get('project_site'),

            # Applicant information
            'applicant_name': request.POST.get('applicant_name'),
            'address': request.POST.get('address'),
            'contact_no': request.POST.get('contact_no'),
            'email': request.POST.get('email'),
            'focal_person': request.POST.get('focal_person'),
            'cid': request.session.get('cid'),

            # Location data
            'dzongkhag_throm': dzongkhag_throm,
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,

            # System fields
            'service_type':service_type,
            'tor_application_no': tor_application_no,
            'applicant_id': request.session.get('email'),
            'colour_code': request.session.get('colour_code'),
            'service_id': request.session.get('service_id'),
            
        }
        ca_auth = None
        if identifier not in ['DR', 'NC', 'OC'] and tor_application_no is None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session.get('ca_auth'),
                dzongkhag_code_id=dzongkhag_code if request.session.get('ca_auth') in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier in ['NC', 'OC']:
            auth_filter = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        elif tor_application_no:
            auth_filter = t_ec_industries_t1_general.objects.filter(application_no=tor_application_no)
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None

        common_fields['ca_authority'] = ca_auth

        # 5. Database operations with proper service_type handling
        with transaction.atomic():
            # Check if application exists with same service_type
            existing_app = t_ec_industries_t1_general.objects.filter(
                application_no=application_no,
                service_type=service_type
            ).first()

            if existing_app:
                # Update existing application
                if identifier == 'NC':
                    update_fields = {
                        'project_name': common_fields['project_name'],
                        'service_type': identifier
                    }
                elif identifier == 'OC':
                    update_fields = {
                        'applicant_name': common_fields['applicant_name'],
                        'service_type': identifier
                    }
                elif identifier == 'DR':
                    protected_fields = {
                        'service_type', 'ca_authority', 'applicant_id', 'colour_code',
                        'activity', 'application_source', 'application_status'
                    }
                    update_fields = {k: v for k, v in common_fields.items() 
                                if k not in protected_fields}
                else:  # General update
                    update_fields = common_fields

                # Perform the update
                t_ec_industries_t1_general.objects.filter(
                    application_no=application_no,
                    service_type=service_type
                ).update(**update_fields)
            else:
                # Create new application
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    **common_fields
                )

            # Update workflow - now including service_type in the filter
            t_workflow_dtls.objects.update_or_create(
                application_no=application_no,
                service_type=service_type,  # Added service_type to ensure unique workflow per service
                defaults={
                    'application_status': 'P',
                    'actor_id': request.session.get('login_id'),
                    'actor_name': request.session.get('name'),
                    'assigned_role_id': '3',
                    'assigned_role_name': 'Reviewer',
                    'service_id': request.session.get('service_id'),
                    'ca_authority': ca_auth,
                    'application_source': 'ECSS',
                    'service_type':service_type
                }
            )

            # Create history record - now properly tracking by service_type
            if not t_application_history.objects.filter(application_no=application_no).exists():
                t_application_history.objects.create(
                application_no=application_no,
                service_type=service_type,  # Added service_type to history
                application_date=timezone.now().date(),
                applicant_id=request.session.get('email'),
                ca_authority=ca_auth,
                service_id=request.session.get('service_id'),
                application_status='P',
                actor_id=request.session.get('login_id'),
                actor_name=request.session.get('name'),
                action_date=timezone.now()
            )

        data['message'] = "success"
    except Exception as e:
        data['error'] = str(e)
        logger.error(f"Error saving application {application_no} (service: {service_type}): {str(e)}", 
                exc_info=True)
    return JsonResponse(data)


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
        disclaimer_identifier = request.POST.get('disclaimer_identifier')
        
        if disclaimer_identifier in ('OC', 'NC'):
            t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())
            data['message'] = "success"
            return JsonResponse(data)
        
        # Get application details
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        main_application = application_details.filter(service_type='Main Activity').first()

        if disclaimer_identifier in ('OC', 'NC'):
            t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())
            data['message'] = "success"
            return JsonResponse(data)
        
        # Get application details
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        main_application = application_details.filter(service_type='Main Activity').first()

        if not main_application:
            data['error'] = "No main application found"
            return JsonResponse(data, status=400)
        
        main_application.action_date = timezone.now()
        main_application.save()

        # Update workflow
        workflow_update = {'action_date': timezone.now()}
        t_workflow_dtls.objects.filter(application_no=application_no,service_type='Main Activity').update(**workflow_update)
        t_application_history.objects.filter(application_no=application_no,service_type='Main Activity').update(
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
    print(applicant_id)
    application_details = t_ec_industries_t1_general.objects.filter(applicant_id=applicant_id,application_status='P',service_type='Main Activity',action_date__isnull=True)
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
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
    
    response = render(request, 'draft/application_list.html',{'application_details':application_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'service_details':service_details, 'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


# EC RENEWAL
def ec_renewal(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
 
    existing_renewals = t_ec_renewal_t1.objects.values_list('ec_reference_no', flat=True)

    # Filter applications that are expired but not yet renewed
    application_details = t_ec_industries_t1_general.objects.filter(
        applicant_id=applicant_id,
        ec_expiry_date__lt=date.today(),
        service_type="Main Activity"
    ).exclude(ec_reference_no__in=existing_renewals)
    renewal_details = t_ec_renewal_t2.objects.filter(application_status=None)
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    #cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
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
    response = render(request, 'renewal.html',{'application_details':application_details,'app_hist_count':app_hist_count,'renewal_details':renewal_details,'service_details':service_details,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response



# TOR DETAILS
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
    service_details = t_service_master.objects.all()
    
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    response = render(request, 'tor/tor_list.html', {'tor_application_count':tor_application_count,'tor_details':tor_details,'service_details':service_details, 'app_hist_count':app_hist_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


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

        context.update({
            'report_list': report_list,
            'cl_application_count': cl_application_count,
            'tor_application_count': tor_application_count,
        })

    elif login_type == 'I':
        ca_authority = request.session['ca_authority']
        expiry_date_threshold = timezone.now() + timedelta(days=30)

        report_list = t_report_submission_t1.objects.filter(ca_authority=ca_authority).exclude(report_status='Pending').values().order_by('submission_date')

        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2', assigned_role_name='Verifier', ca_authority=ca_authority
        ).count()

        expiry_date_threshold = datetime.now().date() + timedelta(days=30)

        non_renewed_applications = t_ec_industries_t1_general.objects.filter(
            applicant_id=login_id,
            ec_expiry_date__lt=expiry_date_threshold,
            service_type="Main Activity"
        ).exclude(
            ec_reference_no__in=Subquery(
                t_ec_renewal_t1.objects.values('ec_reference_no')
            )
        )

        ec_renewal_count = non_renewed_applications.count()

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


def ec_print_list(request):
    applicant_id = request.session.get('email', None)
    assigned_user_id= request.session.get('login_id', None)
    
    # Retrieve t_ec_industries_t1_general objects with application_status='A' and service_type="Main Activity"
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A', service_type="Main Activity")
    
    # Count the number of t_application_history objects related to the logged-in user
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    
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
        expiry_date_threshold = datetime.now().date() + timedelta(days=30)
        
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

# OTHER MODIFICATION DETAILS
# OTHER MODIFICATION DETAILS
def name_change(request):
    email = request.session.get('email', None)
    applicant_id = request.session.get('login_id', None)
    workflow_details = t_workflow_dtls.objects.filter(application_status='A')
    application_details = t_ec_industries_t1_general.objects.filter(application_status='A',applicant_id=email)
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'NC','tor_application_count':tor_application_count})

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
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'OC','tor_application_count':tor_application_count})

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
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'TC','tor_application_count':tor_application_count})

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
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'OC','tor_application_count':tor_application_count})

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
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'CC','tor_application_count':tor_application_count})

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
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=applicant_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'AC','tor_application_count':tor_application_count})

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
    app_hist_count = t_application_history.objects.filter(applicant_id=email).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=email
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'other_modification_details.html', {'workflow_details':workflow_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'cl_application_count':cl_application_count, 'application_details':application_details, 'identifier':'LC','tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_other_modification_details(request):
    ec_reference_no = request.GET.get('ec_reference_no')
    app_no = None

    app_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)

    for app_details in app_details:
        app_no = app_details.application_no

    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'other_modifications/other_modification.html',{'application_details':application_details,'dzongkhag':dzongkhag, 'gewog':gewog,
                                                'village':village,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'application_no':app_no})