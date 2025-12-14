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
from django.db.models import Count, Subquery, OuterRef


from ecs_admin.models import t_competant_authority_master, t_file_attachment, t_service_master, t_dzongkhag_master, t_gewog_master, t_thromde_master, t_user_master, \
    t_village_master, t_bsic_code, t_country_master, t_fees_schedule

from ecs_main.models import t_application_history, t_inspection_monitoring_t1
from proponent.models import t_ec_industries_t11_ec_details, t_ec_industries_t1_general, t_ec_renewal_t1, t_ec_renewal_t2, t_payment_details, t_workflow_dtls

def ec_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all() 
    v_application_count = 0
    r_application_count = 0
    ec_renewal_count = 0
    ca_authority = request.session.get('ca_authority', None)

    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    if ca_authority is not None:
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
        r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=60)
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    response = render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list, 'service_list': service_list})

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
    # dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()


    # if ca_authority == 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         application_status='Approved').values()
    # elif ca_authority == 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Approved').values()
    # elif ca_authority != 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         application_status='Approved').values()
    # elif ca_authority != 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Approved').values()

    if ca_authority == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='A').values()
    elif ca_authority == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='A', service_id=service_id).values()
    elif ca_authority != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            application_status='A').values()
    elif ca_authority != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority, service_id=service_id,
                                                            application_status='A').values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ec_list': ec_list, 'ca_list': ca_list})


def ec_reject_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_reject_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'v_application_count':v_application_count,'r_application_count':r_application_count, 'service_list': service_list})

def view_ec_reject_list(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    ca_authority = request.GET.get('ca_authority')
    dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    # if ca_authority == 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         application_status='Rejected').values()
    # elif ca_authority == 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Rejected').values()
    # elif ca_authority != 'ALL' and dzongkhag_code == 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         application_status='Rejected').values()
    # elif ca_authority != 'ALL' and dzongkhag_code != 'ALL':
    #     ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
    #                                                         ca_authority=ca_authority,
    #                                                         dzongkhag_code=dzongkhag_code,
    #                                                         application_status='Rejected').values()
    if ca_authority == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Rejected').values()
    elif ca_authority == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Rejected',
                                                            service_id=service_id).values()
    elif ca_authority != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            application_status='Rejected').values()
    elif ca_authority != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority, service_id=service_id,
                                                            application_status='Rejected').values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_reject_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count, 'ec_list': ec_list,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list})

def ec_pending_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_pending_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'v_application_count':v_application_count,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'r_application_count':r_application_count, 'service_list': service_list})

def ec_pending_list(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    ca_authority = request.GET.get('ca_authority')
    #dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    if ca_authority == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(application_date__range=[from_date, to_date],
                                                            application_status='P').values()
    elif ca_authority == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(application_date__range=[from_date, to_date],
                                                            application_status='P',
                                                            service_id=service_id).values()
    elif ca_authority != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(application_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            application_status='P').values()
    elif ca_authority != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(application_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority, service_id=service_id,
                                                            application_status='P').values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_pending_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ec_list': ec_list, 'ca_list': ca_list})

def land_use_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    #ca_list = t_competant_authority_master.objects.all().distinct('competent_authority')
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
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
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved').values()
    elif dzongkhag_code == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            service_id=service_id).values()
    elif dzongkhag_code != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code).values()
    elif dzongkhag_code != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code,
                                                            service_id=service_id).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'land_use_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ec_list': ec_list, 'ca_list': ca_list})

def revenue_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all().distinct('competent_authority')
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True,login_type='C').count()
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'revenue_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'client_application_count':client_application_count,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list, 'service_list': service_list})

def revenue_report(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    # service_id = request.GET.get('service_id')
    ca_list = t_competant_authority_master.objects.all()

    ec_list = t_payment_details.objects.filter(transaction_date__range=[from_date, to_date]).values()

    # if service_id == 'ALL':
    #    ec_list = t_payment_details.objects.filter(transaction_date__range=[from_date, to_date]).values()
    # elif service_id != 'ALL':
    #    ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'revenue_report.html', {'ec_list': ec_list,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'v_application_count':v_application_count,'r_application_count':r_application_count})

#Application Status
def application_status_list(request):
    login_type = request.session.get('login_type', None)
    ca_list = t_competant_authority_master.objects.all()
    dzongkhag_list = t_dzongkhag_master.objects.all()
    application_list = []
    ec_renewal_count = 0
    v_application_count = 0
    r_application_count = 0
    app_hist_count = 0
    cl_application_count = 0
    tor_application_count = 0
    applicant_id = request.session.get('email', None)
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True, login_type='C').count()
    
    if login_type == 'C':
        app_hist_count = t_application_history.objects.filter(
            applicant_id=request.session['email']
        ).distinct('application_no').count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        t1_general_subquery = t_ec_industries_t1_general.objects.filter(
            tor_application_no=OuterRef('application_no')
        ).values('tor_application_no')
        
        tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR', applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()

        expiry_date_threshold = datetime.now().date() + timedelta(days=60)

        renewal_expiry_subquery = t_ec_renewal_t1.objects.filter(
            ec_reference_no=OuterRef('ec_reference_no')
        ).values('ec_expiry_date')[:1]

        non_updated_renewals = t_ec_industries_t1_general.objects.filter(
            applicant_id=request.session['email'],
            service_type__in=["Main Activity", "Old EC"],
            ec_expiry_date__lt=expiry_date_threshold,
        ).filter(
            ec_expiry_date__lt=Subquery(renewal_expiry_subquery)
        )

        ec_renewal_count = non_updated_renewals.count()
    
    elif login_type == 'I':
        role = request.session['role']
        ca_authority = request.session.get('ca_authority', None)
        if ca_authority is not None:
            v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
            r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
            expiry_date_threshold = datetime.now().date() + timedelta(days=60)
            ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'], application_status='A', ec_expiry_date__lt=expiry_date_threshold).count()

    # FIX: Use distinct() and order by application date to get unique records
    if login_type == 'C':
        application_list = t_ec_industries_t1_general.objects.filter(
            applicant_id=applicant_id, application_type='New'
        ).order_by('application_no', '-application_date').distinct('application_no')
    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        application_list = t_ec_industries_t1_general.objects.all().order_by('application_no', '-application_date').distinct('application_no')
    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        application_list = t_ec_industries_t1_general.objects.filter(
            ca_authority=ca_authority
        ).order_by('application_no', '-application_date').distinct('application_no')
    
    # If distinct with field doesn't work, use values() with distinct
    # application_list = t_ec_industries_t1_general.objects.filter(
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
        'application_list': application_list, 
        'app_hist_count': app_hist_count, 
        'cl_application_count': cl_application_count, 
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

    if login_type == 'C':
        applicant_id = request.session['email']
    elif login_type == 'I':
        role = request.session['role']
        ca_authority = request.session['ca_authority']

    if login_type == 'C':
        # Get distinct latest applications for citizen
        application_list = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).order_by('application_no', '-action_date', '-record_id').distinct('application_no')
        
    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        # Get distinct latest applications for all
        application_list = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).order_by('application_no', '-action_date', '-record_id').distinct('application_no')
        
    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        # Get distinct latest applications for specific CA authority
        application_list = t_application_history.objects.filter(
            applicant_id=applicant_id
        ).order_by('application_no', '-action_date', '-record_id').distinct('application_no')

    
    cl_application_count = t_workflow_dtls.objects.filter(
        assigned_user_id=request.session['login_id']
    ).count()

    app_hist_count = t_application_history.objects.filter(
        applicant_id=request.session['login_id']
    ).distinct('application_no').count()

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    renewal_expiry_subquery = t_ec_renewal_t1.objects.filter(
        ec_reference_no=OuterRef('ec_reference_no')
    ).values('ec_expiry_date')[:1]

    non_updated_renewals = t_ec_industries_t1_general.objects.filter(
        applicant_id=request.session['email'],
        service_type__in=["Main Activity", "Old EC"],
        ec_expiry_date__lt=expiry_date_threshold,
    ).filter(
        ec_expiry_date__lt=Subquery(renewal_expiry_subquery)
    )

    ec_renewal_count = non_updated_renewals.count()
    
    service_details = t_service_master.objects.all()
    
    return render(request, 'application_history.html', {
        'ca_list': ca_list,
        'service_details': service_details, 
        'dzongkhag_list': dzongkhag_list,
        'application_list': application_list,
        'app_hist_count': app_hist_count,
        'cl_application_count': cl_application_count,
        'ec_renewal_count':ec_renewal_count
    })


def application_status(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    if dzongkhag_code == 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved').values()
    elif dzongkhag_code == 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            service_id=service_id).values()
    elif dzongkhag_code != 'ALL' and service_id == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            application_status='Approved',
                                                            dzongkhag_code=dzongkhag_code).values()
    elif dzongkhag_code != 'ALL' and service_id != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
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
    result = t_ec_industries_t1_general.objects.filter(application_no=application_no,application_no__contains='TOR')
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    for work_details in workflow_details:
        status = work_details.application_status
        ca_auth = work_details.ca_authority
    if result.exists():
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOR')
        tor_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')
        tor_attach_count = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR').count()
        return render(request, 'application_details/tor_form_details.html', {'application_details':application_details,'file_attach':file_attach,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'tor_attach':tor_attach, 'tor_attach_count':tor_attach_count})
    else:
        if service_id != '10':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type=service_code)
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
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
                                                        'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'ec_details':ec_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach, 'rev_lu_attach':rev_lu_attach})
        elif service_id == '10':
            renewal_details_one = t_ec_renewal_t1.objects.filter(application_no=application_no)
            for renewal_details_one in renewal_details_one:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=renewal_details_one.ec_reference_no,service_type='Main Activity')
            renewal_details_two = t_ec_renewal_t2.objects.filter(application_no=application_no)
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ECR')
            reviewer_list = t_user_master.objects.filter(role_id='3')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(
                applicant_id=request.session['login_id']
            ).distinct('application_no').count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'application_details/renewal_application_details.html',{'application_details':application_details,'renewal_details_one':renewal_details_one,'status':status,
                                                                    'dzongkhag':dzongkhag,'gewog':gewog,'village':village,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'renewal_details_two':renewal_details_two,'reviewer_list':reviewer_list,'file_attach':file_attach ,'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
                

#EC Renewal Notifications

def ec_renewal_list(request):
    ca_authority = request.session.get('ca_authority', None)
    ec_renewal_count = 0
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    ec_list = []  # Initialize ec_list with an empty list

    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    if ca_authority is not None:
        ec_list = t_ec_industries_t1_general.objects.filter(
            ca_authority=ca_authority,
            application_status='A',
            ec_expiry_date__lt=expiry_date_threshold
        ).values()
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(
            ca_authority=ca_authority,
            application_status='A',
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
    notice = request.POST.get('notice')
    ca_authority = request.session['ca_authority']
    expiry_date_threshold = datetime.now().date() + timedelta(days=60)

    ec_list = t_ec_industries_t1_general.objects.filter(
        ca_authority=ca_authority,
        application_status='A',
        ec_expiry_date__lt=expiry_date_threshold
    ).values('ec_reference_no', 'applicant_id')

    for ec in ec_list:
        ec_reference_no = ec['ec_reference_no']
        email = [ec['applicant_id']]  # Convert to list for send_mail

        subject = 'Environment Clearance Renewal Notification'
        message = "Dear Sir/Madam, \n\nYour Environmental Clearance No. " + ec_reference_no + " is due for renewal in less than 30 Days. DECC would like to request you to renew the Environmental Clearance before the expiry. \n\nThanking You"

        send_mail(
            subject,
            message,
            'systems@moenr.gov.bt',
            email,
            fail_silently=False,
            auth_user='systems@moenr.gov.bt',
            auth_password='aqjsbjamnzxtadvl',
            connection=None,
            html_message=None
        )

    # Move return OUTSIDE the loop
    return redirect('ec_renewal_list')


