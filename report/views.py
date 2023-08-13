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

from proponent.models import t_ec_industries_t11_ec_details, t_ec_industries_t13_dumpyard, t_ec_industries_t1_general, t_ec_industries_t2_partner_details, \
    t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, \
    t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, \
    t_ec_industries_t9_products_by_products, t_ec_industries_t10_hazardous_chemicals, t_ec_renewal_t1, t_ec_renewal_t2, t_payment_details, t_workflow_dtls

from ecs_admin.models import t_competant_authority_master, t_file_attachment, t_service_master, t_dzongkhag_master, t_gewog_master, t_thromde_master, t_user_master, \
    t_village_master, t_bsic_code, t_country_master, t_fees_schedule

from ecs_main.models import t_application_history, t_inspection_monitoring_t1

def ec_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    # ca_list = t_competant_authority_master.objects.all().distinct('competent_authority')
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list, 'service_list': service_list})

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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_reject_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'v_application_count':v_application_count,'r_application_count':r_application_count, 'service_list': service_list})

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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_pending_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'v_application_count':v_application_count,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'r_application_count':r_application_count, 'service_list': service_list})

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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'land_use_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list, 'service_list': service_list})

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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'revenue_report_form.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'ca_list': ca_list, 'service_list': service_list})

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
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'revenue_report.html', {'ec_list': ec_list,'ec_renewal_count':ec_renewal_count, 'ca_list': ca_list,'v_application_count':v_application_count,'r_application_count':r_application_count})

#Application Status
def application_status_list(request):

    login_type = request.session['login_type']
    ca_list = t_competant_authority_master.objects.all()
    dzongkhag_list = t_dzongkhag_master.objects.all()
    application_list = []
    ec_renewal_count = 0
    v_application_count = 0
    r_application_count = 0
    app_hist_count = 0  # Provide a default value
    cl_application_count = 0  # Provide a default value

    if login_type == 'C':
        applicant_id = request.session['email']
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    elif login_type == 'I':
        role = request.session['role']
        ca_authority = request.session['ca_authority']
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
        r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=30)
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'], application_status='A', ec_expiry_date__lt=expiry_date_threshold).count()

    if login_type == 'C':
        application_list = t_ec_industries_t1_general.objects.filter(applicant_id=applicant_id).values()
    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        application_list = t_ec_industries_t1_general.objects.all()
    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        application_list = t_ec_industries_t1_general.objects.filter(ca_authority=ca_authority).values()
    
    # Return the render statement with the variables as before
    return render(request, 'application_status_list.html', {'ca_list': ca_list, 'ec_renewal_count': ec_renewal_count, 'dzongkhag_list': dzongkhag_list, 'v_application_count': v_application_count, 'r_application_count': r_application_count, 'application_list': application_list, 'app_hist_count': app_hist_count, 'cl_application_count': cl_application_count})





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
        application_list = t_application_history.objects.filter(applicant_id=applicant_id).values()
    elif login_type == 'I' and (role == 'Admin' or role == 'NECS Head'):
        application_list = t_application_history.objects.all()
    elif login_type == 'I' and (role == 'Verifier' or role == 'Reviewer'):
        application_list = t_application_history.objects.filter(ca_authority=ca_authority).values()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    service_details = t_service_master.objects.all()
    return render(request, 'application_history.html', {'ca_list': ca_list,'service_details':service_details, 'dzongkhag_list': dzongkhag_list,
                                                           'application_list': application_list,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count})


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
    application_source = request.GET.get('application_source')
    status = None
    ca_auth = None

    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    for work_details in workflow_details:
        status = work_details.application_status
        ca_auth = work_details.ca_authority
        assigned_role_id = work_details.assigned_role_id

        if service_id == '1':
            if application_source == 'IBLS':
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
                ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
                anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
                anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
                anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
                for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
                gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
                ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
                ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
                reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
                eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
                lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
                rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'ea_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials, 'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details,'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach, 'rev_lu_attach':rev_lu_attach})
            else:
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
                ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
                anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
                anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                file_attach = t_file_attachment.objects.filter(attachment_type='IEE')
                anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
                for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
                gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
                ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
                ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
                reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
                eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
                lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
                rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'iee_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                            'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '2':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='ENR')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'energy_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '3':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'road_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '4':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'transmission_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '5':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'tourism_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '6':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'ground_water_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '7':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count() 
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count() 
            return render(request, 'forest_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '8':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.filter(application_no=application_no).order_by('record_id')
            products_by_products = t_ec_industries_t9_products_by_products.filter(application_no=application_no).order_by('record_id')
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.filter(application_no=application_no).order_by('record_id')
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by('record_id')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='QUA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no,form_type='Main Activity')
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'quarry_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '9':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by('record_id')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            dumpyard_details = t_ec_industries_t13_dumpyard.objects.filter(application_no=application_no).order_by('record_id')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'application_details/general_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'dumpyard_details':dumpyard_details,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce, 'products_by_products': products_by_products,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '10':
            renewal_details_one = t_ec_renewal_t1.objects.filter(application_no=application_no)
            for renewal_details_one in renewal_details_one:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=renewal_details_one.ec_reference_no,form_type='Main Activity')
            renewal_details_two = t_ec_renewal_t2.objects.filter(application_no=application_no)
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ECR')
            reviewer_list = t_user_master.objects.filter(role_id='3')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'renewal_application_details.html',{'application_details':application_details,'renewal_details_one':renewal_details_one,'status':status,
                                                                       'dzongkhag':dzongkhag,'gewog':gewog,'village':village,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'renewal_details_two':renewal_details_two,'reviewer_list':reviewer_list,'file_attach':file_attach ,'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '0':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            thromde = t_thromde_master.objects.all()
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            file_attach = t_file_attachment.objects.filter(attachment_type='TOR')

            return render(request, 'tor_form_details.html', {'application_details':application_details,'file_attach':file_attach,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'reviewer_list':reviewer_list,'assigned_role_id':assigned_role_id, 'status':status})

#EC Renewal Notifications

def ec_renewal_list(request):
    ca_authority = request.session['ca_authority']
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    expiry_date_threshold = datetime.now().date() + timedelta(days=30)

    ec_list = t_ec_industries_t1_general.objects.filter(
        ca_authority=ca_authority,
        application_status='A',
        ec_expiry_date__lt=expiry_date_threshold
    ).values()
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'ec_renewal_list.html',
                  {'dzongkhag_list': dzongkhag_list,'ec_renewal_count':ec_renewal_count, 'ec_list': ec_list, 'ca_list': ca_list})


def send_notification(request):
    notice = request.POST.get('notice')
    ca_authority = request.session['ca_authority']
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)

    ec_list = t_ec_industries_t1_general.objects.filter(
        ca_authority=ca_authority,
        application_status='A',
        ec_expiry_date__lt=expiry_date_threshold
    ).values('ec_reference_no', 'applicant_id')

    for ec in ec_list:
        ec_reference_no = ec['ec_reference_no']
        email = [ec['applicant_id']]  # Convert the email string to a list or tuple

        subject = 'Environment Clearance Renewal Notification'
        message = "Dear Sir/Madam, \n\nYour Environmental Clearance No. " + ec_reference_no + " is due for renewal in less than 30 Days. DECC would like to request you to renew the Environmental Clearance before the expiry. \n\nThanking You"
        send_mail(subject, message, 'systems@moenr.gov.bt', email, fail_silently=False,
                  auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
                  connection=None, html_message=None)

        return redirect(ec_renewal_list)

