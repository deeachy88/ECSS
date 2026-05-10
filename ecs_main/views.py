import json
import threading
import logging
import random
import string
from django.http import JsonResponse
from django.shortcuts import redirect, render
import requests
from ecs_admin.views import bsic_master, get_auth_token
from ecs_admin.models import payment_details_master, t_bsic_code, t_dzongkhag_master, t_file_attachment, t_gewog_master, t_role_master, t_service_master, t_thromde_master, t_user_master, t_village_master
from ecs_main.models import t_application_history, t_inspection_monitoring_t1
from django.utils import timezone
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from datetime import datetime, timedelta, date
from datetime import date
from django.db.models import Count, Subquery, OuterRef,Exists
from django.utils.timezone import now
from django.db.models import Q
from django.db import transaction
from django.db.models import Prefetch, Count, Q, Case, When, Value, BooleanField
from django.db import connection
from collections import defaultdict
from django.conf import settings

from proponent.models import t_ec_additional_information, t_ec_application_t2, t_ec_application_t1, t_ec_compliance, t_fines_penalties, t_payment_details, t_workflow_dtls, t_ec_t1, t_ec_t2, t_ec_t1_history, t_ec_t2_history

logger = logging.getLogger(__name__)

def verify_application_list(request):
    """
    Optimized version - applications are clickable only when ALL payment receipts exist
    """
    ca_authority = request.session.get('ca_authority')
    login_id = request.session.get('login_id')
    
    if not ca_authority or not login_id:
        return render(request, 'application_list.html', {
            'application_data': [],
            'error': 'Invalid session data'
        })
    
    try:
        # Get application list
        application_list = t_workflow_dtls.objects.filter(
            assigned_role_id='2',
            action_date__isnull=False,
            ca_authority=ca_authority,
            application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ']
        ).order_by('-action_date')
        
        #print(f"DEBUG: Applications found: {application_list.count()}")

        # EC Renewal List ( Due for renewal)
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        ec_renewal_count = t_ec_t1.objects.filter(
            ca_authority=ca_authority,
            status='A',
            ec_expiry_date__lt=expiry_date_threshold
        ).count()
        
        # Get application numbers for efficient lookup
        application_nos = [app.application_no for app in application_list]
        
        # OPTIMIZED: Get payment receipts only for applications in our list
        payment_receipt_lookup = {}
        payments = t_payment_details.objects.filter(ref_no__in=application_nos)
        
        # Group payments by ref_no
        payments_by_ref = {}
        for payment in payments:
            if payment.application_no:
                if payment.application_no not in payments_by_ref:
                    payments_by_ref[payment.application_no] = []
                payments_by_ref[payment.application_no].append(payment)
        
        # Check for each ref_no if ALL entries have receipt_no
        for application_no, payment_list in payments_by_ref.items():
            # Check if ALL payments for this ref_no have non-null receipt_no
            all_have_receipt = all(payment.receipt_no is not None and payment.receipt_no != '' 
                                 for payment in payment_list)
            payment_receipt_lookup[application_no] = all_have_receipt
        
        # Get service names
        service_lookup = dict(t_service_master.objects.values_list('service_id', 'service_name'))

        # Industry details lookup (project_name and activity)
        # Step 1: Get all application numbers from workflow
        app_numbers = [app.application_no for app in application_list]

        # Step 2: Check which are renewal applications
        # Get renewal applications and their ec_reference_no
        renewal_apps = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'ec_reference_no')

        # Create mapping: renewal_application_no -> ec_reference_no
        renewal_mapping = {r['application_no']: r['ec_reference_no'] for r in renewal_apps}

        # Step 3: Get project_name and activity for ALL applications
        # First, get direct matches (new applications)
        direct_matches = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'project_name', 'activity')

        # Create lookup for direct matches
        industry_lookup = {}
        for match in direct_matches:
            industry_lookup[match['application_no']] = {
                'project_name': match['project_name'] or 'N/A',
                'activity': match['activity'] or 'N/A'
            }

        # Step 4: Get project_name and activity for renewal applications
        # Get ec_reference_no values from renewal applications
        renewal_ref_nos = list(renewal_mapping.values())

        if renewal_ref_nos:
            # Get original applications for renewal references
            renewal_original_apps = t_ec_application_t1.objects.filter(
                ec_reference_no__in=renewal_ref_nos
            ).values('ec_reference_no', 'project_name', 'activity')

            # Create mapping: ec_reference_no -> project/activity
            renewal_original_lookup = {}
            for app in renewal_original_apps:
                renewal_original_lookup[app['ec_reference_no']] = {
                    'project_name': app['project_name'] or 'N/A',
                    'activity': app['activity'] or 'N/A'
                }

            # Now map renewal application_no to project/activity
            for renewal_app_no, ec_ref_no in renewal_mapping.items():
                if ec_ref_no in renewal_original_lookup:
                    industry_lookup[renewal_app_no] = renewal_original_lookup[ec_ref_no]

        # Process data
        application_data = []
        for app in application_list:
            # Check if application has payments AND all payments have receipts
            has_payments = app.application_no in payment_receipt_lookup
            all_payments_have_receipt = payment_receipt_lookup.get(app.application_no, False)
            
            is_clickable = has_payments and all_payments_have_receipt
            industry_data = industry_lookup.get(app.application_no, {})
            application_data.append({
                'application_no': app.application_no,
                'service_id': app.service_id,
                'service_name': service_lookup.get(app.service_id, 'Service Not Found'),
                'action_date': app.action_date,
                'application_source': app.application_source,
                'is_clickable': is_clickable,  # Only clickable if ALL receipts exist
                'application_status': app.application_status,
                'project_name': industry_data.get('project_name', ''),
                'activity': industry_data.get('activity', '')
            })
        
        # Get counts
        v_application_count = (application_list.filter(
            application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
            ca_authority=ca_authority
        ).count())

        context = {
            'application_data': application_data,
            'v_application_count': v_application_count,
            'ec_renewal_count': ec_renewal_count,
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        context = {
            'application_data': [],
            'error': str(e)
        }
    
    return render(request, 'application_list.html', context)
    

def client_application_list(request):
    """
    Optimized client application list view with preprocessed data
    """
    # Get session data
    login_id = request.session.get('login_id')
    applicant_id = request.session.get('email')
    
    # Validate session data
    if not login_id or not applicant_id:
        context = {
            'application_data': [],
            'cl_application_count': 0,
            'app_hist_count': 0,
            'tor_application_count': 0,
            'error': 'Invalid session data'
        }
        return render(request, 'application_list.html', context)
    
    try:
        # Base query filters
        base_filters = {
            'action_date__isnull': False,
            'assigned_user_id': login_id
        }
        
        # Application status query using Q objects (more efficient)
        status_query = (
            Q(application_status='ALR') | 
            Q(application_status='EATC') | 
            Q(application_status='RS') | 
            Q(application_status='LU') | 
            Q(application_status='ALA')
        )
        
        # Get applications - single query instead of multiple OR queries
        application_list = t_workflow_dtls.objects.filter(
            Q(**base_filters) & status_query
        )
        
        # Prefetch all related data in single queries
        # 1. Services lookup
        service_lookup = {
            service.service_id: service.service_name 
            for service in t_service_master.objects.all()
        }
        
        # 2. Payments lookup - check if ALL entries for each ref_no have receipt_no
        payment_receipt_lookup = {}
        payments = t_payment_details.objects.all()
        
        # Group payments by ref_no
        payments_by_ref = {}
        for payment in payments:
            if payment.ref_no:
                if payment.ref_no not in payments_by_ref:
                    payments_by_ref[payment.ref_no] = []
                payments_by_ref[payment.ref_no].append(payment)
        
        # Check for each ref_no if ALL entries have receipt_no
        for ref_no, payment_list in payments_by_ref.items():
            # Check if ALL payments for this ref_no have non-null receipt_no
            all_have_receipt = all(payment.receipt_no is not None and payment.receipt_no != '' 
                                 for payment in payment_list)
            payment_receipt_lookup[ref_no] = all_have_receipt
        
        # 3. Application history count
        app_hist_count = (
            t_application_history.objects.filter(
                applicant_id=applicant_id)
            .values('application_no')
            .distinct()
            .count()
        )
        # 4. Client application count
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=login_id).count()

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
                status='A'
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

        draft_count = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id,
            application_status='P',
            service_type='Main Activity',
            action_date__isnull=True
        ).count()

        tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',
            applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

        # Industry details lookup (project_name and activity)
        # Step 1: Get all application numbers from workflow
        app_numbers = [app.application_no for app in application_list]

        # Step 2: Check which are renewal applications
        # Get renewal applications and their ec_reference_no
        renewal_apps = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'ec_reference_no')

        # Create mapping: renewal_application_no -> ec_reference_no
        renewal_mapping = {r['application_no']: r['ec_reference_no'] for r in renewal_apps}

        # Step 3: Get project_name and activity for ALL applications
        # First, get direct matches (new applications)
        direct_matches = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'project_name', 'activity')

        # Create lookup for direct matches
        industry_lookup = {}
        for match in direct_matches:
            industry_lookup[match['application_no']] = {
                'project_name': match['project_name'] or 'N/A',
                'activity': match['activity'] or 'N/A'
            }

        # Step 4: Get project_name and activity for renewal applications
        # Get ec_reference_no values from renewal applications
        renewal_ref_nos = list(renewal_mapping.values())

        if renewal_ref_nos:
            # Get original applications for renewal references
            renewal_original_apps = t_ec_application_t1.objects.filter(
                ec_reference_no__in=renewal_ref_nos
            ).values('ec_reference_no', 'project_name', 'activity')

            # Create mapping: ec_reference_no -> project/activity
            renewal_original_lookup = {}
            for app in renewal_original_apps:
                renewal_original_lookup[app['ec_reference_no']] = {
                    'project_name': app['project_name'] or 'N/A',
                    'activity': app['activity'] or 'N/A'
                }

            # Now map renewal application_no to project/activity
            for renewal_app_no, ec_ref_no in renewal_mapping.items():
                if ec_ref_no in renewal_original_lookup:
                    industry_lookup[renewal_app_no] = renewal_original_lookup[ec_ref_no]

        # Process application data
        application_data = []
        for app in application_list:
            # Determine clickability
            # Check if service_id is 0 OR if application has payments AND all payments have receipts
            has_payments = app.application_no in payment_receipt_lookup
            all_payments_have_receipt = payment_receipt_lookup.get(app.application_no, False)
            
            is_clickable = (app.service_id == 0) or (has_payments and all_payments_have_receipt)
            industry_data = industry_lookup.get(app.application_no, {})

            application_data.append({
                'application_no': app.application_no,
                'service_id': app.service_id,
                'service_name': service_lookup.get(app.service_id, 'Service Not Found'),
                'action_date': app.action_date,
                'application_source': app.application_source,
                'is_clickable': is_clickable,
                'application_status': app.application_status,
                'project_name': industry_data.get('project_name', ''),
                'activity': industry_data.get('activity', '')

            })
        
        # Sort by action date (newest first)
        application_data.sort(key=lambda x: x['action_date'], reverse=True)
        
        context = {
            'application_data': application_data,
            'cl_application_count': cl_application_count,
            'app_hist_count': app_hist_count,
            'tor_application_count': tor_application_count,
            'draft_count': draft_count,
            'ec_renewal_count': ec_renewal_count
        }
        
    except Exception as e:
        # Log the error
        print(f"Error in client_application_list: {e}")
        context = {
            'application_data': [],
            'cl_application_count': 0,
            'app_hist_count': 0,
            'tor_application_count': 0,
            'ec_renewal_count': 0,
            'error': 'An error occurred while loading applications'
        }
    
    response = render(request, 'application_list.html', context)
    # Add cache control
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# START Payment Amount Update bt Reviewer/Admin. List of application that needs to ve verified and payment update
def reviewer_application_list_payment(request):
    """
    Optimized reviewer application list view with preprocessed data
    """
    # Get session data
    ca_authority = request.session.get('ca_authority')
    login_id = request.session.get('login_id')
    #print(ca_authority, login_id)

    # Validate session data
    if not ca_authority or not login_id:
        context = {
            'application_data': [],
            'r_application_count': 0,
            'error': 'Invalid session data'
        }
        return render(request, 'application_list.html', context)

    try:
        # Base query filters
        base_filters = {
            'assigned_role_id': '3',
            'action_date__isnull': False,
            'ca_authority': ca_authority,
            'application_status': 'P',
            'assigned_user_id__isnull': True,
        }

        # Get applications - single optimized query
        application_list = (
            t_workflow_dtls.objects
            .filter(Q(**base_filters))
            .exclude(ca_authority=1)
        )

        # Prefetch all related data in single queries
        # 1. Services lookup
        service_lookup = {
            service.service_id: service.service_name
            for service in t_service_master.objects.all()
        }

        # 2. Payments lookup - check if ALL entries for each application_no OR ref_no have receipt_no
        payment_receipt_lookup = {}
        payments = t_payment_details.objects.all()

        # Optimized: Group payments by both application_no and ref_no simultaneously
        for payment in payments:
            # Check by application_no if it exists
            if payment.application_no:
                if payment.application_no not in payment_receipt_lookup:
                    # Initialize with payment data and receipt status
                    payment_receipt_lookup[payment.application_no] = {
                        'payments': [payment],
                        'all_have_receipt': (payment.receipt_no is not None and payment.receipt_no != '')
                    }
                else:
                    # Update existing entry
                    existing_entry = payment_receipt_lookup[payment.application_no]
                    existing_entry['payments'].append(payment)
                    # Update all_have_receipt: must be True for all payments
                    existing_entry['all_have_receipt'] = (
                            existing_entry['all_have_receipt'] and
                            (payment.receipt_no is not None and payment.receipt_no != '')
                    )

            # Also check by ref_no if it exists and is different from application_no
            if payment.ref_no and payment.ref_no != payment.application_no:
                if payment.ref_no not in payment_receipt_lookup:
                    payment_receipt_lookup[payment.ref_no] = {
                        'payments': [payment],
                        'all_have_receipt': (payment.receipt_no is not None and payment.receipt_no != '')
                    }
                else:
                    existing_entry = payment_receipt_lookup[payment.ref_no]
                    existing_entry['payments'].append(payment)
                    existing_entry['all_have_receipt'] = (
                            existing_entry['all_have_receipt'] and
                            (payment.receipt_no is not None and payment.receipt_no != '')
                    )

        # Reviewer application count
        r_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_user_id=login_id,
            assigned_role_name='Reviewer',
            ca_authority=ca_authority
        ).count()

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

        # Industry details lookup (project_name and activity)
        # Industry details lookup (project_name and activity)
        # Step 1: Get all application numbers from workflow
        app_numbers = [app.application_no for app in application_list]

        # Step 2: Check which are renewal applications
        # Get renewal applications and their ec_reference_no
        renewal_apps = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'ec_reference_no')

        # Create mapping: renewal_application_no -> ec_reference_no
        renewal_mapping = {r['application_no']: r['ec_reference_no'] for r in renewal_apps}

        # Step 3: Get project_name and activity for ALL applications
        # First, get direct matches (new applications)
        direct_matches = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'project_name', 'activity')

        # Create lookup for direct matches
        industry_lookup = {}
        for match in direct_matches:
            industry_lookup[match['application_no']] = {
                'project_name': match['project_name'] or 'N/A',
                'activity': match['activity'] or 'N/A'
            }

        # Step 4: Get project_name and activity for renewal applications
        # Get ec_reference_no values from renewal applications
        renewal_ref_nos = list(renewal_mapping.values())

        if renewal_ref_nos:
            # Get original applications for renewal references
            renewal_original_apps = t_ec_application_t1.objects.filter(
                ec_reference_no__in=renewal_ref_nos
            ).values('ec_reference_no', 'project_name', 'activity')

            # Create mapping: ec_reference_no -> project/activity
            renewal_original_lookup = {}
            for app in renewal_original_apps:
                renewal_original_lookup[app['ec_reference_no']] = {
                    'project_name': app['project_name'] or 'N/A',
                    'activity': app['activity'] or 'N/A'
                }

            # Now map renewal application_no to project/activity
            for renewal_app_no, ec_ref_no in renewal_mapping.items():
                if ec_ref_no in renewal_original_lookup:
                    industry_lookup[renewal_app_no] = renewal_original_lookup[ec_ref_no]

        # Process application data
        application_data = []
        for app in application_list:
            # Determine clickability - applications with status 'P' are always clickable
            if app.application_status == 'P':
                is_clickable = True
            else:
                # Check if service_id is 0 OR if application has payments AND all payments have receipts
                # Lookup by both application_no and ref_no (they might be the same or different)
                app_payment_data = payment_receipt_lookup.get(app.application_no)

                if app_payment_data:
                    # Found by application_no
                    all_payments_have_receipt = app_payment_data['all_have_receipt']
                else:
                    # Try looking up by ref_no if application_no is different
                    all_payments_have_receipt = False

                is_clickable = (app.service_id == 0) or (app_payment_data and all_payments_have_receipt)
            industry_data = industry_lookup.get(app.application_no, {})

            application_data.append({
                'application_no': app.application_no,
                'service_id': app.service_id,
                'service_name': service_lookup.get(app.service_id, 'Service Not Found'),
                'action_date': app.action_date,
                'application_source': app.application_source,
                'is_clickable': is_clickable,
                'status': app.application_status,
                'project_name': industry_data.get('project_name', ''),
                'activity': industry_data.get('activity', '')

            })

        # Sort by action date (newest first)
        application_data.sort(key=lambda x: x['action_date'], reverse=True)

        context = {
            'application_data': application_data,
            'r_application_count': r_application_count,
            'p_application_count': p_application_count
        }

    except Exception as e:
        # Log the error
        print(f"Error in reviewer_application_list: {e}")
        context = {
            'application_data': [],
            'r_application_count': 0,
            'error': 'An error occurred while loading applications'
        }

    response = render(request, 'reviewer_application_list_payment.html', context)
    # Add cache control
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
# END Payment Amount Update bt Reviewer.


#START Reviewer Application List.
def reviewer_application_list(request):
    """
    Optimized reviewer application list view with preprocessed data
    """
    # Get session data
    ca_authority = request.session.get('ca_authority')
    login_id = request.session.get('login_id')

    # Validate session data
    if not ca_authority or not login_id:
        context = {
            'application_data': [],
            'r_application_count': 0,
            'error': 'Invalid session data'
        }
        return render(request, 'application_list.html', context)

    try:
        # Base query filters
        base_filters = {
            'assigned_role_id': '3',
            'assigned_user_id' : login_id,
            'action_date__isnull': False,
            'ca_authority': ca_authority
        }

        # Application status query using Q objects
        STATUSES = ['ALS', 'FEATC', 'RSS', 'LUS', 'APP', 'AP', 'P']

        status_query = (
            Q(application_status='R', assigned_role_id='3') |
            Q(application_status='ALS') |
            Q(application_status='FEATC') |
            Q(application_status='RSS') |
            Q(application_status='LUS') |
            Q(application_status='APP') |
            Q(application_status='AP') |
            Q(application_status='P')
        )

        # application_status (R: Forwarded to REVIEWER)
        # assigned_role_id (3: REVIEWER)

        # Get applications - single optimized query
        application_list = t_workflow_dtls.objects.filter(
            Q(**base_filters) & status_query
        )

        # Prefetch all related data in single queries
        # 1. Services lookup
        service_lookup = {
            service.service_id: service.service_name
            for service in t_service_master.objects.all()
        }

        # 2. Payments lookup - check if ALL entries for each application_no OR ref_no have receipt_no
        payment_receipt_lookup = {}
        payments = t_payment_details.objects.all()

        # Optimized: Group payments by both application_no and ref_no simultaneously
        for payment in payments:
            # Check by application_no if it exists
            if payment.application_no:
                if payment.application_no not in payment_receipt_lookup:
                    # Initialize with payment data and receipt status
                    payment_receipt_lookup[payment.application_no] = {
                        'payments': [payment],
                        'all_have_receipt': (payment.receipt_no is not None and payment.receipt_no != '')
                    }
                else:
                    # Update existing entry
                    existing_entry = payment_receipt_lookup[payment.application_no]
                    existing_entry['payments'].append(payment)
                    # Update all_have_receipt: must be True for all payments
                    existing_entry['all_have_receipt'] = (
                        existing_entry['all_have_receipt'] and
                        (payment.receipt_no is not None and payment.receipt_no != '')
                    )

            # Also check by ref_no if it exists and is different from application_no
            if payment.ref_no and payment.ref_no != payment.application_no:
                if payment.ref_no not in payment_receipt_lookup:
                    payment_receipt_lookup[payment.ref_no] = {
                        'payments': [payment],
                        'all_have_receipt': (payment.receipt_no is not None and payment.receipt_no != '')
                    }
                else:
                    existing_entry = payment_receipt_lookup[payment.ref_no]
                    existing_entry['payments'].append(payment)
                    existing_entry['all_have_receipt'] = (
                        existing_entry['all_have_receipt'] and
                        (payment.receipt_no is not None and payment.receipt_no != '')
                    )

        # 3. Reviewer application count
        r_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_user_id=login_id,
            assigned_role_name='Reviewer',
            ca_authority=ca_authority

        ).count()

        # 4. Reviewer application count for Payment update
        p_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_role_name='Reviewer',
            ca_authority=ca_authority,
            assigned_user_id__isnull=True,  # assigned_user_id is null
            action_date__isnull=False  # action_date is not null
        ).exclude(
            ca_authority=1  # Exclude ca_authority = 1
        ).count()

        # Industry details lookup (project_name and activity)
        # Step 1: Get all application numbers from workflow
        app_numbers = [app.application_no for app in application_list]

        # Step 2: Check which are renewal applications
        # Get renewal applications and their ec_reference_no
        renewal_apps = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'ec_reference_no')

        # Create mapping: renewal_application_no -> ec_reference_no
        renewal_mapping = {r['application_no']: r['ec_reference_no'] for r in renewal_apps}

        # Step 3: Get project_name and activity for ALL applications
        # First, get direct matches (new applications)
        direct_matches = t_ec_application_t1.objects.filter(
            application_no__in=app_numbers
        ).values('application_no', 'project_name', 'activity')

        # Create lookup for direct matches
        industry_lookup = {}
        for match in direct_matches:
            industry_lookup[match['application_no']] = {
                'project_name': match['project_name'] or 'N/A',
                'activity': match['activity'] or 'N/A'
            }

        # Step 4: Get project_name and activity for renewal applications
        # Get ec_reference_no values from renewal applications
        renewal_ref_nos = list(renewal_mapping.values())

        if renewal_ref_nos:
            # Get original applications for renewal references
            renewal_original_apps = t_ec_application_t1.objects.filter(
                ec_reference_no__in=renewal_ref_nos
            ).values('ec_reference_no', 'project_name', 'activity')

            # Create mapping: ec_reference_no -> project/activity
            renewal_original_lookup = {}
            for app in renewal_original_apps:
                renewal_original_lookup[app['ec_reference_no']] = {
                    'project_name': app['project_name'] or 'N/A',
                    'activity': app['activity'] or 'N/A'
                }

            # Now map renewal application_no to project/activity
            for renewal_app_no, ec_ref_no in renewal_mapping.items():
                if ec_ref_no in renewal_original_lookup:
                    industry_lookup[renewal_app_no] = renewal_original_lookup[ec_ref_no]

        # Process application data
        application_data = []
        for app in application_list:
            # Determine clickability - applications with status 'P' are always clickable
            if app.application_status == 'P':
                is_clickable = True
            else:
                # Check if service_id is 0 OR if application has payments AND all payments have receipts
                # Lookup by both application_no and ref_no (they might be the same or different)
                app_payment_data = payment_receipt_lookup.get(app.application_no)

                if app_payment_data:
                    # Found by application_no
                    all_payments_have_receipt = app_payment_data['all_have_receipt']
                else:
                    # Try looking up by ref_no if application_no is different
                    all_payments_have_receipt = False

                is_clickable = (app.service_id == 0) or (app_payment_data and all_payments_have_receipt)
            industry_data = industry_lookup.get(app.application_no, {})

            application_data.append({
                'application_no': app.application_no,
                'service_id': app.service_id,
                'service_name': service_lookup.get(app.service_id, 'Service Not Found'),
                'action_date': app.action_date,
                'application_source': app.application_source,
                'is_clickable': is_clickable,
                'status': app.application_status,
                'project_name': industry_data.get('project_name', ''),
                'activity': industry_data.get('activity', '')

            })

        # Sort by action date (newest first)
        application_data.sort(key=lambda x: x['action_date'], reverse=True)

        context = {
            'application_data': application_data,
            'r_application_count': r_application_count,
            'p_application_count': p_application_count
        }

    except Exception as e:
        # Log the error
        print(f"Error in reviewer_application_list: {e}")
        context = {
            'application_data': [],
            'r_application_count': 0,
            'error': 'An error occurred while loading applications'
        }

    response = render(request, 'application_list.html', context)
    # Add cache control
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
# END Reviewer Application List.

# Admin Payment Update LIST START
def admin_application_list(request):
    """
    Optimized reviewer application list view with preprocessed data
    """
    # Get session data
    ca_authority = request.session.get('ca_authority')
    login_id = request.session.get('login_id')
    print(ca_authority, login_id)

    # Validate session data
    if not ca_authority or not login_id:
        context = {
            'application_data': [],
            'r_application_count': 0,
            'error': 'Invalid session data'
        }
        return render(request, 'application_list.html', context)

    try:
        # Base query filters
        base_filters = {
            'assigned_role_id': '3',
            'action_date__isnull': False,
            'ca_authority': '1',
            'application_status': 'P'
        }

        # Get applications - single optimized query
        application_list = t_workflow_dtls.objects.filter(
            Q(**base_filters)
        )

        # Prefetch all related data in single queries
        # 1. Services lookup
        service_lookup = {
            service.service_id: service.service_name
            for service in t_service_master.objects.all()
        }

        # 2. Payments lookup - check if ALL entries for each application_no OR ref_no have receipt_no
        payment_receipt_lookup = {}
        payments = t_payment_details.objects.all()

        # Optimized: Group payments by both application_no and ref_no simultaneously
        for payment in payments:
            # Check by application_no if it exists
            if payment.application_no:
                if payment.application_no not in payment_receipt_lookup:
                    # Initialize with payment data and receipt status
                    payment_receipt_lookup[payment.application_no] = {
                        'payments': [payment],
                        'all_have_receipt': (payment.receipt_no is not None and payment.receipt_no != '')
                    }
                else:
                    # Update existing entry
                    existing_entry = payment_receipt_lookup[payment.application_no]
                    existing_entry['payments'].append(payment)
                    # Update all_have_receipt: must be True for all payments
                    existing_entry['all_have_receipt'] = (
                            existing_entry['all_have_receipt'] and
                            (payment.receipt_no is not None and payment.receipt_no != '')
                    )

            # Also check by ref_no if it exists and is different from application_no
            if payment.ref_no and payment.ref_no != payment.application_no:
                if payment.ref_no not in payment_receipt_lookup:
                    payment_receipt_lookup[payment.ref_no] = {
                        'payments': [payment],
                        'all_have_receipt': (payment.receipt_no is not None and payment.receipt_no != '')
                    }
                else:
                    existing_entry = payment_receipt_lookup[payment.ref_no]
                    existing_entry['payments'].append(payment)
                    existing_entry['all_have_receipt'] = (
                            existing_entry['all_have_receipt'] and
                            (payment.receipt_no is not None and payment.receipt_no != '')
                    )

        # 3. Reviewer application count
        r_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_role_name='Reviewer',
            ca_authority='1'
        ).count()

        # Industry details lookup (project_name and activity)
        industry_lookup = {
            industry.application_no: {
                'project_name': industry.project_name,
                'activity': industry.activity
            }
            for industry in t_ec_application_t1.objects.all()
        }

        # Process application data
        application_data = []
        for app in application_list:
            # Determine clickability - applications with status 'P' are always clickable
            if app.application_status == 'P':
                is_clickable = True
            else:
                # Check if service_id is 0 OR if application has payments AND all payments have receipts
                # Lookup by both application_no and ref_no (they might be the same or different)
                app_payment_data = payment_receipt_lookup.get(app.application_no)

                if app_payment_data:
                    # Found by application_no
                    all_payments_have_receipt = app_payment_data['all_have_receipt']
                else:
                    # Try looking up by ref_no if application_no is different
                    all_payments_have_receipt = False

                is_clickable = (app.service_id == 0) or (app_payment_data and all_payments_have_receipt)
            industry_data = industry_lookup.get(app.application_no, {})

            application_data.append({
                'application_no': app.application_no,
                'service_id': app.service_id,
                'service_name': service_lookup.get(app.service_id, 'Service Not Found'),
                'action_date': app.action_date,
                'application_source': app.application_source,
                'is_clickable': is_clickable,
                'status': app.application_status,
                'project_name': industry_data.get('project_name', ''),
                'activity': industry_data.get('activity', '')

            })

        # Sort by action date (newest first)
        application_data.sort(key=lambda x: x['action_date'], reverse=True)

        context = {
            'application_data': application_data,
            'r_application_count': r_application_count
        }

    except Exception as e:
        # Log the error
        print(f"Error in reviewer_application_list: {e}")
        context = {
            'application_data': [],
            'r_application_count': 0,
            'error': 'An error occurred while loading applications'
        }

    response = render(request, 'admin_application_list.html', context)
    # Add cache control
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# Admin Payment Update LIST END

# APPLICATION LISTS FORM IBLS
def ibls_application_list(request):
    role_id = request.session['role_id']
    verifier_list = t_user_master.objects.filter(role_id='2')
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(service_type='AP')
    application_list = t_workflow_dtls.objects.filter(application_status='P', assigned_role_id=role_id, action_date__isnull=False)
    client_application_count = t_user_master.objects.filter(
                accept_reject__isnull=True,
                login_type='C'
            ).count()
    response = render(request, 'application_list.html',{'application_details':application_list,'client_application_count':client_application_count,'verifier_list':verifier_list,'service_details':service_details,'payment_details':payment_details})
    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# def payment_list(request):
#     login_id = request.session['login_id']
#     payment_details = t_payment_details.objects.filter(transaction_no__isnull=True)
#     service_details = t_service_master.objects.all()
#     return render(request, 'payment_list.html', {'payment_details': payment_details,'service_details':service_details})

def payment_list(request):
    applicant_id = request.session.get('email', None)
    assigned_user_id = request.session.get('login_id', None)
    ca_authority = request.session.get('ca_authority', None)
    login_id = request.session.get('login_id', None)

 #   payment_details = t_payment_details.objects.filter(
 #       payer_email__in=t_ec_application_t1.objects.filter(ca_authority=ca_authority).values('applicant_id')
 #   ).order_by('ref_no')  # Assuming ref_no is your application number

    payment_details = t_payment_details.objects.filter(
    ca_authority = ca_authority).order_by('record_id')

    # Get application list
    application_list = t_workflow_dtls.objects.filter(
        assigned_role_id='2',
        action_date__isnull=False,
        ca_authority=ca_authority,
        application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ']
    ).order_by('-action_date')

    # EC Renewal List ( Due for renewal)
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(
        ca_authority=ca_authority,
        status='A',
        ec_expiry_date__lt=expiry_date_threshold
    ).count()

    # Reviewer application count
    r_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_user_id=login_id,
        assigned_role_name='Reviewer',
        ca_authority=ca_authority
    ).count()

    p_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_role_name='Reviewer',
        ca_authority=ca_authority,
        assigned_user_id__isnull=True,  # assigned_user_id is null
        action_date__isnull=False  # action_date is not null
    ).exclude(
        ca_authority=1  # Exclude ca_authority = 1
    ).count()

    # Add formatted description with custom mapping
    for payment in payment_details:
        # Clean up the description
        clean_desc = payment.description.replace('_', ' ').title()
        
        # Map specific values
        if clean_desc == "New Application":
            payment.display_description = "Application Fees"
        elif clean_desc == "Additional Application":  # Add more mappings as needed
            payment.display_description = "Additional Fees"
        else:
            payment.display_description = clean_desc
    
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_application_t1.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Get counts
    v_application_count = application_list.filter(application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ']).count()

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_application_t1.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    
    response = render(request, 'payment_list.html',
                  {'payment_details': payment_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'service_details': service_details,'tor_application_count':tor_application_count, 'ec_renewal_count':ec_renewal_count, 'v_application_count':v_application_count, 'r_application_count':r_application_count, 'p_application_count':p_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_application_details(request):
    application_no = request.GET.get('application_no')
    service_id = request.GET.get('service_id')

    service_master = t_service_master.objects.filter(
        service_id=service_id
    ).first()

    attachments = service_master.attachments if service_master else ''

    status = None
    ca_auth = None
    assigned_role_id = None
    assigned_role_name = None
    result = t_ec_application_t1.objects.filter(application_no=application_no,application_no__contains='TOR')
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)

    pay_details = payment_details_master.objects.filter(
        Q(payment_type='AP') | Q(payment_type='FINE')
    )
    # pay_details is used to list down the payment in the additional payment dropdown

    for work_details in workflow_details:
        status = work_details.application_status
        ca_auth = work_details.ca_authority
        assigned_role_name = work_details.assigned_role_name
        assigned_role_id = work_details.assigned_role_id
        assigned_user_id = work_details.assigned_user_id

    # work_details- assigned_role_name, assigned_role_id, status are used for hiding/unhide the sections in the
    # tor_form_details.html, application_details.html and renewal_application_details.html pages
    if result.exists():
        application_details = t_ec_application_t1.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        reviewer_list = t_user_master.objects.filter(role_id__in=['3', '5'], agency_code=ca_auth)
        file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOR')
        tor_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')
        additional_info = t_ec_additional_information.objects.filter(application_no=application_no).order_by('-record_id')
        payment_details = t_payment_details.objects.filter(ref_no=application_no).order_by('-record_id')
        attachments = attachments
        return render(request, 'tor_form_details.html', {'application_details':application_details,'file_attach':file_attach,'dzongkhag':dzongkhag,'additional_info':additional_info,'payment_details':payment_details,'gewog':gewog, 'village':village, 'thromde':thromde, 'reviewer_list':reviewer_list,'assigned_role_id':assigned_role_id, 'assigned_user_id':assigned_user_id,'status':status,'tor_attach':tor_attach,'pay_details':pay_details,'attachments': attachments})
    else:
        if service_id == '10':
            #renewal_details_one = t_ec_application_t1.objects.filter(application_no=application_no)
            #for renewal_details_one in renewal_details_one:
            #    application_details = t_ec_application_t1.objects.filter(application_no=renewal_details_one.application_no,service_type='Main Activity')
            application_details = t_ec_application_t1.objects.filter(application_no=application_no)
            renewal_details_two = t_ec_compliance.objects.filter(application_no=application_no)
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GEN')
            ec_details = t_ec_application_t2.objects.filter(application_no=application_no).order_by(
                'order','ec_type')
            reviewer_list = t_user_master.objects.filter(
                role_id__in=['3', '5'],
                agency_code=ca_auth
            )
            reject_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RRJ')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            ren_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ECR')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            renewal_details = t_ec_application_t1.objects.filter(application_no=application_no)
            additional_info = t_ec_additional_information.objects.filter(application_no=application_no).order_by('-record_id')
            payment_details = t_payment_details.objects.filter(ref_no=application_no).order_by('-record_id')
            attachments = attachments
            return render(request, 'application_details_renewal.html',{'application_details':application_details,'assigned_role_name':assigned_role_name,'additional_info':additional_info,'payment_details':payment_details,'status':status,'pay_details':pay_details,
                                                                    'dzongkhag':dzongkhag,'renewal_details':renewal_details,'ren_attach':ren_attach,'gewog':gewog,'village':village,'ai_attach':ai_attach,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'renewal_details_two':renewal_details_two,
                                                                       'ec_details':ec_details, 'reviewer_list':reviewer_list,'file_attach':file_attach,'reject_attach':reject_attach,'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach,'attachments': attachments})

        elif service_id == '11':
            application_details = t_ec_application_t1.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECNC')
            ec_details = t_ec_application_t2.objects.filter(application_no=application_no).order_by('order','ec_type')
            reviewer_list = t_user_master.objects.filter(
                role_id__in=['3', '5'],
                agency_code=ca_auth
            )
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='EATC')
            reject_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RRJ')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            additional_info = t_ec_additional_information.objects.filter(application_no=application_no).order_by(
                '-record_id')
            payment_details = t_payment_details.objects.filter(ref_no=application_no).order_by('-record_id')
            return render(request, 'application_details_nc.html',
                          {'reviewer_list': reviewer_list, 'assigned_role_name': assigned_role_name, 'status': status,
                           'ai_attach': ai_attach, 'application_details': application_details,
                           'application_no': application_no, 'dzongkhag': dzongkhag, 'gewog': gewog,
                           'pay_details': pay_details, 'village': village, 'file_attach': file_attach,
                           'app_hist_count': app_hist_count, 'cl_application_count': cl_application_count,
                           'ec_details': ec_details, 'eatc_attach': eatc_attach, 'reject_attach': reject_attach,
                           'lu_attach': lu_attach, 'rev_lu_attach': rev_lu_attach, 'additional_info': additional_info,
                           'payment_details': payment_details, 'attachments': attachments})

        elif service_id == '12':
            application_details = t_ec_application_t1.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECOC')
            ec_details = t_ec_application_t2.objects.filter(application_no=application_no).order_by('order','ec_type')
            reviewer_list = t_user_master.objects.filter(
                role_id__in=['3', '5'],
                agency_code=ca_auth
            )
            #eatc_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='EATC')
            reject_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RRJ')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            additional_info = t_ec_additional_information.objects.filter(application_no=application_no).order_by(
                '-record_id')
            payment_details = t_payment_details.objects.filter(ref_no=application_no).order_by('-record_id')
            attachments = attachments
            return render(request, 'application_details_oc.html',
                          {'reviewer_list': reviewer_list, 'assigned_role_name': assigned_role_name, 'status': status,
                           'ai_attach': ai_attach, 'application_details': application_details,
                           'application_no': application_no, 'dzongkhag': dzongkhag, 'gewog': gewog,
                           'pay_details': pay_details, 'village': village, 'file_attach': file_attach,
                           'app_hist_count': app_hist_count, 'cl_application_count': cl_application_count,
                           'ec_details': ec_details, 'reject_attach': reject_attach,
                           'lu_attach': lu_attach, 'rev_lu_attach': rev_lu_attach, 'additional_info': additional_info,
                           'payment_details': payment_details, 'attachments': attachments})

        else :
            application_details = t_ec_application_t1.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            #file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='GEN')
            file_attach = t_file_attachment.objects.filter(
                application_no=application_no
            ).exclude(
                attachment_type__in=['EATC', 'LU', 'RLU']
            )
            ec_details = t_ec_application_t2.objects.filter(application_no=application_no).order_by('order','ec_type')
            reviewer_list = t_user_master.objects.filter(
                role_id__in=['3', '5'],
                agency_code=ca_auth
            )
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='EATC')
            reject_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RRJ')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            additional_info = t_ec_additional_information.objects.filter(application_no=application_no).order_by(
                '-record_id')
            payment_details = t_payment_details.objects.filter(ref_no=application_no).order_by('-record_id')
            attachments = attachments
            return render(request, 'application_details.html',
                          {'reviewer_list': reviewer_list, 'assigned_role_name': assigned_role_name, 'status': status,
                           'ai_attach': ai_attach, 'application_details': application_details,
                           'application_no': application_no, 'dzongkhag': dzongkhag, 'gewog': gewog,
                           'pay_details': pay_details, 'village': village, 'file_attach': file_attach,
                           'app_hist_count': app_hist_count, 'cl_application_count': cl_application_count,
                           'ec_details': ec_details, 'eatc_attach': eatc_attach, 'reject_attach': reject_attach,
                           'lu_attach': lu_attach, 'rev_lu_attach': rev_lu_attach, 'additional_info': additional_info,
                           'payment_details': payment_details, 'attachments': attachments})

        return None


def resubmit_application(request):
    application_no = request.POST.get('application_no')
    remarks = request.POST.get('resubmit_remarks')

    application_details = t_ec_application_t1.objects.filter(application_no=application_no)
    application_details.update(resubmit_remarks=remarks)
    application_details.update(resubmit_date=date.today())

    for details in application_details:
        email = details.applicant_id
        user_details = t_user_master.objects.filter(email_id=email)
        for users in user_details:
            login_id = users.login_id
        workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
        workflow_details.update(assigned_user_id=login_id)
        workflow_details.update(assigned_role_id=None)
        workflow_details.update(assigned_role_name=None)
        workflow_details.update(action_date=date.today())
        workflow_details.update(actor_id=request.session['login_id'])
        workflow_details.update(actor_name=request.session['name'])
        for work_details in workflow_details:
            service_id = work_details.service_id
            service_details = t_service_master.objects.filter(service_id=service_id)
            for service in service_details:
                service_name = service.service_name
                send_ec_resubmission_email(email, application_no, service_name)
    return redirect(reviewer_application_list)



def validate_receipt_no(request):
    data = dict()
    receipt_no = request.GET.get('receipt_no')
    receipt_no_count = t_payment_details.objects.filter(transaction_no=receipt_no).count()

    if receipt_no_count > 0:
        data['status'] = "Exists"
    else:
        data['status'] = "No Exists"
    return JsonResponse(data)


def update_payment_details(request):
    application_no = request.POST.get('application_no')
    payment_type = request.POST.get('payment_type')
    transaction_no = request.POST.get('transaction_no')
    amount = request.POST.get('amount')
    instrument_no = request.POST.get('instrument_no')
    transaction_date = request.POST.get('transaction_date')
    applicant = None
    service_id = None
    fine_details = t_payment_details.objects.filter(ref_no=application_no, service_type='Fines And Penalties')
    if fine_details.exists():
        fine_details.update(transaction_no=transaction_no, amount=amount,
                               instrument_no=instrument_no, transaction_date=transaction_date)
        work_details = t_fines_penalties.objects.filter(application_no=application_no)
        work_details.update(fines_status='FPP') # Fines Paid
        application_details = t_ec_application_t1.objects.filter(application_no=application_no)
        for app_det in application_details:
            applicant = app_det.applicant_id
            service_id = app_det.service_id
            ca_auth = app_det.ca_authority
            t_application_history.objects.create(application_no=application_no,
                    application_status='FPP',
                    action_date=date.today(),
                    actor_id=request.session['login_id'], 
                    actor_name=request.session['name'],
                    applicant_id=applicant,
                    remarks='Fines Payment Made',
                    service_id=service_id,
                    ca_authority=ca_auth)
    else:
        payment_details = t_payment_details.objects.filter(ref_no=application_no, service_type='AP')
        if payment_details.exists():
            payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                                instrument_no=instrument_no, transaction_date=transaction_date)
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='APP')
            work_details.update(assigned_role_id='3')
            work_details.update(assigned_role_name='Reviewer')
            work_details.update(action_date=date.today())
            application_details = t_ec_application_t1.objects.filter(application_no=application_no, service_type='Main Activity')
            application_details.update(application_status='APP')
            application_details.update(action_date=date.today())
            application_details = t_ec_application_t1.objects.filter(application_no=application_no)
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
                ca_auth = app_det.ca_authority
            t_application_history.objects.create(application_no=application_no,
                    application_status='P',
                    action_date=date.today(),
                    actor_id=request.session['login_id'], 
                    actor_name=request.session['name'],
                    applicant_id=applicant,
                    remarks='Additional Payment Made',
                    service_id=service_id,
                    ca_authority=ca_auth)
        else:
            payment_details = t_payment_details.objects.filter(ref_no=application_no)
            payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                                    instrument_no=instrument_no, transaction_date=transaction_date)
            application_details = t_ec_application_t1.objects.filter(application_no=application_no)
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
                ca_auth = app_det.ca_authority
            t_application_history.objects.create(application_no=application_no,
                    application_status='P',
                    action_date=date.today(),
                    actor_id=request.session['login_id'], 
                    actor_name=request.session['name'],
                    applicant_id=applicant,
                    remarks='Payment Made',
                    service_id=service_id,
                    ca_authority=ca_auth)
    return redirect(payment_list)

def get_ec_no(request):
    last_ec_no = t_ec_application_t1.objects.exclude(application_type='Old_EC').aggregate(Max('ec_reference_no'))
    lastECNo = last_ec_no['ec_reference_no__max']
    if not lastECNo:
        year = timezone.now().year
        newECNo = "EC" + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastECNo)[9:12]
        substring = int(substring) + 1
        ecNo = str(substring).zfill(4)
        year = timezone.now().year
        newECNo ="EC" + "-" + str(year) + "-" + ecNo
    return newECNo

def get_tor_clearance_no(request,service_id):
    service_name = None
    last_cl_no = t_ec_application_t1.objects.aggregate(Max('tor_clearance_no'))
    lastClearnaceNo = last_cl_no['tor_clearance_no__max']

    if service_id == '1':
        service_name='IEE'
    elif service_id == '2':
        service_name='ENE'
    elif service_id == '3':
        service_name='ROA'
    elif service_id == '4':
        service_name='TRA'
    elif service_id == '5':
        service_name='TOU'
    elif service_id == '6':
        service_name='GWA'
    elif service_id == '7':
        service_name='FOR'
    elif service_id == '8':
        service_name='QUA'
    else:
        service_name='GEN'    

    if not lastClearnaceNo:
        year = timezone.now().year
        newClearanceNo = "TOR" + "-" + str(service_name) + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastClearnaceNo)[13:17]
        substring = int(substring) + 1
        ecNo = str(substring).zfill(4)
        year = timezone.now().year
        newClearanceNo ="TOR" + "-" + str(service_name) + "-" + str(year) + "-" + ecNo
    return newClearanceNo


def save_eatc_attachment(request):
    data = {}

    if 'eatc_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    eatc_attach = request.FILES['eatc_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    # Simply use the full application number + underscore + filename
    # This gives: "OC-2026-00705_TDSReport_2024.pdf"
    file_name = f"{app_no}_{eatc_attach.name}"

    year = timezone.now().year
    fs = FileSystemStorage(f"attachments/{year}/EATC/")

    if fs.exists(file_name):
        data['form_is_valid'] = False
        data['error'] = "File already exists"
    else:
        fs.save(file_name, eatc_attach)
        file_url = f"attachments/{year}/EATC/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)


def save_eatc_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='EATC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')

    return render(request, 'file_attachment_page_eatc.html', {'file_attach': file_attach})


def save_reject_attachment(request):
    data = dict()
    reject_attach = request.FILES['reject_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "-" + str(app_no)[4:8] + "-" + str(app_no)[9:13] + "-" + reject_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RRJ/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, reject_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/RRJ" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_reject_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,
                                     attachment_type='RRJ')
    reject_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RRJ')

    return render(request, 'reject_attachment_page.html', {'reject_attach': reject_attach})


def forward_application(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        identifier = request.POST.get('identifier')
        forward_to = request.POST.get('forward_to')
        record_id = request.POST.get('record_id')
        applicant_id = request.POST.get('applicant_id')

        actor_id = request.session['login_id'],
        reject_remarks = request.POST.get('reject_remarks')

        #print(record_id)

        applicant = None
        applicant_name = None
        service_id = None
        account_head = None
        payment_type = None
        service_type = None
        description = None
        email = None
        login_id = None
        
        workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)

        # COMMENTED BELOW AFTER ADDING EC TABLES (T1 AND T2).
        # HENCEFORTH THE EC DETAILS WILL BE SAVED IN THESE TABLES OF APPROVAL
        #if 'REN' in str(application_no):
        #    renewal_details = t_ec_application_t1.objects.filter(application_no=application_no).first()
        #    if renewal_details:
        #        application_details = t_ec_application_t1.objects.filter(ec_reference_no=renewal_details.ec_reference_no)
        #    else:
        #        application_details = []
        #else:
        #    application_details = t_ec_application_t1.objects.filter(application_no=application_no)

        application_details = t_ec_application_t1.objects.filter(application_no=application_no)

        # Extract applicant, service_id, and email
        for app_det in application_details:
            if app_det.application_type == "OC":
                applicant = app_det.buyer_email
                applicant_name = app_det.buyer_applicant_name
                email = app_det.buyer_email
            else:
                applicant = app_det.applicant_id
                applicant_name = app_det.applicant_name
                email = app_det.applicant_id
            service_id = app_det.service_id

        # Update the application
        if 'REN' in str(application_no):
            payment_type = "RENEW"
            service_type = "Renewal"
            description = "RENEWAL APPLICATION"
        elif 'TOR' in str(application_no):
            payment_type = "TOR"
            service_type = "TOR"
            description = "TOR APPLICATION"
        else:
            payment_type='NEW'
            service_type = "Main Activity"
            description = "NEW APPLICATION"

        payment_details = payment_details_master.objects.filter(payment_type=payment_type)
        for pay_dets in payment_details:
            account_head = pay_dets.account_head_code

        if identifier == 'V':
            workflow_details.update(action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=forward_to, assigned_role_id='2',assigned_role_name='Verifier')
            t_application_history.objects.create(application_no=application_no,
                        application_status='P',
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='To Verifier',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "ibls_application_list"
        elif identifier == 'P':
            total_amount = request.POST.get('amount')
            workflow_details.update(actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_role_id='2',assigned_role_name='Verifier')
            application_details.update(fee=total_amount)
            t_application_history.objects.create(application_no=application_no,
                        application_status='P',
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='To Verifier',
                        service_id=service_id)
            # CALLING THE PAYMENT FUNCTION
            make_payment_request(request,application_no,total_amount,description,account_head,service_type)
            
            # EMAIL FOR PAYMENT TO APPLICANTS
            # send_payment_mail11(applicant_name, email, application_no, total_amount)
            # Start the thread ONLY after successful DB commit
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_payment_mail_in_background,
                    args=(applicant_name, email, application_no, total_amount),
                    daemon=True
                ).start()
            )
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'R': #Forward to Reviewer
            workflow_details.update(application_status='R', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=forward_to, assigned_role_id='3',assigned_role_name='Reviewer')
            application_details.update(application_status='R', assigned_to=forward_to, assigned_date=date.today(), assigned_by=request.session['login_id'])
            t_application_history.objects.create(application_no=application_no,
                        application_status='R',
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='To Reviewer',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'AL': #Additional Information - Application forwarded to Verifier
            additional_info_letter = request.POST.get('additional_info_letter')
            due_date = request.POST.get('due_date')

            application_details.update(ai_date=date.today(), application_status='ALR')
            user_details = t_user_master.objects.filter(email_id=email)
            for user_data in user_details:
                login_id = user_data.login_id
            t_ec_additional_information.objects.create(
                application_no=application_no,
                additional_info_ca=additional_info_letter,
                additional_info_ca_date=date.today(),
                additional_info_due_date=due_date,
                applicant_id=applicant_id
            )
            t_application_history.objects.create(application_status='ALR',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Additional Info Required',
                        service_id=service_id)
            # workflow_details.update(application_status='ALR', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='2',assigned_role_name='Verifier')
            workflow_details.update(application_status='ALR', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id = login_id, assigned_role_id = None, assigned_role_name = None)
            # Get applicant name/email safely (pick one)
            app_obj = application_details.first()
            name = app_obj.applicant_name
            emailId = app_obj.email

            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"

            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_al_email_in_background,
                    args=(name, emailId, application_no, additional_info_letter),
                    daemon=True
                ).start()
            )
        elif identifier == 'ALA': #Additional Information accepted- Application forwarded to Proponent
            application_details.update(ai_date=date.today(),application_status='ALA')
            user_details = t_user_master.objects.filter(email_id=email)
            for user_details in user_details:
                login_id = user_details.login_id
            workflow_details.update(application_status='ALA', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='ALA',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Additional Info Approved',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'ALR': #Additional Information Submitted by Reviewer - Application forwarded to Verifier
            application_details.update(ai_date=date.today(),application_status='ALR')
            user_details = t_user_master.objects.filter(email_id=email)
            for user_data in user_details:
                login_id = user_data.login_id
            workflow_details.update(application_status='ALR', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='ALR',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Additional Info Rejected',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'ALS': #Additional Information Submitted by Proponent - Application forwarded to Reviewer
            additional_info = request.POST.get('additional_info')
            for reviewer_details in application_details:
                reviewer_id = reviewer_details.assigned_to
            additional_details = t_ec_additional_information.objects.filter(record_id=record_id)
            additional_details.update(additional_info_proponent=additional_info,additional_info_proponent_date=date.today())
            application_details.update(ai_date=date.today(),application_status='ALS')
            t_application_history.objects.create(application_status='ALS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Additional Info Submitted',
                        service_id=service_id)
            workflow_details.update(application_status='ALS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=reviewer_id, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'EATC': #EATC information submitted. - Application forwarded to Verifier
            application_details.update(application_status='EATC')
            user_details = t_user_master.objects.filter(email_id=email)
            for user_details in user_details:
                login_id = user_details.login_id
            workflow_details.update(application_status='EATC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='EATC',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='EATC Attach Requested',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'FEATC': #EATC - Application forwarded to Proponent
            application_details.update(application_status='FEATC')
            t_application_history.objects.create(application_status='FEATC',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='EATC Attachment Made',
                        service_id=service_id)
            workflow_details.update(application_status='FEATC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'RS':
            application_details.update(application_status='RS')
            user_details = t_user_master.objects.filter(email_id=email)
            for user_details in user_details:
                login_id = user_details.login_id
            workflow_details.update(application_status='RS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='RS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Resumit Application For Clearification',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'RSS':
            application_details.update(application_status='RSS')
            t_application_history.objects.create(application_status='RSS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Application Resubmitted',
                        service_id=service_id)
            resubmit_remarks = request.POST.get('resubmit_remarks')
            application_details.update(resubmit_remarks=resubmit_remarks)
            application_details.update(resubmit_date=date.today())
            workflow_details.update(application_status='RSS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'AP': #Additional Payment Required - Application forwarded to Proponent
            additional_payment_amount = request.POST.get('additional_payment_amount')
            application_details.update(application_status='AP')
            t_application_history.objects.create(application_status='AP',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Additional Payment Required',
                        service_id=service_id)
            workflow_details.update(
                action_date=date.today(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                application_status='AP'
            )
    
            make_payment_request(request,application_no,additional_payment_amount,'ADDITIONAL PAYMENT',account_head,service_type)

            for work_details in workflow_details:
                service_id = work_details.service_id
                service_details = t_service_master.objects.filter(service_id=service_id)
                for service in service_details:
                    service_name = service.service_name
                    for email_id in application_details:
                        emailId = email_id.email
                        # Start the thread ONLY after successful DB commit
                        transaction.on_commit(
                            lambda: threading.Thread(
                                target=_send_ec_additional_payment_mail_in_background,
                                args=(applicant_name, emailId, application_no, service_name, additional_payment_amount),
                                daemon=True
                            ).start()
                        )
                        # send_ec_ap_email(application_no, emailId, application_no, service_name,additional_payment_amount)
                        data['message'] = "success"
                        data['redirect_to'] = "reviewer_application_list"

        elif identifier == 'LU':
            # Get user info
            user_detail = t_user_master.objects.filter(email_id=email).first()
            application_details.update(application_status='LU')
            
            # Update workflow
            workflow_details.update(
                application_status='LU',
                action_date=date.today(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id=None,
                assigned_role_name=None,
                assigned_user_id=user_detail.login_id if user_detail else None
            )
            
            # Create history
            t_application_history.objects.create(
                application_status='LU',
                application_no=application_no,
                action_date=date.today(),
                actor_id=request.session['login_id'],
                applicant_id=applicant,
                service_id=service_id,
                remarks='Legal Undertaking Request'
            )
            
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'LUS':
            for reviewer_details in application_details:
                reviewer_id = reviewer_details.assigned_to
            application_details.update(application_status='LUS')
            t_application_history.objects.create(application_status='LUS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='Legal Undertaking attached',
                        service_id=service_id)
            workflow_details.update(application_status='LUS', action_date=date.today(),
                                    actor_id=request.session['login_id'], actor_name=request.session['name'],
                                    assigned_user_id=reviewer_id, assigned_role_id='3', assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'DEC':
            # 1. Update application status to 'DEC'
            ec_expiry_date = request.POST.get('ec_expiry_date_r')
            tat_r = request.POST.get('tat_ecr')
            # Convert to integer
            try:
                tat_r = int(tat_r) if tat_r else None
            except (ValueError, TypeError):
                tat_r = None
            application_details.update(
                application_status='DEC',
                ec_expiry_date=ec_expiry_date,
                tat=tat_r
            )
            # 2. Record in application history
            t_application_history.objects.create(
                application_status='DEC',
                application_no=application_no,
                action_date=date.today(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks='Draft EC forwarded to Verifier for Approval',
                service_id=service_id

            )

            # 3. Update workflow details
            workflow_details.update(
                application_status='DEC',
                action_date=date.today(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_user_id=None,
                assigned_role_id='2',
                assigned_role_name='Verifier'
            )

            # 5. Initialize date tracker
            dates = {
                'approval': None,    # LUS
                'submission': None,   # P
                'ai': None,          # ALR
                'resubmit': None      # RSS
            }

            # 6. Extract dates from application history
            for app_details in t_application_history.objects.filter(application_no=application_no):
                if app_details.application_status == 'LUS':
                    print("LUS:", app_details.action_date)
                    dates['approval'] = app_details.action_date
                elif app_details.application_status == 'P':
                    print("P:", app_details.action_date)
                    dates['submission'] = app_details.application_date
                elif app_details.application_status == 'ALR':
                    print("ALR:", app_details.action_date)
                    dates['ai'] = app_details.action_date
                elif app_details.application_status == 'RSS':
                    print("RSS:", app_details.action_date)
                    dates['resubmit'] = app_details.action_date

            # 7. Calculate TAT (with None checks)
            tat = 0  # Default if dates are missing

            # Case 1: Only submission + approval dates exist
            if dates['submission'] and dates['approval'] and not dates['ai'] and not dates['resubmit']:
                tat = (dates['approval'] - dates['submission']).days

            # Case 2: All dates exist (with AI + Resubmission)
            elif dates['submission'] and dates['approval'] and dates['ai'] and dates['resubmit']:
                total_days = (dates['approval'] - dates['submission']).days
                ai_resubmit_days = (dates['ai'] - dates['resubmit']).days
                tat = max(total_days - ai_resubmit_days, 0)  # Prevent negative TAT

            # 8. Update TAT in DB (if valid)
            # if tat > 0:
            #    application_details.update(tat=tat)
            # else:
            #    application_details.update(tat=tat)

            # 9. Return response
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"

        elif identifier == 'A':
            ec_expiry_date = request.POST.get('ec_expiry_date_v')
            tat_v = request.POST.get('tat_ecv')
            fmfsr_no = request.POST.get('fmfsr_no')
            print(fmfsr_no)

            # Convert TAT to integer safely
            try:
                tat_v = int(tat_v) if tat_v else None
            except (ValueError, TypeError):
                tat_v = None

            # Get application object
            app_obj = application_details.first()
            if not app_obj:
                raise ValueError(f"No application found for application_no={application_no}")

            # Normalize type to uppercase to avoid case issues
            application_type = (getattr(app_obj, 'application_type', '') or '').upper()
            old_ec_ref = app_obj.ec_reference_no
            modification_old_ec_ref = app_obj.prev_ec_reference_no

            # Determine EC number policy
            if application_type in ('NEW', 'TC', 'PC', 'CC', 'AC', 'LC'):
                ec_no = get_ec_no(request)  # new EC for NEW and MODIFICATION
            else:
                # NC/OC/RENEWAL: keep existing EC
                ec_no = old_ec_ref

            with transaction.atomic():
                # STEP 1: Handle EC History for MODIFICATION and RENEWAL
                if application_type in ('RENEWAL', 'OC', 'NC') and old_ec_ref:
                    _move_ec_to_history(old_ec_ref)

                elif application_type in ('TC', 'PC', 'CC', 'AC', 'LC') and modification_old_ec_ref:
                    _move_ec_to_history(old_ec_ref)
                    t_ec_t1.objects.filter(ec_reference_no=modification_old_ec_ref).update(
                        status='R',
                        r_updated_date=now()
                    )
                    #print(f"Marked old EC {modification_old_ec_ref} as 'R' (replaced)")

                # STEP 2: Update Application Tables
                if application_type in ('TC', 'PC', 'CC', 'AC', 'LC'):
                    application_details.update(
                        ec_reference_no=ec_no
                        #prev_ec_reference_no=old_ec_ref,
                    )
                    t_ec_application_t2.objects.filter(
                        application_no=application_no
                    ).update(ec_reference_no=ec_no)

                elif application_type == 'NEW':
                    application_details.update(ec_reference_no=ec_no)
                    t_ec_application_t2.objects.filter(
                        application_no=application_no
                    ).update(ec_reference_no=ec_no)

                elif application_type == 'RENEWAL':
                    # keep same EC number; expiry updated below
                    application_details.update(ec_reference_no=old_ec_ref)

                else:  # NC / OC
                    application_details.update(ec_reference_no=old_ec_ref)

                # Common updates for all types
                application_details.update(
                    ec_approve_date=now(),
                    application_status='A',
                    tat=tat_v,
                    ec_expiry_date=ec_expiry_date
                )

                workflow_details.update(
                    assigned_user_id=None,
                    assigned_role_id=None,
                    assigned_role_name=None,
                    action_date=now(),
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    application_status='A'
                )

                # Application History
                t_application_history.objects.create(
                    application_status='A',
                    application_no=application_no,
                    action_date=now(),
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    applicant_id=app_obj.applicant_id,
                    remarks='Approved',
                    service_id=app_obj.service_id
                )

                # STEP 3: Handle EC Tables (t_ec_t1 and t_ec_t2) and Their History
                service_name = t_service_master.objects.filter(
                    service_id=app_obj.service_id
                ).values_list('service_name', flat=True).first()
                #applicant_name = app_obj.applicant_name
                #email = app_obj.email

                ec_refs = [ec_no] if ec_no else list(application_details.values_list('ec_reference_no', flat=True))

                if application_type == 'NEW':
                    _handle_new_application_ec_tables(ec_refs, application_no)
                elif application_type in ('TC', 'PC', 'CC', 'AC', 'LC'):
                    _handle_modification_application_ec_tables(ec_refs, application_no)
                elif application_type == 'RENEWAL':
                    _handle_renewal_application_ec_tables(ec_refs, application_no)
                elif application_type == 'OC':
                    _handle_oc_application_ec_tables(ec_refs, application_no)
                elif application_type == 'NC':
                    _handle_nc_application_ec_tables(ec_refs, application_no)

                # Email notification (runs after successful commit)
                transaction.on_commit(
                    lambda: threading.Thread(
                        target=_send_ec_approve_email_in_background,
                        args=(applicant_name, email, application_no, service_name, ec_no),
                        daemon=True
                    ).start()
                )
                # =====================================================
                # PUSH TO MAS ONLY FOR NEW + APPROVED
                # =====================================================
                if application_type == 'NEW' and fmfsr_no:
                    transaction.on_commit(
                        lambda: threading.Thread(
                            target=push_ec_to_mas,
                            args=(fmfsr_no, ec_no, ec_expiry_date),
                            daemon=True
                        ).start()
                    )

            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"

        elif identifier == 'FT': # forward TOR form
            tor_remarks = request.POST.get('tor_remarks')
            application_details.update(tor_remarks=tor_remarks,application_status='FT')
            t_application_history.objects.create(application_status='FT',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='TOR Forwared',
                        service_id=service_id)
            workflow_details.update(application_status='FT', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='2',assigned_role_name='Verifier')
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'AT': # Approve TOR form
            application_details.update(tor_approve_date=date.today(),application_status='A')
            t_application_history.objects.create(application_status='A',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='TOR Approved',
                        service_id=service_id)
            workflow_details.update(assigned_user_id=None)
            workflow_details.update(assigned_role_id=None)
            workflow_details.update(assigned_role_name=None)
            workflow_details.update(action_date=date.today())
            workflow_details.update(actor_id=request.session['login_id'])
            workflow_details.update(actor_name=request.session['name'])
            workflow_details.update(application_status='A')
            for work_details in workflow_details:
                service_id = work_details.service_id
                service_details = t_service_master.objects.filter(service_id=service_id)
                for service in service_details:
                    service_name = service.service_name
                    for app_obj in application_details:
                        emailId = app_obj.email
                        name = app_obj.applicant_name
                        tor_clearance_no = get_tor_clearance_no(request,service_id)
                        application_details.update(tor_clearance_no=tor_clearance_no)
                        data['message'] = "success"
                        data['redirect_to'] = "verify_application_list"
                        transaction.on_commit(
                            lambda: threading.Thread(
                                target=_send_tor_approve_email_in_background,
                                args=(name, emailId, tor_clearance_no),
                                daemon=True
                            ).start()
                        )
        elif identifier == 'RRJ':  #Reject EC Application at Reviewer's level
            reject_remarks = request.POST.get('reject_remarks')
            tat_days = request.POST.get('tat_days')
            # If these are querysets, update is fine
            application_details.update(
                application_status='RRJ',
                reject_date=timezone.now().date(),
                reject_remarks=reject_remarks,
                tat=tat_days,
            )
            t_application_history.objects.create(
                application_status='RRJ',
                application_no=application_no,
                action_date=timezone.now().date(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks=reject_remarks,
                service_id=service_id
            )
            workflow_details.update(
                assigned_user_id=None,
                assigned_role_id='2',
                assigned_role_name='Verifier',
                action_date=timezone.now().date(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                application_status='RRJ'
            )

        elif identifier == 'RJ':  # Reject Application
            reject_reason = request.POST.get('reject_reason', '').strip()
            tat_days = request.POST.get('tat_v')
            # If these are querysets, update is fine
            application_details.update(
                application_status='RJ',
                reject_date=timezone.now().date(),
                reject_remarks=reject_reason,
                tat=tat_days,
            )
            t_application_history.objects.create(
                application_status='RJ',
                application_no=application_no,
                action_date=timezone.now().date(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks=reject_reason,
                service_id=service_id
            )
            workflow_details.update(
                assigned_user_id=None,
                assigned_role_id=None,
                assigned_role_name=None,
                action_date=timezone.now().date(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                application_status='RJ'
            )
            # Get applicant name/email safely (pick one)
            app_obj = application_details.first()
            name = app_obj.applicant_name
            emailId = app_obj.email
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
            transaction.on_commit(
                lambda: threading.Thread(
                    target=_send_tor_reject_email_in_background,
                    args=(name, emailId, application_no, reject_reason),
                    daemon=True
                ).start()
            )
    except Exception as e:
        print('An error occurred:', e)
        error_msg = str(e)
        data['error'] = str(error_msg.split("\n")[0])
    return JsonResponse(data)

def _move_ec_to_history(ec_reference_no):
    existing_t1_records = t_ec_t1.objects.filter(ec_reference_no=ec_reference_no)
    t1_history_objects = []
    print('inside_move_ec_to_history')

    for record in existing_t1_records:
        t1_history_objects.append(t_ec_t1_history(
            application_source=record.application_source,
            activity=record.activity,
            project_description=record.project_description,
            service_id=record.service_id,
            colour_code=record.colour_code,
            service_type=record.service_type,
            ca_authority=record.ca_authority,
            proponent_type=record.proponent_type,
            applicant_id=record.applicant_id,
            applicant_name=record.applicant_name,
            address=record.address,
            cid=record.cid,
            contact_no=record.contact_no,
            email=record.email,
            project_name=record.project_name,
            focal_person=record.focal_person,
            dzongkhag_throm=record.dzongkhag_throm,
            thromde_id=record.thromde_id,
            dzongkhag_code=record.dzongkhag_code,
            gewog_code=record.gewog_code,
            village_code=record.village_code,
            location_name=record.location_name,
            ec_reference_no=record.ec_reference_no,
            prev_ec_reference_no=record.prev_ec_reference_no,
            ec_approve_date=record.ec_approve_date,
            ec_expiry_date=record.ec_expiry_date,
            tor_approve_date=record.tor_approve_date,
            tor_remarks=record.tor_remarks,
            tor_clearance_no=record.tor_clearance_no,
            status=record.status,
            history_date=now(),
            history_action='MOVED_TO_HISTORY',
            application_no=record.application_no,
            fmfsr_no=record.fmfsr_no
        ))

    if t1_history_objects:
        t_ec_t1_history.objects.bulk_create(t1_history_objects)

    existing_t2_records = t_ec_t2.objects.filter(ec_reference_no=ec_reference_no)
    t2_history_objects = []

    for record in existing_t2_records:
        t2_history_objects.append(t_ec_t2_history(
            ec_reference_no=record.ec_reference_no,
            ec_type=record.ec_type,
            ec_heading=record.ec_heading,
            ec_terms=record.ec_terms,
            history_date=now(),
            history_action='MOVED_TO_HISTORY',
            application_no=record.application_no,
            order=record.order
        ))

    if t2_history_objects:
        t_ec_t2_history.objects.bulk_create(t2_history_objects)


def _handle_new_application_ec_tables(ec_refs, application_no):
    existing_t1_refs = set(
        t_ec_t1.objects.filter(ec_reference_no__in=ec_refs).values_list('ec_reference_no', flat=True))
    #source_t1_records = t_ec_application_t1.objects.filter(ec_reference_no__in=ec_refs, application_no=application_no).exclude(
    #    ec_reference_no__in=existing_t1_refs)
    source_t1_records = t_ec_application_t1.objects.filter(ec_reference_no__in=ec_refs,
                                                           application_no=application_no)
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
            application_no=application_no,
            fmfsr_no=source.fmfsr_no
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
            history_date=now(),
            history_action='NEW_APPLICATION',
            application_no=application_no,
            fmfsr_no=source.fmfsr_no
        ))

    if t1_objects_to_create:
        t_ec_t1.objects.bulk_create(t1_objects_to_create)
        t_ec_t1_history.objects.bulk_create(t1_history_objects)

    source_t2_records = t_ec_application_t2.objects.filter(ec_reference_no__in=ec_refs, application_no=application_no)
    t2_objects_to_create = []
    t2_history_objects = []

    for s in source_t2_records:
        t2_objects_to_create.append(t_ec_t2(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            application_no=application_no,
            order=s.order
        ))

        t2_history_objects.append(t_ec_t2_history(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            history_date=now(),
            history_action='NEW_APPLICATION',
            application_no=application_no,
            order=s.order
        ))

    if t2_objects_to_create:
        t_ec_t2.objects.bulk_create(t2_objects_to_create)
        t_ec_t2_history.objects.bulk_create(t2_history_objects)


def _handle_modification_application_ec_tables(ec_refs, application_no):
    """
    Handle EC tables for MODIFICATION applications.
    Create new EC records with new EC number (old records already moved to history).
    """
    # For MODIFICATION, we create completely new records with the new EC number
    # The old records have already been moved to history by _move_ec_to_history()

    # CREATE new t_ec_t1 records
    source_t1_records = t_ec_application_t1.objects.filter(ec_reference_no__in=ec_refs)
    t1_objects_to_create = []
    t1_history_objects = []

    for source in source_t1_records:
        # Create main table record
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
            application_no=application_no,
            fmfsr_no=source.fmfsr_no
        )
        t1_objects_to_create.append(t1_record)

        # Create history table record
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
            history_date=now(),
            history_action='MODIFICATION',
            application_no=application_no,
            fmfsr_no=source.fmfsr_no
        ))

    if t1_objects_to_create:
        t_ec_t1.objects.bulk_create(t1_objects_to_create)
        t_ec_t1_history.objects.bulk_create(t1_history_objects)

    # CREATE new t_ec_t2 records
    source_t2_records = t_ec_application_t2.objects.filter(ec_reference_no__in=ec_refs)
    t2_objects_to_create = []
    t2_history_objects = []

    for s in source_t2_records:
        t2_objects_to_create.append(t_ec_t2(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            application_no=s.application_no,
            order=s.order
        ))

        t2_history_objects.append(t_ec_t2_history(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            history_date=now(),
            history_action='MODIFICATION',
            application_no=s.application_no,
            order=s.order
        ))

    if t2_objects_to_create:
        t_ec_t2.objects.bulk_create(t2_objects_to_create)
        t_ec_t2_history.objects.bulk_create(t2_history_objects)


def _handle_renewal_application_ec_tables(ec_refs, application_no):
    source_t1_records = t_ec_application_t1.objects.filter(ec_reference_no__in=ec_refs, application_no=application_no)
    t1_history_objects = []
    for s in source_t1_records:
        updated_count = t_ec_t1.objects.filter(ec_reference_no=s.ec_reference_no).update(
            application_source=s.application_source,
            activity=s.activity,
            project_description=s.project_description,
            colour_code=s.colour_code,
            service_type=s.service_type,
            ca_authority=s.ca_authority,
            proponent_type=s.proponent_type,
            applicant_id=s.applicant_id,
            applicant_name=s.applicant_name,
            address=s.address,
            cid=s.cid,
            contact_no=s.contact_no,
            email=s.email,
            project_name=s.project_name,
            focal_person=s.focal_person,
            dzongkhag_throm=s.dzongkhag_throm,
            thromde_id=s.thromde_id,
            dzongkhag_code=s.dzongkhag_code,
            gewog_code=s.gewog_code,
            village_code=s.village_code,
            location_name=s.location_name,
            prev_ec_reference_no=s.prev_ec_reference_no,
            ec_approve_date=s.ec_approve_date,
            ec_expiry_date=s.ec_expiry_date,
            tor_approve_date=s.tor_approve_date,
            tor_remarks=s.tor_remarks,
            tor_clearance_no=s.tor_clearance_no,
            status='A',
            application_no=application_no,
            fmfsr_no=s.fmfsr_no
        )

        if updated_count > 0:
            t1_history_objects.append(t_ec_t1_history(
                application_source=s.application_source,
                activity=s.activity,
                project_description=s.project_description,
                service_id=s.service_id,
                colour_code=s.colour_code,
                service_type=s.service_type,
                ca_authority=s.ca_authority,
                proponent_type=s.proponent_type,
                applicant_id=s.applicant_id,
                applicant_name=s.applicant_name,
                address=s.address,
                cid=s.cid,
                contact_no=s.contact_no,
                email=s.email,
                project_name=s.project_name,
                focal_person=s.focal_person,
                dzongkhag_throm=s.dzongkhag_throm,
                thromde_id=s.thromde_id,
                dzongkhag_code=s.dzongkhag_code,
                gewog_code=s.gewog_code,
                village_code=s.village_code,
                location_name=s.location_name,
                ec_reference_no=s.ec_reference_no,
                prev_ec_reference_no=s.prev_ec_reference_no,
                ec_approve_date=s.ec_approve_date,
                ec_expiry_date=s.ec_expiry_date,
                tor_approve_date=s.tor_approve_date,
                tor_remarks=s.tor_remarks,
                tor_clearance_no=s.tor_clearance_no,
                status='A',
                history_date=now(),
                history_action='RENEWAL',
                application_no=application_no,
                fmfsr_no=s.fmfsr_no
            ))

    if t1_history_objects:
        t_ec_t1_history.objects.bulk_create(t1_history_objects)

    t_ec_t2.objects.filter(ec_reference_no__in=ec_refs).delete()
    source_t2_records = t_ec_application_t2.objects.filter(ec_reference_no__in=ec_refs, application_no=application_no)
    t2_objects_to_create = []
    t2_history_objects = []

    for s in source_t2_records:
        t2_objects_to_create.append(t_ec_t2(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            application_no=s.application_no,
            order=s.order
        ))

        t2_history_objects.append(t_ec_t2_history(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            history_date=now(),
            history_action='RENEWAL',
            application_no=application_no,
            order=s.order

        ))

    if t2_objects_to_create:
        t_ec_t2.objects.bulk_create(t2_objects_to_create)
        t_ec_t2_history.objects.bulk_create(t2_history_objects)


def _handle_oc_application_ec_tables(ec_refs, application_no):
    source_t1_records = t_ec_application_t1.objects.filter(ec_reference_no__in=ec_refs,
                                                           application_no=application_no)
    print('inside_handle_oc_application_ec_tables')
    t1_history_objects = []
    for s in source_t1_records:
        updated_count = t_ec_t1.objects.filter(ec_reference_no=s.ec_reference_no).update(
            application_source=s.application_source,
            activity=s.activity,
            project_description=s.project_description,
            colour_code=s.colour_code,
            service_type=s.service_type,
            ca_authority=s.ca_authority,
            proponent_type=s.buyer_proponent_type,
            applicant_id=s.buyer_email,
            applicant_name=s.buyer_applicant_name,
            address=s.buyer_address,
            cid=s.buyer_cid,
            contact_no=s.buyer_contact_no,
            email=s.buyer_email,
            project_name=s.project_name,
            focal_person=s.focal_person,
            dzongkhag_throm=s.dzongkhag_throm,
            thromde_id=s.thromde_id,
            dzongkhag_code=s.dzongkhag_code,
            gewog_code=s.gewog_code,
            village_code=s.village_code,
            location_name=s.location_name,
            prev_ec_reference_no=s.prev_ec_reference_no,
            ec_approve_date=s.ec_approve_date,
            ec_expiry_date=s.ec_expiry_date,
            tor_approve_date=s.tor_approve_date,
            tor_remarks=s.tor_remarks,
            tor_clearance_no=s.tor_clearance_no,
            status='A',
            application_no=application_no,
            fmfsr_no=s.fmfsr_no
        )

        if updated_count > 0:
            t1_history_objects.append(t_ec_t1_history(
                application_source=s.application_source,
                activity=s.activity,
                project_description=s.project_description,
                service_id=s.service_id,
                colour_code=s.colour_code,
                service_type=s.service_type,
                ca_authority=s.ca_authority,
                proponent_type=s.proponent_type,
                applicant_id=s.applicant_id,
                applicant_name=s.applicant_name,
                address=s.address,
                cid=s.cid,
                contact_no=s.contact_no,
                email=s.email,
                project_name=s.project_name,
                focal_person=s.focal_person,
                dzongkhag_throm=s.dzongkhag_throm,
                thromde_id=s.thromde_id,
                dzongkhag_code=s.dzongkhag_code,
                gewog_code=s.gewog_code,
                village_code=s.village_code,
                location_name=s.location_name,
                ec_reference_no=s.ec_reference_no,
                prev_ec_reference_no=s.prev_ec_reference_no,
                ec_approve_date=s.ec_approve_date,
                ec_expiry_date=s.ec_expiry_date,
                tor_approve_date=s.tor_approve_date,
                tor_remarks=s.tor_remarks,
                tor_clearance_no=s.tor_clearance_no,
                status='A',
                history_date=now(),
                history_action='OWNERSHIP CHANGE',
                application_no=application_no,
                fmfsr_no=s.fmfsr_no
            ))

    if t1_history_objects:
        t_ec_t1_history.objects.bulk_create(t1_history_objects)

    t_ec_t2.objects.filter(ec_reference_no__in=ec_refs).delete()
    source_t2_records = t_ec_application_t2.objects.filter(ec_reference_no__in=ec_refs,
                                                           application_no=application_no)
    t2_objects_to_create = []
    t2_history_objects = []

    for s in source_t2_records:
        t2_objects_to_create.append(t_ec_t2(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            application_no=s.application_no,
            order=s.order
        ))

        t2_history_objects.append(t_ec_t2_history(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            history_date=now(),
            history_action='OWNERSHIP CHANGE',
            application_no=application_no,
            order=s.order
        ))

    if t2_objects_to_create:
        t_ec_t2.objects.bulk_create(t2_objects_to_create)
        t_ec_t2_history.objects.bulk_create(t2_history_objects)

def _handle_nc_application_ec_tables(ec_refs, application_no):
    source_t1_records = t_ec_application_t1.objects.filter(ec_reference_no__in=ec_refs,
                                                           application_no=application_no)
    t1_history_objects = []
    for s in source_t1_records:
        updated_count = t_ec_t1.objects.filter(ec_reference_no=s.ec_reference_no).update(
            application_source=s.application_source,
            activity=s.activity,
            project_description=s.project_description,
            colour_code=s.colour_code,
            service_type=s.service_type,
            ca_authority=s.ca_authority,
            proponent_type=s.proponent_type,
            applicant_id=s.applicant_id,
            applicant_name=s.applicant_name,
            address=s.address,
            cid=s.cid,
            contact_no=s.contact_no,
            email=s.email,
            project_name=s.new_project_name,
            focal_person=s.focal_person,
            dzongkhag_throm=s.dzongkhag_throm,
            thromde_id=s.thromde_id,
            dzongkhag_code=s.dzongkhag_code,
            gewog_code=s.gewog_code,
            village_code=s.village_code,
            location_name=s.location_name,
            prev_ec_reference_no=s.prev_ec_reference_no,
            ec_approve_date=s.ec_approve_date,
            ec_expiry_date=s.ec_expiry_date,
            tor_approve_date=s.tor_approve_date,
            tor_remarks=s.tor_remarks,
            tor_clearance_no=s.tor_clearance_no,
            status='A',
            application_no=application_no,
            fmfsr_no=s.fmfsr_no
        )

        if updated_count > 0:
            t1_history_objects.append(t_ec_t1_history(
                application_source=s.application_source,
                activity=s.activity,
                project_description=s.project_description,
                service_id=s.service_id,
                colour_code=s.colour_code,
                service_type=s.service_type,
                ca_authority=s.ca_authority,
                proponent_type=s.proponent_type,
                applicant_id=s.applicant_id,
                applicant_name=s.applicant_name,
                address=s.address,
                cid=s.cid,
                contact_no=s.contact_no,
                email=s.email,
                project_name=s.project_name,
                focal_person=s.focal_person,
                dzongkhag_throm=s.dzongkhag_throm,
                thromde_id=s.thromde_id,
                dzongkhag_code=s.dzongkhag_code,
                gewog_code=s.gewog_code,
                village_code=s.village_code,
                location_name=s.location_name,
                ec_reference_no=s.ec_reference_no,
                prev_ec_reference_no=s.prev_ec_reference_no,
                ec_approve_date=s.ec_approve_date,
                ec_expiry_date=s.ec_expiry_date,
                tor_approve_date=s.tor_approve_date,
                tor_remarks=s.tor_remarks,
                tor_clearance_no=s.tor_clearance_no,
                status='A',
                history_date=now(),
                history_action='NAME CHANGE',
                application_no=application_no,
                fmfsr_no=s.fmfsr_no
            ))

    if t1_history_objects:
        t_ec_t1_history.objects.bulk_create(t1_history_objects)

    t_ec_t2.objects.filter(ec_reference_no__in=ec_refs).delete()
    source_t2_records = t_ec_application_t2.objects.filter(ec_reference_no__in=ec_refs,
                                                           application_no=application_no)
    t2_objects_to_create = []
    t2_history_objects = []

    for s in source_t2_records:
        t2_objects_to_create.append(t_ec_t2(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            application_no=s.application_no,
            order=s.order
        ))

        t2_history_objects.append(t_ec_t2_history(
            ec_reference_no=s.ec_reference_no,
            ec_type=s.ec_type,
            ec_heading=s.ec_heading,
            ec_terms=s.ec_terms,
            history_date=now(),
            history_action='NAME CHANGE',
            application_no=application_no,
            order=s.order
        ))

    if t2_objects_to_create:
        t_ec_t2.objects.bulk_create(t2_objects_to_create)
        t_ec_t2_history.objects.bulk_create(t2_history_objects)

# =====================================================
# API PUSH FUNCTION   start
# =====================================================
def push_ec_to_mas(fmfs_id, ec_no, ec_expiry_date):
    try:
        # Step 1: Get Token
        token_response = requests.post(
            "https://stg-sso.tech.gov.bt/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(
                "wz_hmjRfUWx4ZGyUfL1KfQrAReka",
                "qIAoW01LGvU7XW5tHF_ZuuSNSGUa"
            ),
            timeout=30
        )

        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            print("MAS TOKEN FAILED:", token_json)
            return

        # Step 2: Payload
        payload = {
            "ec_status": "APPROVED",
            "ec_expiry_date": ec_expiry_date,
            "ec_no": ec_no,
            "fmfs_id": fmfs_id
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Step 3: Call API
        response = requests.post(
            "https://staging-datahub-apim.tech.gov.bt/mas_ecss_quarryleaseserviceapi/1.0.0/updateLease",
            json=payload,
            headers=headers,
            timeout=30
        )

        print("MAS PUSH STATUS:", response.status_code)
        print("MAS PUSH RESPONSE:", response.text)

    except Exception as e:
        print("MAS PUSH ERROR:", str(e))

# =====================================================
# API PUSH FUNCTION   end
# =====================================================

def _send_tor_reject_email_in_background(name, email_id, application_no, reject_reason):
    try:
        send_tor_reject_application_mail(name, email_id, application_no, reject_reason)
    except Exception:
        logger.exception("Failed to send Application reject email for application_no=%s", application_no)
def send_tor_reject_application_mail(name, email_id, application_no, reject_reason):
    subject = "Application Rejected"
    message = (
        f"Dear {name},\n\n"
        f"Your Application Number {application_no} has been rejected.\n"
        f"Reason: {reject_reason}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,  # ensure this is set
        recipient_list=[email_id],
        fail_silently=False,
    )

def _send_tor_approve_email_in_background(name, email_id, tor_clearance_no):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_tor_approve_application_mail(name, email_id, tor_clearance_no)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", tor_clearance_no)

def send_tor_approve_application_mail(name, email_id, tor_clearance_no):
    subject = "TOR Application Approved"
    message = (
        f"Dear {name},\n\n"
        f"Your TOR Application has been Approved.\n"
        f"Your TOR reference number is: {tor_clearance_no}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )

def _send_approve_email_in_background(name, email_id, application_no, tor_remarks):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_approve_application_mail(name, email_id, application_no, tor_remarks)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_approve_application_mail(name, email_id, application_no, reject_remarks):
    subject = "Application Submitted"
    message = (
        f"Dear {name},\n\n"
        f"Your Application has been Rejected.\n"
        f"Your application number is: {application_no}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )

def _send_al_email_in_background(name, email_id, application_no, additional_info):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_al_application_mail(name, email_id, application_no, additional_info)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_al_application_mail(name, email_id, application_no, additional_info):
    subject = "Additional Information Required"
    message = (
        f"Dear {name},\n\n"
        f"Please Provide Additional Information For  Your application number is: {application_no}\n"
        f"Additional Information: {additional_info}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email_id],
        fail_silently=False,
    )

def generate_new_ap_no():
    service_code = 'AP'
    current_year = str(timezone.now().year)
    pattern = f"^{service_code}-{current_year}-\\d{{4}}$"
    
    try:
        # Get all matching application numbers
        matching_numbers = t_payment_details.objects.filter(
            application_no__regex=pattern
        ).values_list('application_no', flat=True)
        
        if not matching_numbers:
            return f"{service_code}-{current_year}-0001"
        
        # Extract and find max sequence number
        max_seq = 0
        for app_no in matching_numbers:
            try:
                seq = int(app_no[-4:])
                if seq > max_seq:
                    max_seq = seq
            except ValueError:
                continue
        
        next_seq = max_seq + 1
        return f"{service_code}-{current_year}-{str(next_seq).zfill(4)}"
        
    except Exception as e:
        print(f"Error generating application number: {e}")
        return f"{service_code}-{current_year}-0001"


def days_between(start_date, end_date):
    if start_date and end_date:
        # Ensure both are date objects, otherwise parse them
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        return abs((end_date - start_date).days)
    return 0

def get_random_tax_no(length):
    digits = string.digits
    tax_no = ''.join(random.choice(digits) for i in range(length))
    return tax_no

def make_payment_request(request, application_no, total_amount, description, service_code, service_type):
    token = get_birms_token()
    new_app_no = generate_new_ap_no() if description == "ADDITIONAL PAYMENT" else application_no

    # Fetch application details
    if 'REN' in str(application_no):
        renewal = t_ec_application_t1.objects.filter(application_no=application_no).first()
        app_details = t_ec_application_t1.objects.filter(ec_reference_no=renewal.ec_reference_no) if renewal else []
    else:
        app_details = t_ec_application_t1.objects.filter(application_no=application_no)

    # Use first record if available
    app_det = app_details.first() if app_details else None

    if not app_det:
        print(f"No application details found for {application_no}")
        return

    # Extract required fields
    taxPayerDocumentNo = app_det.cid
    mob_no = app_det.contact_no
    app_name = app_det.applicant_name
    proponent_type = app_det.proponent_type
    email_id = app_det.applicant_id

    # Override taxPayerDocumentNo for non-individual proponents
    if proponent_type != 4:
        taxPayerDocumentNo = get_random_tax_no(8)

    # Endpoint URL
    url = "https://birmsstagging.drc.gov.bt/api-services/moenr-service/api/v1/paymentdetails/create"

    # Prepare payload
    payload = {
        "platform": "Environment Clearance Services System",
        "refNo": new_app_no,
        "taxPayerNo": None,
        "taxPayerDocumentNo": taxPayerDocumentNo,
        "paymentRequestDate": date.today().isoformat(),
        "agencyCode": "DTH1552",
        "payerEmail": email_id,
        "mobileNo": mob_no,
        "totalPayableAmount": total_amount,
        "paymentDueDate": None,
        "taxPayerName": app_name,
        "code": "moenr",
        "paymentLists": [
            {
                "serviceCode": service_code,
                "description": description,
                "payableAmount": total_amount
            }
        ]
    }

    headers = {'Authorization': f"Bearer {token}"}

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()  # Raises HTTPError for bad responses
        data = response.json()
        paymentAdviceNo = data.get('content', {}).get('paymentAdviceNo')
        print(paymentAdviceNo)
        insert_app_payment_details(request, application_no, description, total_amount, service_type, paymentAdviceNo, new_app_no)
        print("Payment request successful:", data)
    except requests.exceptions.RequestException as e:
        print("Payment request failed:", e)
        if response is not None:
            print("Response:", response.text)


def save_lu_attachment(request):
    data = {}

    if 'lu_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    lu_attach = request.FILES['lu_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    # Simply use the full application number + underscore + filename
    # This gives: "OC-2026-00705_TDSReport_2024.pdf"
    file_name = f"{app_no}_{lu_attach.name}"

    year = timezone.now().year
    fs = FileSystemStorage(f"attachments/{year}/LU/")

    if fs.exists(file_name):
        data['form_is_valid'] = False
        data['error'] = "File already exists"
    else:
        fs.save(file_name, lu_attach)
        file_url = f"attachments/{year}/LU/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)

def _send_payment_mail_in_background(name, email, application_no, amount):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_payment_mail(name, email, application_no, amount)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_payment_mail(name, email, application_no, amount):
    subject = "Application Accepted"
    message = (
        f"Dear {name},\n\n"
        f"Your application registered under the application number : {application_no} is accepted.\n"
        f"You are required to make a payment of Nu.: {amount}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )

def _send_ec_additional_payment_mail_in_background(name, email, application_no, service_name, additional_payment_amount):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_additional_payment_mail(name, email, application_no, service_name, additional_payment_amount)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_additional_payment_mail(name, email, application_no, service_name, additional_payment_amount):
    subject = "ADDITIONAL PAYMENT"
    message = (
        f"Dear Sir {name},\n\n"
        f"Your EC application number: {application_no} for : {service_name} has additional payment.\n"
        f"You are required to make an additional payment of Nu.: {additional_payment_amount}\n\n"
        f"Thanking You\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )


def _send_ec_approve_email_in_background (applicant_name, email, application_no, service_name, ec_no):
    """
        Thread target: never uses request/session. Only uses passed primitives.
        """
    try:
        send_ec_approve_email_mail(applicant_name, email, application_no, service_name, ec_no)
    except Exception:
        # Don't crash the web request; just log the failure.
        logger.exception("Failed to send submit email for application_no=%s", application_no)

def send_ec_approve_email_mail(applicant_name, email, application_no, service_name, ec_no):
    subject = 'APPLICATION APPROVED'
    message = (
            f"Dear Sir {applicant_name},\n\n"
            f"Your EC application number: {application_no} for : {service_name} has been APPROVED.\n"
            f"Your EC Reference Number is : {ec_no}\n\n"
            f"Thanking You\n"
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )



def send_tor_approve_email(email, application_no, service_name, tor_clearance_no):
    print("send_tor_approve_email")
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir/Madam," \
              "" \
              "Your TOR Application For" + service_name + " Has Been Approved. Draft TOR Has been attached for your reference. " \
                                                          " Your Application No is " + application_no + " And Tor Clearance No is" + tor_clearance_no + " Thank You" \
                                                                                                                                                        " . "
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)


def send_ec_resubmission_email(email, application_no, service_name):
    subject = 'APPLICATION RESUBMISSION'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Having" \
                                                         " Application No " + application_no + " Has Been Sent For Resubmission. Please Check The Application And Resubmit It."
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)




def save_lu_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='LU')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')

    return render(request, 'lu_attachment_page.html', {'lu_attach': file_attach})


def save_rev_lu_attachment(request):
    data = {}

    if 'rev_lu_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    lu_attach = request.FILES['rev_lu_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    # Simply use the full application number + underscore + filename
    # This gives: "OC-2026-00705_TDSReport_2024.pdf"
    file_name = f"{app_no}_{lu_attach.name}"

    year = timezone.now().year
    fs = FileSystemStorage(f"attachments/{year}/RLU/")

    if fs.exists(file_name):
        data['form_is_valid'] = False
        data['error'] = "File already exists"
    else:
        fs.save(file_name, lu_attach)
        file_url = f"attachments/{year}/RLU/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)

def save_rev_lu_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='RLU')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')

    return render(request, 'rev_lu_attachment_page.html', {'rev_lu_attach': file_attach})

def delete_rev_lu_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)

    for file in file:
        file_name = file.attachment
        file_n = f"{application_no}_{file_name}"
        print(file_n)
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RLU")
        fs.delete(str(file_n))
    file.delete()

    rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RLU')
    return render(request, 'rev_lu_attachment_page.html', {'rev_lu_attach':rev_lu_attach})

# TOR ATTACHMENTS
def save_rev_tor_attachment(request):
    data = {}

    if 'rev_tor_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    rev_tor_attach = request.FILES['rev_tor_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    # Simply use the full application number + underscore + filename
    # This gives: "OC-2026-00705_TDSReport_2024.pdf"
    file_name = f"{app_no}_{rev_tor_attach.name}"

    year = timezone.now().year
    fs = FileSystemStorage(f"attachments/{year}/RTOR/")

    if fs.exists(file_name):
        data['form_is_valid'] = False
        data['error'] = "File already exists"
    else:
        fs.save(file_name, rev_tor_attach)
        file_url = f"attachments/{year}/RTOR/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)

def save_rev_tor_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='RTOR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')

    return render(request, 'tor_attachment_page.html', {'tor_attach': file_attach})

def delete_rev_tor_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = file.attachment
        file_n = f"{application_no}_{file_name}"
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RTOR")
        fs.delete(str(file_n))
    file.delete()
    tor_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RTOR')
    return render(request, 'tor_attachment_page.html', {'tor_attach': tor_attach})

def save_ver_tor_attachment(request):
    data = {}

    if 'ver_tor_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    rev_tor_attach = request.FILES['ver_tor_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    # Simply use the full application number + underscore + filename
    # This gives: "OC-2026-00705_TDSReport_2024.pdf"
    file_name = f"{app_no}_{rev_tor_attach.name}"

    year = timezone.now().year
    fs = FileSystemStorage(f"attachments/{year}/RTOR/")

    if fs.exists(file_name):
        data['form_is_valid'] = False
        data['error'] = "File already exists"
    else:
        fs.save(file_name, rev_tor_attach)
        file_url = f"attachments/{year}/RTOR/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)

def save_ver_tor_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='RTOR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')

    return render(request, 'tor_ver_attachment_page.html', {'tor_attach': file_attach})

def delete_ver_tor_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = file.attachment
        file_n = f"{application_no}_{file_name}"
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RTOR")
        fs.delete(str(file_n))
    file.delete()
    tor_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RTOR')
    return render(request, 'tor_ver_attachment_page.html', {'tor_attach': tor_attach})

def save_ai_attachment(request):
    data = {}

    if 'ai_attach' not in request.FILES:
        return HttpResponseBadRequest("No file uploaded")

    ai_attach = request.FILES['ai_attach']
    app_no = request.POST.get('application_no')

    if not app_no:
        return HttpResponseBadRequest("application_no is required")

    # Simply use the full application number + underscore + filename
    # This gives: "OC-2026-00705_TDSReport_2024.pdf"
    file_name = f"{app_no}_{ai_attach.name}"

    year = timezone.now().year
    fs = FileSystemStorage(f"attachments/{year}/AI/")

    if fs.exists(file_name):
        data['form_is_valid'] = False
        data['error'] = "File already exists"
    else:
        fs.save(file_name, ai_attach)
        file_url = f"attachments/{year}/AI/{file_name}"
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name

    return JsonResponse(data)


def save_ai_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='AI')
    ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')

    return render(request, 'ai_attachment_page.html', {'ai_attach': ai_attach})

def delete_ai_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)

    for file in file:
        file_name = file.attachment
        file_n = f"{application_no}_{file_name}"
        print(file_n)
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/AI")
        fs.delete(str(file_n))
    file.delete()

    rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='AI')
    return render(request, 'rev_lu_attachment_page.html', {'rev_lu_attach':rev_lu_attach})




def delete_lu_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = file.attachment
        file_n = f"{application_no}_{file_name}"
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/LU")
        fs.delete(str(file_n))
    file.delete()

    lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='LU')
    return render(request, 'lu_attachment_page.html', {'lu_attach':lu_attach})


def save_draft_ec_details(request):
    application_no = request.POST.get('application_no')
    ec_reference_no = request.POST.get('ec_reference_no')
    ec_type = request.POST.get('ec_type')
    order = request.POST.get('order')
    ec_heading = request.POST.get('ec_heading')
    ec_terms = request.POST.get('ec_terms')

    # Set default order and heading based on type
    if ec_type == 'Header':
        order = 1
        ec_heading = ''
    elif ec_type == 'Footer':
        order = 1  # Large number to ensure it appears last
        ec_heading = ''
    elif ec_type == 'Terms':
        # Convert order to int, default to 100 if not provided
        try:
            order = int(order) if order and order.strip() else 100
        except ValueError:
            order = 100
        # Keep user-provided heading or set default
        if not ec_heading or ec_heading.strip() == '':
            ec_heading = 'Terms and Conditions'
    else:
        order = 50  # Default fallback
        ec_heading = ec_heading or 'General'

    print(f"Final Order: {order}, Type: {ec_type}, Heading: {ec_heading}")

    t_ec_application_t2.objects.create(
        application_no=application_no,
        ec_type=ec_type,
        order=order,
        ec_heading=ec_heading,
        ec_terms=ec_terms,
        ec_reference_no=ec_reference_no
    )

    ec_details = t_ec_application_t2.objects.filter(
        application_no=application_no
    ).order_by('order', 'record_id')

    return render(request, 'ec_draft_details.html', {'ec_details': ec_details})

def update_draft_ec_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    ec_type = request.POST.get('ec_type')
    order = request.POST.get('order')
    ec_heading = request.POST.get('ec_heading')
    ec_terms = request.POST.get('ec_terms')

    # Validate required fields
    if not record_id or not application_no:
        return JsonResponse({'error': 'Missing record ID or application number'}, status=400)

    # Set default order and heading based on type
    if ec_type == 'Header':
        order = 1
        ec_heading = ''
    elif ec_type == 'Footer':
        order = 1
        ec_heading = ''
    elif ec_type == 'Terms':
        try:
            order = int(order) if order and order.strip() else 100
        except ValueError:
            order = 100
        if not ec_heading or ec_heading.strip() == '':
            ec_heading = 'Terms and Conditions'
    else:
        order = 50
        ec_heading = ec_heading or 'General'

    # Update the record
    try:
        updated_rows = t_ec_application_t2.objects.filter(
            record_id=record_id
        ).update(
            ec_type=ec_type,
            order=order,
            ec_heading=ec_heading,
            ec_terms=ec_terms
        )

        if updated_rows == 0:
            return JsonResponse({'error': 'No record found'}, status=404)

        # Reload updated list
        ec_details = t_ec_application_t2.objects.filter(
            application_no=application_no
        ).order_by('order', 'record_id')

        return render(request, 'ec_draft_details.html', {'ec_details': ec_details})

    except Exception as e:
        print(f"Error updating draft EC: {e}")
        return JsonResponse({'error': 'Failed to update record'}, status=500)


def delete_draft_ec_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    ec_details = t_ec_application_t2.objects.filter(record_id=record_id)
    ec_details.delete()
    ec_details = t_ec_application_t2.objects.filter(application_no=application_no).order_by('record_id')

    return render(request, 'ec_draft_details.html', {'ec_details':ec_details})

# Inspection Report
def inspection_list(request):
    login_id = request.session.get('login_id')
    print('inside inspection_list')

    inspection_list = t_inspection_monitoring_t1.objects.filter(record_status='Active').order_by('inspection_date')
    user_list = t_user_master.objects.all()
    v_application_count = 0
    r_application_count = 0
    ec_renewal_count = 0
    p_application_count = 0

    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True, login_type='C').count()
    ca_authority = request.session.get('ca_authority', None)

    ec_details = t_ec_application_t1.objects.all()
    
    if ca_authority is not None: 
        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2',
            assigned_role_name='Verifier',
            action_date__isnull=False,
            application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
            ca_authority=request.session['ca_authority']
        ).count()
        # Reviewer application count
        r_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_user_id=login_id,
            assigned_role_name='Reviewer',
            ca_authority=ca_authority
        ).count()

        p_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='3',
            assigned_role_name='Reviewer',
            ca_authority=ca_authority,
            assigned_user_id__isnull=True,  # assigned_user_id is null
            action_date__isnull=False  # action_date is not null
        ).exclude(
            ca_authority=1  # Exclude ca_authority = 1
        ).count()

        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    
    response = render(request, 'inspection/inspection.html', {
        'client_application_count': client_application_count,
        'inspection_list': inspection_list,
        'ec_renewal_count': ec_renewal_count,
        'v_application_count': v_application_count,
        'r_application_count': r_application_count,
        'p_application_count': p_application_count,
        'user_list': user_list, 
        'ec_details': ec_details
    })
    return response

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
    

def view_inspection_details(request):
    inspection_reference_no = request.GET.get('inspection_reference_no')
    inspection_details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=inspection_reference_no)
    file_attach = t_file_attachment.objects.filter(application_no=inspection_reference_no)
    return render(request, 'inspection/inspection_details.html',
                  {'inspection_details':inspection_details, 'file_attach':file_attach})

def inspection_submission_form(request):
    applicant = request.session['email']
    ec_details = t_ec_application_t1.objects.filter(ec_reference_no__isnull=False)
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    return render(request, 'inspection/inspection_submission.html', {'ec_details': ec_details,'r_application_count':r_application_count})

def load_ec_details(request):
    data = dict()
    ec_reference_no = request.GET.get('ec_reference_no')
    ec_detail_list = t_ec_application_t1.objects.filter(ec_reference_no=ec_reference_no)
    for ec_detail_list in ec_detail_list:
        data["applicant_name"],data["project_name"],data["address"],data["ca_authority"],data["applicant_id"] = ec_detail_list.applicant_name, ec_detail_list.project_name, ec_detail_list.address, ec_detail_list.ca_authority, ec_detail_list.applicant_id
    return JsonResponse(data)

def add_inspection(request):
    data = dict()
    service_code = 'ins'
    reference_no = get_inspection_submission_ref_no(request, service_code)
    inspection_type = request.POST.get('inspection_type')
    inspection_date = request.POST.get('inspection_date')
    inspection_reason = request.POST.get('inspection_reason')
    ec_clearance_no = request.POST.get('ec_clearance_no')
    proponent_name = request.POST.get('proponent_name')
    project_name = request.POST.get('project_name')
    address = request.POST.get('address')
    observation = request.POST.get('observation')
    team_leader = request.POST.get('team_leader')
    team_members = request.POST.get('team_members')
    remarks = request.POST.get('remarks')
    fines_penalties = request.POST.get('fines_penalties')
    inspection_status = request.POST.get('inspection_status')
    applicant_id = request.POST.get('applicant_id')
    
    t_inspection_monitoring_t1.objects.create(inspection_type=inspection_type, inspection_date=inspection_date,
                                              inspection_reference_no=reference_no, inspection_reason=inspection_reason,
                                              ec_clearance_no=ec_clearance_no, project_name=project_name,
                                              proponent_name=proponent_name, address=address, observation=observation,
                                              team_leader=team_leader, team_members=team_members, remarks=remarks,
                                              fines_penalties=fines_penalties, status=inspection_status,
                                              login_id=applicant_id,
                                              updated_by_ca=request.session['login_id'], record_status='Active')
    data['ref_no'] = reference_no
    return JsonResponse(data)

def load_inspection_attachment_details(request):
    referenceNo = request.GET.get('attachment_refNo')
    print(referenceNo)
    attachment_details = t_file_attachment.objects.filter(application_no=referenceNo)
    return render(request, 'inspection/inspection_file_attachment.html',
                  {'file_attach': attachment_details})

def get_inspection_details(request, record_id):
    file_attach = t_file_attachment.objects.filter(application_no=record_id)
    inspection_details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=record_id)
    ec_details = t_ec_application_t1.objects.filter(ec_reference_no__isnull=False)
    return render(request, 'inspection/edit_inspection.html', {'inspection_details': inspection_details,
                                                               'file_attach': file_attach, 'ec_details': ec_details})

def get_formatted_date(date):
    if not date:
        return ''  # handle case when date is empty or None

    formatted_date = date.strftime('%d/%m/%Y')
    return formatted_date

def edit_inspection(request):
    edit_record_id = request.POST.get('record_id')
    edit_inspection_type = request.POST.get('inspection_type')
    edit_inspection_date = request.POST.get('inspection_date')
    edit_inspection_reason = request.POST.get('inspection_reason')
    edit_ec_clearance_no = request.POST.get('ec_clearance_no')
    edit_proponent_name = request.POST.get('proponent_name')
    edit_project_name = request.POST.get('project_name')
    edit_address = request.POST.get('address')
    edit_observation = request.POST.get('observation')
    edit_team_leader = request.POST.get('team_leader')
    edit_team_members = request.POST.get('team_members')
    edit_remarks = request.POST.get('remarks')
    edit_fines_penalties = request.POST.get('fines_penalties')
    edit_inspection_status = request.POST.get('inspection_status')
    inspection_details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=edit_record_id)
    inspection_details.update(inspection_type=edit_inspection_type, inspection_date=edit_inspection_date,
                              inspection_reason=edit_inspection_reason, ec_clearance_no=edit_ec_clearance_no,
                              proponent_name=edit_proponent_name, project_name=edit_project_name, address=edit_address,
                              observation=edit_observation, team_leader=edit_team_leader, team_members=edit_team_members,
                              remarks=edit_remarks, fines_penalties=edit_fines_penalties,
                              status=edit_inspection_status, updated_by_ca=request.session['login_id']
                              )

    return redirect(inspection_list)

def delete_inspection(request):
    delete_record_id = request.POST.get('record_id')
    inspection_details = t_inspection_monitoring_t1.objects.filter(record_id=delete_record_id)
    inspection_details.update(record_status='Deleted', updated_by_ca=request.session['login_id'])
    return redirect(inspection_list)

def get_inspection_submission_ref_no(request, service_code):
    last_reference_no = t_inspection_monitoring_t1.objects.aggregate(Max('inspection_reference_no'))
    lastRefNo = last_reference_no['inspection_reference_no__max']
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

def submit_inspection_form(request):
    reference_no = request.POST.get('record_id')
    created_on = datetime.now()
    t_inspection_monitoring_t1.objects.filter(
        inspection_reference_no=reference_no
    ).update(updated_on=created_on)

    return JsonResponse({'status': 'success'})


def add_inspection_report_file(request):
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


def add_inspection_report_file_name(request):
    app_no = request.POST.get('refNo')
    fileName = request.POST.get('filename')
    file_url = request.POST.get('file_url')

    t_file_attachment.objects.create(application_no=app_no,
                                     file_path=file_url, attachment=fileName)
    file_attach = t_file_attachment.objects.filter(application_no=app_no)
    return render(request, 'inspection/inspection_file_attachment.html', {'file_attach': file_attach})


# EndInspection
def get_birms_token():
    """
    get an auth token
    """
    credentials = {'username': 'ECSS',
                   'password': 'ECSs@2024!'
                   }

    headers = {'Accept': 'application/json'}

    try:
        # Send POST request to authenticate
        res = requests.post('https://birmsstagging.drc.gov.bt/api-services/core-module/api/v1/auth/external-users/logMeIn',
                            json=credentials, headers=headers, verify=False)

        # Check if request was successful (status code 200)
        if res.status_code == 200:
            # Extract access token from response JSON
            #print("Response content:", res.text)
            json_data = res.json()
            access_token = json_data['content']['tokenDto']['accessToken']
            return access_token
        else:
            print("Authentication failed. Status code:", res.status_code)
    except Exception as e:
        print("An error occurred:", e)

def get_fines_penalties_details(request):
    ec_ref_no = request.GET.get('ec_ref_no')
    ca_authority = request.session.get('ca_authority')
    #print(ca_authority)

    application_details = t_ec_t1.objects.filter(ec_reference_no=ec_ref_no, ca_authority=ca_authority)
    ec_count = (
            t_ec_t1.objects.filter(ec_reference_no=ec_ref_no,ca_authority=ca_authority)
    ).count()

    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'fines_penalties_details.html', {'application_details':application_details, 'ca_authority':ca_authority, 'ec_count':ec_count, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def save_fines_penalties(request):
    data = dict()
    try:
        application_no = get_application_no_fp()
        fines_penalties_remarks = request.POST.get('fines_penalties_remarks')
        ec_no = request.POST.get('ec_ref_no')
        proponent_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        validity = request.POST.get('ec_expiry_date')
        amount = request.POST.get('fines_and_penalties')
        ca_authority = request.POST.get('ca_authority')
        
        parsed_date = datetime.strptime(validity, "%d-%m-%Y")
        formatted_date = parsed_date.strftime("%Y-%m-%d")

        t_fines_penalties.objects.create(application_no=application_no,
                                        fines_date=date.today(),
                                        ec_no=ec_no,
                                        proponent_name=proponent_name,
                                        address=address,
                                        validity=formatted_date,
                                        amount=amount,
                                        fines_status='P',
                                        ca_authority=ca_authority,
                                        remarks=fines_penalties_remarks
                                        )
        application_details = t_ec_t1.objects.filter(ec_reference_no=ec_no)
        for app_det in application_details:
            applicationno = app_det.application_no
            applicant = app_det.applicant_id
            service_id = app_det.service_id
            ca_auth = app_det.ca_authority
            cid_no = app_det.cid
            mob_no = app_det.contact_no
            app_name = app_det.applicant_name
            email = app_det.email
            t_application_history.objects.create(application_no=applicationno,
                application_status='FP',
                application_date=date.today(),
                action_date=date.today(),
                actor_id=request.session['login_id'], 
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks='Fines Payment Pending',
                service_id=service_id,
                ca_authority=ca_auth)
            
            token = get_birms_token()
            #print("Token:", token)

            url = "https://birmsstagging.drc.gov.bt/api-services/moenr-service/api/v1/paymentdetails/create"
            today_date_str = date.today().isoformat()

            payload = {
                "platform": "Environment Clearance Services System",
                "refNo": application_no,
                "taxPayerNo": "11122233344",
                "taxPayerDocumentNo": "222333444555",
                "paymentRequestDate": today_date_str,
                "agencyCode": "DTH1552",
                "payerEmail": email,
                "mobileNo": mob_no,
                "totalPayableAmount": amount,
                "paymentDueDate": None,
                "taxPayerName": app_name,
                "code": "moenr",
                "paymentLists": [
                    {
                        "serviceCode": "211",
                        "description": "Fine and Penalities",
                        "payableAmount": amount
                    }
                ]
            }

            headers = {'Authorization': "Bearer {}".format(token)}
            
            try:
                response = requests.post(url, headers=headers, json=payload, verify=False)
                print(payload)
                print("Response Status Code:", response.status_code)
                print("Response Content:", response.text)

                # Check if the response content is empty
                if response.status_code == 200:
                    try:
                        data = response.json()  # Parse response JSON
                        paymentAdviceNo = data['content']['paymentAdviceNo']
                        #insert_app_payment_details(request, application_no, "fines_penalties", amount, "fines_penalties", paymentAdviceNo,None)
                       
                        t_payment_details.objects.create(
                            ref_no=application_no,
                            payment_request_date=date.today(),
                            tax_payer_name=app_name,
                            agency_code="DTH1552",
                            tax_payer_document_no=cid_no,
                            mobile_no=mob_no,
                            payer_email=email,
                            description="fines_and_penalties",
                            total_payable_amount=amount,
                            service_type="FINE",
                            payment_advice_no=paymentAdviceNo,
                            payment_type='Fines and Penalties',
                            application_no=application_no,
                            ca_authority=ca_authority
                        )
                    except ValueError as e:
                        print("Failed to parse JSON response:", e)
                
                else:
                    print("Payment request failed with status code:", response.status_code)
                    print("Response text:", response.text)
            except requests.exceptions.RequestException as e:
                print("HTTP Request failed:", e)
        application_details = t_ec_application_t1.objects.filter(application_no=application_no)
        for application_details in application_details:
            fines_penalties_email(application_details.email, application_no, amount)
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def get_application_no_fp():
    result = t_fines_penalties.objects.aggregate(Max('application_no'))
    last_no = result['application_no__max']
    year = timezone.now().year

    if not last_no:
        new_no = f"FNP-{year}-0001"
    else:
        seq = int(str(last_no).split("-")[2]) + 1
        new_no = f"FNP-{year}-{str(seq).zfill(4)}"

    return new_no

def insert_app_payment_details(request, application_no, description, total_amount, service_type, paymentAdviceNo, new_app_no):
    #print("insert_app_payment_details")
    cid_no = None
    mob_no = None
    identifier = None
    app_name = None
    email_id = None
    payment_type = None
    
    # app_details = t_ec_application_t1.objects.filter(application_no=application_no)

    if 'REN' in str(application_no):
        application_details = t_ec_application_t1.objects.filter(application_no=application_no).first()
        if application_details:
            app_details = t_ec_application_t1.objects.filter(
                ec_reference_no=application_details.ec_reference_no)
        else:
            app_details = []
    else:
        app_details = t_ec_application_t1.objects.filter(application_no=application_no)

    if description == "NEW APPLICATION":
        identifier = "new_application"
        payment_type = "Application Fee"
    elif description == "ADDITIONAL PAYMENT":
        identifier = "additional_payment"
        payment_type = "Additional Payment"
    elif description == "RENEWAL APPLICATION":
        identifier = "renewal_application"
        payment_type = "Renewal Fee"
    else:
        identifier = "tor_form"
    
    for app_det in app_details:
        cid_no = app_det.cid
        mob_no = app_det.contact_no
        app_name = app_det.applicant_name
        email_id = app_det.applicant_id
        ca_authority = app_det.ca_authority

    if 'new' in identifier or 'tor' in identifier or 'renewal' in identifier or 'fines' in identifier or 'additional' in identifier:
        t_payment_details.objects.create(
            ref_no=application_no,
            payment_request_date=date.today(),
            tax_payer_name=app_name,
            agency_code="DTH1552",
            tax_payer_document_no=cid_no,
            mobile_no=mob_no,
            payer_email=email_id,
            description=identifier,
            total_payable_amount=total_amount,
            service_type=service_type,
            payment_advice_no=paymentAdviceNo,
            application_no=new_app_no,
            payment_type=payment_type,
            ca_authority=ca_authority
        )
    
    #return redirect(identifier)
    return redirect(verify_application_list)

def fines_penalties_email(email_id, application_no, amount):
    subject = 'FINES AND PENALTY'
    message = "Dear Sir," \
              "" \
              "Your Application No" + application_no + "Has Has Fines and Penalty " \
              " of Nu. " + amount + " . Please Pay To Further Proceess Your Application." 
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    
#TOR Details
def tor_to_verifier(request):
    application_no = request.POST.get('application_no')

    application_details = t_ec_application_t1.objects.filter(application_no=application_no)
    application_details.update(application_status='V') #Tor Submitted to Verifier/approver
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    workflow_details.update(assigned_user_id=None)
    workflow_details.update(assigned_role_id='3')
    workflow_details.update(assigned_role_name='Verifier')
    workflow_details.update(action_date=date.today())
    workflow_details.update(actor_id=request.session['login_id'])
    workflow_details.update(actor_name=request.session['name'])
    workflow_details.update(application_status='V')
    
    return redirect(reviewer_application_list)

def approve_tor_application(request):
    application_no = request.POST.get('application_no')

    application_details = t_ec_application_t1.objects.filter(application_no=application_no)
    application_details.update(application_status='A') #Tor Submitted to Verifier/approver
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    workflow_details.update(assigned_user_id=None)
    workflow_details.update(assigned_role_id='3')
    workflow_details.update(assigned_role_name='Verifier')
    workflow_details.update(action_date=date.today())
    workflow_details.update(actor_id=request.session['login_id'])
    workflow_details.update(actor_name=request.session['name'])
    workflow_details.update(application_status='A')
    for work_details in workflow_details:
        service_id = work_details.service_id
        service_details = t_service_master.objects.filter(service_id=service_id)
        for service in service_details:
            service_name = service.service_name
            for email_id in application_details:
                emailId = email_id.email
                tor_clearance_no = get_tor_clearance_no(request,service_id)
                send_tor_approve_email(emailId, application_no, service_name, tor_clearance_no)
                application_details.update(tor_clearance_no=tor_clearance_no)
    return redirect(verify_application_list)

def tor_submit_email(email_id, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your TOR Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " . " 
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    
def fines_penalties(request):
    login_id = request.session.get('login_id')
    ca_authority = request.session.get('ca_authority')

    v_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='2',
        assigned_role_name='Verifier',
        action_date__isnull=False,
        application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
        ca_authority=request.session['ca_authority']
    ).count()
    # Reviewer application count
    r_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_user_id=login_id,
        assigned_role_name='Reviewer',
        ca_authority=ca_authority
    ).count()

    p_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_role_name='Reviewer',
        ca_authority=ca_authority,
        assigned_user_id__isnull=True,  # assigned_user_id is null
        action_date__isnull=False  # action_date is not null
    ).exclude(
        ca_authority=1  # Exclude ca_authority = 1
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                          status='A',
                                                          ec_expiry_date__lt=expiry_date_threshold).count()

    response = render(request, 'fines_penalties.html',
                  {'v_application_count': v_application_count, 'r_application_count': r_application_count,
                   'p_application_count': p_application_count})



    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def insert_payment_details(request,application_no,account_head, proponent_name,total_amount,ec_no):
    t_payment_details.objects.create(application_no=application_no,
            service_type='Fines And Penalties',
            application_date=date.today(), 
            proponent_name=proponent_name,
            amount=total_amount,
            account_head_code=account_head,
            ec_no=ec_no)
    return redirect(fines_penalties)

def ec_expired_list(request):
    current_date = timezone.now().date()
    expired_list = t_ec_application_t1.objects.filter(ec_expiry_date__lt=current_date, application_status='A',is_revoked__isnull=True)
    service_details = t_service_master.objects.all()
    return render(request,'expired_list.html',{'expired_list':expired_list, 'service_details':service_details})

def save_renew_attachment_reviewer(request):
    data = dict()
    ea_attach = request.FILES['renewal_attach']
    file_name = ea_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ECRV/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ea_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/ECRV" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_renew_attachment_details_reviewer(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='ECRV')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='ECRV')

    return render(request, 'renewal_attachment_page.html', {'file_attach': file_attach})