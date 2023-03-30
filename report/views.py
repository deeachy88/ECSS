from datetime import date, datetime, timedelta

from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils import formats

from proponent.models import t_ec_industries_t1_general, t_ec_industries_t2_partner_details, \
    t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, \
    t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, \
    t_ec_industries_t9_products_by_products, t_ec_industries_t10_hazardous_chemicals

from ecs_admin.models import t_competant_authority_master, t_service_master, t_dzongkhag_master, t_gewog_master, \
    t_village_master, t_bsic_code, t_country_master, t_fees_schedule

from ecs_main.models import t_inspection_monitoring_t1

def ec_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all().distinct('competent_authority')
    service_list = t_service_master.objects.filter(service_id__in=[1, 2, 3, 4, 5, 6, 7, 8, 9]).values()
    return render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list, 'ca_list': ca_list, 'service_list': service_list})

def view_ec_list(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    service_id = request.GET.get('service_id')
    ca_authority = request.GET.get('ca_authority')
    dzongkhag_code = request.GET.get('dzongkhag_code')
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()

    if ca_authority == 'ALL' and dzongkhag_code == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date]).values()
    elif ca_authority == 'ALL' and dzongkhag_code != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            dzongkhag_code=dzongkhag_code).values()
    elif ca_authority != 'ALL' and dzongkhag_code == 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority).values()
    elif ca_authority != 'ALL' and dzongkhag_code != 'ALL':
        ec_list = t_ec_industries_t1_general.objects.filter(ec_approve_date__range=[from_date, to_date],
                                                            ca_authority=ca_authority,
                                                            dzongkhag_code=dzongkhag_code).values()
    return render(request, 'ec_list.html',
                  {'dzongkhag_list': dzongkhag_list, 'ec_list': ec_list, 'ca_list': ca_list})

def ec_rejected_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.all()
    return render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list, 'ca_list': ca_list, 'service_list': service_list})
def ec_pending_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.all()
    return render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list, 'ca_list': ca_list, 'service_list': service_list})
def land_use_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.all()
    return render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list, 'ca_list': ca_list, 'service_list': service_list})
def revenue_report_form(request):
    dzongkhag_list = t_dzongkhag_master.objects.all()
    ca_list = t_competant_authority_master.objects.all()
    service_list = t_service_master.objects.all()
    return render(request, 'ec_report_form.html',
                  {'dzongkhag_list': dzongkhag_list, 'ca_list': ca_list, 'service_list': service_list})