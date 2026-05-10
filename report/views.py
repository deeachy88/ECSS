from datetime import date, datetime, timedelta
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils import formats
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Count, Subquery, OuterRef, Exists
from django.db.models import Sum
from collections import defaultdict

import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

logger = logging.getLogger(__name__)

from ecs_admin.models import t_competant_authority_master, t_file_attachment, t_service_master, t_dzongkhag_master, t_gewog_master, t_thromde_master, t_user_master, \
    t_village_master, t_bsic_code, t_country_master, t_fees_schedule, t_other_details

from ecs_main.models import t_application_history, t_inspection_monitoring_t1
from proponent.models import t_ec_application_t2, t_ec_application_t1, t_ec_compliance, t_payment_details, \
    t_workflow_dtls, t_ec_t1, t_ec_t2, t_ec_additional_information, t_ec_ai_remainder


def ec_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all() 
    v_application_count = 0
    r_application_count = 0
    p_application_count = 0
    ec_renewal_count = 0
    ca_authority = request.session.get('ca_authority', None)
    login_id=request.session.get('login_id', None)

    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    if ca_authority is not None:
        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2',
            assigned_role_name='Verifier',
            action_date__isnull=False,
            application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
            ca_authority=request.session['ca_authority']).count()

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
        ).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    response = render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'p_application_count':p_application_count, 'ca_list': ca_list, 'service_list': service_list})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_ec_list(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    ca_authority = request.GET.get('ca_authority')
    login_id = request.session.get('login_id')
    # dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    ca_auth= request.session['ca_authority']

    r_application_count = 0
    p_application_count = 0
    ec_renewal_count = 0
    v_application_count = 0

    # if ca_authority == 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         application_status='Approved').values()
    # elif ca_authority == 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Approved').values()
    # elif ca_authority != 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         application_status='Approved').values()
    # elif ca_authority != 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Approved').values()

    if ca_authority == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='A').values()
    elif ca_authority == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='A', service_id=service_id).values()
    elif ca_authority != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            application_status='A').values()
    elif ca_authority != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority, service_id=service_id,
                                                            application_status='A').values()
    # Verifier application count
    v_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='2',
        assigned_role_name='Verifier',
        ca_authority=ca_auth
    ).count()

    # Reviewer application count
    r_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_user_id=login_id,
        assigned_role_name='Reviewer',
        ca_authority=ca_auth
    ).count()

    p_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_role_name='Reviewer',
        ca_authority=ca_auth,
        assigned_user_id__isnull=True,  # assigned_user_id is null
        action_date__isnull=False  # action_date is not null
    ).count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                              status='A',
                                                                              ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count,'p_application_count':p_application_count, 'ec_list': ec_list, 'ca_list': ca_list})


def ec_reject_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                              status='A',
                                                                              ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_reject_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'v_application_count':v_application_count,'r_application_count':r_application_count, 'service_list': service_list})

def view_ec_reject_list(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    ca_authority = request.GET.get('ca_authority')
    dzongkhag_code = request.GET.get('dzongkhag_code')
    login_id = request.session.get('login_id')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    ca_auth = request.session.get('ca_authority')
    print(ca_auth)
    print(ca_authority)

    # if ca_authority == 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         application_status='Rejected').values()
    # elif ca_authority == 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Rejected').values()
    # elif ca_authority != 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         application_status='Rejected').values()
    # elif ca_authority != 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Rejected').values()
    if ca_authority == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Rejected').values()
    elif ca_authority == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Rejected',
                                                            service_id=service_id).values()
    elif ca_authority != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            application_status='Rejected').values()
    elif ca_authority != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority, service_id=service_id,
                                                            application_status='Rejected').values()
    v_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='2',
        assigned_role_name='Verifier',
        ca_authority=ca_auth
    ).count()
    # Reviewer application count
    r_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_user_id=login_id,
        assigned_role_name='Reviewer',
        ca_authority=ca_auth
    ).count()

    p_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_role_name='Reviewer',
        ca_authority=ca_auth,
        assigned_user_id__isnull=True,  # assigned_user_id is null
        action_date__isnull=False  # action_date is not null
    ).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                              status='A',
                                                                              ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_reject_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count, 'ec_list': ec_list,'v_application_count':v_application_count,'r_application_count':r_application_count, 'p_application_count':p_application_count, 'ca_list': ca_list})

def ec_pending_report_form(request):
    login_id = request.session.get('login_id')
    ca_authority = request.session.get('ca_authority')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    v_application_count = 0
    r_application_count = 0
    p_application_count = 0
    ec_renewal_count = 0

    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
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
    ).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(
        accept_reject__isnull=True,
        login_type='C'
    ).count()
    ec_renewal_count = t_ec_t1.objects.filter(
        ca_authority=request.session['ca_authority'],
        status='A',
        ec_expiry_date__lt=expiry_date_threshold
    ).count()
    return render(request, 'ec_pending_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'v_application_count':v_application_count,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'r_application_count':r_application_count, 'p_application_count':p_application_count, 'service_list': service_list})

def ec_pending_list(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    ca_authority = request.GET.get('ca_authority')
    #dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    ca_auth = request.session.get('ca_authority')
    login_id = request.session.get('login_id')

    if ca_authority == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(application_date__range=[from_date, to_date],
                                                            application_status='P').values()
    elif ca_authority == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(application_date__range=[from_date, to_date],
                                                            application_status='P',
                                                            service_id=service_id).values()
    elif ca_authority != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(application_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            application_status='P').values()
    elif ca_authority != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(application_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority, service_id=service_id,
                                                            application_status='P').values()
    # Verifier application count
    v_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='2',
        assigned_role_name='Verifier',
        ca_authority=ca_auth
    ).count()

    # Reviewer application count
    r_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_user_id=login_id,
        assigned_role_name='Reviewer',
        ca_authority=ca_auth
    ).count()

    p_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='3',
        assigned_role_name='Reviewer',
        ca_authority=ca_auth,
        assigned_user_id__isnull=True,  # assigned_user_id is null
        action_date__isnull=False  # action_date is not null
    ).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                              status='A',
                                                                              ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_pending_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'p_application_count':p_application_count,'ec_list': ec_list, 'ca_list': ca_list})

def land_use_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    #ca_list = t_competant_authority_master.objects.all().distinct('competent_authority')
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                              status='A',
                                                                              ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'land_use_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list, 'service_list': service_list})

def land_use_report(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    if dzongkhag_code == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved').values()
    elif dzongkhag_code == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            service_id=service_id).values()
    elif dzongkhag_code != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code).values()
    elif dzongkhag_code != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code,
                                                            service_id=service_id).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'land_use_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ec_list': ec_list, 'ca_list': ca_list})

def revenue_report_form(request):
    login_id = request.session.get('login_id')
    ca_authority = request.session.get('ca_authority')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all().distinct('competent_authority')
    v_application_count = 0
    r_application_count = 0
    p_application_count = 0
    ec_renewal_count = 0
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
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
    ).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'revenue_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'p_application_count':p_application_count, 'ca_list': ca_list, 'service_list': service_list})

def revenue_report(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    # service_id = request.GET.get('service_id')
    login_id = request.session.get('login_id')
    ca_list = t_competant_authority_master.objects.all()
    ca_authority = request.session.get('ca_authority')

    # Convert date strings to timezone-aware datetime objects
    from_datetime = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
    to_datetime = timezone.make_aware(datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))

    ec_list = t_payment_details.objects.filter(
        ca_authority=ca_authority,
        receipt_date__range=[from_datetime, to_datetime]
    ).values()

    # Calculate sum of total_payable_amount

    total_sum = t_payment_details.objects.filter(
        ca_authority=ca_authority,
        receipt_date__date__gte=from_date,
        receipt_date__date__lte=to_date
    ).aggregate(total=Sum('total_payable_amount'))['total'] or 0

    # Verifier application count
    v_application_count = t_workflow_dtls.objects.filter(
        assigned_role_id='2',
        assigned_role_name='Verifier',
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
    ).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'revenue_report.html', {'ec_list': ec_list,'total_sum':total_sum, 'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'v_application_count':v_application_count,'r_application_count':r_application_count, 'p_application_count':p_application_count})

#Application Status
def application_status_list(request):
    login_type = request.session.get('login_type', None)
    login_id = request.session['login_id']
    ca_list = t_competant_authority_master.objects.all()
    dzongkhag_list = t_dzongkhag_master.objects.all()
    application_list = []
    ec_renewal_count = 0
    v_application_count = 0
    r_application_count = 0
    p_application_count = 0
    draft_count = 0
    app_hist_count = 0
    cl_application_count = 0
    tor_application_count = 0
    applicant_id = request.session.get('email', None)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True, login_type='C').count()
    
    if login_type == 'C': # 'C' is client OR Proponent
        app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()

        email_id = request.session['email']
       # login_id = request.session['login_id']

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
    
    elif login_type == 'I':  # 'I' is Internal OR Competent Authority
        role = request.session['role']
        ca_authority = request.session.get('ca_authority', None)
        if ca_authority is not None:
            v_application_count = t_workflow_dtls.objects.filter(
                assigned_role_id='2',
                assigned_role_name='Verifier',
                action_date__isnull=False,
                application_status__in=['P', 'DEC', 'AL', 'FT', 'V', 'RRJ'],
                ca_authority=request.session['ca_authority']).count()

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
                ca_authority=ca_authority,
                assigned_user_id__isnull=True,  # assigned_user_id is null
                action_date__isnull=False  # action_date is not null
            ).exclude(
                ca_authority=1  # Exclude ca_authority = 1
            ).count()
            # print(p_application_count)

            expiry_date_threshold = datetime.now().date() + timedelta(days=60)
            ec_renewal_count = t_ec_t1.objects.filter(ca_authority=request.session['ca_authority'], status='A', ec_expiry_date__lt=expiry_date_threshold).count()

    # FIX: Use distinct() and order by application date to get unique records
    if login_type == 'C':
        application_list = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id, application_type='New'
        ).order_by('application_no', '-application_date').distinct('application_no')
    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        application_list = t_ec_application_t1.objects.all().order_by('application_no', '-application_date').distinct('application_no')
    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        application_list = t_ec_application_t1.objects.filter(
            ca_authority=ca_authority
        ).order_by('application_no', '-application_date').distinct('application_no')
    
    # If distinct with field doesn't work, use values() with distinct
    # application_list = t_ec_application_t1.objects.filter(
    #     applicant_id=applicant_id
    # ).values('application_no', 'application_date', 'applicant_name', 'project_name', 
    #          'address', 'ec_reference_no', 'ec_approve_date', 'application_status',
    #          'service_id', 'application_source').distinct()

    response = render(request, 'application_status_list.html', {
        'client_application_count': client_application_count,
        'ca_list': ca_list, 
        'ec_renewal_count': ec_renewal_count, 
        'dzongkhag_list': dzongkhag_list, 
        'v_application_count': v_application_count, 
        'r_application_count': r_application_count,
        'p_application_count': p_application_count,
        'application_list': application_list, 
        'app_hist_count': app_hist_count, 
        'cl_application_count': cl_application_count,
        'draft_count': draft_count,
        'tor_application_count': tor_application_count
    })

    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def application_history(request):
    login_type = request.session['login_type']
    ca_list = t_competant_authority_master.objects.all()
    dzongkhag_list = t_dzongkhag_master.objects.all()
    application_list = []
    applicant_id = request.session.get('email', None)
    assigned_user_id = request.session.get('login_id', None)

    if login_type == 'C':
        applicant_id = request.session['email']
    elif login_type == 'I':
        role = request.session['role']
        ca_authority = request.session['ca_authority']

    if login_type == 'C':
        # Get distinct latest applications for citizen
        application_list = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id
        ).order_by('application_no', '-action_date', '-record_id').distinct('application_no')
        
    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        # Get distinct latest applications for all
        application_list = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id
        ).order_by('application_no', '-action_date', '-record_id').distinct('application_no')
        
    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        # Get distinct latest applications for specific CA authority
        application_list = t_ec_application_t1.objects.filter(
            applicant_id=applicant_id
        ).order_by('application_no', '-action_date', '-record_id').distinct('application_no')

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
    
    service_details = t_service_master.objects.all()
    
    return render(request, 'application_history.html', {
        'ca_list': ca_list,
        'service_details': service_details, 
        'dzongkhag_list': dzongkhag_list,
        'application_list': application_list,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'ec_renewal_count':ec_renewal_count,
        'draft_count': draft_count
    })


def application_status(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    if dzongkhag_code == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved').values()
    elif dzongkhag_code == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            service_id=service_id).values()
    elif dzongkhag_code != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code).values()
    elif dzongkhag_code != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_application_t1.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code,
                                                            service_id=service_id).values()

    return render(request, 'application_status.html',
                  {'dzongkhag_list': dzongkhag_list, 'ec_list': ec_list, 'ca_list': ca_list})


def client_application_details(request):
    application_no = request.GET.get('application_no')
    service_id = request.GET.get('service_id')
    status = None
    ca_auth = None
    service_code = None

    service_master = t_service_master.objects.filter(
        service_id=service_id
    ).first()
    attachments = service_master.attachments if service_master else ''

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
    result = t_ec_application_t1.objects.filter(application_no=application_no,application_no__contains='TOR')
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    for work_details in workflow_details:
        status = work_details.application_status
        ca_auth = work_details.ca_authority
    if result.exists():
        application_details = t_ec_application_t1.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOR')
        tor_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')
        tor_attach_count = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR').count()
        return render(request, 'application_details/tor_details.html', {'application_details':application_details,'file_attach':file_attach,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'tor_attach':tor_attach, 'tor_attach_count':tor_attach_count, 'attachments':attachments})
    else:
        #if service_id != '10':
        application_details = t_ec_application_t1.objects.filter(application_no=application_no,service_type='Main Activity')
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        file_attach = t_file_attachment.objects.filter(
            application_no=application_no
        ).exclude(
            attachment_type__in=['EATC', 'LU', 'RLU', 'AI', 'ECNC', 'ENOC', 'ECR', 'REPORT', 'RRJ', 'RTOR', 'TOR']
        )
        ec_details = t_ec_application_t2.objects.filter(application_no=application_no)
        reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
        eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
        lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
        rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
        app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['login_id']
        ).distinct('application_no').count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'application_details/application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'status':status,
                                                    'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'file_attach':file_attach,
                                                    'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'ec_details':ec_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach, 'rev_lu_attach':rev_lu_attach, 'attachments':attachments})
        #elif service_id == '10':
        #    renewal_details_one = t_ec_renewal_t1.objects.filter(application_no=application_no)
       #     for renewal_details_one in renewal_details_one:
       #         application_details = t_ec_application_t1.objects.filter(ec_reference_no=renewal_details_one.ec_reference_no,service_type='Main Activity')
       #     renewal_details_two = t_ec_compliance.objects.filter(application_no=application_no)
       #     file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ECR')
       #     reviewer_list = t_user_master.objects.filter(role_id='3')
       #     dzongkhag = t_dzongkhag_master.objects.all()
       #     gewog = t_gewog_master.objects.all()
       #     village = t_village_master.objects.all()
       #     lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
       #     rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
       #     app_hist_count = t_application_history.objects.filter(
       #         applicant_id=request.session['login_id']
       #     ).distinct('application_no').count()
       #     cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
       #     return render(request, 'application_details/renewal_application_details.html',{'application_details':application_details,'renewal_details_one':renewal_details_one,'status':status,
       #                                                             'dzongkhag':dzongkhag,'gewog':gewog,'village':village,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'renewal_details_two':renewal_details_two,'reviewer_list':reviewer_list,'file_attach':file_attach ,'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach,'attachments':attachments})

#EC Renewal Notifications
def ec_renewal_list(request):
    ca_authority = request.session.get('ca_authority', None)
    ec_renewal_count = 0
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    ec_list = []  # Initialize ec_list with an empty list

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    if ca_authority is not None:
        ec_list = t_ec_t1.objects.filter(
            ca_authority=ca_authority,
            status='A',
            ec_expiry_date__lt=expiry_date_threshold
        ).values()
        ec_renewal_count = t_ec_t1.objects.filter(
            ca_authority=ca_authority,
            status='A',
            ec_expiry_date__lt=expiry_date_threshold
        ).count()

    response = render(request, 'ec_renewal_list.html',
                    {'dzongkhag_list': dzongkhag_list, 'ec_renewal_count': ec_renewal_count, 'ec_list': ec_list,
                    'ca_list': ca_list})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def send_notification(request):
    try:
        ca_authority          = request.session['ca_authority']
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)

        ec_list = t_ec_t1.objects.filter(
            ca_authority       = ca_authority,
            status = 'A',
            ec_expiry_date__lt = expiry_date_threshold
        ).values('ec_reference_no', 'applicant_id')

        for ec in ec_list:
            ec_reference_no = ec['ec_reference_no']
            email           = ec['applicant_id']  # plain string — list wrapping done in send_notification_mail

            with transaction.atomic():
                transaction.on_commit(lambda ec_ref=ec_reference_no, em=email: threading.Thread(
                    target=_send_notification_mail_in_background,
                    args=(em, ec_ref),
                    daemon=True
                ).start())

        return redirect('ec_renewal_list')

    except Exception as exc:
        logger.exception("send_notification failed for ca_authority=%s", ca_authority)
        return redirect('ec_renewal_list')


def _send_notification_mail_in_background(email, ec_reference_no):
    """
    Thread target: never uses request/session. Only uses passed primitives.
    """
    try:
        send_notification_mail(email, ec_reference_no)
    except Exception:
        logger.exception(
            "Failed to send renewal notification email to=%s for ec_reference_no=%s",
            email, ec_reference_no
        )


def send_notification_mail(email, ec_reference_no):
    subject = "Environment Clearance Renewal Notification"
    message = (
        f"Dear Sir/Madam,\n\n"
        f"Your Environmental Clearance No. {ec_reference_no} is due for renewal "
        f"in less than 60 days. DECC would like to request you to renew the "
        f"Environmental Clearance before the expiry.\n\n"
        f"Thanking You,\nECS System Team"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[email],
        fail_silently=False,
    )


# ADDITIONAL INFORMATION List
def ai_list(request):
    login_type = request.session.get('login_type', None)
    login_id = request.session['login_id']
    ca_list = t_competant_authority_master.objects.all()
    dzongkhag_list = t_dzongkhag_master.objects.all()
    application_list = []
    ec_renewal_count = 0
    v_application_count = 0
    r_application_count = 0
    p_application_count = 0
    draft_count = 0
    app_hist_count = 0
    cl_application_count = 0
    tor_application_count = 0
    applicant_id = request.session.get('email', None)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True, login_type='C').count()

    if login_type == 'C':  # 'C' is client OR Proponent
        app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()

        email_id = request.session['email']


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

    elif login_type == 'I':  # 'I' is Internal OR Competent Authority
        role = request.session['role']
        ca_authority = request.session.get('ca_authority', None)
        if ca_authority is not None:
            v_application_count = t_workflow_dtls.objects.filter(
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=request.session['ca_authority']
            ).count()

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

            expiry_date_threshold = datetime.now().date() + timedelta(days=60)
            ec_renewal_count = t_ec_t1.objects.filter(
                ca_authority=request.session['ca_authority'],
                status='A',
                ec_expiry_date__lt=expiry_date_threshold
            ).count()

    # 1. Subquery to fetch applicant_name
    applicant_name_sq = t_ec_application_t1.objects.filter(
        application_no=OuterRef('application_no')
    ).values('applicant_name')[:1]

    # 2. Build application_list based on login_type
    if login_type == 'C':
        application_list = (
            t_ec_additional_information.objects.filter(
                applicant_id=applicant_id,
                additional_info_proponent__isnull=True
            )
            .annotate(applicant_name=Subquery(applicant_name_sq))
            .order_by('application_no')
        )

    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        valid_application_nos = t_ec_application_t1.objects.values_list(
            'application_no', flat=True
        ).distinct()

        application_list = (
            t_ec_additional_information.objects.filter(
                application_no__in=valid_application_nos,
                additional_info_proponent__isnull=True
            )
            .annotate(applicant_name=Subquery(applicant_name_sq))
            .order_by('application_no')
        )

    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        valid_application_nos = t_ec_application_t1.objects.filter(
            ca_authority=ca_authority
        ).values_list('application_no', flat=True).distinct()

        application_list = (
            t_ec_additional_information.objects.filter(
                application_no__in=valid_application_nos,
                additional_info_proponent__isnull=True
            )
            .annotate(applicant_name=Subquery(applicant_name_sq))
            .order_by('application_no')
        )

    # 3. Fetch all reminders for the records in application_list
    #    and group them by precord_id into a dict
    record_ids = [app.record_id for app in application_list]

    reminders = t_ec_ai_remainder.objects.filter(
        precord_id__in=record_ids
    ).order_by('precord_id', 'reminder_sent')  # oldest to latest

    # { record_id: [reminder1, reminder2, ...] }
    reminder_map = defaultdict(list)
    for r in reminders:
        reminder_map[r.precord_id].append(r)

    # 4. Attach reminder_list and reminder_count to each app object
    for app in application_list:
        app.reminder_list = reminder_map.get(app.record_id, [])
        app.reminder_count = len(app.reminder_list)

    # 5. Pass to template
    response = render(request, 'ai_list.html', {
        'application_list': application_list,
        'client_application_count': client_application_count,
        'ca_list': ca_list,
        'ec_renewal_count': ec_renewal_count,
        'dzongkhag_list': dzongkhag_list,
        'v_application_count': v_application_count,
        'r_application_count': r_application_count,
        'p_application_count':p_application_count,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'draft_count': draft_count,
        'tor_application_count': tor_application_count,
    })

    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response