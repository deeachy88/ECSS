from datetime import date, timedelta
from django.shortcuts import render, redirect
from ecs_main.models import t_application_history
from ecs_main.views import client_application_list, payment_list
from proponent.models import t_ec_industries_t11_ec_details, t_ec_industries_t12_drainage_details, t_ec_industries_t13_dumpyard, t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, t_ec_renewal_t1, t_ec_renewal_t2, t_payment_details, t_workflow_dtls, t_ec_industries_t9_products_by_products, t_ec_industries_t10_hazardous_chemicals, t_report_submission_t1, t_report_submission_t2
from ecs_admin.models import payment_details_master, t_user_master, t_bsic_code, t_competant_authority_master, t_fees_schedule, t_file_attachment, t_dzongkhag_master, t_gewog_master, t_service_master, t_thromde_master, t_village_master
# Create your views here.
from django.db.models import Count, Subquery, OuterRef
from datetime import datetime
from django.db.models import Max
from django.utils import timezone
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count
from django.utils.timezone import now
from django.db.models import OuterRef, Subquery, Q
from django.db.models.functions import Now
from django.shortcuts import render
from datetime import timedelta

def new_application(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    bsic_details = t_bsic_code.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'new_application.html',{'bsic_details':bsic_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def new_ea_application(request):
    service_code = 'IEA'
    application_no = get_application_no(request, service_code, '1')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'industry_ea_form.html',
                {'thromde':thromde,'partner_details': partner_details, 'machine_equipment': machine_equipment,
                'raw_materials': raw_materials,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,
                'project_product': project_product, 'ancillary_road': ancillary_road, 'power_line': power_line,
                'application_no': application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def new_road_application(request):
    service_code = 'ROA'
    application_no = get_application_no(request, service_code, '3')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    drainage_type = t_ec_industries_t12_drainage_details.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'road_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'drainage_type':drainage_type})

def new_transmission_application(request):
    service_code = 'TRA'
    application_no = get_application_no(request, service_code, '4')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'transmission_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})

def new_forestry_application(request):
    service_code = 'FOR'
    application_no = get_application_no(request, service_code, '7')
    request.session['application_no'] = application_no
    forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'forest_form.html',{'thromde':thromde,'forest_produce':forest_produce,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})

def new_general_application(request):
    service_code = 'GEN'
    application_no = get_application_no(request, service_code, '9')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'general_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})

def new_ground_water_application(request):
    service_code = 'GWA' 
    application_no = get_application_no(request, service_code, '6')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'ground_water_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})

def new_energy_application(request):
    service_code = 'ENE' 
    application_no = get_application_no(request, service_code, '2')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'energy_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})

def new_tourism_application(request):
    service_code = 'TOU' 
    application_no = get_application_no(request, service_code, '5')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'tourism_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})

def new_quarry_application(request):
    service_code = 'QUA' 
    application_no = get_application_no(request, service_code, '8')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'quarry_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})


def new_application_form(request):
    application_no = request.session['application_no']
    service_id = request.session['service_id']
    application_source = None
    status = None

    appl_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
    for appl_details in appl_details:
        application_source = appl_details.application_source

    if service_id == 1:
        if application_source == 'IBLS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.all()
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
            project_product = t_ec_industries_t4_project_product.objects.all()
            raw_materials = t_ec_industries_t5_raw_materials.objects.all()
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
            power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
            forest_produce = t_ec_industries_t8_forest_produce.objects.all()
            products_by_products = t_ec_industries_t9_products_by_products.objects.all()
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'pending_application/industry_ea_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials, 'status':status,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details,'ancillary_details':ancillary_details,'service_id':service_id})
        else:
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'pending_application/industry_iee_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                        'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 2:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/energy_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog,
                                                     'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 3:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/road_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 4:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/transmission_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 5:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/tourism_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 6:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/ground_water_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 7:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/forest_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 8:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/quarry_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == 9:
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce.objects.all()
        products_by_products = t_ec_industries_t9_products_by_products.objects.all()
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.all()
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'pending_application/general_form.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})

def industry_ancillary_form(request):
    application_no = request.session['application_no']
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    final_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'industry_ancillary_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'final_product':final_product,'ancillary_road':ancillary_road, 'power_line':power_line,
                                                     'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def ground_water_ancillary_form(request):
    application_no = request.session['application_no']
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    final_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'ground_water_ancillary_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'final_product':final_product,'ancillary_road':ancillary_road, 'power_line':power_line,
                                                     'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def forest_ancillary_form(request):
    application_no = request.session['application_no']
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    final_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'forest_ancillary_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'final_product':final_product,'ancillary_road':ancillary_road, 'power_line':power_line,
                                                     'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def general_ancillary_form(request):
    application_no = request.session['application_no']
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    final_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'general_ancillary_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'final_product':final_product,'ancillary_road':ancillary_road, 'power_line':power_line,
                                                     'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def transmission_ancillary_form(request):
    application_no = request.session['application_no']
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'transmission_ancillary_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                     'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})


def get_application_no(request, service_code, service_id):
    if service_code == "TOR":
        application_no= t_ec_industries_t1_general.objects.filter(application_no__contains='TOR').aggregate(Max('application_no'))
    else:
        application_no= t_ec_industries_t1_general.objects.exclude(service_id=service_id, application_no__contains='TOR').filter(application_no__contains=service_code).aggregate(Max('application_no'))
    last_application_no= application_no['application_no__max']
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


def add_machine_tool_details(request):
    application_no = request.POST.get('application_no')
    machine_tool = request.POST.get('machine_tool')
    machine_tool_qty = request.POST.get('machine_tool_qty')
    machine_tool_installed_capacity = request.POST.get('machine_tool_installed_capacity')

    t_ec_industries_t3_machine_equipment.objects.create(application_no=application_no,machine_name=machine_tool,
                                                        qty=machine_tool_qty,installed_capacity=machine_tool_installed_capacity)
    machine_equipment=t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no).order_by('record_id')
    return render(request, 'details_machine_equipment_tool.html',{'machine_equipment':machine_equipment})

def add_project_product(request):
    application_no = request.POST.get('application_no')
    product_name = request.POST.get('product_name')
    name_location_type = request.POST.get('name_location_type')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t4_project_product.objects.create(application_no= application_no, product_name= product_name,
                                                        name_location_type= name_location_type,storage_method= storage_method)
    project_product = t_ec_industries_t4_project_product.objects.filter(application_no= application_no).order_by(
        'record_id')
    return render(request, 'final_products.html', {'project_product': project_product})

def add_raw_materials(request):
    application_no = request.POST.get('application_no')
    raw_material = request.POST.get('raw_material')
    qty = request.POST.get('qty')
    source = request.POST.get('source')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t5_raw_materials.objects.create(application_no= application_no,raw_material=raw_material,
                                                        qty= qty,source=source,storage_method=storage_method)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'raw_materials.html', {'raw_materials': raw_materials})

def update_raw_materials(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    raw_material = request.POST.get('raw_material')
    qty = request.POST.get('qty')
    source = request.POST.get('source')
    storage_method = request.POST.get('storage_method')

    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(record_id=record_id)
    raw_materials.update(raw_material=raw_material,qty=qty,
                         source=source, storage_method= storage_method)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'raw_materials.html', {'raw_materials': raw_materials})

def delete_raw_materials(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    raw_materials_details = t_ec_industries_t5_raw_materials.objects.filter(record_id=record_id)
    raw_materials_details.delete()
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'raw_materials.html', {'raw_materials': raw_materials})

def update_machine_tool_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    machine_tool = request.POST.get('machine_tool')
    machine_tool_qty = request.POST.get('machine_tool_qty')
    machine_tool_installed_capacity = request.POST.get('machine_tool_installed_capacity')

    machine_equipment_details = t_ec_industries_t3_machine_equipment.objects.filter(record_id=record_id)
    machine_equipment_details.update(machine_name=machine_tool,qty=machine_tool_qty,installed_capacity=machine_tool_installed_capacity)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no= application_no).order_by('record_id')
    return render(request, 'details_machine_equipment_tool.html',{'machine_equipment':machine_equipment})

def delete_machine_tool_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    machine_equipment_details = t_ec_industries_t3_machine_equipment.objects.filter(record_id=record_id)
    machine_equipment_details.delete()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'details_machine_equipment_tool.html', {'machine_equipment': machine_equipment})

def add_partner_details(request):
    application_no = request.POST.get('application_no')
    partner_type = request.POST.get('partner_type')
    partner_cid = request.POST.get('partner_cid')
    partner_name = request.POST.get('partner_name')
    partner_address = request.POST.get('partner_address')

    t_ec_industries_t2_partner_details.objects.create(application_no=application_no,partner_type=partner_type,
                                                    partner_cid=partner_cid, partner_name=partner_name, partner_address=partner_address)
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no= application_no).order_by(
        'record_id')
    return render(request, 'partner_details.html',{'partner_details':partner_details})

def update_partner_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    partner_type = request.POST.get('partner_type')
    partner_cid = request.POST.get('partner_cid')
    partner_name = request.POST.get('partner_name')
    partner_address = request.POST.get('partner_address')

    partner_details = t_ec_industries_t2_partner_details.objects.filter(record_id=record_id)
    partner_details.update(partner_type=partner_type, partner_cid=partner_cid, partner_name=partner_name, partner_address=partner_address)
    partner_type_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'partner_details.html',{'partner_details':partner_type_details})


def delete_partner_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    partner_type_details = t_ec_industries_t2_partner_details.objects.filter(record_id=record_id)
    partner_type_details.delete()
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'partner_details.html', {'partner_details': partner_details})


def save_iee_application(request):
    data = {'message': 'failure'}
    
    try:
        application_no = request.POST.get('application_no')
        identifier = request.POST.get('identifier')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        tor_application_no = request.POST.get('tor_application_no')
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
            'application_type': 'New',
            'service_type': request.POST.get('service_type'),
            'applicant_id': request.session['email'],
            'applicant_name': request.POST.get('applicant_name'),
            'address': request.POST.get('address'),
            'cid':request.POST.get('cid'),
            'contact_no':request.POST.get('contact_no'),
            'email':request.POST.get('email'),
            'focal_person':request.POST.get('focal_person'),
            'industry_type':request.POST.get('industry_type'),
            'establishment_type': request.POST.get('establishment_type'),
            'industry_classification':request.POST.get('industry_classification'),
            'dzongkhag_code':dzongkhag_code,
            'gewog_code':gewog_code,
            'village_code':village_code,
            'thromde_id':thromde_id,
            'location_name':request.POST.get('location_name'),
            'industrial_area_acre':request.POST.get('industrial_area_acre'),
            'state_reserve_forest_acre':request.POST.get('state_reserve_forest_acre'),
            'private_area_acre':request.POST.get('private_area_acre'),
            'others_area_acre':request.POST.get('others_area_acre'),
            'total_area_acre':request.POST.get('total_area_acre'),
            'green_area_acre':request.POST.get('green_area_acre'),
            'production_process_flow':request.POST.get('production_process_flow'),
            'project_objective':request.POST.get('project_objective'),
            'project_no_of_workers':request.POST.get('project_no_of_workers'),
            'project_cost':request.POST.get('project_cost'),
            'project_duration':request.POST.get('project_duration'),
            'ec_reference_no':request.POST.get('ec_reference_no'),
            'service_type':request.POST.get('service_type'),
            'tor_application_no':request.POST.get('tor_application_no'),
            'application_status':'P',
            'project_name':request.POST.get('project_name'),
            'project_category':request.POST.get('project_category'),
            'dzongkhag_throm':dzongkhag_throm,
            'location_name':request.POST.get('project_site')
        }
        
        with transaction.atomic():
            ca_auth = None
            if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
                auth_filter = t_competant_authority_master.objects.filter(
                    competent_authority=request.session['ca_auth'],
                    dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
                )
                ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
            elif identifier == 'NC' or identifier == 'OC':
                auth_filter = t_ec_industries_t1_general.objects.filter(
                    application_no=application_no
                )
                ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
            else:
                auth_filter = t_ec_industries_t1_general.objects.filter(
                    application_no=tor_application_no
                )
                ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
            
            if identifier == 'NC':
                t_ec_industries_t1_general.objects.filter(application_no=application_no).update(
                    project_name=request.POST.get('project_name'),service_type=identifier
                )
            elif identifier == 'OC':
                t_ec_industries_t1_general.objects.filter(application_no=application_no).update(
                    applicant_name=request.POST.get('applicant_name'),service_type=identifier
                )
            elif identifier == 'DR':
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
                if application_details.exists():
                    application_details.update(**common_data)
                else:
                    new_data = {
                        'ca_authority': ca_auth,
                        'service_id': request.session['service_id'],
                        'application_source': 'ECSS',
                        'broad_activity_code': request.session['broad_activity_code'],
                        'specific_activity_code': request.session['specific_activity_code'],
                        'category': request.session['category'],
                        'colour_code': request.session['colour_code'],
                    }
                    t_ec_industries_t1_general.objects.create(**common_data, **new_data)
                # Break out of the loop since the processing is done
            elif identifier in ['TC', 'PC', 'LC', 'CC']:
                for app_det in t_ec_industries_t1_general.objects.filter(application_no=application_no):
                    t_ec_industries_t1_general.objects.create(**common_data, service_id=app_det.service_id, application_source='ECSS')
                # Break out of the loop since the processing is done
            else:
                new_data = {
                    'ca_authority': ca_auth,
                    'service_id': request.session['service_id'],
                    'application_source': 'ECSS',
                    'broad_activity_code': request.session['broad_activity_code'],
                    'specific_activity_code': request.session['specific_activity_code'],
                    'category': request.session['category'],
                    'colour_code': request.session['colour_code'],
                }
                t_ec_industries_t1_general.objects.create(**common_data, **new_data)
                # Break out of the loop since the processing is done
            
            t_application_history.objects.create(
                application_no=application_no,
                application_date=timezone.now().date(),
                applicant_id=request.session['email'],
                ca_authority=ca_auth,
                service_id=request.session['service_id'],
                application_status='P',
                action_date=None,
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                remarks=None,
                status=None
            )
            if identifier == 'NC' or identifier == 'OC':
                work_details = t_workflow_dtls.objects.filter(application_no=application_no)
                work_details.update(application_status='P',
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    assigned_role_id='2',
                    assigned_role_name='Verifier')
            else:
                t_workflow_dtls.objects.create(
                    application_no=application_no,
                    service_id=request.session['service_id'],
                    application_status='P',
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    assigned_role_id='2',
                    assigned_role_name='Verifier',
                    ca_authority=ca_auth,
                    application_source='ECSS'
                )
            data['message'] = 'success'
    except Exception as e:
        print('An error occurred:', e)
    
    return JsonResponse(data)


def save_terrain_baseline_details(request):
    data = dict()
    try:
        application_no = request.POST.get('terrain_baseline_application_no')
        proposed_location_justification = request.POST.get('proposed_location_justification')
        terrain_elevation = request.POST.get('terrain_elevation')
        terrain_slope = request.POST.get('terrain_slope')
        bl_protected_area_name = request.POST.get('bl_protected_area_name')
        bl_protected_area_distance = request.POST.get('bl_protected_area_distance')
        bl_migratory_route_name = request.POST.get('bl_migratory_route_name')
        bl_migratory_route_distance = request.POST.get('bl_migratory_route_distance')
        bl_wetland_name = request.POST.get('bl_wetland_name')
        bl_wetland_distance = request.POST.get('bl_wetland_distance')
        bl_water_bodies_name = request.POST.get('bl_water_bodies_name')
        bl_water_bodies_distance = request.POST.get('bl_water_bodies_distance')
        bl_fmu_name = request.POST.get('bl_fmu_name')
        bl_fmu_distance = request.POST.get('bl_fmu_distance')
        bl_agricultural_name = request.POST.get('bl_agricultural_name')
        bl_agricultural_distance = request.POST.get('bl_agricultural_distance')
        bl_settlement_name = request.POST.get('bl_settlement_name')
        bl_settlement_distance = request.POST.get('bl_settlement_distance')
        bl_road_name = request.POST.get('bl_road_name')
        bl_road_distance = request.POST.get('bl_road_distance')
        bl_public_infra_name = request.POST.get('bl_public_infra_name')
        bl_public_infra_distance = request.POST.get('bl_public_infra_distance')
        bl_school_name = request.POST.get('bl_school_name')
        bl_school_distance = request.POST.get('bl_school_distance')
        bl_heritage_name = request.POST.get('bl_heritage_name')
        bl_heritage_distance = request.POST.get('bl_heritage_distance')
        bl_tourist_facility_name = request.POST.get('bl_tourist_facility_name')
        bl_tourist_facility_distance = request.POST.get('bl_tourist_facility_distance')
        bl_impt_installation_name = request.POST.get('bl_impt_installation_name')
        bl_impt_installation_distance = request.POST.get('bl_impt_installation_distance')
        bl_industries_name = request.POST.get('bl_industries_name')
        bl_industries_distance = request.POST.get('bl_industries_distance')
        bl_others = request.POST.get('bl_others')
        bl_others_name = request.POST.get('bl_others_name')
        bl_others_distance = request.POST.get('bl_others_distance')
        technology_used = request.POST.get('technology_used')
        technology_total_capacity = request.POST.get('technology_total_capacity')
        energy_source = request.POST.get('energy_source')
        energy_source_justification = request.POST.get('energy_source_justification')

        baseline_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        baseline_details.update(proposed_location_justification=proposed_location_justification,
                                terrain_elevation=terrain_elevation,
                                terrain_slope=terrain_slope,
                                bl_protected_area_name=bl_protected_area_name,
                                bl_protected_area_distance=bl_protected_area_distance,
                                bl_migratory_route_name=bl_migratory_route_name,
                                bl_migratory_route_distance=bl_migratory_route_distance,
                                bl_wetland_name=bl_wetland_name,
                                bl_wetland_distance=bl_wetland_distance,
                                bl_water_bodies_name=bl_water_bodies_name,
                                bl_water_bodies_distance=bl_water_bodies_distance,
                                bl_fmu_name=bl_fmu_name,
                                bl_fmu_distance=bl_fmu_distance,
                                bl_agricultural_name=bl_agricultural_name,
                                bl_agricultural_distance=bl_agricultural_distance,
                                bl_settlement_name=bl_settlement_name,
                                bl_settlement_distance=bl_settlement_distance,
                                bl_road_name=bl_road_name,
                                bl_road_distance=bl_road_distance,
                                bl_public_infra_name=bl_public_infra_name,
                                bl_public_infra_distance=bl_public_infra_distance,
                                bl_school_name=bl_school_name,
                                bl_school_distance=bl_school_distance,
                                bl_heritage_name=bl_heritage_name,
                                bl_heritage_distance=bl_heritage_distance,
                                bl_tourist_facility_name=bl_tourist_facility_name,
                                bl_tourist_facility_distance=bl_tourist_facility_distance,
                                bl_impt_installation_name=bl_impt_installation_name,
                                bl_impt_installation_distance=bl_impt_installation_distance,
                                bl_industries_name=bl_industries_name,
                                bl_industries_distance=bl_industries_distance,
                                bl_others=bl_others,
                                bl_others_name=bl_others_name,
                                bl_others_distance=bl_others_distance,
                                technology_used=technology_used,
                                technology_total_capacity=technology_total_capacity,
                                energy_source=energy_source,
                                energy_source_justification=energy_source_justification
                                )
        data['message'] = "success"
        return JsonResponse(data)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
        return JsonResponse(data)

def save_water_requirement_details(request):
    data = dict()
    try:
        application_no = request.POST.get('water_requirement_application_no')
        water_required = request.POST.get('water_required')
        water_provided_by = request.POST.get('water_provided_by')
        water_raw_material_source = request.POST.get('water_raw_material_source')
        water_raw_material_qty_day = request.POST.get('#water_raw_material_qty_day')
        water_raw_material_recycle_day = request.POST.get('#water_raw_material_recycle_day')
        water_cleaning_source = request.POST.get('#water_cleaning_source')
        water_cleaning_qty_day = request.POST.get('#water_cleaning_qty_day')
        water_cleaning_recycle_day = request.POST.get('#water_cleaning_recycle_day')
        water_process_source = request.POST.get('#water_process_source')
        water_process_qty_day = request.POST.get('#water_process_qty_day')
        water_process_recycle_day = request.POST.get('#water_process_recycle_day')
        water_domestic_source = request.POST.get('#water_domestic_source')
        water_domestic_qty_day = request.POST.get('#water_domestic_qty_day')
        water_domestic_recycle_day = request.POST.get('#water_domestic_recycle_day')
        water_dust_compression_source = request.POST.get('#water_dust_compression_source')
        water_dust_compression_qty_day = request.POST.get('#water_dust_compression_qty_day')
        water_dust_compression_recycle_day = request.POST.get('#water_dust_compression_recycle_day')
        water_others_name = request.POST.get('#water_others_name')
        water_others_source = request.POST.get('#water_others_source')
        water_others_qty_day = request.POST.get('#water_others_qty_day')
        total_water_consumption = request.POST.get('#total_water_consumption')
        total_water_recycled = request.POST.get('#total_water_recycled')
        water_downstream_users = request.POST.get('#water_downstream_users')
        water_flow_rate_lean = request.POST.get('#water_flow_rate_lean')
        water_source_distance = request.POST.get('#water_source_distance')

        water_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        water_details.update(water_required=water_required,
                             water_provide_by_iestate=water_provided_by,
                             water_raw_material_source=water_raw_material_source,
                             water_raw_material_qty_day=water_raw_material_qty_day,
                             water_raw_material_recycle_day=water_raw_material_recycle_day,
                             water_cleaning_source=water_cleaning_source,
                             water_cleaning_qty_day=water_cleaning_qty_day,
                             water_cleaning_recycle_day=water_cleaning_recycle_day,
                             water_process_source=water_process_source,
                             water_process_qty_day=water_process_qty_day,
                             water_process_recycle_day=water_process_recycle_day,
                             water_domestic_source=water_domestic_source,
                             water_domestic_qty_day=water_domestic_qty_day,
                             water_domestic_recycle_day=water_domestic_recycle_day,
                             water_dust_compression_source=water_dust_compression_source,
                             water_dust_compression_qty_day=water_dust_compression_qty_day,
                             water_dust_compression_recycle_day=water_dust_compression_recycle_day,
                             water_others_name=water_others_name,
                             water_others_source=water_others_source,
                             water_others_qty_day=water_others_qty_day,
                             total_water_consumption=total_water_consumption,
                             total_water_recycled=total_water_recycled,
                             water_downstream_users=water_downstream_users,
                             water_flow_rate_lean=water_flow_rate_lean,
                             water_source_distance=water_source_distance
                             )
        data['message'] = "success"
        return JsonResponse(data)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_anc_approach_road_details(request):
    data = dict()
    try:
        application_no = request.POST.get('approach_road_application_no')
        anc_road_required = request.POST.get('anc_road_required')
        anc_road_blast_required = request.POST.get('anc_road_blast_required')
        if anc_road_required == 'Yes':
            anc_road_length = request.POST.get('anc_road_length')
            anc_road_start_point = request.POST.get('anc_road_start_point')
            anc_road_end_point = request.POST.get('anc_road_end_point')
            anc_road_blast_type = request.POST.get('anc_road_blast_type')
            anc_road_blast_qty = request.POST.get('anc_road_blast_qty')
            anc_road_blast_location = request.POST.get('anc_road_blast_location')
            anc_road_blast_frequency_time = request.POST.get('anc_road_blast_frequency_time')

            approach_road_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            approach_road_details.update(anc_road_required=anc_road_required,
                                        anc_road_length=anc_road_length,
                                        anc_road_start_point=anc_road_start_point,
                                        anc_road_end_point=anc_road_end_point,
                                        anc_road_blast_required=anc_road_blast_required,
                                        anc_road_blast_type=anc_road_blast_type,
                                        anc_road_blast_qty=anc_road_blast_qty,
                                        anc_road_blast_location=anc_road_blast_location,
                                        anc_road_blast_frequency_time=anc_road_blast_frequency_time
                                        )
        else:
            approach_road_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            approach_road_details.update(anc_road_required=anc_road_required,anc_road_blast_required=anc_road_blast_required)
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_anc_power_line_form(request):
    data = dict()
    try:
        application_no = request.POST.get('power_line_application_no')
        anc_power_line_required = request.POST.get('anc_power_line_required')
        if anc_power_line_required == 'Yes':
            anc_power_line_voltage = request.POST.get('anc_power_line_voltage')
            anc_power_line_length = request.POST.get('anc_power_line_length')
            anc_power_line_start_point = request.POST.get('anc_power_line_start_point')
            anc_power_line_end_point = request.POST.get('anc_power_line_end_point')
            anc_power_line_storing_method = request.POST.get('anc_power_line_storing_method')

            power_line_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            power_line_details.update(anc_power_line_required=anc_power_line_required,
                                    anc_power_line_voltage=anc_power_line_voltage,
                                    anc_power_line_length=anc_power_line_length,
                                    anc_power_line_start_point=anc_power_line_start_point,
                                    anc_power_line_end_point=anc_power_line_end_point,
                                    anc_power_line_storing_method=anc_power_line_storing_method
                                    )
        else:
            power_line_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            power_line_details.update(anc_power_line_required=anc_power_line_required)
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_anc_other_details(request):
    data = dict()
    try:
        application_no = request.POST.get('others_application_no')
        anc_other_crushing_unit = request.POST.get('anc_other_crushing_unit')
        anc_other_surface_collection = request.POST.get('anc_other_surface_collection')
        anc_other_ground_water = request.POST.get('anc_other_ground_water')
        anc_other_mineral = request.POST.get('anc_other_mineral')
        anc_other_general = request.POST.get('anc_other_general')
        anc_other_housing_colony = request.POST.get('anc_other_housing_colony')
        anc_power_excavation = request.POST.get('anc_power_excavation')
        anc_other_bridge = request.POST.get('anc_other_bridge')
        anc_other_concrete_building = request.POST.get('anc_other_concrete_building')
        anc_other_asphalt_plant = request.POST.get('anc_other_asphalt_plant')
        anc_other_ropeway = request.POST.get('anc_other_ropeway')

        anc_other_crushing_unit = anc_other_crushing_unit if anc_other_crushing_unit else None
        anc_other_surface_collection = anc_other_surface_collection if anc_other_surface_collection else None
        anc_other_ground_water = anc_other_ground_water if anc_other_ground_water else None
        anc_other_mineral = anc_other_mineral if anc_other_mineral else None
        anc_other_general = anc_other_general if anc_other_general else None
        anc_other_housing_colony = anc_other_housing_colony if anc_other_housing_colony else None
        anc_power_excavation = anc_power_excavation if anc_power_excavation else None
        anc_other_bridge = anc_other_bridge if anc_other_bridge else None
        anc_other_concrete_building = anc_other_concrete_building if anc_other_concrete_building else None
        anc_other_asphalt_plant = anc_other_asphalt_plant if anc_other_asphalt_plant else None
        anc_other_ropeway = anc_other_ropeway if anc_other_ropeway else None

        anc_other_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        anc_other_details.update(anc_other_crushing_unit=anc_other_crushing_unit,
                                    anc_other_surface_collection=anc_other_surface_collection,
                                    anc_other_ground_water=anc_other_ground_water,
                                    anc_other_mineral=anc_other_mineral,
                                    anc_other_general=anc_other_general,
                                    anc_other_housing_colony=anc_other_housing_colony,
                                    anc_power_excavation=anc_power_excavation,
                                    anc_other_bridge=anc_other_bridge,
                                    anc_other_concrete_building=anc_other_concrete_building,
                                    anc_other_asphalt_plant=anc_other_asphalt_plant,
                                    anc_other_ropeway=anc_other_ropeway
                                  )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_solid_waste_details(request):
    data = dict()
    try:
        application_no = request.POST.get('solid_waste_application_no')
        en_impact_allocated_budget = request.POST.get('en_impact_allocated_budget')
        en_impact_hazardous_waste_list = request.POST.get('en_impact_hazardous_waste_list')
        en_impact_hazardous_waste_source = request.POST.get('en_impact_hazardous_waste_source')
        en_impact_hazardous_waste_qty_annum = request.POST.get('en_impact_hazardous_waste_qty_annum')
        en_impact_hazardous_waste_mgt_plan = request.POST.get('en_impact_hazardous_waste_mgt_plan')
        en_impact_non_hazardous_waste_list = request.POST.get('en_impact_non_hazardous_waste_list')
        en_impact_non_hazardous_waste_source = request.POST.get('en_impact_non_hazardous_waste_source')
        en_impact_non_hazardous_waste_qty_annum = request.POST.get('en_impact_non_hazardous_waste_qty_annum')
        en_impact_non_hazardous_waste_mgt_plan = request.POST.get('en_impact_non_hazardous_waste_mgt_plan')
        en_impact_medical_waste_list = request.POST.get('en_impact_medical_waste_list')
        en_impact_medical_waste_source = request.POST.get('en_impact_medical_waste_source')
        en_impact_medical_waste_qty_annum = request.POST.get('en_impact_medical_waste_qty_annum')
        en_impact_medical_waste_mgt_plan = request.POST.get('en_impact_medical_waste_mgt_plan')
        en_impact_ewaste_list = request.POST.get('en_impact_ewaste_list')
        en_impact_ewaste_source = request.POST.get('en_impact_ewaste_source')
        en_impact_ewaste_qty_annum = request.POST.get('en_impact_ewaste_qty_annum')
        en_impact_ewaste_mgt_plan = request.POST.get('en_impact_ewaste_mgt_plan')
        en_impact_others_waste_list = request.POST.get('en_impact_others_waste_list')
        en_impact_others_waste_source = request.POST.get('en_impact_others_waste_source')
        en_impact_others_waste_qty_annum = request.POST.get('en_impact_others_waste_qty_annum')
        en_impact_others_waste_mgt_plan = request.POST.get('en_impact_others_waste_mgt_plan')

        anc_other_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        anc_other_details.update(en_impact_allocated_budget=en_impact_allocated_budget,
                                 en_impact_hazardous_waste_list=en_impact_hazardous_waste_list,
                                 en_impact_hazardous_waste_source=en_impact_hazardous_waste_source,
                                 en_impact_hazardous_waste_qty_annum=en_impact_hazardous_waste_qty_annum,
                                 en_impact_hazardous_waste_mgt_plan=en_impact_hazardous_waste_mgt_plan,
                                 en_impact_non_hazardous_waste_list=en_impact_non_hazardous_waste_list,
                                 en_impact_non_hazardous_waste_source=en_impact_non_hazardous_waste_source,
                                 en_impact_non_hazardous_waste_qty_annum=en_impact_non_hazardous_waste_qty_annum,
                                 en_impact_non_hazardous_waste_mgt_plan=en_impact_non_hazardous_waste_mgt_plan,
                                 en_impact_medical_waste_list=en_impact_medical_waste_list,
                                 en_impact_medical_waste_source=en_impact_medical_waste_source,
                                 en_impact_medical_waste_qty_annum=en_impact_medical_waste_qty_annum,
                                 en_impact_medical_waste_mgt_plan=en_impact_medical_waste_mgt_plan,
                                 en_impact_ewaste_list=en_impact_ewaste_list,
                                 en_impact_ewaste_source=en_impact_ewaste_source,
                                 en_impact_ewaste_qty_annum=en_impact_ewaste_qty_annum,
                                 en_impact_ewaste_mgt_plan=en_impact_ewaste_mgt_plan,
                                 en_impact_others_waste_list=en_impact_others_waste_list,
                                 en_impact_others_waste_source=en_impact_others_waste_source,
                                 en_impact_others_waste_qty_annum=en_impact_others_waste_qty_annum,
                                 en_impact_others_waste_mgt_plan=en_impact_others_waste_mgt_plan
                                 )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_effluent_details(request):
    data = dict()
    try:
        application_no = request.POST.get('effluent_application_no')
        en_waste_water_generate = request.POST.get('en_waste_water_generate')
        waste_water_nh3n_source = request.POST.get('waste_water_nh3n_source')
        waste_water_nh3n_discharge = request.POST.get('waste_water_nh3n_discharge')
        waste_water_nh3n_treatment = request.POST.get('waste_water_nh3n_treatment')
        waste_water_nh3n_name_location = request.POST.get('waste_water_nh3n_name_location')
        waste_water_arsenic_source = request.POST.get('waste_water_arsenic_source')
        waste_water_arsenic_discharge = request.POST.get('waste_water_arsenic_discharge')
        waste_water_arsenic_treatment = request.POST.get('waste_water_arsenic_treatment')
        waste_water_arsenic_name_location = request.POST.get('waste_water_arsenic_name_location')
        waste_water_bod_source = request.POST.get('waste_water_bod_source')
        waste_water_bod_discharge = request.POST.get('waste_water_bod_discharge')
        waste_water_bod_treatment = request.POST.get('waste_water_bod_treatment')
        waste_water_bod_name_location = request.POST.get('waste_water_bod_name_location')
        waste_water_boron_source = request.POST.get('waste_water_boron_source')
        waste_water_boron_discharge = request.POST.get('waste_water_boron_discharge')
        waste_water_boron_treatment = request.POST.get('waste_water_boron_treatment')
        waste_water_boron_name_location = request.POST.get('waste_water_boron_name_location')
        waste_water_cadmium_source = request.POST.get('waste_water_cadmium_source')
        waste_water_cadmium_discharge = request.POST.get('waste_water_cadmium_discharge')
        waste_water_cadmium_treatment = request.POST.get('waste_water_cadmium_treatment')
        waste_water_cadmium_name_location = request.POST.get('waste_water_cadmium_name_location')
        waste_water_cod_source = request.POST.get('waste_water_cod_source')
        waste_water_cod_discharge = request.POST.get('waste_water_cod_discharge')
        waste_water_cod_treatment = request.POST.get('waste_water_cod_treatment')
        waste_water_cod_name_location = request.POST.get('waste_water_cod_name_location')
        waste_water_cloride_source = request.POST.get('waste_water_cloride_source')
        waste_water_cloride_discharge = request.POST.get('waste_water_cloride_discharge')
        waste_water_cloride_treatment = request.POST.get('waste_water_cloride_treatment')
        waste_water_cloride_name_location = request.POST.get('waste_water_cloride_name_location')
        waste_water_chromium_source = request.POST.get('waste_water_chromium_source')
        waste_water_chromium_discharge = request.POST.get('waste_water_chromium_discharge')
        waste_water_chromium_treatment = request.POST.get('waste_water_chromium_treatment')
        waste_water_chromium_name_location = request.POST.get('waste_water_chromium_name_location')
        waste_water_chromium_hex_source = request.POST.get('waste_water_chromium_hex_source')
        waste_water_chromium_hex_discharge = request.POST.get('waste_water_chromium_hex_discharge')
        waste_water_chromium_hex_treatment = request.POST.get('waste_water_chromium_hex_treatment')
        waste_water_chromium_hex_name_location = request.POST.get('waste_water_chromium_hex_name_location')
        waste_water_copper_source = request.POST.get('waste_water_copper_source')
        waste_water_copper_discharge = request.POST.get('waste_water_copper_discharge')
        waste_water_copper_treatment = request.POST.get('waste_water_copper_treatment')
        waste_water_copper_name_location = request.POST.get('waste_water_copper_name_location')
        waste_water_cyanide_source = request.POST.get('waste_water_cyanide_source')
        waste_water_cyanide_discharge = request.POST.get('waste_water_cyanide_discharge')
        waste_water_cyanide_treatment = request.POST.get('waste_water_cyanide_treatment')
        waste_water_cyanide_name_location = request.POST.get('waste_water_cyanide_name_location')
        waste_water_floride_source = request.POST.get('waste_water_floride_source')
        waste_water_floride_discharge = request.POST.get('waste_water_floride_discharge')
        waste_water_floride_treatment = request.POST.get('waste_water_floride_treatment')
        waste_water_floride_name_location = request.POST.get('waste_water_floride_name_location')
        waste_water_phosphate_source = request.POST.get('waste_water_phosphate_source')
        waste_water_phosphate_discharge = request.POST.get('waste_water_phosphate_discharge')
        waste_water_phosphate_treatment = request.POST.get('waste_water_phosphate_treatment')
        waste_water_phosphate_name_location = request.POST.get('waste_water_phosphate_name_location')
        waste_water_nitrate_source = request.POST.get('waste_water_nitrate_source')
        waste_water_nitrate_discharge = request.POST.get('waste_water_nitrate_discharge')
        waste_water_nitrate_treatment = request.POST.get('waste_water_nitrate_treatment')
        waste_water_nitrate_name_location = request.POST.get('waste_water_nitrate_name_location')
        waste_water_iron_source = request.POST.get('waste_water_iron_source')
        waste_water_iron_discharge = request.POST.get('waste_water_iron_discharge')
        waste_water_iron_treatment = request.POST.get('waste_water_iron_treatment')
        waste_water_iron_name_location = request.POST.get('waste_water_iron_name_location')
        waste_water_lead_source = request.POST.get('waste_water_lead_source')
        waste_water_lead_discharge = request.POST.get('waste_water_lead_discharge')
        waste_water_lead_treatment = request.POST.get('waste_water_lead_treatment')
        waste_water_lead_name_location = request.POST.get('waste_water_lead_name_location')
        waste_water_manganese_source = request.POST.get('waste_water_manganese_source')
        waste_water_manganese_discharge = request.POST.get('waste_water_manganese_discharge')
        waste_water_manganese_treatment = request.POST.get('waste_water_manganese_treatment')
        waste_water_manganese_name_location = request.POST.get('waste_water_manganese_name_location')
        waste_water_mercury_source = request.POST.get('waste_water_mercury_source')
        waste_water_mercury_discharge = request.POST.get('waste_water_mercury_discharge')
        waste_water_mercury_treatment = request.POST.get('waste_water_mercury_treatment')
        waste_water_mercury_name_location = request.POST.get('waste_water_mercury_name_location')
        waste_water_nickel_source = request.POST.get('waste_water_nickel_source')
        waste_water_nickel_discharge = request.POST.get('waste_water_nickel_discharge')
        waste_water_nickel_treatment = request.POST.get('waste_water_nickel_treatment')
        waste_water_nickel_name_location = request.POST.get('waste_water_nickel_name_location')
        waste_water_oil_source = request.POST.get('waste_water_oil_source')
        waste_water_oil_discharge = request.POST.get('waste_water_oil_discharge')
        waste_water_oil_treatment = request.POST.get('waste_water_oil_treatment')
        waste_water_oil_name_location = request.POST.get('waste_water_oil_name_location')
        waste_water_ph_source = request.POST.get('waste_water_ph_source')
        waste_water_ph_discharge = request.POST.get('waste_water_ph_discharge')
        waste_water_ph_treatment = request.POST.get('waste_water_ph_treatment')
        waste_water_ph_name_location = request.POST.get('waste_water_ph_name_location')
        waste_water_phenolic_source = request.POST.get('waste_water_phenolic_source')
        waste_water_phenolic_discharge = request.POST.get('waste_water_phenolic_discharge')
        waste_water_phenolic_treatment = request.POST.get('waste_water_phenolic_treatment')
        waste_water_phenolic_name_location = request.POST.get('waste_water_phenolic_name_location')
        waste_water_selenium_source = request.POST.get('waste_water_selenium_source')
        waste_water_selenium_discharge = request.POST.get('waste_water_selenium_discharge')
        waste_water_selenium_treatment = request.POST.get('waste_water_selenium_treatment')
        waste_water_selenium_name_location = request.POST.get('waste_water_selenium_name_location')
        waste_water_so4_source = request.POST.get('waste_water_so4_source')
        waste_water_so4_discharge = request.POST.get('waste_water_so4_discharge')
        waste_water_so4_treatment = request.POST.get('waste_water_so4_treatment')
        waste_water_so4_name_location = request.POST.get('waste_water_so4_name_location')
        waste_water_s_source = request.POST.get('waste_water_s_source')
        waste_water_s_discharge = request.POST.get('waste_water_s_discharge')
        waste_water_s_treatment = request.POST.get('waste_water_s_treatment')
        waste_water_s_name_location = request.POST.get('waste_water_s_name_location')
        waste_water_tds_source = request.POST.get('waste_water_tds_source')
        waste_water_tds_discharge = request.POST.get('waste_water_tds_discharge')
        waste_water_tds_treatment = request.POST.get('waste_water_tds_treatment')
        waste_water_tds_name_location = request.POST.get('waste_water_tds_name_location')
        waste_water_tss_source = request.POST.get('waste_water_tss_source')
        waste_water_tss_discharge = request.POST.get('waste_water_tss_discharge')
        waste_water_tss_treatment = request.POST.get('waste_water_tss_treatment')
        waste_water_tss_name_location = request.POST.get('waste_water_tss_name_location')
        waste_water_temp_source = request.POST.get('waste_water_temp_source')
        waste_water_temp_discharge = request.POST.get('waste_water_temp_discharge')
        waste_water_temp_treatment = request.POST.get('waste_water_temp_treatment')
        waste_water_temp_name_location = request.POST.get('waste_water_temp_name_location')
        waste_water_tkn_source = request.POST.get('waste_water_tkn_source')
        waste_water_tkn_discharge = request.POST.get('waste_water_tkn_discharge')
        waste_water_tkn_treatment = request.POST.get('waste_water_tkn_treatment')
        waste_water_tkn_name_location = request.POST.get('waste_water_tkn_name_location')
        waste_water_residual_cloride_source = request.POST.get('waste_water_residual_cloride_source')
        waste_water_residual_cloride_discharge = request.POST.get('waste_water_residual_cloride_discharge')
        waste_water_residual_cloride_treatment = request.POST.get('waste_water_residual_cloride_treatment')
        waste_water_residual_cloride_name_location = request.POST.get('waste_water_residual_cloride_name_location')
        waste_water_zinc_source = request.POST.get('waste_water_zinc_source')
        waste_water_zinc_discharge = request.POST.get('waste_water_zinc_discharge')
        waste_water_zinc_treatment = request.POST.get('waste_water_zinc_treatment')
        waste_water_zinc_name_location = request.POST.get('waste_water_zinc_name_location')
        waste_water_ammonia_source = request.POST.get('waste_water_ammonia_source')
        waste_water_ammonia_discharge = request.POST.get('waste_water_ammonia_discharge')
        waste_water_ammonia_treatment = request.POST.get('waste_water_ammonia_treatment')
        waste_water_ammonia_name_location = request.POST.get('waste_water_ammonia_name_location')
        waste_water_colour_source = request.POST.get('waste_water_colour_source')
        waste_water_colour_discharge = request.POST.get('waste_water_colour_discharge')
        waste_water_colour_treatment = request.POST.get('waste_water_colour_treatment')
        waste_water_colour_name_location = request.POST.get('waste_water_colour_name_location')
        waste_water_treatment_plant_capacity = request.POST.get('waste_water_treatment_plant_capacity')
        waste_water_qty_per_annum = request.POST.get('waste_water_qty_per_annum')
        waste_water_treatment_plant_etp = request.POST.get('waste_water_treatment_plant_etp')
        waste_water_treatment_sludge_qty = request.POST.get('waste_water_treatment_sludge_qty')
        waste_water_treatment_plant_name_location = request.POST.get('waste_water_treatment_plant_name_location')

        effluent_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        effluent_details.update(en_waste_water_generate=en_waste_water_generate,
                                waste_water_nh3n_source=waste_water_nh3n_source,
                                waste_water_nh3n_discharge=waste_water_nh3n_discharge,
                                waste_water_nh3n_treatment=waste_water_nh3n_treatment,
                                waste_water_nh3n_name_location=waste_water_nh3n_name_location,
                                waste_water_arsenic_source=waste_water_arsenic_source,
                                waste_water_arsenic_discharge=waste_water_arsenic_discharge,
                                waste_water_arsenic_treatment=waste_water_arsenic_treatment,
                                waste_water_arsenic_name_location=waste_water_arsenic_name_location,
                                waste_water_bod_source=waste_water_bod_source,
                                waste_water_bod_discharge=waste_water_bod_discharge,
                                waste_water_bod_treatment=waste_water_bod_treatment,
                                waste_water_bod_name_location=waste_water_bod_name_location,
                                waste_water_boron_source=waste_water_boron_source,
                                waste_water_boron_discharge=waste_water_boron_discharge,
                                waste_water_boron_treatment=waste_water_boron_treatment,
                                waste_water_boron_name_location=waste_water_boron_name_location,
                                waste_water_cadmium_source=waste_water_cadmium_source,
                                waste_water_cadmium_discharge=waste_water_cadmium_discharge,
                                waste_water_cadmium_treatment=waste_water_cadmium_treatment,
                                waste_water_cadmium_name_location=waste_water_cadmium_name_location,
                                waste_water_cod_source=waste_water_cod_source,
                                waste_water_cod_discharge=waste_water_cod_discharge,
                                waste_water_cod_treatment=waste_water_cod_treatment,
                                waste_water_cod_name_location=waste_water_cod_name_location,
                                waste_water_cloride_source=waste_water_cloride_source,
                                waste_water_cloride_discharge=waste_water_cloride_discharge,
                                waste_water_cloride_treatment=waste_water_cloride_treatment,
                                waste_water_cloride_name_location=waste_water_cloride_name_location,
                                waste_water_chromium_source=waste_water_chromium_source,
                                waste_water_chromium_discharge=waste_water_chromium_discharge,
                                waste_water_chromium_treatment=waste_water_chromium_treatment,
                                waste_water_chromium_name_location=waste_water_chromium_name_location,
                                waste_water_chromium_hex_source=waste_water_chromium_hex_source,
                                waste_water_chromium_hex_discharge=waste_water_chromium_hex_discharge,
                                waste_water_chromium_hex_treatment=waste_water_chromium_hex_treatment,
                                waste_water_chromium_hex_name_location=waste_water_chromium_hex_name_location,
                                waste_water_copper_source=waste_water_copper_source,
                                waste_water_copper_discharge=waste_water_copper_discharge,
                                waste_water_copper_treatment=waste_water_copper_treatment,
                                waste_water_copper_name_location=waste_water_copper_name_location,
                                waste_water_cyanide_source=waste_water_cyanide_source,
                                waste_water_cyanide_discharge=waste_water_cyanide_discharge,
                                waste_water_cyanide_treatment=waste_water_cyanide_treatment,
                                waste_water_cyanide_name_location=waste_water_cyanide_name_location,
                                waste_water_floride_source=waste_water_floride_source,
                                waste_water_floride_discharge=waste_water_floride_discharge,
                                waste_water_floride_treatment=waste_water_floride_treatment,
                                waste_water_floride_name_location=waste_water_floride_name_location,
                                waste_water_phosphate_source=waste_water_phosphate_source,
                                waste_water_phosphate_discharge=waste_water_phosphate_discharge,
                                waste_water_phosphate_treatment=waste_water_phosphate_treatment,
                                waste_water_phosphate_name_location=waste_water_phosphate_name_location,
                                waste_water_nitrate_source=waste_water_nitrate_source,
                                waste_water_nitrate_discharge=waste_water_nitrate_discharge,
                                waste_water_nitrate_treatment=waste_water_nitrate_treatment,
                                waste_water_nitrate_name_location=waste_water_nitrate_name_location,
                                waste_water_iron_source=waste_water_iron_source,
                                waste_water_iron_discharge=waste_water_iron_discharge,
                                waste_water_iron_treatment=waste_water_iron_treatment,
                                waste_water_iron_name_location=waste_water_iron_name_location,
                                waste_water_lead_source=waste_water_lead_source,
                                waste_water_lead_discharge=waste_water_lead_discharge,
                                waste_water_lead_treatment=waste_water_lead_treatment,
                                waste_water_lead_name_location=waste_water_lead_name_location,
                                waste_water_manganese_source=waste_water_manganese_source,
                                waste_water_manganese_discharge=waste_water_manganese_discharge,
                                waste_water_manganese_treatment=waste_water_manganese_treatment,
                                waste_water_manganese_name_location=waste_water_manganese_name_location,
                                waste_water_mercury_source=waste_water_mercury_source,
                                waste_water_mercury_discharge=waste_water_mercury_discharge,
                                waste_water_mercury_treatment=waste_water_mercury_treatment,
                                waste_water_mercury_name_location=waste_water_mercury_name_location,
                                waste_water_nickel_source=waste_water_nickel_source,
                                waste_water_nickel_discharge=waste_water_nickel_discharge,
                                waste_water_nickel_treatment=waste_water_nickel_treatment,
                                waste_water_nickel_name_location=waste_water_nickel_name_location,
                                waste_water_oil_source=waste_water_oil_source,
                                waste_water_oil_discharge=waste_water_oil_discharge,
                                waste_water_oil_treatment=waste_water_oil_treatment,
                                waste_water_oil_name_location=waste_water_oil_name_location,
                                waste_water_ph_source=waste_water_ph_source,
                                waste_water_ph_discharge=waste_water_ph_discharge,
                                waste_water_ph_treatment=waste_water_ph_treatment,
                                waste_water_ph_name_location=waste_water_ph_name_location,
                                waste_water_phenolic_source=waste_water_phenolic_source,
                                waste_water_phenolic_discharge=waste_water_phenolic_discharge,
                                waste_water_phenolic_treatment=waste_water_phenolic_treatment,
                                waste_water_phenolic_name_location=waste_water_phenolic_name_location,
                                waste_water_selenium_source=waste_water_selenium_source,
                                waste_water_selenium_discharge=waste_water_selenium_discharge,
                                waste_water_selenium_treatment=waste_water_selenium_treatment,
                                waste_water_selenium_name_location=waste_water_selenium_name_location,
                                waste_water_so4_source=waste_water_so4_source,
                                waste_water_so4_discharge=waste_water_so4_discharge,
                                waste_water_so4_treatment=waste_water_so4_treatment,
                                waste_water_so4_name_location=waste_water_so4_name_location,
                                waste_water_s_source=waste_water_s_source,
                                waste_water_s_discharge=waste_water_s_discharge,
                                waste_water_s_treatment=waste_water_s_treatment,
                                waste_water_s_name_location=waste_water_s_name_location,
                                waste_water_tds_source=waste_water_tds_source,
                                waste_water_tds_discharge=waste_water_tds_discharge,
                                waste_water_tds_treatment=waste_water_tds_treatment,
                                waste_water_tds_name_location=waste_water_tds_name_location,
                                waste_water_tss_source=waste_water_tss_source,
                                waste_water_tss_discharge=waste_water_tss_discharge,
                                waste_water_tss_treatment=waste_water_tss_treatment,
                                waste_water_tss_name_location=waste_water_tss_name_location,
                                waste_water_temp_source=waste_water_temp_source,
                                waste_water_temp_discharge=waste_water_temp_discharge,
                                waste_water_temp_treatment=waste_water_temp_treatment,
                                waste_water_temp_name_location=waste_water_temp_name_location,
                                waste_water_tkn_source=waste_water_tkn_source,
                                waste_water_tkn_discharge=waste_water_tkn_discharge,
                                waste_water_tkn_treatment=waste_water_tkn_treatment,
                                waste_water_tkn_name_location=waste_water_tkn_name_location,
                                waste_water_residual_cloride_source=waste_water_residual_cloride_source,
                                waste_water_residual_cloride_discharge=waste_water_residual_cloride_discharge,
                                waste_water_residual_cloride_treatment=waste_water_residual_cloride_treatment,
                                waste_water_residual_cloride_name_location=waste_water_residual_cloride_name_location,
                                waste_water_zinc_source=waste_water_zinc_source,
                                waste_water_zinc_discharge=waste_water_zinc_discharge,
                                waste_water_zinc_treatment=waste_water_zinc_treatment,
                                waste_water_zinc_name_location=waste_water_zinc_name_location,
                                waste_water_ammonia_source=waste_water_ammonia_source,
                                waste_water_ammonia_discharge=waste_water_ammonia_discharge,
                                waste_water_ammonia_treatment=waste_water_ammonia_treatment,
                                waste_water_ammonia_name_location=waste_water_ammonia_name_location,
                                waste_water_colour_source=waste_water_colour_source,
                                waste_water_colour_discharge=waste_water_colour_discharge,
                                waste_water_colour_treatment=waste_water_colour_treatment,
                                waste_water_colour_name_location=waste_water_colour_name_location,
                                waste_water_treatment_plant_capacity=waste_water_treatment_plant_capacity,
                                waste_water_qty_per_annum=waste_water_qty_per_annum,
                                waste_water_treatment_plant_etp=waste_water_treatment_plant_etp,
                                waste_water_treatment_sludge_qty=waste_water_treatment_sludge_qty,
                                waste_water_treatment_plant_name_location=waste_water_treatment_plant_name_location
                                )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_industry_emission_details(request):
    data = dict()
    try:
        application_no = request.POST.get('industry_emission_application_no')
        en_industry_emission_generate = request.POST.get('en_industry_emission_generate')
        en_spm_emission_expected = request.POST.get('en_spm_emission_expected')
        en_so2_emission_expected = request.POST.get('en_so2_emission_expected')
        en_nox_emission_expected = request.POST.get('en_nox_emission_expected')
        en_co_emission_expected = request.POST.get('en_co_emission_expected')
        en_fluoride_emission_expected = request.POST.get('en_fluoride_emission_expected')
        en_pol_control_device_stack_height = request.POST.get('en_pol_control_device_stack_height')
        en_pol_control_device_stack_diameter = request.POST.get('en_pol_control_device_stack_diameter')
        en_pol_control_device_dimension = request.POST.get('en_pol_control_device_dimension')
        en_pol_control_device_volume = request.POST.get('en_pol_control_device_volume')
        en_pol_control_device_temp = request.POST.get('en_pol_control_device_temp')
        en_air_pollution_control_device_capacity = request.POST.get('en_air_pollution_control_device_capacity')
        en_air_pollution_control_pcd_dimension = request.POST.get('en_air_pollution_control_pcd_dimention')


        industry_emission_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        industry_emission_details.update(en_industry_emission_generate=en_industry_emission_generate,
                                         en_spm_emission_expected=en_spm_emission_expected,
                                         en_so2_emission_expected=en_so2_emission_expected,
                                         en_nox_emission_expected=en_nox_emission_expected,
                                         en_co_emission_expected=en_co_emission_expected,
                                         en_fluoride_emission_expected=en_fluoride_emission_expected,
                                         en_pol_control_device_stack_height=en_pol_control_device_stack_height,
                                         en_pol_control_device_stack_diameter=en_pol_control_device_stack_diameter,
                                         en_pol_control_device_dimension=en_pol_control_device_dimension,
                                         en_pol_control_device_volume=en_pol_control_device_volume,
                                         en_pol_control_device_temp=en_pol_control_device_temp,
                                         en_air_pollution_control_device_capacity=en_air_pollution_control_device_capacity,
                                         en_air_pollution_control_pcd_dimension=en_air_pollution_control_pcd_dimension,
                                         )
        data['message'] = "success"
        return JsonResponse(data)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
        return JsonResponse(data)

def save_noise_level_details(request):
    data = dict()
    try:
        application_no = request.POST.get('noise_level_application_no')
        en_noise_ind_area_day = request.POST.get('en_noise_ind_area_day')
        en_noise_ind_area_night = request.POST.get('en_noise_ind_area_night')
        en_noise_ind_area_mgt_plan = request.POST.get('en_noise_ind_area_mgt_plan')
        en_noise_mixed_area_day = request.POST.get('en_noise_mixed_area_day')
        en_noise_mixed_area_night = request.POST.get('en_noise_mixed_area_night')
        en_noise_mixed_area_mgt_plan = request.POST.get('en_noise_mixed_area_mgt_plan')
        en_noise_sen_area_day = request.POST.get('en_noise_sen_area_day')
        en_noise_sen_area_night = request.POST.get('en_noise_sen_area_night')
        en_noise_sen_area_mgt_plan = request.POST.get('en_noise_sen_area_mgt_plan')


        noise_level_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        noise_level_details.update(en_noise_ind_area_day=en_noise_ind_area_day,
                                   en_noise_ind_area_night=en_noise_ind_area_night,
                                   en_noise_ind_area_mgt_plan=en_noise_ind_area_mgt_plan,
                                   en_noise_mixed_area_day=en_noise_mixed_area_day,
                                   en_noise_mixed_area_night=en_noise_mixed_area_night,
                                   en_noise_mixed_area_mgt_plan=en_noise_mixed_area_mgt_plan,
                                   en_noise_sen_area_day=en_noise_sen_area_day,
                                   en_noise_sen_area_night=en_noise_sen_area_night,
                                   en_noise_sen_area_mgt_plan=en_noise_sen_area_mgt_plan
                                   )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_other_impact_details(request):
    data = dict()
    try:
        application_no = request.POST.get('other_impact_application_no')
        en_other_impact_odour_source = request.POST.get('en_other_impact_odour_source')
        en_other_impact_odour_qty = request.POST.get('en_other_impact_odour_qty')
        en_other_impact_odour_mgt_plan = request.POST.get('en_other_impact_odour_mgt_plan')
        en_other_impact_fugutive_source = request.POST.get('en_other_impact_fugutive_source')
        en_other_impact_fugutive_qty = request.POST.get('en_other_impact_fugutive_qty')
        en_other_impact_fugutive_mgt_plan = request.POST.get('en_other_impact_fugutive_mgt_plan')
        en_other_impact_slope_source = request.POST.get('en_other_impact_slope_source')
        en_other_impact_slope_qty = request.POST.get('en_other_impact_slope_qty')
        en_other_impact_slope_mgt_plan = request.POST.get('en_other_impact_slope_mgt_plan')
        en_other_impact_aesthetic_source = request.POST.get('en_other_impact_aesthetic_source')
        en_other_impact_aesthetic_qty = request.POST.get('en_other_impact_aesthetic_qty')
        en_other_impact_aesthetic_mgt_plan = request.POST.get('en_other_impact_aesthetic_mgt_plan')
        en_other_impact_mucks_source = request.POST.get('en_other_impact_mucks_source')
        en_other_impact_mucks_qty = request.POST.get('en_other_impact_mucks_qty')
        en_other_impact_mucks_mgt_plan = request.POST.get('en_other_impact_mucks_mgt_plan')
        en_other_impact_sewerage_source = request.POST.get('en_other_impact_sewerage_source')
        en_other_impact_sewerage_qty = request.POST.get('en_other_impact_sewerage_qty')
        en_other_impact_sewerage_mgt_plan = request.POST.get('en_other_impact_sewerage_mgt_plan')
        en_other_impact_erosion_source = request.POST.get('en_other_impact_erosion_source')
        en_other_impact_erosion_qty = request.POST.get('en_other_impact_erosion_qty')
        en_other_impact_erosion_mgt_plan = request.POST.get('en_other_impact_erosion_mgt_plan')
        en_other_impact_storm_water_source = request.POST.get('en_other_impact_storm_water_source')
        en_other_impact_storm_water_qty = request.POST.get('en_other_impact_storm_water_qty')
        en_other_impact_storm_water_mgt_plan = request.POST.get('en_other_impact_storm_water_mgt_plan')
        en_other_impact_habitat_source = request.POST.get('en_other_impact_habitat_source')
        en_other_impact_habitat_qty = request.POST.get('en_other_impact_habitat_qty')
        en_other_impact_habitat_mgt_plan = request.POST.get('en_other_impact_habitat_mgt_plan')
        en_other_impact_socio_source = request.POST.get('en_other_impact_socio_source')
        en_other_impact_socio_qty = request.POST.get('en_other_impact_socio_qty')
        en_other_impact_socio_mgt_plan = request.POST.get('en_other_impact_socio_mgt_plan')
        en_other_impact_water_source_source = request.POST.get('en_other_impact_water_source_source')
        en_other_impact_water_source_qty = request.POST.get('en_other_impact_water_source_qty')
        en_other_impact_water_source_mgt_plan = request.POST.get('en_other_impact_water_source_mgt_plan')
        en_other_impact_other_source = request.POST.get('en_other_impact_other_source')
        en_other_impact_other_qty = request.POST.get('en_other_impact_other_qty')
        en_other_impact_other_mgt_plan = request.POST.get('en_other_impact_other_mgt_plan')

        other_impact_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        other_impact_details.update(en_other_impact_odour_source=en_other_impact_odour_source,
                                    en_other_impact_odour_qty=en_other_impact_odour_qty,
                                    en_other_impact_odour_mgt_plan=en_other_impact_odour_mgt_plan,
                                    en_other_impact_fugutive_source=en_other_impact_fugutive_source,
                                    en_other_impact_fugutive_qty=en_other_impact_fugutive_qty,
                                    en_other_impact_fugutive_mgt_plan=en_other_impact_fugutive_mgt_plan,
                                    en_other_impact_slope_source=en_other_impact_slope_source,
                                    en_other_impact_slope_qty=en_other_impact_slope_qty,
                                    en_other_impact_slope_mgt_plan=en_other_impact_slope_mgt_plan,
                                    en_other_impact_aesthetic_source=en_other_impact_aesthetic_source,
                                    en_other_impact_aesthetic_qty=en_other_impact_aesthetic_qty,
                                    en_other_impact_aesthetic_mgt_plan=en_other_impact_aesthetic_mgt_plan,
                                    en_other_impact_mucks_source=en_other_impact_mucks_source,
                                    en_other_impact_mucks_qty=en_other_impact_mucks_qty,
                                    en_other_impact_mucks_mgt_plan=en_other_impact_mucks_mgt_plan,
                                    en_other_impact_sewerage_source=en_other_impact_sewerage_source,
                                    en_other_impact_sewerage_qty=en_other_impact_sewerage_qty,
                                    en_other_impact_sewerage_mgt_plan=en_other_impact_sewerage_mgt_plan,
                                    en_other_impact_erosion_source=en_other_impact_erosion_source,
                                    en_other_impact_erosion_qty=en_other_impact_erosion_qty,
                                    en_other_impact_erosion_mgt_plan=en_other_impact_erosion_mgt_plan,
                                    en_other_impact_storm_water_source=en_other_impact_storm_water_source,
                                    en_other_impact_storm_water_qty=en_other_impact_storm_water_qty,
                                    en_other_impact_storm_water_mgt_plan=en_other_impact_storm_water_mgt_plan,
                                    en_other_impact_habitat_source=en_other_impact_habitat_source,
                                    en_other_impact_habitat_qty=en_other_impact_habitat_qty,
                                    en_other_impact_habitat_mgt_plan=en_other_impact_habitat_mgt_plan,
                                    en_other_impact_socio_source=en_other_impact_socio_source,
                                    en_other_impact_socio_qty=en_other_impact_socio_qty,
                                    en_other_impact_socio_mgt_plan=en_other_impact_socio_mgt_plan,
                                    en_other_impact_water_source_source=en_other_impact_water_source_source,
                                    en_other_impact_water_source_qty=en_other_impact_water_source_qty,
                                    en_other_impact_water_source_mgt_plan=en_other_impact_water_source_mgt_plan,
                                    en_other_impact_other_source=en_other_impact_other_source,
                                    en_other_impact_other_qty=en_other_impact_other_qty,
                                    en_other_impact_other_mgt_plan=en_other_impact_other_mgt_plan
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def submit_iee_application(request):
    data = dict()
    try:
        application_no = request.POST.get('iee_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')
        
        app_hist_details = t_application_history.objects.filter(application_no=application_no)
        app_hist_details.update(action_date=date.today())

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

        ancillary_amount = 0
        main_amount = 0
        total_amount = 0
        service_id = None
        application_type = None
        anc_details = 0
        anc_forms = ['Ancillary']

        for details in application_details:
            service_id = details.service_id
            application_type = details.application_type

            if details.service_type in anc_forms:
                anc_details += 1

        if anc_details > 0 and identifier != 'Ancillary':
            data['message'] = "not submitted"
        else:
            application_details.update(action_date=date.today())

            if identifier == 'Ancillary':
                t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').update(action_date=date.today())
                t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=date.today())
                data['message'] = "success"
            elif identifier in ('OC', 'NC'):
                t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=date.today())
                data['message'] = "success"
            else:
                ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary', application_status='P').count()
                if ancillary_count != 0:
                    data['message'] = "not submitted"
                else:
                    t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity').update(action_date=date.today())
                    t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=date.today())

                    fees_details = t_fees_schedule.objects.filter(Q(service_id=service_id) | Q(fee_type='application'))
                    for fees_detail in fees_details:
                        main_amount = int(fees_detail.rate) + int(fees_detail.application_fee)
                        break

                    ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()
                    if ancillary_application_details_count > 0:
                        anc_fees_details = t_fees_schedule.objects.filter(Q(service_id=service_id) & ~Q(fee_type='application'))
                        for anc_fees_detail in anc_fees_details:
                            ancillary_amount += int(anc_fees_detail.rate)

                    total_amount = main_amount + ancillary_amount
                    insert_app_payment_details(request, application_no, 'new_iee_application', total_amount, application_type)
                    send_payment_mail(request.session['name'], request.session['email'], total_amount)
                    data['message'] = "success"

    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"

    return JsonResponse(data)

def save_industry_ancillary_application(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        project_category = request.POST.get('project_category')
        application_type = request.POST.get('application_type')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        cid = request.POST.get('cid')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        focal_person = request.POST.get('focal_person')
        industry_type = request.POST.get('industry_type')
        establishment_type = request.POST.get('establishment_type')
        industry_classification = request.POST.get('industry_classification')
        dzongkhag_code = request.POST.get('dzo_throm')
        gewog_code = request.POST.get('gewog')
        village_code = request.POST.get('vil_chiwog')
        location_name = request.POST.get('location_name')
        industrial_area_acre = request.POST.get('industrial_area_acre')
        state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
        private_area_acre = request.POST.get('private_area_acre')
        others_area_acre = request.POST.get('others_area_acre')
        total_area_acre = request.POST.get('total_area_acre')
        green_area_acre = request.POST.get('green_area_acre')
        production_process_flow = request.POST.get('production_process_flow')
        project_objective = request.POST.get('project_objective')
        project_no_of_workers = request.POST.get('project_no_of_workers')
        project_cost = request.POST.get('project_cost')
        project_duration = request.POST.get('project_duration')

        t_ec_industries_t1_general.objects.create(
            application_no=application_no,
            application_date=date.today(),
            application_type='New',
            service_type='Ancillary',
            ca_authority=None,
            applicant_id=request.session['email'],
            colour_code=None,
            project_name=project_name,
            project_category=project_category,
            applicant_name=applicant_name,
            address=address,
            cid=cid,
            contact_no=contact_no,
            email=email,
            focal_person=focal_person,
            industry_type=industry_type,
            establishment_type=establishment_type,
            industry_classification=industry_classification,
            dzongkhag_code=dzongkhag_code,
            gewog_code=gewog_code,
            village_code=village_code,
            location_name=location_name,
            industrial_area_acre=industrial_area_acre,
            state_reserve_forest_acre=state_reserve_forest_acre,
            private_area_acre=private_area_acre,
            others_area_acre=others_area_acre,
            total_area_acre=total_area_acre,
            green_area_acre=green_area_acre,
            production_process_flow=production_process_flow,
            project_objective=project_objective,
            project_no_of_workers=project_no_of_workers,
            project_cost=project_cost,
            project_duration=project_duration
            )
        t_workflow_dtls.objects.create(application_no=application_no, 
                                        service_id=request.session['service_id'],
                                        application_status='P',
                                        action_date=None,
                                        actor_id=None,
                                        actor_name=None,
                                        assigned_user_id=None,
                                        assigned_role_id='2',
                                        assigned_role_name='Verifier',
                                        result=None,
                                        ca_authority=None,
                                        dzongkhag_thromde_id=None,
                                        application_source='ECSS'
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


def add_product_details(request):
    application_no = request.POST.get('application_no')
    partner_type = request.POST.get('partner_type')
    partner_cid = request.POST.get('partner_cid')
    partner_name = request.POST.get('partner_name')
    partner_address = request.POST.get('partner_address')

    t_ec_industries_t2_partner_details.objects.create(application_no=application_no,partner_type=partner_type,
                                                    partner_cid=partner_cid, partner_name=partner_name, partner_address=partner_address)
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no= application_no).order_by(
        'record_id')
    return render(request, 'partner_details.html',{'partner_details':partner_details})

def get_specific_activity_description(request):
    broad_activity_code = request.GET.get('broad_activity_code')
    specific_activity_description = t_bsic_code.objects.filter(broad_activity_code=broad_activity_code)
    return render(request, 'specific_activity_description_list.html',
                  {'specific_activity_description':specific_activity_description})

def get_category(request):
    specific_activity_code = request.GET.get('specific_activity_code')
    category_details = t_bsic_code.objects.filter(specific_activity_code=specific_activity_code)
    return render(request, 'category_list.html',
                  {'category_details':category_details})

def get_application_service_id(request):
    data = dict()
    broad_activity_code = request.GET.get('broad_activity_code')
    specific_activity_code = request.GET.get('specific_activity_code')
    category = request.GET.get('category')

    category_details = t_bsic_code.objects.filter(broad_activity_code=broad_activity_code,specific_activity_code=specific_activity_code,category=category)
    for cat_details in category_details:
        print(cat_details.competent_authority)
        request.session['ca_auth'] = cat_details.competent_authority
        request.session['colour_code'] = cat_details.colour_code
        request.session['service_id'] = cat_details.service_id
        request.session['broad_activity_code'] = cat_details.broad_activity_code
        request.session['specific_activity_code'] = cat_details.specific_activity_code
        request.session['has_tor'] = cat_details.has_tor
        request.session['category'] = cat_details.category
        data['service_id'] = cat_details.service_id
        data['colour_code'] = cat_details.colour_code
        data['ca_auth'] = cat_details.competent_authority
        data['has_tor'] = cat_details.has_tor
    return JsonResponse(data)

# IEE DETAILS
def load_gewog(request):
    dzongkhag_id = request.GET.get('dzongkhag_id')
    gewog_list = t_gewog_master.objects.filter(dzongkhag_code_id=dzongkhag_id).order_by('gewog_name')
    return render(request, 'gewog_list.html', {'gewog_list': gewog_list})

def load_village(request):
    gewog_id = request.GET.get('gewog_id')
    village_list = t_village_master.objects.filter(gewog_code_id=gewog_id).order_by('village_name')
    return render(request, 'village_list.html', {'village_list': village_list})

def new_iee_application(request):
    service_code = 'IEE'
    application_no = get_application_no(request, service_code, '1')
    request.session['application_no'] = application_no
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
    final_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    return render(request, 'industry_iee_form.html',{'thromde':thromde,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                    'final_product':final_product,'ancillary_road':ancillary_road, 'power_line':power_line,
                                                    'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})
def save_iee_attachment(request):
    data = dict()
    iee_attach = request.FILES['iee_attach']
    file_name = iee_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/IEE/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, iee_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/IEE" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_iee_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='IEE')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEE')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_anc_iee_attachment(request):
    data = dict()
    iee_attach = request.FILES['iee_attach']
    file_name = iee_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/IEEANC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, iee_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/IEEANC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_anc_iee_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='IEE')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def save_anc_power_line_details(request):
    application_no = request.POST.get('application_no')
    line_chainage_from = request.POST.get('line_chainage_from')
    line_chainage_to = request.POST.get('line_chainage_to')
    land_type = request.POST.get('land_type')
    terrain = request.POST.get('terrain')
    tower_type = request.POST.get('tower_type')
    no_of_tower = request.POST.get('no_of_tower')
    row = request.POST.get('row')
    area_required = request.POST.get('area_required')

    t_ec_industries_t7_ancillary_power_line.objects.create(application_no=application_no,line_chainage_from=line_chainage_from,
                                                           line_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                                                           tower_type=tower_type,no_of_tower=no_of_tower,row=row,area_required=area_required)
    anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by('record_id')
    return render(request,'anc_power_line_details.html', {'anc_power_line_details':anc_power_line_details})

def update_anc_power_line_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    line_chainage_from = request.POST.get('line_chainage_from')
    line_chainage_to = request.POST.get('line_chainage_to')
    land_type = request.POST.get('land_type')
    terrain = request.POST.get('terrain')
    tower_type = request.POST.get('tower_type')
    no_of_tower = request.POST.get('no_of_tower')
    row = request.POST.get('row')
    area_required = request.POST.get('area_required')

    power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(record_id=record_id)
    power_line_details.update(application_no=application_no,line_chainage_from=line_chainage_from,
                                                           line_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                                                           tower_type=tower_type,no_of_tower=no_of_tower,row=row,area_required=area_required)
    anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by('record_id')
    return render(request,'anc_power_line_details.html', {'anc_power_line_details':anc_power_line_details})

def delete_anc_power_line_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(record_id=record_id)
    power_line_details.delete()
    anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'anc_power_line_details.html', {'anc_power_line_details': anc_power_line_details})

def save_anc_road_details(request):
    application_no = request.POST.get('application_no')
    line_chainage_from = request.POST.get('road_line_chainage_from')
    line_chainage_to = request.POST.get('road_line_chainage_to')
    land_type = request.POST.get('road_land_type')
    terrain = request.POST.get('road_terrain')
    road_width = request.POST.get('road_width')
    row = request.POST.get('road_row')
    area_required = request.POST.get('road_area_required')
    # dzongkhag = request.POST.get('dzongkhag')
    # gewog = request.POST.get('gewog')
    # village = request.POST.get('village')

    t_ec_industries_t6_ancillary_road.objects.create(application_no=application_no,road_chainage_from=line_chainage_from,
                                                    road_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                                                    road_width=road_width,row=row,area_required=area_required)
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
    return render(request,'anc_approach_road_details.html', {'anc_road_details':anc_road_details})

def update_anc_road_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    line_chainage_from = request.POST.get('line_chainage_from')
    line_chainage_to = request.POST.get('line_chainage_to')
    land_type = request.POST.get('land_type')
    terrain = request.POST.get('terrain')
    road_width = request.POST.get('road_width')
    row = request.POST.get('row')
    area_required = request.POST.get('area_required')

    road_details = t_ec_industries_t6_ancillary_road.objects.filter(record_id=record_id)
    road_details.update(application_no=application_no,road_chainage_from=line_chainage_from,
                       road_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                       road_width=road_width,row=row,area_required=area_required)
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
    return render(request,'anc_approach_road_details.html', {'anc_road_details':anc_road_details})

def delete_anc_road_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    road_details = t_ec_industries_t6_ancillary_road.objects.filter(record_id=record_id)
    road_details.delete()
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'anc_approach_road_details.html', {'anc_road_details': anc_road_details})

def save_approach_road_details(request):
    application_no = request.POST.get('application_no')
    line_chainage_from = request.POST.get('road_line_chainage_from')
    line_chainage_to = request.POST.get('road_line_chainage_to')
    land_type = request.POST.get('road_land_type')
    road_terrain = request.POST.get('road_terrain')
    road_width = request.POST.get('road_width')
    row = request.POST.get('road_row')
    area_required = request.POST.get('road_area_required')
    dzongkhag = request.POST.get('dzongkhag')
    gewog = request.POST.get('gewog')
    village = request.POST.get('village')

    t_ec_industries_t6_ancillary_road.objects.create(application_no=application_no,road_chainage_from=line_chainage_from,
                                                    road_chainage_to=line_chainage_to,land_type=land_type,terrain=road_terrain,
                                                    road_width=road_width,row=row,area_required=area_required,dzongkhag=dzongkhag,gewog=gewog,village=village)
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request,'approach_road_details.html', {'anc_road_details':anc_road_details, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def update_approach_road_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    line_chainage_from = request.POST.get('line_chainage_from')
    line_chainage_to = request.POST.get('line_chainage_to')
    land_type = request.POST.get('land_type')
    terrain = request.POST.get('terrain')
    road_width = request.POST.get('road_width')
    row = request.POST.get('row')
    area_required = request.POST.get('area_required')
    dzongkhag = request.POST.get('dzongkhag')
    gewog = request.POST.get('gewog')
    village = request.POST.get('village')

    road_details = t_ec_industries_t6_ancillary_road.objects.filter(record_id=record_id)
    road_details.update(application_no=application_no,line_chainage_from=line_chainage_from,
                       line_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                       road_width=road_width,row=row,area_required=area_required,dzongkhag=dzongkhag,gewog=gewog,village=village)
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request,'approach_road_details.html', {'anc_road_details':anc_road_details, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def delete_approach_road_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    road_details = t_ec_industries_t6_ancillary_road.objects.filter(record_id=record_id)
    road_details.delete()
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'approach_road_details.html', {'anc_road_details': anc_road_details})

def add_types_of_drain(request):
    application_no = request.POST.get('application_no')
    drain_type = request.POST.get('drain_type')
    chainage = request.POST.get('chainage')

    t_ec_industries_t12_drainage_details.objects.create(application_no=application_no,drain_type=drain_type,chainage=chainage)
    drainage_type = t_ec_industries_t12_drainage_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'types_of_drains.html', {'drainage_type': drainage_type})

def update_types_of_drain(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    drain_type = request.POST.get('drain_type')
    chainage = request.POST.get('chainage')

    drain_details = t_ec_industries_t12_drainage_details.objects.filter(record_id=record_id)

    drain_details.update(drain_type=drain_type,chainage=chainage)
    drainage_type = t_ec_industries_t12_drainage_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'types_of_drains.html', {'drainage_type': drainage_type})

def delete_types_of_drain(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    road_details = t_ec_industries_t12_drainage_details.objects.filter(record_id=record_id)
    road_details.delete()
    drainage_type = t_ec_industries_t12_drainage_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'types_of_drains.html', {'drainage_type': drainage_type})

def add_forestry_produce_details(request):
    application_no = request.POST.get('application_no')
    produce_name = request.POST.get('produce_name')
    quantity_annum = request.POST.get('quantity_annum')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t8_forest_produce.objects.create(application_no=application_no, produce_name=produce_name,
                                                    qty=quantity_annum, storage_method=storage_method)
    forestry_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'forestry_produce.html', {'forestry_produce': forestry_produce})

def update_forestry_produce_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    produce_name = request.POST.get('produce_name')
    quantity_annum = request.POST.get('quantity_annum')
    storage_method = request.POST.get('storage_method')

    forestry_produce_details = t_ec_industries_t8_forest_produce.objects.filter(record_id=record_id)
    forestry_produce_details.update(produce_name=produce_name, qty=quantity_annum, storage_method=storage_method)
    forestry_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'forestry_produce.html', {'forestry_produce': forestry_produce})

def delete_forestry_produce_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    forestry_produce_details = t_ec_industries_t8_forest_produce.objects.filter(record_id=record_id)
    forestry_produce_details.delete()
    forestry_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'forestry_produce.html', {'forestry_produce': forestry_produce})

def save_forest_attachment(request):
    data = dict()
    forest_attach = request.FILES['forest_attach']
    file_name = forest_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/FO/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, forest_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/FO" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_forest_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='FO')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FO')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_anc_forest_attachment(request):
    data = dict()
    forest_attach = request.FILES['forest_attach']
    file_name = forest_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/FOANC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, forest_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/FOANC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_anc_forest_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='FOANC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FOANC')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_ground_water_attachment(request):
    data = dict()
    ground_water_attach = request.FILES['ground_water_attach']
    file_name = ground_water_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GW/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ground_water_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/GW" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_ground_water_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='GW')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GW')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_anc_ground_water_attachment(request):
    data = dict()
    ground_water_attach = request.FILES['ground_water_attach']
    file_name = ground_water_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GWANC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ground_water_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/GWANC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_anc_ground_water_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='GW')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_general_attachment(request):
    data = dict()
    general_attach = request.FILES['general_attach']
    file_name = general_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GEN/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/GEN" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_general_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='GEN')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GEN')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_road_attachment(request):
    data = dict()
    road_attach = request.FILES['road_attach']
    file_name = road_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/ROA/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, road_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/ROA" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_road_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='ROA')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ROA')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

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

def save_anc_general_attachment(request):
    data = dict()
    general_attach = request.FILES['general_attach']
    file_name = general_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/GENANC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/GENANC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_anc_general_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='GENANC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def add_final_product_details(request):
    application_no = request.POST.get('application_no')
    product_name = request.POST.get('produce_name')
    name_location_type = request.POST.get('name_location')
    if name_location_type:
        quantity_annum = None
        name_location_type = request.POST.get('name_location')
    else:
        quantity_annum = request.POST.get('quantity_annum')
        name_location_type = None
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t4_project_product.objects.create(application_no=application_no, product_name=product_name,
                                                    quantity_annum=quantity_annum,name_location_type=name_location_type, storage_method=storage_method)
    final_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'final_products.html', {'final_product': final_product})

def update_final_product_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    product_name = request.POST.get('produce_name')
    name_location_type = request.POST.get('name_location')
    if name_location_type:
        quantity_annum = None
        name_location_type = request.POST.get('name_location')
    else:
        quantity_annum = request.POST.get('quantity_annum')
        name_location_type = None
    storage_method = request.POST.get('storage_method')

    final_product_details = t_ec_industries_t4_project_product.objects.filter(record_id=record_id)
    final_product_details.update(product_name=product_name, quantity_annum=quantity_annum,name_location_type=name_location_type, storage_method=storage_method)
    final_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'final_products.html', {'final_product': final_product})

def delete_final_product_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    final_product_details = t_ec_industries_t4_project_product.objects.filter(record_id=record_id)
    final_product_details.delete()
    final_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'final_products.html', {'final_product': final_product})

def add_forest_produce_details(request):
    application_no = request.POST.get('application_no')
    produce_name = request.POST.get('produce_name')
    quantity_annum = request.POST.get('quantity_annum')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t8_forest_produce.objects.create(application_no=application_no, produce_name=produce_name,
                                                    qty=quantity_annum, storage_method=storage_method)
    final_product = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'forestry_produce.html', {'final_product': final_product})

def update_forest_produce_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    produce_name = request.POST.get('produce_name')
    quantity_annum = request.POST.get('quantity_annum')
    storage_method = request.POST.get('storage_method')

    final_product_details = t_ec_industries_t8_forest_produce.objects.filter(record_id=record_id)
    final_product_details.update(produce_name=produce_name, qty=quantity_annum, storage_method=storage_method)
    final_product = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'forestry_produce.html', {'forestry_produce': final_product})

def delete_forest_produce_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    final_product_details = t_ec_industries_t8_forest_produce.objects.filter(record_id=record_id)
    final_product_details.delete()
    final_product = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'forestry_produce.html', {'final_product': final_product})

def save_transmission_attachment(request):
    data = dict()
    general_attach = request.FILES['transmission_attach']
    file_name = general_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TRA/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/TRA" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_transmission_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='TRA')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TRA')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_tourism_attachment(request):
    data = dict()
    general_attach = request.FILES['tourism_attach']
    file_name = general_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/TOU/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/TOU" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_tourism_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='TOU')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOU')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})

def save_quarry_attachment(request):
    data = dict()
    general_attach = request.FILES['quarry_attach']
    file_name = general_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/QUA/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, general_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/QUA" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_quarry_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='QUA')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='QUA')

    return render(request, 'application_attachment_page.html', {'file_attach': file_attach})


#EA Details
def save_ea_attachment(request):
    data = dict()
    ea_attach = request.FILES['ea_attach']
    file_name = ea_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/IEA/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ea_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/IEA" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_ea_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='EA')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='IEA')

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})


def save_products_by_products_details(request):
    application_no = request.POST.get('application_no')
    type = request.POST.get('product_type')
    product_name = request.POST.get('product_name')
    qty = request.POST.get('product_qty')
    storage_method = request.POST.get('product_storage_method')

    t_ec_industries_t9_products_by_products.objects.create(application_no=application_no, type=type, product_name=product_name,
                                     qty=qty, storage_method=storage_method)
    products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no).order_by('record_id')

    return render(request, 'products_by_products.html', {'products_by_products': products_by_products})

def update_products_by_products_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    type = request.POST.get('product_type')
    product_name = request.POST.get('product_name')
    qty = request.POST.get('product_qty')
    storage_method = request.POST.get('storage_method')

    products_by_products_details = t_ec_industries_t9_products_by_products.objects.filter(record_id=record_id)
    products_by_products_details.update(type=type,product_name=product_name, qty=qty, storage_method=storage_method)
    products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'final_products.html', {'final_product': products_by_products})

def delete_products_by_products_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    products_by_products_details = t_ec_industries_t9_products_by_products.objects.filter(record_id=record_id)
    products_by_products_details.delete()
    products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'products_by_products.html', {'products_by_products': products_by_products})

def save_ea_hazardous_details(request):
    application_no = request.POST.get('application_no')
    chemical_name = request.POST.get('chemical_name')
    qty = request.POST.get('qty')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t10_hazardous_chemicals.objects.create(application_no=application_no, chemical_name=chemical_name,
                                     qty=qty, storage_method=storage_method)
    hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no).order_by('record_id')

    return render(request, 'hazardous_chemicals.html', {'hazardous_chemicals': hazardous_chemicals})

def update_ea_hazardous_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    chemical_name = request.POST.get('chemical_name')
    qty = request.POST.get('qty')
    storage_method = request.POST.get('storage_method')

    hazardous_chemicals_details = t_ec_industries_t10_hazardous_chemicals.objects.filter(record_id=record_id)
    hazardous_chemicals_details.update(type=type,chemical_name=chemical_name, qty=qty, storage_method=storage_method)
    hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'hazardous_chemicals.html', {'hazardous_chemicals': hazardous_chemicals})

def delete_ea_hazardous_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    hazardous_chemicals_details = t_ec_industries_t10_hazardous_chemicals.objects.filter(record_id=record_id)
    hazardous_chemicals_details.delete()
    hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'hazardous_chemicals.html', {'hazardous_chemicals': hazardous_chemicals})

def save_terrain_baseline_details_one(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        bl_tpsm_sampling_location_one = request.POST.get('bl_tpsm_sampling_location_one')
        bl_tpsm_sampling_location_two = request.POST.get('bl_tpsm_sampling_location_two')
        bl_tpsm_sampling_location = request.POST.get('bl_tpsm_sampling_location')
        bl_rpm_sampling_location_one = request.POST.get('bl_rpm_sampling_location_one')
        bl_rpm_sampling_location_two = request.POST.get('bl_rpm_sampling_location_two')
        bl_rpm_sampling_location = request.POST.get('bl_rpm_sampling_location')
        bl_so2_sampling_location_one = request.POST.get('bl_so2_sampling_location_one')
        bl_so2_sampling_location_two = request.POST.get('bl_so2_sampling_location_two')
        bl_so2_sampling_location = request.POST.get('bl_so2_sampling_location')
        bl_nox_sampling_location_one = request.POST.get('bl_nox_sampling_location_one')
        bl_nox_sampling_location_two = request.POST.get('bl_nox_sampling_location_two')
        bl_nox_sampling_location = request.POST.get('bl_nox_sampling_location')
        bl_co_sampling_location_one = request.POST.get('bl_co_sampling_location_one')
        bl_co_sampling_location_two = request.POST.get('bl_co_sampling_location_two')
        bl_co_sampling_location = request.POST.get('bl_co_sampling_location')
        bl_other_poll_sampling_location_one = request.POST.get('bl_other_poll_sampling_location_one')
        bl_other_poll_sampling_location_two = request.POST.get('bl_other_poll_sampling_location_two')
        bl_other_poll_sampling_location = request.POST.get('bl_other_poll_sampling_location')
        bl_geo_coordinates_sampling_location_one = request.POST.get('bl_geo_coordinates_sampling_location_one')
        bl_geo_coordinates_sampling_location_two = request.POST.get('bl_geo_coordinates_sampling_location_two')
        bl_geo_coordinates_sampling_location = request.POST.get('bl_geo_coordinates_sampling_location')
        bl_air_temperature = request.POST.get('bl_air_temperature')
        bl_air_humidity = request.POST.get('bl_air_humidity')
        bl_air_rainfall = request.POST.get('bl_air_rainfall')
        bl_air_wind_direction = request.POST.get('bl_air_wind_direction')
        bl_air_wind_speed = request.POST.get('bl_air_wind_speed')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(bl_tpsm_sampling_location_one=bl_tpsm_sampling_location_one,
                                    bl_tpsm_sampling_location_two=bl_tpsm_sampling_location_two,
                                    bl_tpsm_sampling_location=bl_tpsm_sampling_location,
                                    bl_rpm_sampling_location_one=bl_rpm_sampling_location_one,
                                    bl_rpm_sampling_location_two=bl_rpm_sampling_location_two,
                                    bl_rpm_sampling_location=bl_rpm_sampling_location,
                                    bl_so2_sampling_location_one=bl_so2_sampling_location_one,
                                    bl_so2_sampling_location_two=bl_so2_sampling_location_two,
                                    bl_so2_sampling_location=bl_so2_sampling_location,
                                    bl_nox_sampling_location_one=bl_nox_sampling_location_one,
                                    bl_nox_sampling_location_two=bl_nox_sampling_location_two,
                                    bl_nox_sampling_location=bl_nox_sampling_location,
                                    bl_co_sampling_location_one=bl_co_sampling_location_one,
                                    bl_co_sampling_location_two=bl_co_sampling_location_two,
                                    bl_co_sampling_location=bl_co_sampling_location,
                                    bl_other_poll_sampling_location_one=bl_other_poll_sampling_location_one,
                                    bl_other_poll_sampling_location_two=bl_other_poll_sampling_location_two,
                                    bl_other_poll_sampling_location=bl_other_poll_sampling_location,
                                    bl_geo_coordinates_sampling_location_one=bl_geo_coordinates_sampling_location_one,
                                    bl_geo_coordinates_sampling_location_two=bl_geo_coordinates_sampling_location_two,
                                    bl_geo_coordinates_sampling_location=bl_geo_coordinates_sampling_location,
                                    bl_air_temperature=bl_air_temperature,
                                    bl_air_humidity=bl_air_humidity,
                                    bl_air_rainfall=bl_air_rainfall,
                                    bl_air_wind_direction=bl_air_wind_direction,
                                    bl_air_wind_speed=bl_air_wind_speed)
        data['message'] = "success"
        return JsonResponse(data)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
        return JsonResponse(data)
    
def save_terrain_baseline_details_two(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        bl_nb_sampling_location = request.POST.get('bl_nb_sampling_location')
        bl_sb_sampling_location = request.POST.get('bl_sb_sampling_location')
        bl_eb_sampling_location = request.POST.get('bl_eb_sampling_location')
        bl_wb_sampling_location = request.POST.get('bl_wb_sampling_location')
        bl_others_sampling_location = request.POST.get('bl_others_sampling_location')
        bl_ambient_ph = request.POST.get('bl_ambient_ph')
        bl_ambient_tss = request.POST.get('bl_ambient_tss')
        bl_ambient_tds = request.POST.get('bl_ambient_tds')
        bl_ambient_conductivity = request.POST.get('bl_ambient_conductivity')
        bl_ambient_bod = request.POST.get('bl_ambient_bod')
        bl_ambient_cod = request.POST.get('bl_ambient_cod') 
        bl_ambient_flora = request.POST.get('bl_ambient_flora')
        bl_ambient_fauna = request.POST.get('bl_ambient_fauna')
        bl_socio_settlement_name = request.POST.get('bl_socio_settlement_name')
        bl_socio_total_population = request.POST.get('bl_socio_total_population')
        bl_socio_income_source = request.POST.get('bl_socio_income_source')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(bl_nb_sampling_location=bl_nb_sampling_location,
                                    bl_sb_sampling_location=bl_sb_sampling_location,
                                    bl_eb_sampling_location=bl_eb_sampling_location,
                                    bl_wb_sampling_location=bl_wb_sampling_location,
                                    bl_others_sampling_location=bl_others_sampling_location,
                                    bl_ambient_ph=bl_ambient_ph,
                                    bl_ambient_tss=bl_ambient_tss,
                                    bl_ambient_tds=bl_ambient_tds,
                                    bl_ambient_conductivity=bl_ambient_conductivity,
                                    bl_ambient_bod=bl_ambient_bod,
                                    bl_ambient_cod=bl_ambient_cod,
                                    bl_ambient_flora=bl_ambient_flora,
                                    bl_ambient_fauna=bl_ambient_fauna,
                                    bl_socio_settlement_name=bl_socio_settlement_name,
                                    bl_socio_total_population=bl_socio_total_population,
                                    bl_socio_income_source=bl_socio_income_source)
        data['message'] = "success"
        return JsonResponse(data)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
        return JsonResponse(data)

def submit_ea_application(request):
    data = dict()
    try:
        application_no = request.POST.get('ea_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')
        
        app_hist_details = t_application_history.objects.filter(application_no=application_no)
        app_hist_details.update(action_date=date.today())

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        anc_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()

        ancillary_amount = 0
        main_amount = 0
        total_amount = 0
        service_id = None
        application_type = None

        for details in application_details:
            service_id = details.service_id
            application_type = details.application_type
            anc_other_crushing_unit = details.anc_other_crushing_unit
            anc_other_surface_collection = details.anc_other_surface_collection
            anc_other_ground_water = details.anc_other_ground_water
            anc_other_mineral = details.anc_other_mineral
            anc_other_general = details.anc_other_general
            anc_other_transmission = details.anc_other_transmission

            if any([anc_other_crushing_unit == 'Yes', anc_other_surface_collection == 'Yes', anc_other_ground_water == 'Yes', anc_other_mineral == 'Yes', anc_other_general == 'Yes', anc_other_transmission == 'Yes']):
                if anc_details == 0:
                    data['message'] = "not submitted"
                else:
                    application_details.update(action_date=date.today())
                    if identifier == 'Ancillary':
                        t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').update(action_date=date.today())
                        t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=date.today())
                        data['message'] = "success"
                    elif identifier in ('OC', 'NC'):
                        t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=date.today())
                        data['message'] = "success"
                    else:
                        ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary', application_status='P').count()
                        if ancillary_count:
                            data['message'] = "not submitted"
                        else:
                            t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity').update(action_date=date.today())
                            t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=date.today())

                            fees_details = t_fees_schedule.objects.filter(Q(service_id=service_id) | Q(fee_type='application'))
                            for fees_detail in fees_details:
                                main_amount = int(fees_detail.rate) + int(fees_detail.application_fee)
                                break

                            ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()
                            if ancillary_application_details_count:
                                anc_fees_details = t_fees_schedule.objects.filter(Q(service_id=service_id) & ~Q(fee_type='application'))
                                for anc_fees_detail in anc_fees_details:
                                    ancillary_amount += int(anc_fees_detail.rate)

                            total_amount = main_amount + ancillary_amount
                            insert_app_payment_details(request, application_no, 'new_ea_application', total_amount, application_type)
                            send_payment_mail(request.session['name'], request.session['email'], total_amount)
                            data['message'] = "success"

    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"

    return JsonResponse(data)


#Common Details
def save_project_details(request):
    data = dict()
    try:
        application_no = request.POST.get('project_details_application_no')
        project_objective = request.POST.get('project_objective')
        project_beneficiaries = request.POST.get('project_beneficiaries')
        proposed_route_reason = request.POST.get('proposed_route_reason')
        project_cost = request.POST.get('project_cost')
        project_duration = request.POST.get('project_duration')
        production_capacity = request.POST.get('production_capacity')
        stripping_ratio = request.POST.get('stripping_ratio')
        bench_height = request.POST.get('bench_height')
        bench_width = request.POST.get('bench_width')
        right_of_way = request.POST.get('right_of_way')
        length_of_transmission = request.POST.get('length_of_transmission')
        transmission_voltage_level = request.POST.get('transmission_voltage_level')
        starting_point_transmission = request.POST.get('starting_point_transmission')
        transmission_termination_point = request.POST.get('transmission_termination_point')
        construction_substation = request.POST.get('construction_substation')
        transmission_numbers = request.POST.get('transmission_numbers')
        transmission_area = request.POST.get('transmission_area')
        location_transmission = request.POST.get('location_transmission')
        no_of_workers = request.POST.get('no_of_workers')
        project_output = request.POST.get('project_output')
        month_season_name = request.POST.get('month_season_name')
        machineries_type_number = request.POST.get('machineries_type_number')
        abstraction_type = request.POST.get('abstraction_type')
        total_requirement = request.POST.get('total_requirement')
        borewell_installed_capacity = request.POST.get('borewell_installed_capacity')
        geo_coordinates = request.POST.get('geo_coordinates')
        borewell_width_depth = request.POST.get('borewell_width_depth')
        borewell_depth_dec = request.POST.get('borewell_depth_dec')
        borewell_depth_jan = request.POST.get('borewell_depth_jan')
        borewell_depth_feb = request.POST.get('borewell_depth_feb')
        proposed_location_justification = request.POST.get('proposed_location_justification')
        blast_required = request.POST.get('blast_required') 
        blast_type = request.POST.get('blast_type')
        blast_qty = request.POST.get('blast_qty')
        blast_frequency_time = request.POST.get('blast_frequency_time')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(project_objective=project_objective,
                                    project_beneficiaries=project_beneficiaries,
                                    proposed_route_reason=proposed_route_reason,
                                    project_cost=project_cost,
                                    project_duration=project_duration,
                                    production_capacity=production_capacity,
                                    stripping_ratio=stripping_ratio,
                                    bench_height=bench_height,
                                    bench_width=bench_width,
                                    right_of_way=right_of_way,
                                    length_of_transmission=length_of_transmission,
                                    transmission_voltage_level=transmission_voltage_level,
                                    starting_point_transmission=starting_point_transmission,
                                    transmission_termination_point=transmission_termination_point,
                                    construction_substation=construction_substation,
                                    transmission_numbers=transmission_numbers,
                                    transmission_area=transmission_area,
                                    location_transmission=location_transmission,
                                    project_no_of_workers=no_of_workers,
                                    project_output=project_output,
                                    month_season_name=month_season_name,
                                    machineries_type_number=machineries_type_number,
                                    abstraction_type=abstraction_type,
                                    total_requirement=total_requirement,
                                    borewell_installed_capacity=borewell_installed_capacity,
                                    geo_coordinates=geo_coordinates,
                                    borewell_width_depth=borewell_width_depth,
                                    borewell_depth_dec=borewell_depth_dec,
                                    borewell_depth_jan=borewell_depth_jan,
                                    borewell_depth_feb=borewell_depth_feb,
                                    proposed_location_justification=proposed_location_justification,
                                    blast_required=blast_required, 
                                    blast_type=blast_type,
                                    blast_qty=blast_qty,
                                    blast_frequency_time=blast_frequency_time
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def ec_renewal(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
 
    application_details = t_ec_industries_t1_general.objects.filter(applicant_id=applicant_id,ec_expiry_date__lt=date.today(), service_type="Main Activity")
    renewal_details = t_ec_renewal_t2.objects.filter(application_status=None)
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    #cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'renewal.html',{'application_details':application_details,'app_hist_count':app_hist_count,'renewal_details':renewal_details,'service_details':service_details,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def ec_renewal_details(request):
    ec_reference_no = request.GET.get('ec_reference_no')
    service_code = 'REN'
    application_no = get_application_no(request, service_code, '10')
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no,service_type="Main Activity")
    ec_data = t_ec_industries_t11_ec_details.objects.filter(ec_reference_no=ec_reference_no,ec_type='Terms')
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    ec_application_details = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)
    if ec_application_details.exists():
        ec_details = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)    
        return render(request, 'renewal_details.html',{'application_details':application_details,'application_no':application_no, 'ec_details':ec_details,
                                                        'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})
    else:
        for ec_data in ec_data:
            t_ec_renewal_t2.objects.create(application_no=application_no, ec_reference_no=ec_reference_no,ec_heading=ec_data.ec_heading,ec_terms=ec_data.ec_terms)
        ec_details = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)    
        return render(request, 'renewal_details.html',{'application_details':application_details,'application_no':application_no, 'ec_details':ec_details,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village})
    

def save_general_water_requirement(request):
    data = dict()
    try:
        application_no = request.POST.get('general_water_application_no')
        energy_source = request.POST.get('energy_source')
        water_excavated_muck = request.POST.get('water_excavated_muck')
        water_required = request.POST.get('water_required')
        water_provided_by = request.POST.get('water_provided_by')
        water_raw_material_source = request.POST.get('water_raw_material_source')
        water_raw_material_qty_day = request.POST.get('#water_raw_material_qty_day')
        water_raw_material_recycle_day = request.POST.get('#water_raw_material_recycle_day')
        water_cleaning_source = request.POST.get('#water_cleaning_source')
        water_cleaning_qty_day = request.POST.get('#water_cleaning_qty_day')
        water_cleaning_recycle_day = request.POST.get('#water_cleaning_recycle_day')
        water_process_source = request.POST.get('#water_process_source')
        water_process_qty_day = request.POST.get('#water_process_qty_day')
        water_process_recycle_day = request.POST.get('#water_process_recycle_day')
        water_domestic_source = request.POST.get('#water_domestic_source')
        water_domestic_qty_day = request.POST.get('#water_domestic_qty_day')
        water_domestic_recycle_day = request.POST.get('#water_domestic_recycle_day')
        water_dust_compression_source = request.POST.get('#water_dust_compression_source')
        water_dust_compression_qty_day = request.POST.get('#water_dust_compression_qty_day')
        water_dust_compression_recycle_day = request.POST.get('#water_dust_compression_recycle_day')
        water_others_name = request.POST.get('#water_others_name')
        water_others_source = request.POST.get('#water_others_source')
        water_others_qty_day = request.POST.get('#water_others_qty_day')
        water_downstream_users = request.POST.get('#water_downstream_users')
        water_flow_rate_lean = request.POST.get('#water_flow_rate_lean')
        water_source_distance = request.POST.get('#water_source_distance')

        water_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

        water_details.update(energy_source=energy_source,
                             water_excavated_muck=water_excavated_muck,
                             water_required=water_required,
                             water_provide_by_iestate=water_provided_by,
                             water_raw_material_source=water_raw_material_source,
                             water_raw_material_qty_day=water_raw_material_qty_day,
                             water_raw_material_recycle_day=water_raw_material_recycle_day,
                             water_cleaning_source=water_cleaning_source,
                             water_cleaning_qty_day=water_cleaning_qty_day,
                             water_cleaning_recycle_day=water_cleaning_recycle_day,
                             water_process_source=water_process_source,
                             water_process_qty_day=water_process_qty_day,
                             water_process_recycle_day=water_process_recycle_day,
                             water_domestic_source=water_domestic_source,
                             water_domestic_qty_day=water_domestic_qty_day,
                             water_domestic_recycle_day=water_domestic_recycle_day,
                             water_dust_compression_source=water_dust_compression_source,
                             water_dust_compression_qty_day=water_dust_compression_qty_day,
                             water_dust_compression_recycle_day=water_dust_compression_recycle_day,
                             water_others_name=water_others_name,
                             water_others_source=water_others_source,
                             water_others_qty_day=water_others_qty_day,
                             water_downstream_users=water_downstream_users,
                             water_flow_rate_lean=water_flow_rate_lean,
                             water_source_distance=water_source_distance
                             )
        data['message'] = "success"
        return JsonResponse(data)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)
    
def submit_transmission_application(request):
    data = dict()
    try:
        application_no = request.POST.get('ea_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')

        application_details_main = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity').first()
        application_details_ancillary = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').first()
        anc_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()

        if application_details_main:
            service_id = application_details_main.service_id
            application_type = application_details_main.application_type
            anc_other_crushing_unit = application_details_main.anc_other_crushing_unit
            anc_other_surface_collection = application_details_main.anc_other_surface_collection
            anc_other_ground_water = application_details_main.anc_other_ground_water
            anc_other_mineral = application_details_main.anc_other_mineral
            anc_other_general = application_details_main.anc_other_general
            anc_other_transmission = application_details_main.anc_other_transmission

            if (anc_other_crushing_unit == 'Yes' or anc_other_surface_collection == 'Yes' or
                anc_other_ground_water == 'Yes' or anc_other_mineral == 'Yes' or
                anc_other_general == 'Yes' or anc_other_transmission == 'Yes') and anc_details == 0:
                data['message'] = "not submitted"
            else:
                t_application_history.objects.filter(application_no=application_no).update(action_date=timezone.now())

                if identifier == 'Ancillary':
                    application_details_ancillary.action_date = timezone.now()
                    application_details_ancillary.save()
                    t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())
                    data['message'] = "success"
                elif identifier in ('OC', 'NC'):
                    t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())
                    data['message'] = "success"
                else:
                    ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary', application_status='P').count()
                    if ancillary_count > 0:
                        data['message'] = "not submitted"
                    else:
                        application_details_main.action_date = timezone.now()
                        application_details_main.save()
                        t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())

                        fees_details = t_fees_schedule.objects.filter(service_id=service_id).first()
                        main_amount = fees_details.rate + fees_details.application_fee

                        ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()
                        if ancillary_application_details_count > 0:
                            ancillary_amount = fees_details.rate
                            total_amount = main_amount + ancillary_amount
                        else:
                            total_amount = main_amount

                        insert_app_payment_details(request, application_no, 'new_transmission_application', total_amount, application_type)
                        send_payment_mail(request.session['name'], request.session['email'], total_amount)
                        data['message'] = "success"

    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"

    return JsonResponse(data)


#General Application Details
def submit_general_application(request):
    data = dict()
    try:
        application_no = request.POST.get('general_disclaimer_application_no')
        identifier = request.POST.get('anc_identifier')
        disclaimer_identifier = request.POST.get('disclaimer_identifier')
        
        if disclaimer_identifier in ('OC', 'NC'):
            t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())
            data['message'] = "success"
        else:
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details_main = application_details.filter(service_type='Main Activity').first()
            application_details_ancillary = application_details.filter(service_type='Ancillary').first()
            anc_details = application_details.filter(service_type='Ancillary').count()

            if application_details_main:
                service_id = application_details_main.service_id
                application_type = application_details_main.application_type
                anc_other_crushing_unit = application_details_main.anc_other_crushing_unit
                anc_other_surface_collection = application_details_main.anc_other_surface_collection
                anc_other_ground_water = application_details_main.anc_other_ground_water
                anc_other_mineral = application_details_main.anc_other_mineral
                anc_other_general = application_details_main.anc_other_general
                anc_other_transmission = application_details_main.anc_other_transmission

                if (anc_other_crushing_unit == 'Yes' or anc_other_surface_collection == 'Yes' or
                    anc_other_ground_water == 'Yes' or anc_other_mineral == 'Yes' or
                    anc_other_general == 'Yes' or anc_other_transmission == 'Yes') and anc_details == 0:
                    data['message'] = "not submitted"
                else:
                    if identifier == 'Ancillary':
                        application_details_ancillary.action_date = timezone.now()
                        application_details_ancillary.save()
                        t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())
                        data['message'] = "success"
                    else:
                        ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary', application_status='P').count()
                        if ancillary_count > 0:
                            data['message'] = "not submitted"
                        else:
                            application_details_main.action_date = timezone.now()
                            application_details_main.save()
                            t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now())

                            fees_details = t_fees_schedule.objects.filter(service_id=service_id).first()
                            main_amount = fees_details.rate + fees_details.application_fee

                            ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()
                            if ancillary_application_details_count > 0:
                                ancillary_amount = fees_details.rate
                                total_amount = main_amount + ancillary_amount
                            else:
                                total_amount = main_amount
                            app_hist_details = t_application_history.objects.filter(application_no=application_no)
                            app_hist_details.update(remarks='Your Application Submitted')
                            app_hist_details.update(action_date=timezone.now())
                            insert_app_payment_details(request, application_no, 'new_general_application', total_amount, application_type)
                            send_payment_mail(request.session['name'], request.session['email'], total_amount)
                            data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"

    return JsonResponse(data)

def send_payment_mail(name, email_id, amount):
    subject = 'Application Submitted'
    message = "Dear " + name + " Your Application for ECS System Is Submitted. Please Make A Payment of " \
              + str(amount) + ""
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
def send_tor_payment_mail(name, email_id, amount):
    subject = 'Application Submitted'
    message = "Dear " + name + " Your TOR Application for ECS System Is Submitted. Please Make A Payment of " \
              + str(amount) + ""
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
#TOR
def tor_form(request):
    service_code = 'TOR'
    application_no = get_application_no(request, service_code, None)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    thromde = t_thromde_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()

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
        insert_app_payment_details(request, application_no, 'tor_form', 500, None)
        send_tor_payment_mail(request.session['name'], request.session['email'], 500)
        data['message'] = 'success'
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = 'failure'
    return JsonResponse(data)


def tor_list(request):
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no') 
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_details = t_workflow_dtls.objects.filter(
        application_status='A',application_no__contains='TOR'
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    )
    tor_application_count = t_workflow_dtls.objects.filter(
        application_status='A',application_no__contains='TOR'
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()
    service_details = t_service_master.objects.all()
    applicant_id = request.session.get('email', None)
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    response = render(request, 'tor/tor_list.html', {'tor_application_count':tor_application_count,'tor_details':tor_details,'service_details':service_details, 'app_hist_count':app_hist_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_tor_application_details(request):
    tor_application_no = request.GET.get('application_no')
    service_id = request.GET.get('service_id')
    app_det = t_ec_industries_t1_general.objects.filter(application_no=tor_application_no)
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
    tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_workflow_dtls.objects.filter(
        application_status='A',application_no__contains='TOR'
    ).exclude(
        application_no__in=Subquery(t1_general_subquery)
    ).count()
    for app_det in app_det:
        request.session['ca_auth'] = app_det.ca_authority
        request.session['colour_code'] = app_det.colour_code
        request.session['service_id'] = app_det.service_id
        request.session['broad_activity_code'] = app_det.broad_activity_code
        request.session['specific_activity_code'] = app_det.specific_activity_code
        request.session['category'] = app_det.category

    if service_id == '1':
        service_code = 'IEE'
        application_no = get_application_no(request, service_code, '1')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        final_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        return render(request, 'tor/industry_iee_form.html',{'thromde':thromde,'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'final_product':final_product,'ancillary_road':ancillary_road, 'power_line':power_line,
                                                        'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '2':
        service_code = 'ENE' 
        application_no = get_application_no(request, service_code, '2')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'energy_form.html',{'tor_application_count':tor_application_count,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '3':
        service_code = 'ROA'
        application_no = get_application_no(request, service_code, '3')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        drainage_type = t_ec_industries_t12_drainage_details.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'road_form.html',{'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'drainage_type':drainage_type, 'thromde':thromde})
    elif service_id == '4':
        service_code = 'TRA'
        application_no = get_application_no(request, service_code, '4')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'transmission_form.html',{'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '5':
        service_code = 'TOU' 
        application_no = get_application_no(request, service_code, '5')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'tourism_form.html',{'tor_application_count':tor_application_count,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '6':
        service_code = 'GWA' 
        application_no = get_application_no(request, service_code, '6')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'ground_water_form.html',{'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '7':
        service_code = 'FOR'
        application_no = get_application_no(request, service_code, '7')
        request.session['application_no'] = application_no
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'forest_form.html',{'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,'forest_produce':forest_produce,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                    'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '8':
        service_code = 'QUA' 
        application_no = get_application_no(request, service_code, '8')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'quarry_form.html',{'tor_application_count':tor_application_count,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})
    elif service_id == '9':
        service_code = 'GEN'
        application_no = get_application_no(request, service_code, '9')
        request.session['application_no'] = application_no
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'general_form.html',{'tor_application_count':tor_application_count,'tor_application_no':tor_application_no,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no,
                                                        'dzongkhag':dzongkhag,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'gewog':gewog, 'village':village, 'thromde':thromde})

def insert_app_payment_details(request,application_no, identifier,total_amount,application_type):
    if 'new' in identifier:
        payment_details = payment_details_master.objects.filter(payment_type='NEW')
        for pay_details in payment_details:      
            t_payment_details.objects.create(application_no=application_no,
                    application_type=application_type,
                    application_date=date.today(), 
                    proponent_name=request.session['name'],
                    amount=total_amount,
                    account_head_code=pay_details.account_head_code)
    elif 'tor' in identifier:
        payment_details = payment_details_master.objects.filter(payment_type='TOR')
        for pay_details in payment_details:      
            t_payment_details.objects.create(application_no=application_no,
                    application_type=application_type,
                    application_date=date.today(), 
                    proponent_name=request.session['name'],
                    amount=total_amount,
                    account_head_code=pay_details.account_head_code)
    return redirect(identifier)

def insert_payment_details(request,application_no,account_head, identifier):
    main_application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
    ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary').count()

    service_id = request.session['service_id']
    industry_classification = None
    main_amount = 0
    ancillary_amount = 0
    total_amount = 0
    power_generation = None
    road_length = None
    length_of_transmission = None
    total_area_acre = None

    for application in main_application_details:
        industry_classification = application.industry_classification
        power_generation = application.power_generation
        road_length = application.road_length

        if service_id == 1 and industry_classification == 'Small':
            fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
            for fees_details in fees_details:
                main_amount = fees_details.rate + fees_details.application_fee
        elif service_id == 1 and industry_classification == 'Medium':
            fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
            for fees_details in fees_details:
                main_amount = fees_details.rate + fees_details.application_fee
        elif service_id == 1 and industry_classification == 'Large':
            fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
            for fees_details in fees_details:
                main_amount = fees_details.rate + fees_details.application_fee
        elif service_id == 1 and industry_classification == 'Cottage':
            fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
            for fees_details in fees_details:
                main_amount = fees_details.rate + fees_details.application_fee
        elif service_id == 2:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = (fees_details.rate * power_generation) + fees_details.application_fee
        elif service_id == 3:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = (fees_details.rate * road_length) + fees_details.application_fee
        elif service_id == 4:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = (fees_details.rate * length_of_transmission) + fees_details.application_fee
        elif service_id == 5:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = fees_details.rate  + fees_details.application_fee
        elif service_id == 6:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = fees_details.rate  + fees_details.application_fee
        elif service_id == 7:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = (fees_details.rate * total_area_acre) + fees_details.application_fee
        elif service_id == 8:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = (fees_details.rate * total_area_acre) * fees_details.application_fee
        elif service_id == 9:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = fees_details.rate + fees_details.application_fee
        elif service_id == 10:
            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
            for fees_details in fees_details:
                main_amount = fees_details.rate + fees_details.application_fee

    if ancillary_application_details_count > 0:
        ancillary_application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        
        for ancillary_application in ancillary_application_details:
            industry_classification = ancillary_application.industry_classification
            power_generation = ancillary_application.power_generation
            road_length = ancillary_application.road_length
        
            if service_id == 1 and industry_classification == 'Small':
                fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
                for fees_details in fees_details:
                    ancillary_amount = fees_details.rate
            elif service_id == 1 and industry_classification == 'Medium':
                fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
                for fees_details in fees_details:
                    main_amount = fees_details.rate
            elif service_id == 1 and industry_classification == 'Large':
                fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
                for fees_details in fees_details:
                    ancillary_amount = fees_details.rate
            elif service_id == 1 and industry_classification == 'Cottage':
                fees_details = t_fees_schedule.objects.filter(service_id=service_id, parameter=industry_classification)
                for fees_details in fees_details:
                    ancillary_amount = fees_details.rate
            elif service_id == 2:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = (fees_details.rate * power_generation)
            elif service_id == 3:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = (fees_details.rate * road_length)
            elif service_id == 4:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = (fees_details.rate * length_of_transmission)
            elif service_id == 5:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = fees_details.rate
            elif service_id == 6:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = fees_details.rate
            elif service_id == 7:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = (fees_details.rate * total_area_acre)
            elif service_id == 8:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = (fees_details.rate * total_area_acre)
            elif service_id == 9:
                fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                for fees_details in fees_details:
                    ancillary_amount = fees_details.rate
        
        total_amount = main_amount + ancillary_amount
        print(total_amount)

        t_payment_details.objects.create(application_no=application_no,
            application_type= application.application_type,
            application_date=application.application_date, 
            proponent_name=application.applicant_name,
            amount=total_amount,
            account_head_code=account_head)
    return redirect(identifier)


def insert_renewal_payment_details(request,application_no,ec_reference_no,service_id,account_head, identifier):
    main_application_details = t_payment_details.objects.filter(ec_no=ec_reference_no,account_head_code='131370003')

    main_amount = 0
    amount = 0

    fees_details = t_fees_schedule.objects.filter(service_id=service_id)
    for main_application_details in main_application_details:
        amount = main_application_details.amount
    for fees_details in fees_details:
        main_amount = (fees_details.rate * amount)/100 + fees_details.application_fee
        
    for application in main_application_details:
        t_payment_details.objects.create(application_no=application_no,
            application_type= application.application_type,
            application_date=application.application_date, 
            proponent_name=application.applicant_name,
            amount=main_amount,
            account_head_code=account_head)
    return redirect(identifier)

# Road Application Details
def save_road_application(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        project_category = request.POST.get('project_category')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        cid = request.POST.get('cid')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        focal_person = request.POST.get('focal_person')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        
        bl_protected_area_name = request.POST.get('bl_protected_area_name')
        bl_protected_area_distance = request.POST.get('bl_protected_area_distance')
        bl_migratory_route_name = request.POST.get('bl_migratory_route_name')
        bl_migratory_route_distance = request.POST.get('bl_migratory_route_distance')
        bl_wetland_name = request.POST.get('bl_wetland_name')
        bl_wetland_distance = request.POST.get('bl_wetland_distance')
        bl_water_bodies_name = request.POST.get('bl_water_bodies_name')
        bl_water_bodies_distance = request.POST.get('bl_water_bodies_distance')
        bl_fmu_name = request.POST.get('bl_fmu_name')
        bl_fmu_distance = request.POST.get('bl_fmu_distance')
        bl_agricultural_name = request.POST.get('bl_agricultural_name')
        bl_agricultural_distance = request.POST.get('bl_agricultural_distance')
        bl_settlement_name = request.POST.get('bl_settlement_name')
        bl_settlement_distance = request.POST.get('bl_settlement_distance')
        bl_road_name = request.POST.get('bl_road_name')
        bl_road_distance = request.POST.get('bl_road_distance')
        bl_public_infra_name = request.POST.get('bl_public_infra_name')
        bl_public_infra_distance = request.POST.get('bl_public_infra_distance')
        bl_school_name = request.POST.get('bl_school_name')
        bl_school_distance = request.POST.get('bl_school_distance')
        bl_heritage_name = request.POST.get('bl_heritage_name')
        bl_heritage_distance = request.POST.get('bl_heritage_distance')
        bl_tourist_facility_name = request.POST.get('bl_tourist_facility_name')
        bl_tourist_facility_distance = request.POST.get('bl_tourist_facility_distance')
        bl_impt_installation_name = request.POST.get('bl_impt_installation_name')
        bl_impt_installation_distance = request.POST.get('bl_impt_installation_distance')
        bl_industries_name = request.POST.get('bl_industries_name')
        bl_industries_distance = request.POST.get('bl_industries_distance')
        bl_others = request.POST.get('bl_others')
        bl_others_name = request.POST.get('bl_others_name')
        bl_others_distance = request.POST.get('bl_others_distance')
        identifier = request.POST.get('identifier')
        ec_reference_no = request.POST.get('ec_reference_no')
        service_type = request.POST.get('service_type')
        tor_application_no = request.POST.get('tor_application_no')

        ca_auth = None
        if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier == 'NC' or identifier == 'OC':
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=tor_application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None

        if(identifier == 'NC'):
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(project_name=project_name, service_type=identifier)
        elif(identifier == 'OC'):
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(applicant_name=applicant_name, service_type=identifier)
        elif(identifier == 'DR'): # This is For Draft Applications
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            if application_details.exists():
                application_details.update(
                    application_type='New',
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    bl_protected_area_name=bl_protected_area_name,
                    bl_protected_area_distance=bl_protected_area_distance,
                    bl_migratory_route_name=bl_migratory_route_name,
                    bl_migratory_route_distance=bl_migratory_route_distance,
                    bl_wetland_name=bl_wetland_name,
                    bl_wetland_distance=bl_wetland_distance,
                    bl_water_bodies_name=bl_water_bodies_name,
                    bl_water_bodies_distance=bl_water_bodies_distance,
                    bl_fmu_name=bl_fmu_name,
                    bl_fmu_distance=bl_fmu_distance,
                    bl_agricultural_name=bl_agricultural_name,
                    bl_agricultural_distance=bl_agricultural_distance,
                    bl_settlement_name=bl_settlement_name,
                    bl_settlement_distance=bl_settlement_distance,
                    bl_road_name=bl_road_name,
                    bl_road_distance=bl_road_distance,
                    bl_public_infra_name=bl_public_infra_name,
                    bl_public_infra_distance=bl_public_infra_distance,
                    bl_school_name=bl_school_name,
                    bl_school_distance=bl_school_distance,
                    bl_heritage_name=bl_heritage_name,
                    bl_heritage_distance=bl_heritage_distance,
                    bl_tourist_facility_name=bl_tourist_facility_name,
                    bl_tourist_facility_distance=bl_tourist_facility_distance,
                    bl_impt_installation_name=bl_impt_installation_name,
                    bl_impt_installation_distance=bl_impt_installation_distance,
                    bl_industries_name=bl_industries_name,
                    bl_industries_distance=bl_industries_distance,
                    bl_others=bl_others,
                    bl_others_name=bl_others_name,
                    bl_others_distance=bl_others_distance,
                    )
            else:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=date.today(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=ca_auth,
                    applicant_id=request.session['email'],
                    colour_code=request.session['colour_code'],
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    bl_protected_area_name=bl_protected_area_name,
                    bl_protected_area_distance=bl_protected_area_distance,
                    bl_migratory_route_name=bl_migratory_route_name,
                    bl_migratory_route_distance=bl_migratory_route_distance,
                    bl_wetland_name=bl_wetland_name,
                    bl_wetland_distance=bl_wetland_distance,
                    bl_water_bodies_name=bl_water_bodies_name,
                    bl_water_bodies_distance=bl_water_bodies_distance,
                    bl_fmu_name=bl_fmu_name,
                    bl_fmu_distance=bl_fmu_distance,
                    bl_agricultural_name=bl_agricultural_name,
                    bl_agricultural_distance=bl_agricultural_distance,
                    bl_settlement_name=bl_settlement_name,
                    bl_settlement_distance=bl_settlement_distance,
                    bl_road_name=bl_road_name,
                    bl_road_distance=bl_road_distance,
                    bl_public_infra_name=bl_public_infra_name,
                    bl_public_infra_distance=bl_public_infra_distance,
                    bl_school_name=bl_school_name,
                    bl_school_distance=bl_school_distance,
                    bl_heritage_name=bl_heritage_name,
                    bl_heritage_distance=bl_heritage_distance,
                    bl_tourist_facility_name=bl_tourist_facility_name,
                    bl_tourist_facility_distance=bl_tourist_facility_distance,
                    bl_impt_installation_name=bl_impt_installation_name,
                    bl_impt_installation_distance=bl_impt_installation_distance,
                    bl_industries_name=bl_industries_name,
                    bl_industries_distance=bl_industries_distance,
                    bl_others=bl_others,
                    bl_others_name=bl_others_name,
                    bl_others_distance=bl_others_distance,
                    application_status='P',
                    service_id=request.session['service_id'],
                    broad_activity_code=request.session['broad_activity_code'] ,
                    specific_activity_code=request.session['specific_activity_code'],
                    category=request.session['category']
                    )
        elif identifier== 'TC' or identifier== 'PC' or identifier == 'LC' or identifier == 'CC':
            application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
            for app_det in application_details:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=date.today(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=app_det.ca_authority,
                    applicant_id=request.session['email'],
                    colour_code=app_det.colour_code,
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    bl_protected_area_name=bl_protected_area_name,
                    bl_protected_area_distance=bl_protected_area_distance,
                    bl_migratory_route_name=bl_migratory_route_name,
                    bl_migratory_route_distance=bl_migratory_route_distance,
                    bl_wetland_name=bl_wetland_name,
                    bl_wetland_distance=bl_wetland_distance,
                    bl_water_bodies_name=bl_water_bodies_name,
                    bl_water_bodies_distance=bl_water_bodies_distance,
                    bl_fmu_name=bl_fmu_name,
                    bl_fmu_distance=bl_fmu_distance,
                    bl_agricultural_name=bl_agricultural_name,
                    bl_agricultural_distance=bl_agricultural_distance,
                    bl_settlement_name=bl_settlement_name,
                    bl_settlement_distance=bl_settlement_distance,
                    bl_road_name=bl_road_name,
                    bl_road_distance=bl_road_distance,
                    bl_public_infra_name=bl_public_infra_name,
                    bl_public_infra_distance=bl_public_infra_distance,
                    bl_school_name=bl_school_name,
                    bl_school_distance=bl_school_distance,
                    bl_heritage_name=bl_heritage_name,
                    bl_heritage_distance=bl_heritage_distance,
                    bl_tourist_facility_name=bl_tourist_facility_name,
                    bl_tourist_facility_distance=bl_tourist_facility_distance,
                    bl_impt_installation_name=bl_impt_installation_name,
                    bl_impt_installation_distance=bl_impt_installation_distance,
                    bl_industries_name=bl_industries_name,
                    bl_industries_distance=bl_industries_distance,
                    bl_others=bl_others,
                    bl_others_name=bl_others_name,
                    bl_others_distance=bl_others_distance,
                    application_status='P',
                    service_id=app_det.service_id
                )
        else:
            t_ec_industries_t1_general.objects.create(
                application_no=application_no,
                application_date=date.today(),
                application_type='New',
                service_type=service_type,
                ca_authority=ca_auth,
                applicant_id=request.session['email'],
                colour_code=request.session['colour_code'],
                project_name=project_name,
                project_category=project_category,
                applicant_name=applicant_name,
                address=address,
                cid=cid,
                contact_no=contact_no,
                email=email,
                focal_person=focal_person,
                dzongkhag_throm=dzongkhag_throm,
                thromde_id=thromde_id,
                dzongkhag_code=dzongkhag_code,
                gewog_code=gewog_code,
                village_code=village_code,
                bl_protected_area_name=bl_protected_area_name,
                bl_protected_area_distance=bl_protected_area_distance,
                bl_migratory_route_name=bl_migratory_route_name,
                bl_migratory_route_distance=bl_migratory_route_distance,
                bl_wetland_name=bl_wetland_name,
                bl_wetland_distance=bl_wetland_distance,
                bl_water_bodies_name=bl_water_bodies_name,
                bl_water_bodies_distance=bl_water_bodies_distance,
                bl_fmu_name=bl_fmu_name,
                bl_fmu_distance=bl_fmu_distance,
                bl_agricultural_name=bl_agricultural_name,
                bl_agricultural_distance=bl_agricultural_distance,
                bl_settlement_name=bl_settlement_name,
                bl_settlement_distance=bl_settlement_distance,
                bl_road_name=bl_road_name,
                bl_road_distance=bl_road_distance,
                bl_public_infra_name=bl_public_infra_name,
                bl_public_infra_distance=bl_public_infra_distance,
                bl_school_name=bl_school_name,
                bl_school_distance=bl_school_distance,
                bl_heritage_name=bl_heritage_name,
                bl_heritage_distance=bl_heritage_distance,
                bl_tourist_facility_name=bl_tourist_facility_name,
                bl_tourist_facility_distance=bl_tourist_facility_distance,
                bl_impt_installation_name=bl_impt_installation_name,
                bl_impt_installation_distance=bl_impt_installation_distance,
                bl_industries_name=bl_industries_name,
                bl_industries_distance=bl_industries_distance,
                bl_others=bl_others,
                bl_others_name=bl_others_name,
                bl_others_distance=bl_others_distance,
                application_status='P',
                service_id=request.session['service_id'],
                broad_activity_code=request.session['broad_activity_code'] ,
                specific_activity_code=request.session['specific_activity_code'],
                category=request.session['category']
                )
        
        t_application_history.objects.create(
                                                application_no=application_no,
                                                application_date=date.today(),
                                                applicant_id=request.session['email'],
                                                ca_authority=ca_auth,
                                                service_id=request.session['service_id'], 
                                                application_status='P', 
                                                action_date=None, 
                                                actor_id=request.session['login_id'],
                                                actor_name=request.session['name'], 
                                                remarks=None, 
                                                status=None 
                                            )
        
        if identifier == 'NC' or identifier == 'OC':
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier')
        else:
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_auth,
                application_source='ECSS'
            )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

# General Application Details
def save_general_application(request):
    data = {}
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        project_category = request.POST.get('project_category')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        focal_person = request.POST.get('focal_person')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        industrial_area_acre = request.POST.get('industrial_area_acre')
        state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
        private_area_acre = request.POST.get('private_area_acre')
        others_area_acre = request.POST.get('others_area_acre')
        total_area_acre = request.POST.get('total_area_acre')
        project_site = request.POST.get('project_site')
        identifier = request.POST.get('identifier')
        tor_application_no = request.POST.get('tor_application_no')
        service_type = request.POST.get('service_type')
        ca_auth = None
        if tor_application_no is None:
            if identifier in ['DR', 'NC', 'OC']:
                if identifier == 'NC' or identifier == 'OC':
                    auth_filter = t_ec_industries_t1_general.objects.filter(application_no=application_no)
                    ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
                else:
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
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(application_no=tor_application_no)
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None

        print(ca_auth)

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

        with transaction.atomic():
            if identifier == 'NC':
                application_details.update(project_name=project_name, service_type=identifier)
            elif identifier == 'OC':
                application_details.update(applicant_name=applicant_name, application_type=identifier)
            elif identifier == 'DR':
                if application_details.exists():
                    application_details.update(
                        application_type='New',
                        project_name=project_name,
                        project_category=project_category,
                        applicant_name=applicant_name,
                        address=address,
                        contact_no=contact_no,
                        email=email,
                        location_name=project_site,
                        dzongkhag_throm=dzongkhag_throm,
                        thromde_id=thromde_id,
                        focal_person=focal_person,
                        dzongkhag_code=dzongkhag_code,
                        gewog_code=gewog_code,
                        village_code=village_code,
                        industrial_area_acre=industrial_area_acre,
                        state_reserve_forest_acre=state_reserve_forest_acre,
                        private_area_acre=private_area_acre,
                        others_area_acre=others_area_acre,
                        total_area_acre=total_area_acre,
                    )
                else:
                    t_ec_industries_t1_general.objects.create(
                        application_no=application_no,
                        application_date=timezone.now().date(),
                        application_type='New',
                        service_type=service_type,
                        ca_authority=ca_auth,
                        applicant_id=request.session['email'],
                        colour_code=request.session['colour_code'],
                        project_name=project_name,
                        project_category=project_category,
                        applicant_name=applicant_name,
                        address=address,
                        contact_no=contact_no,
                        email=email,
                        location_name=project_site,
                        dzongkhag_throm=dzongkhag_throm,
                        thromde_id=thromde_id,
                        focal_person=focal_person,
                        dzongkhag_code=dzongkhag_code,
                        gewog_code=gewog_code,
                        village_code=village_code,
                        industrial_area_acre=industrial_area_acre,
                        state_reserve_forest_acre=state_reserve_forest_acre,
                        private_area_acre=private_area_acre,
                        others_area_acre=others_area_acre,
                        total_area_acre=total_area_acre,
                        application_status='P',
                        service_id=request.session['service_id'],
                        broad_activity_code=request.session['broad_activity_code'],
                        specific_activity_code=request.session['specific_activity_code'],
                        category=request.session['category'],
                        application_source='ECSS',
                        tor_application_no=tor_application_no
                    )
            elif identifier in ['TC', 'PC', 'LC', 'CC']:
                for app_det in application_details:
                    t_ec_industries_t1_general.objects.create(
                        application_no=application_no,
                        application_date=timezone.now().date(),
                        application_type='New',
                        service_type=identifier,
                        ca_authority=app_det.ca_authority,
                        applicant_id=request.session['email'],
                        colour_code=app_det.colour_code,
                        project_name=project_name,
                        project_category=project_category,
                        applicant_name=applicant_name,
                        location_name=project_site,
                        address=address,
                        contact_no=contact_no,
                        email=email,
                        focal_person=focal_person,
                        dzongkhag_throm=dzongkhag_throm,
                        thromde_id=thromde_id,
                        dzongkhag_code=dzongkhag_code,
                        gewog_code=gewog_code,
                        village_code=village_code,
                        industrial_area_acre=industrial_area_acre,
                        state_reserve_forest_acre=state_reserve_forest_acre,
                        private_area_acre=private_area_acre,
                        others_area_acre=others_area_acre,
                        total_area_acre=total_area_acre,
                        application_status='P',
                        service_id=app_det.service_id,
                        application_source='ECSS'
                    )
            else:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=timezone.now().date(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=ca_auth,
                    applicant_id=request.session['email'],
                    colour_code=request.session['colour_code'],
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    contact_no=contact_no,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    location_name=project_site,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    application_status='P',
                    service_id=request.session['service_id'],
                    broad_activity_code=request.session['broad_activity_code'],
                    specific_activity_code=request.session['specific_activity_code'],
                    category=request.session['category'],
                    application_source='ECSS',
                    tor_application_no=tor_application_no
                )

            t_application_history.objects.create(
                application_no=application_no,
                application_date=timezone.now().date(),
                applicant_id=request.session['email'],
                ca_authority=ca_auth,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name']
            )
            if identifier == 'NC' or identifier == 'OC':
                work_details = t_workflow_dtls.objects.filter(application_no=application_no)
                work_details.update(application_status='P',
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    assigned_role_id='2',
                    assigned_role_name='Verifier')
            else:
                t_workflow_dtls.objects.create(
                    application_no=application_no,
                    service_id=request.session['service_id'],
                    application_status='P',
                    actor_id=request.session['login_id'],
                    actor_name=request.session['name'],
                    assigned_role_id='2',
                    assigned_role_name='Verifier',
                    ca_authority=ca_auth,
                    application_source='ECSS'
                )
        data['message'] = 'success'
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = 'failure'
    return JsonResponse(data)


# Forest Application Details
def save_forest_application(request):
    data = {}
    try:
        identifier = request.POST.get('identifier')
        # Fetch ca_auth for non-draft applications
        tor_application_no = request.POST.get('tor_application_no')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code, gewog_code, village_code, thromde_id = None, None, None, request.POST.get('thromde_id')
        else:
            dzongkhag_code, gewog_code, village_code, thromde_id = request.POST.get('dzongkhag'), request.POST.get('gewog'), request.POST.get('vil_chiwog'), None
        # Application details
        ca_auth = None
        if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=request.POST.get('dzo_throm') if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier == 'NC' or identifier == 'OC':
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=request.POST.get('application_no')
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=tor_application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        application_details = {
            'application_no':request.POST.get('application_no'),
            'application_date':timezone.now().date(),
            'application_type':'New',
            'project_name': request.POST.get('project_name'),
            'project_category': request.POST.get('project_category'),
            'applicant_name': request.POST.get('applicant_name'),
            'address': request.POST.get('address'),
            'cid': request.POST.get('cid'),
            'contact_no': request.POST.get('contact_no'),
            'email': request.POST.get('email'),
            'focal_person': request.POST.get('focal_person'),
            'dzongkhag_throm': request.POST.get('dzongkhag_throm'),
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'thromde_id': thromde_id,        
            'industrial_area_acre': request.POST.get('industrial_area_acre'),
            'state_reserve_forest_acre': request.POST.get('state_reserve_forest_acre'),
            'private_area_acre': request.POST.get('private_area_acre'),
            'others_area_acre': request.POST.get('others_area_acre'),
            'total_area_acre': request.POST.get('total_area_acre'),
            'max_evacuation_depth': request.POST.get('max_evacuation_depth'),
            'terrain_elevation': request.POST.get('terrain_elevation'),
            'terrain_slope': request.POST.get('terrain_slope'),
            'service_type': request.POST.get('service_type'),
            'ca_authority':ca_auth,
            'applicant_id':request.session['email'],
            'colour_code':request.session['colour_code'],
        }

        with transaction.atomic():
            if identifier == 'NC' or identifier == 'OC':
                application_instance = t_ec_industries_t1_general.objects.filter(application_no=request.POST.get('application_no')).first()
                if application_instance:
                    application_instance.project_name = request.POST.get('project_name') if identifier == 'NC' else application_instance.project_name
                    application_instance.applicant_name = request.POST.get('applicant_name') if identifier == 'OC' else application_instance.applicant_name
                    application_instance.service_type=identifier
                    application_instance.save()
                else:
                    raise ValueError("Application does not exist.")
            elif identifier == 'DR':
                application_instance, created = t_ec_industries_t1_general.objects.get_or_create(application_no=request.POST.get('application_no'))
                if not created:
                    for field, value in application_details.items():
                        setattr(application_instance, field, value)
                    application_instance.save()
                else:
                    raise ValueError("Application does not exist.")
            elif identifier in ['TC', 'PC', 'LC', 'CC']:
                ec_reference_no = request.POST.get('ec_reference_no')
                for app_det in t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no):
                    t_ec_industries_t1_general.objects.create(application_no=request.POST.get('application_no'), ec_reference_no=ec_reference_no, **application_details)
            else:
                t_ec_industries_t1_general.objects.create(**application_details)

            t_application_history.objects.create(
                application_no=request.POST.get('application_no'),
                application_date=timezone.now().date(),
                applicant_id=request.session['email'],
                ca_authority=ca_auth,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name']
            )

        if identifier == 'NC' or identifier == 'OC':
            work_details = t_workflow_dtls.objects.filter(application_no=request.POST.get('application_no'))
            work_details.update(application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier')
        else:
            t_workflow_dtls.objects.create(
                application_no=request.POST.get('application_no'),
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_auth,
                application_source='ECSS'
            )

        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


def submit_forest_application(request):
    data = {}
    try:
        application_no = request.POST.get('forest_disclaimer_application_no')
        identifier = request.POST.get('anc_identifier')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details_main = application_details.filter(service_type='Main Activity').first()
        application_details_ancillary = application_details.filter(service_type='Ancillary').first()
        anc_details = application_details.filter(service_type='Ancillary').count()

        if application_details_main:
            service_id = application_details_main.service_id
            application_type = application_details_main.application_type
            anc_other_crushing_unit = application_details_main.anc_other_crushing_unit
            anc_other_surface_collection = application_details_main.anc_other_surface_collection
            anc_other_ground_water = application_details_main.anc_other_ground_water
            anc_other_mineral = application_details_main.anc_other_mineral
            anc_other_general = application_details_main.anc_other_general
            anc_other_transmission = application_details_main.anc_other_transmission

            ancillary_conditions = (
                anc_other_crushing_unit == 'Yes' or
                anc_other_surface_collection == 'Yes' or
                anc_other_ground_water == 'Yes' or
                anc_other_mineral == 'Yes' or
                anc_other_general == 'Yes' or
                anc_other_transmission == 'Yes'
            )

            if ancillary_conditions and anc_details == 0:
                data['message'] = "not submitted"
            else:
                if identifier == 'Ancillary':
                    application_details_ancillary.action_date = timezone.now()
                    application_details_ancillary.save()
                elif identifier in ('OC', 'NC'):
                    pass  # Nothing to do for 'OC' and 'NC'
                else:
                    ancillary_count = t_ec_industries_t1_general.objects.filter(
                        application_no=application_no,
                        service_type='Ancillary',
                        application_status='P'
                    ).count()
                    if ancillary_count > 0:
                        data['message'] = "not submitted"
                    else:
                        application_details_main.action_date = timezone.now()
                        application_details_main.save()

                        fees_details = t_fees_schedule.objects.filter(service_id=service_id).first()
                        main_amount = fees_details.rate + fees_details.application_fee

                        ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(
                            application_no=application_no,
                            service_type='Ancillary'
                        ).count()

                        if ancillary_application_details_count > 0:
                            ancillary_amount = fees_details.rate
                            total_amount = main_amount + ancillary_amount
                        else:
                            total_amount = main_amount
                        
                        app_hist_details = t_application_history.objects.filter(application_no=application_no)
                        app_hist_details.update(remarks='Your Application Submitted')
                        app_hist_details.update(action_date=timezone.now())

                        insert_app_payment_details(
                            request,
                            application_no,
                            'new_forest_application',
                            total_amount,
                            application_type
                        )
                        send_payment_mail(request.session['name'], request.session['email'], total_amount)

                data['message'] = "success"

    except Exception as e:
        print(e)
        data['message'] = "failure"

    return JsonResponse(data)

# ground water
def save_ground_water_application(request):
    data = {}
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        project_category = request.POST.get('project_category')
        applicant_name = request.POST.get('applicant_name')
        application_type = request.POST.get('application_type')
        address = request.POST.get('address')
        cid = request.POST.get('cid')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        focal_person = request.POST.get('focal_person')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        industrial_area_acre = request.POST.get('industrial_area_acre')
        state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
        private_area_acre = request.POST.get('private_area_acre')
        others_area_acre = request.POST.get('others_area_acre')
        total_area_acre = request.POST.get('total_area_acre')
        max_evacuation_depth = request.POST.get('max_evacuation_depth')
        land_form = request.POST.get('land_form')
        terrain_elevation = request.POST.get('terrain_elevation')
        terrain_slope = request.POST.get('terrain_slope')
        identifier = request.POST.get('identifier')
        ec_reference_no = request.POST.get('ec_reference_no')
        tor_application_no = request.POST.get('tor_application_no')
        service_type = request.POST.get('service_type')

        ca_auth = None

        if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier == 'NC' or identifier == 'OC':
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=tor_application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None

        application_data = {
            'project_name': project_name,
            'project_category': project_category,
            'applicant_name': applicant_name,
            'application_type': 'New' if identifier == 'DR' else application_type,
            'address': address,
            'cid': cid,
            'contact_no': contact_no,
            'email': email,
            'focal_person': focal_person,
            'dzongkhag_code': dzongkhag_code,
            'gewog_code': gewog_code,
            'village_code': village_code,
            'industrial_area_acre': industrial_area_acre,
            'state_reserve_forest_acre': state_reserve_forest_acre,
            'private_area_acre': private_area_acre,
            'others_area_acre': others_area_acre,
            'total_area_acre': total_area_acre,
            'max_evacuation_depth': max_evacuation_depth,
            'land_form': land_form,
            'terrain_elevation': terrain_elevation,
            'terrain_slope': terrain_slope,
            'dzongkhag_throm':dzongkhag_throm,
            'thromde_id':thromde_id
        }

        if identifier == 'NC':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(project_name=project_name, service_type=identifier)
        elif identifier == 'OC':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(applicant_name=applicant_name, service_type=identifier)
        else:
            application_data.update({
                'application_no': application_no,
                'application_date': timezone.now().date(),
                'service_type': service_type,
                'ca_authority': ca_auth,
                'applicant_id': request.session['email'],
                'colour_code': request.session['colour_code'],
                'application_status': 'P',
                'service_id': request.session['service_id'],
                'broad_activity_code': request.session['broad_activity_code'],
                'specific_activity_code': request.session['specific_activity_code'],
                'category': request.session['category'],
            })

            if identifier == 'DR':
                t_ec_industries_t1_general.objects.update_or_create(application_no=application_no, defaults=application_data)
            elif identifier in ['TC', 'PC', 'LC', 'CC']:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                for app_detail in application_details:
                    t_ec_industries_t1_general.objects.create(**application_data, service_id=app_detail.service_id)
            else:
                t_ec_industries_t1_general.objects.create(**application_data)

        t_application_history.objects.create(
            application_no=application_no,
            application_date=timezone.now().date(),
            applicant_id=request.session['email'],
            ca_authority=ca_auth,
            service_id=request.session['service_id'],
            application_status='P',
            action_date=None,
            actor_id=request.session['login_id'],
            actor_name=request.session['name'],
            remarks=None,
            status=None
        )

        if identifier == 'NC' or identifier == 'OC':
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier')
        else:
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_auth,
                application_source='ECSS'
            )

        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


def save_ground_water_requirement(request):
    data = dict()
    try:
        application_no = request.POST.get('ground_water_application_no')
        energy_source = request.POST.get('energy_source')
        water_source_ph =  request.POST.get('water_source_ph')
        water_source_turbidity = request.POST.get('water_source_turbidity')
        water_source_conductivity = request.POST.get('water_source_conductivity')
        water_source_ecoli = request.POST.get('water_source_ecoli')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(energy_source=energy_source,
                                    water_source_ph=water_source_ph,
                                    water_source_turbidity=water_source_turbidity,
                                    water_source_conductivity=water_source_conductivity,
                                    water_source_ecoli=water_source_ecoli
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def submit_ground_water_application(request):
    data = {}
    try:
        application_no = request.POST.get('ea_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')
        main_amount = 0
        ancillary_amount = 0
        total_amount = 0
        application_type = None
        anc_types = ['anc_other_crushing_unit', 'anc_other_surface_collection', 'anc_other_ground_water', 'anc_other_mineral', 'anc_other_general', 'anc_other_transmission']

        main_activity_form = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity').first()
        ancillary_form_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()
        app_hist_details = t_application_history.objects.filter(application_no=application_no)
        app_hist_details.update(action_date=timezone.now().date())

        if main_activity_form:
            service_id = main_activity_form.service_id
            application_type = main_activity_form.application_type
            ancillary_values = [getattr(main_activity_form, anc_type) for anc_type in anc_types]

        if any(ancillary_values):
            if ancillary_form_count == 0:
                data['message'] = "not submitted"
            else:
                main_activity_form.update(action_date=timezone.now().date())
                if identifier == 'Ancillary':
                    ancillary_form = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary')
                    ancillary_form.update(action_date=timezone.now().date())
                    workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                    workflow_dtls.update(action_date=timezone.now().date())
                    data['message'] = "success"
                else:
                    if identifier in ['OC', 'NC']:
                        workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                        workflow_dtls.update(action_date=timezone.now().date())
                        data['message'] = "success"
                    else:
                        ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary', application_status='P').count()
                        if ancillary_count > 0 or ancillary_count < 0:
                            data['message'] = "not submitted"
                        else:
                            main_activity_form.update(action_date=timezone.now().date())
                            workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                            workflow_dtls.update(action_date=timezone.now().date())
                            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                            for fee_detail in fees_details:
                                main_amount = int(fee_detail.rate) + int(fee_detail.application_fee)
                                ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()
                                if ancillary_application_details_count > 0:
                                    ancillary_amount = fee_detail.rate
                                    total_amount = main_amount + ancillary_amount
                                else:
                                    total_amount = main_amount
                                insert_app_payment_details(request, application_no, 'new_ground_water_application', total_amount, application_type)
                                send_payment_mail(request.session['name'], request.session['email'], total_amount)
                            data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


def save_alternative_analysis(request):
    data = dict()
    try:
        application_no = request.POST.get('alternative_analysis_application_no')
        alternative_surface_water = request.POST.get('alternative_surface_water') 
        alternative_capital_expenditure = request.POST.get('alternative_capital_expenditure')
        alternative_adequate_justification = request.POST.get('alternative_adequate_justification')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(alternative_surface_water=alternative_surface_water, 
                                    alternative_capital_expenditure=alternative_capital_expenditure,
                                    alternative_adequate_justification=alternative_adequate_justification,
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)
# Quarry Application Details
def save_quarry_application(request):
    data = {}
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        project_category = request.POST.get('project_category')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        cid = request.POST.get('cid')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        focal_person = request.POST.get('focal_person')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        focal_person = request.POST.get('focal_person')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        industrial_area_acre = request.POST.get('industrial_area_acre')
        state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
        private_area_acre = request.POST.get('private_area_acre')
        others_area_acre = request.POST.get('others_area_acre')
        total_area_acre = request.POST.get('total_area_acre')
        actual_mineable_area = request.POST.get('actual_mineable_area')
        green_belt_area = request.POST.get('green_belt_area')
        terrain_elevation = request.POST.get('terrain_elevation')
        terrain_slope = request.POST.get('terrain_slope')
        identifier = request.POST.get('identifier')
        ec_reference_no = request.POST.get('ec_reference_no')
        tor_application_no = request.POST.get('tor_application_no')
        service_type = request.POST.get('service_type')

        ca_auth = None
        if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier == 'NC' or identifier == 'OC':
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=tor_application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        if identifier == 'NC':
            application_details.update(project_name=project_name,service_type=identifier)
        elif identifier == 'OC':
            application_details.update(applicant_name=applicant_name, service_type=identifier)
        elif identifier == 'DR':
            if not application_details.exists():
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=timezone.now().date(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=ca_auth,
                    applicant_id=request.session['email'],
                    colour_code=request.session['colour_code'],
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    actual_mineable_area=actual_mineable_area,
                    green_area_acre=green_belt_area,
                    terrain_elevation=terrain_elevation,
                    terrain_slope=terrain_slope,
                    application_status='P',
                    service_id=request.session['service_id'],
                    broad_activity_code=request.session['broad_activity_code'],
                    specific_activity_code=request.session['specific_activity_code'],
                    category=request.session['category']
                )
        elif identifier in ['TC', 'PC', 'LC', 'CC']:
            for app_det in application_details.filter(ec_reference_no=ec_reference_no):
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=timezone.now().date(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=app_det.ca_authority,
                    applicant_id=request.session['email'],
                    colour_code=app_det.colour_code,
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    actual_mineable_area=actual_mineable_area,
                    green_area_acre=green_belt_area,
                    terrain_elevation=terrain_elevation,
                    terrain_slope=terrain_slope,
                    application_status='P',
                    service_id=app_det.service_id
                )
        else:
            t_ec_industries_t1_general.objects.create(
                application_no=application_no,
                application_date=timezone.now().date(),
                application_type='New',
                service_type=service_type,
                ca_authority=ca_auth,
                applicant_id=request.session['email'],
                colour_code=request.session['colour_code'],
                project_name=project_name,
                project_category=project_category,
                applicant_name=applicant_name,
                address=address,
                cid=cid,
                dzongkhag_throm=dzongkhag_throm,
                thromde_id=thromde_id,
                contact_no=contact_no,
                email=email,
                focal_person=focal_person,
                dzongkhag_code=dzongkhag_code,
                gewog_code=gewog_code,
                village_code=village_code,
                industrial_area_acre=industrial_area_acre,
                state_reserve_forest_acre=state_reserve_forest_acre,
                private_area_acre=private_area_acre,
                others_area_acre=others_area_acre,
                total_area_acre=total_area_acre,
                actual_mineable_area=actual_mineable_area,
                green_area_acre=green_belt_area,
                terrain_elevation=terrain_elevation,
                terrain_slope=terrain_slope,
                application_status='P',
                service_id=request.session['service_id'],
                broad_activity_code=request.session['broad_activity_code'],
                specific_activity_code=request.session['specific_activity_code'],
                category=request.session['category']
            )

        t_application_history.objects.create(
            application_no=application_no,
            application_date=timezone.now().date(),
            applicant_id=request.session['email'],
            ca_authority=ca_auth,
            service_id=request.session['service_id'],
            application_status='P',
            action_date=None,
            actor_id=request.session['login_id'],
            actor_name=request.session['name'],
            remarks=None,
            status=None
        )

        if identifier == 'NC' or identifier == 'OC':
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier')
        else:
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_auth,
                application_source='ECSS'
            )

        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


def submit_quarry_application(request):
    data = {}
    try:
        application_no = request.POST.get('ea_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')

        # Update application history action_date
        t_application_history.objects.filter(application_no=application_no).update(action_date=timezone.now().date())

        main_activity_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity')
        ancillary_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()

        anc_other_fields = ['anc_other_crushing_unit', 'anc_other_surface_collection', 'anc_other_ground_water', 'anc_other_mineral', 'anc_other_general', 'anc_other_transmission']
        application_type = None

        for main_activity_detail in main_activity_details:
            service_id = main_activity_detail.service_id
            application_type = main_activity_detail.application_type
            anc_other_values = [getattr(main_activity_detail, field) for field in anc_other_fields]

        if any(anc_other_value == 'Yes' for anc_other_value in anc_other_values):
            if ancillary_details_count == 0:
                data['message'] = "not submitted"
            else:
                # Update action_date for the main activity
                main_activity_details.update(action_date=timezone.now().date())
                if identifier == 'Ancillary':
                    # Update action_date for the ancillary details
                    t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').update(action_date=timezone.now().date())
                    # Update action_date for the workflow details
                    t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now().date())
                    data['message'] = "success"
                else:
                    if identifier in ['OC', 'NC']:
                        # Update action_date for the workflow details
                        t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now().date())
                        data['message'] = "success"
                    else:
                        ancillary_pending_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary', application_status='P').count()
                        if ancillary_pending_count > 0:
                            data['message'] = "not submitted"
                        else:
                            # Update action_date for the main activity
                            main_activity_details.update(action_date=timezone.now().date())
                            # Update action_date for the workflow details
                            t_workflow_dtls.objects.filter(application_no=application_no).update(action_date=timezone.now().date())

                            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                            main_amount = sum(int(fees.rate) + int(fees.application_fee) for fees in fees_details)
                            ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary').count()

                            if ancillary_application_details_count > 0:
                                ancillary_amount = sum(fees.rate for fees in fees_details)
                                total_amount = main_amount + ancillary_amount
                            else:
                                total_amount = main_amount

                            insert_app_payment_details(request, application_no, 'new_quarry_application', total_amount, application_type)
                            send_payment_mail(request.session['name'], request.session['email'], total_amount)

                            data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)



# Road Application Details
def road_project_details(request):
    data = dict()
    try:
        application_no = request.POST.get('project_details_one_application_no')
        project_objective = request.POST.get('project_objective')
        proposed_route_reason = request.POST.get('proposed_route_reason')
        project_cost = request.POST.get('project_cost')
        project_duration = request.POST.get('project_duration')
        road_length = request.POST.get('road_length')
        starting_point = request.POST.get('starting_point')
        terminating_point = request.POST.get('terminating_point')
        road_row_width = request.POST.get('road_row_width')
        formation_width = request.POST.get('formation_width')
        pavement_width = request.POST.get('pavement_width')
        pavement_material = request.POST.get('pavement_material')
        extracted_material_vol = request.POST.get('extracted_material_vol')
        maximum_road_gradient = request.POST.get('maximum_road_gradient')
        cross_drains = request.POST.get('cross_drains')
        box_culvert = request.POST.get('box_culvert')
        bridges = request.POST.get('bridges')
        bridge_width = request.POST.get('bridge_width')
        bridge_length = request.POST.get('bridge_length')
        side_drain = request.POST.get('side_drain')
        side_drain_length = request.POST.get('side_drain_length')
        side_drain_length = request.POST.get('side_drain_length')
        side_drain_dimensions = request.POST.get('side_drain_dimensions')
        box_drain_length = request.POST.get('box_drain_length')
        

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(project_objective=project_objective,
                                   proposed_route_reason=proposed_route_reason,
                                   project_cost=project_cost,
                                   project_duration=project_duration,
                                    road_length =road_length, 
                                    starting_point =starting_point,
                                    terminating_point =terminating_point,
                                    road_row_width=road_row_width, 
                                    formation_width=formation_width, 
                                    pavement_width=pavement_width, 
                                    pavement_material=pavement_material, 
                                    extracted_material_vol=extracted_material_vol, 
                                    maximum_road_gradient=maximum_road_gradient, 
                                    cross_drains=cross_drains,
                                    box_culvert=box_culvert, 
                                    bridges=bridges, 
                                    bridge_width=bridge_width, 
                                    bridge_length=bridge_length, 
                                    side_drain=side_drain, 
                                    side_drain_length=side_drain_length, 
                                    side_drain_dimensions=side_drain_dimensions, 
                                    box_drain_length=box_drain_length 
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def road_project_details_one(request):
    data = dict()
    try:
        application_no = request.POST.get('project_details_application_no')
        blast_required = request.POST.get('blast_required') 
        blast_type = request.POST.get('blast_type')
        blast_qty = request.POST.get('blast_qty')
        blast_location = request.POST.get('blast_location')
        blast_frequency_time = request.POST.get('blast_frequency_time')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        application_details.update(blast_required=blast_required, 
                                    blast_type=blast_type,
                                    blast_qty=blast_qty,
                                    blast_location=blast_location,
                                    blast_frequency_time=blast_frequency_time
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def road_project_details_two(request):
    data = dict()
    try:
        application_no = request.POST.get('project_details_two_application_no')
        water_excavated_muck = request.POST.get('water_excavated_muck')
        water_required = request.POST.get('water_required')
        water_provided_by = request.POST.get('water_provided_by')
        water_raw_material_source = request.POST.get('water_raw_material_source')
        water_raw_material_qty_day = request.POST.get('#water_raw_material_qty_day')
        water_raw_material_recycle_day = request.POST.get('#water_raw_material_recycle_day')
        water_cleaning_source = request.POST.get('#water_cleaning_source')
        water_cleaning_qty_day = request.POST.get('#water_cleaning_qty_day')
        water_cleaning_recycle_day = request.POST.get('#water_cleaning_recycle_day')
        water_process_source = request.POST.get('#water_process_source')
        water_process_qty_day = request.POST.get('#water_process_qty_day')
        water_process_recycle_day = request.POST.get('#water_process_recycle_day')
        water_domestic_source = request.POST.get('#water_domestic_source')
        water_domestic_qty_day = request.POST.get('#water_domestic_qty_day')
        water_domestic_recycle_day = request.POST.get('#water_domestic_recycle_day')
        water_dust_compression_source = request.POST.get('#water_dust_compression_source')
        water_dust_compression_qty_day = request.POST.get('#water_dust_compression_qty_day')
        water_dust_compression_recycle_day = request.POST.get('#water_dust_compression_recycle_day')
        water_others_name = request.POST.get('#water_others_name')
        water_others_source = request.POST.get('#water_others_source')
        water_others_qty_day = request.POST.get('#water_others_qty_day')

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

        application_details.update(water_excavated_muck=water_excavated_muck,
                             water_required=water_required,
                             water_provide_by_iestate=water_provided_by,
                             water_raw_material_source=water_raw_material_source,
                             water_raw_material_qty_day=water_raw_material_qty_day,
                             water_raw_material_recycle_day=water_raw_material_recycle_day,
                             water_cleaning_source=water_cleaning_source,
                             water_cleaning_qty_day=water_cleaning_qty_day,
                             water_cleaning_recycle_day=water_cleaning_recycle_day,
                             water_process_source=water_process_source,
                             water_process_qty_day=water_process_qty_day,
                             water_process_recycle_day=water_process_recycle_day,
                             water_domestic_source=water_domestic_source,
                             water_domestic_qty_day=water_domestic_qty_day,
                             water_domestic_recycle_day=water_domestic_recycle_day,
                             water_dust_compression_source=water_dust_compression_source,
                             water_dust_compression_qty_day=water_dust_compression_qty_day,
                             water_dust_compression_recycle_day=water_dust_compression_recycle_day,
                             water_others_name=water_others_name,
                             water_others_source=water_others_source,
                             water_others_qty_day=water_others_qty_day
                             )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def submit_road_application(request):
    data = dict()
    try:
        application_no = request.POST.get('road_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')
        app_hist_details = t_application_history.objects.filter(application_no=application_no)
        app_hist_details.update(action_date=date.today())
        if identifier == 'OC' or identifier == 'NC':
            workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
            workflow_dtls.update(action_date=date.today())
            data['message'] = "success"
        else:
            ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary', application_status='P').count()
            if(ancillary_count > 0):
                data['message'] = "not submitted"
            else:
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
                application_details.update(action_date=date.today())
                workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                workflow_dtls.update(action_date=date.today())
                insert_payment_details(request, application_no, 'submit_road_application')
                data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

#Energy Application Details
def save_energy_application(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        cid = request.POST.get('cid')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        focal_person = request.POST.get('focal_person')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        industrial_area_acre = request.POST.get('industrial_area_acre')
        state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
        private_area_acre = request.POST.get('private_area_acre')
        others_area_acre = request.POST.get('others_area_acre')
        total_area_acre = request.POST.get('total_area_acre')
        identifier = request.POST.get('identifier')
        ec_reference_no = request.POST.get('ec_reference_no')
        tor_application_no = request.POST.get('tor_application_no')
        service_type = request.POST.get('service_type')
        
        ca_auth = None
        if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier == 'NC' or identifier == 'OC':
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=tor_application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None

        if(identifier == 'NC'):
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(project_name=project_name, service_type=identifier)
        elif(identifier == 'OC'):
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(applicant_name=applicant_name, service_type=identifier)
        elif(identifier == 'DR'): # This is For Draft Applications
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            if application_details.exists():
                application_details.update(
                    application_type='New',
                    project_name=project_name,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,

                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    )
            else:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=date.today(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=ca_auth,
                    applicant_id=request.session['email'],
                    colour_code=request.session['colour_code'],
                    project_name=project_name,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    application_status='P',
                    service_id=request.session['service_id'],
                    broad_activity_code=request.session['broad_activity_code'] ,
                    specific_activity_code=request.session['specific_activity_code'],
                    category=request.session['category']
                    )
        elif identifier== 'TC' or identifier== 'PC' or identifier == 'LC' or identifier == 'CC':
            application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
            for app_det in application_details:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=date.today(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=app_det.ca_authority,
                    applicant_id=request.session['email'],
                    colour_code=app_det.colour_code,
                    project_name=project_name,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    application_status='P',
                    service_id=app_det.service_id
                )
        else:
            t_ec_industries_t1_general.objects.create(
                application_no=application_no,
                application_date=date.today(),
                application_type='New',
                service_type=service_type,
                ca_authority=ca_auth,
                applicant_id=request.session['email'],
                colour_code=request.session['colour_code'],
                project_name=project_name,
                applicant_name=applicant_name,
                address=address,
                cid=cid,
                contact_no=contact_no,
                email=email,
                focal_person=focal_person,
                dzongkhag_code=dzongkhag_code,
                gewog_code=gewog_code,
                village_code=village_code,
                industrial_area_acre=industrial_area_acre,
                state_reserve_forest_acre=state_reserve_forest_acre,
                private_area_acre=private_area_acre,
                others_area_acre=others_area_acre,
                total_area_acre=total_area_acre,
                application_status='P',
                service_id=request.session['service_id'],
                broad_activity_code=request.session['broad_activity_code'] ,
                specific_activity_code=request.session['specific_activity_code'],
                category=request.session['category']
                )
            
        t_application_history.objects.create(
                                                application_no=application_no,
                                                application_date=date.today(),
                                                applicant_id=request.session['email'],
                                                ca_authority=ca_auth,
                                                service_id=request.session['service_id'], 
                                                application_status='P', 
                                                action_date=None, 
                                                actor_id=request.session['login_id'],
                                                actor_name=request.session['name'], 
                                                remarks=None, 
                                                status=None 
                                            )
        
        if identifier == 'NC' or identifier == 'OC':
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier')
        else:
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_auth,
                application_source='ECSS'
            )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def submit_energy_application(request):
    data = dict()
    try:
        application_no = request.POST.get('ea_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')
        service_id = None
        main_amount = 0 
        ancillary_amount = 0
        total_amount = 0
        application_type = None
        anc_other_crushing_unit = None
        anc_other_surface_collection = None
        anc_other_ground_water = None
        anc_other_mineral = None
        anc_other_general = None
        anc_other_transmission = None

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
        anc_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary').count()
        app_hist_details = t_application_history.objects.filter(application_no=application_no)
        app_hist_details.update(action_date=date.today())
        
        for application_details in application_details:
            service_id = application_details.service_id
            application_type = application_details.application_type
            anc_other_crushing_unit = application_details.anc_other_crushing_unit
            anc_other_surface_collection = application_details.anc_other_surface_collection
            anc_other_ground_water = application_details.anc_other_ground_water
            anc_other_mineral = application_details.anc_other_mineral
            anc_other_general = application_details.anc_other_general
            anc_other_transmission = application_details.anc_other_transmission

        if anc_other_crushing_unit == 'Yes' or anc_other_surface_collection == 'Yes' or anc_other_ground_water == 'Yes' or anc_other_mineral == 'Yes' or anc_other_general == 'Yes' or anc_other_transmission == 'Yes':
            if anc_details == 0:
                data['message'] = "not submitted"
            else:
                application_details.update(action_date=date.today())
                if identifier == 'Ancillary':
                    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary')
                    application_details.update(action_date=date.today())
                    workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                    workflow_dtls.update(action_date=date.today())
                    data['message'] = "success"
                else:
                    if identifier == 'OC' or identifier == 'NC':
                        workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                        workflow_dtls.update(action_date=date.today())
                        data['message'] = "success"
                    else:
                        ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary', application_status='P').count()
                        if(ancillary_count > 0):
                            data['message'] = "not submitted"
                        elif(ancillary_count < 0):
                            data['message'] = "not submitted"
                        else:
                            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity')
                            application_details.update(action_date=date.today())
                            workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                            workflow_dtls.update(action_date=date.today())
                            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                            for fees_details in fees_details:
                                main_amount = int(fees_details.rate)
                                main_amount += int(fees_details.application_fee)
                                ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary').count()
                                if ancillary_application_details_count > 0:
                                    fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                                    for fees_details in fees_details:
                                        ancillary_amount = fees_details.rate
                                        total_amount = main_amount + ancillary_amount
                                else:
                                    total_amount=main_amount
                                insert_app_payment_details(request, application_no, 'submit_energy_application ',total_amount,application_type)
                                send_payment_mail(request.session['name'],request.session['email'], total_amount)
                            data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


def save_tourism_application(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        project_name = request.POST.get('project_name')
        project_category = request.POST.get('project_category')
        applicant_name = request.POST.get('applicant_name')
        address = request.POST.get('address')
        cid = request.POST.get('cid')
        contact_no = request.POST.get('contact_no')
        email = request.POST.get('email')
        dzongkhag_throm = request.POST.get('dzongkhag_throm')
        focal_person = request.POST.get('focal_person')
        if dzongkhag_throm == 'Thromde':
            dzongkhag_code = None
            gewog_code = None
            village_code = None
            thromde_id = request.POST.get('thromde_id')
        else:
            dzongkhag_code = request.POST.get('dzongkhag')
            gewog_code = request.POST.get('gewog')
            village_code = request.POST.get('vil_chiwog')
            thromde_id = None
        industrial_area_acre = request.POST.get('industrial_area_acre')
        state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
        private_area_acre = request.POST.get('private_area_acre')
        others_area_acre = request.POST.get('others_area_acre')
        total_area_acre = request.POST.get('total_area_acre')
        identifier = request.POST.get('identifier')
        tor_application_no = request.POST.get('tor_application_no')
        service_type = request.POST.get('service_type')
        

        ca_auth = None
        if identifier != 'DR' or identifier != 'NC' or identifier != 'OC' and tor_application_no == None:
            auth_filter = t_competant_authority_master.objects.filter(
                competent_authority=request.session['ca_auth'],
                dzongkhag_code_id=dzongkhag_code if request.session['ca_auth'] in ['DEC', 'THROMDE'] else None
            )
            ca_auth = auth_filter.first().competent_authority_id if auth_filter.exists() else None
        elif identifier == 'NC' or identifier == 'OC':
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        else:
            auth_filter = t_ec_industries_t1_general.objects.filter(
                application_no=tor_application_no
            )
            ca_auth = auth_filter.first().ca_authority if auth_filter.exists() else None
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

        if(identifier == 'NC'):
            application_details.update(project_name=project_name)
        elif(identifier == 'OC'):
            application_details.update(applicant_name=applicant_name)
        elif(identifier == 'DR'): # This is For Draft Applications
            if application_details.exists():
                application_details.update(
                    application_type='New',
                        project_name=project_name,
                        project_category=project_category,
                        applicant_name=applicant_name,
                        address=address,
                        cid=cid,
                        contact_no=contact_no,
                        email=email,
                        focal_person=focal_person,
                        dzongkhag_throm=dzongkhag_throm,
                        thromde_id=thromde_id,
                        dzongkhag_code=dzongkhag_code,
                        gewog_code=gewog_code,
                        village_code=village_code,
                        industrial_area_acre=industrial_area_acre,
                        state_reserve_forest_acre=state_reserve_forest_acre,
                        private_area_acre=private_area_acre,
                        others_area_acre=others_area_acre,
                        total_area_acre=total_area_acre
                    )
            else:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=date.today(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=ca_auth,
                    applicant_id=request.session['email'],
                    colour_code=request.session['colour_code'],
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    application_status='P',
                    service_id=request.session['service_id'],
                    broad_activity_code=request.session['broad_activity_code'] ,
                    specific_activity_code=request.session['specific_activity_code'],
                    category=request.session['category']
                    )
        elif identifier== 'TC' or identifier== 'PC' or identifier == 'LC' or identifier == 'CC':
            for app_det in application_details:
                t_ec_industries_t1_general.objects.create(
                    application_no=application_no,
                    application_date=date.today(),
                    application_type='New',
                    service_type=service_type,
                    ca_authority=app_det.ca_authority,
                    applicant_id=request.session['email'],
                    colour_code=app_det.colour_code,
                    project_name=project_name,
                    project_category=project_category,
                    applicant_name=applicant_name,
                    address=address,
                    cid=cid,
                    contact_no=contact_no,
                    email=email,
                    focal_person=focal_person,
                    dzongkhag_throm=dzongkhag_throm,
                    thromde_id=thromde_id,
                    dzongkhag_code=dzongkhag_code,
                    gewog_code=gewog_code,
                    village_code=village_code,
                    industrial_area_acre=industrial_area_acre,
                    state_reserve_forest_acre=state_reserve_forest_acre,
                    private_area_acre=private_area_acre,
                    others_area_acre=others_area_acre,
                    total_area_acre=total_area_acre,
                    application_status='P',
                    service_id=app_det.service_id
                )
        else:
            t_ec_industries_t1_general.objects.create(
                application_no=application_no,
                application_date=date.today(),
                application_type='New',
                service_type=service_type,
                ca_authority=ca_auth,
                applicant_id=request.session['email'],
                colour_code=request.session['colour_code'],
                project_name=project_name,
                project_category=project_category,
                applicant_name=applicant_name,
                address=address,
                cid=cid,
                contact_no=contact_no,
                email=email,
                focal_person=focal_person,
                dzongkhag_throm=dzongkhag_throm,
                thromde_id=thromde_id,
                dzongkhag_code=dzongkhag_code,
                gewog_code=gewog_code,
                village_code=village_code,
                industrial_area_acre=industrial_area_acre,
                state_reserve_forest_acre=state_reserve_forest_acre,
                private_area_acre=private_area_acre,
                others_area_acre=others_area_acre,
                total_area_acre=total_area_acre,
                application_status='P',
                service_id=request.session['service_id'],
                broad_activity_code=request.session['broad_activity_code'] ,
                specific_activity_code=request.session['specific_activity_code'],
                category=request.session['category']
                )
        
        t_application_history.objects.create(
                                                application_no=application_no,
                                                application_date=date.today(),
                                                applicant_id=request.session['email'],
                                                ca_authority=ca_auth,
                                                service_id=request.session['service_id'], 
                                                application_status='P', 
                                                action_date=None, 
                                                actor_id=request.session['login_id'],
                                                actor_name=request.session['name'], 
                                                remarks=None, 
                                                status=None 
                                            )
        
        if identifier == 'NC' or identifier == 'OC':
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier')
        else:
            t_workflow_dtls.objects.create(
                application_no=application_no,
                service_id=request.session['service_id'],
                application_status='P',
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_role_id='2',
                assigned_role_name='Verifier',
                ca_authority=ca_auth,
                application_source='ECSS'
            )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def save_tourism_sewerage_details(request):
    data = dict()
    try:
        application_no = request.POST.get('sewerage_application_no')
        waste_water_bod_source = request.POST.get('waste_water_bod_source')
        waste_water_bod_discharge = request.POST.get('waste_water_bod_discharge')
        waste_water_bod_treatment = request.POST.get('waste_water_bod_treatment')
        waste_water_tss_source = request.POST.get('waste_water_tss_source')
        waste_water_tss_discharge = request.POST.get('waste_water_tss_discharge')
        waste_water_tss_treatment = request.POST.get('waste_water_tss_treatment')
        waste_water_fecal_source = request.POST.get('waste_water_fecal_source')
        waste_water_fecal_discharge = request.POST.get('waste_water_fecal_discharge')
        waste_water_fecal_treatment = request.POST.get('waste_water_fecal_treatment')
        waste_water_ph_source = request.POST.get('waste_water_ph_source')
        waste_water_ph_discharge = request.POST.get('waste_water_ph_discharge')
        waste_water_ph_treatment = request.POST.get('waste_water_ph_treatment')
        waste_water_cod_source = request.POST.get('waste_water_cod_source')
        waste_water_cod_discharge = request.POST.get('waste_water_cod_discharge')
        waste_water_cod_treatment = request.POST.get('waste_water_cod_treatment') 
        sewerage_quantity = request.POST.get('sewerage_quantity')
        capacity_stp = request.POST.get('capacity_stp')
        dimension_stp = request.POST.get('dimension_stp')
        sludge_quantity_mgt_plan = request.POST.get('sludge_quantity_mgt_plan')
        sewerage_water_source_distance = request.POST.get('sewerage_water_source_distance')
        

        sewerage_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        sewerage_details.update(waste_water_bod_source =waste_water_bod_source,
                                 waste_water_bod_discharge =waste_water_bod_discharge,
                                 waste_water_bod_treatment =waste_water_bod_treatment,
                                 waste_water_tss_source =waste_water_tss_source,
                                 waste_water_tss_discharge =waste_water_tss_discharge,
                                 waste_water_tss_treatment =waste_water_tss_treatment,
                                 waste_water_fecal_source =waste_water_fecal_source,
                                 waste_water_fecal_discharge =waste_water_fecal_discharge,
                                 waste_water_fecal_treatment =waste_water_fecal_treatment,
                                 waste_water_ph_source =waste_water_ph_source,
                                 waste_water_ph_discharge =waste_water_ph_discharge,
                                 waste_water_ph_treatment =waste_water_ph_treatment,
                                 waste_water_cod_source =waste_water_cod_source,
                                 waste_water_cod_discharge =waste_water_cod_discharge,
                                 waste_water_cod_treatment =waste_water_cod_treatment, 
                                 sewerage_quantity =sewerage_quantity,
                                 capacity_stp =capacity_stp,
                                 dimension_stp =dimension_stp,
                                 sludge_quantity_mgt_plan =sludge_quantity_mgt_plan,
                                 sewerage_water_source_distance =sewerage_water_source_distance
                                )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def submit_tourism_application(request):
    data = dict()
    try:
        application_no = request.POST.get('ea_disclaimer_application_no')
        identifier = request.POST.get('disc_identifier')
        service_id = None
        main_amount = 0 
        ancillary_amount = 0
        total_amount = 0
        application_type = None
        anc_other_crushing_unit = None
        anc_other_surface_collection = None
        anc_other_ground_water = None
        anc_other_mineral = None
        anc_other_general = None
        anc_other_transmission = None

        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
        anc_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary').count()
        app_hist_details = t_application_history.objects.filter(application_no=application_no)
        app_hist_details.update(action_date=date.today())

        for application_details in application_details:
            service_id = application_details.service_id
            application_type = application_details.application_type
            anc_other_crushing_unit = application_details.anc_other_crushing_unit
            anc_other_surface_collection = application_details.anc_other_surface_collection
            anc_other_ground_water = application_details.anc_other_ground_water
            anc_other_mineral = application_details.anc_other_mineral
            anc_other_general = application_details.anc_other_general
            anc_other_transmission = application_details.anc_other_transmission

        if anc_other_crushing_unit == 'Yes' or anc_other_surface_collection == 'Yes' or anc_other_ground_water == 'Yes' or anc_other_mineral == 'Yes' or anc_other_general == 'Yes' or anc_other_transmission == 'Yes':
            if anc_details == 0:
                data['message'] = "not submitted"
            else:
                application_details.update(action_date=date.today())
                if identifier == 'Ancillary':
                    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Ancillary')
                    application_details.update(action_date=date.today())
                    workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                    workflow_dtls.update(action_date=date.today())
                    data['message'] = "success"
                else:
                    if identifier == 'OC' or identifier == 'NC':
                        workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                        workflow_dtls.update(action_date=date.today())
                        data['message'] = "success"
                    else:
                        ancillary_count = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary', application_status='P').count()
                        if(ancillary_count > 0):
                            data['message'] = "not submitted"
                        elif(ancillary_count < 0):
                            data['message'] = "not submitted"
                        else:
                            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity')
                            application_details.update(action_date=date.today())
                            workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
                            workflow_dtls.update(action_date=date.today())
                            fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                            for fees_details in fees_details:
                                main_amount = int(fees_details.rate)
                                main_amount += int(fees_details.application_fee)
                                ancillary_application_details_count = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary').count()
                                if ancillary_application_details_count > 0:
                                    fees_details = t_fees_schedule.objects.filter(service_id=service_id)
                                    for fees_details in fees_details:
                                        ancillary_amount = fees_details.rate
                                        total_amount = main_amount + ancillary_amount
                                else:
                                    total_amount=main_amount
                                insert_app_payment_details(request, application_no, 'submit_tourism_application ',total_amount,application_type)
                                send_payment_mail(request.session['name'],request.session['email'], total_amount)
                            data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


#Other Modifications
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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
    identifier = request.GET.get('identifier')

    if identifier == 'NC' or 'OC':
        app_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
        for app_details in app_details:
            service_id = app_details.service_id
            app_no = app_details.application_no
            application_source = app_details.application_source
            request.session['service_id'] = service_id
            if service_id == 1:
                if application_source == 'IBLS':
                    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                    forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                    products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                    hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                    dzongkhag = t_dzongkhag_master.objects.all()
                    gewog = t_gewog_master.objects.all()
                    village = t_village_master.objects.all()
                    application_no = get_application_no(request, 'IEA', '1')
                    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                    return render(request, 'other_modification/ea_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                                'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                                'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
                else:
                    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                    machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                    project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                    raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                    ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                    power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                    forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                    products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                    hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                    dzongkhag = t_dzongkhag_master.objects.all()
                    gewog = t_gewog_master.objects.all()
                    village = t_village_master.objects.all()
                    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                    return render(request, 'other_modification/iee_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                                'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 
                                                                'village':village,'application_no':application_no,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 2:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/energy_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog,
                                                            'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 3:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/road_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog,
                                                            'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 4:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/transmission_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog,
                                                            'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 5:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/tourism_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 6:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/ground_water_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 7:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/forest_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'identifier':identifier,'application_no':app_no})
            elif service_id == 8:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/quarry_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
            elif service_id == 9:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=app_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=app_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=app_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=app_no)
                ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=app_no)
                power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=app_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=app_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=app_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=app_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'other_modification/general_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'identifier':identifier, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'application_no':app_no})
        else:
            app_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
            for app_details in app_details:
                service_id = app_details.service_id
                app_no = app_details.application_no
                application_source = app_details.application_source
                request.session['service_id'] = service_id
                if service_id == 1:
                    if application_source == 'IBLS':
                        return redirect(new_ea_application)
                    else:
                        return redirect(new_iee_application)
                elif service_id == 2:
                    return redirect(new_energy_application)
                elif service_id == 3:
                    return redirect(new_road_application)
                elif service_id == 4:
                    return redirect(new_transmission_application)
                elif service_id == 5:
                    return redirect(new_tourism_application)
                elif service_id == 6:
                    return redirect(new_ground_water_application)
                elif service_id == 7:
                    return redirect(new_forestry_application)
                elif service_id == 8:
                    return redirect(new_quarry_application)
                else:
                    return redirect(new_general_application)
                        
    
# Draft Application Details
def draft_application_list(request):
    assigned_user_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    application_details = t_ec_industries_t1_general.objects.filter(application_status='P',service_type='Main Activity',action_date__isnull=True)
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    
    response = render(request, 'draft/application_list.html',{'application_details':application_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'service_details':service_details, 'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_draft_application_details(request):
    application_no = request.GET.get('application_no')
    request.session['application_no'] = application_no
    service_id = request.GET.get('service_id')
    application_source = request.GET.get('application_source')
    status = None

    if service_id == '1':
        if application_source == 'IBLS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            thromde = t_thromde_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'draft/ea_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials, 'status':status,
                                                        'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details,'ancillary_details':ancillary_details,'service_id':service_id})
        else:
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            thromde = t_thromde_master.objects.all()
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'draft/iee_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                        'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '2':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/energy_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog,
                                                     'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '3':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/road_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '4':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/transmission_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '5':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/tourism_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '6':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/ground_water_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '7':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/forest_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '8':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['login_id']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/quarry_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    elif service_id == '9':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
        project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
        raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
        power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
        forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
        products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
        app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
        cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
        return render(request, 'draft/general_application_details.html',{'thromde':thromde,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'service_id':service_id})
    
def update_draft_application(request):
    application_no = request.POST.get(application_no)
    service_id = request.POST.get('service_id')
    application_no = request.POST.get('application_no')
    project_name = request.POST.get('project_name')
    project_category = request.POST.get('project_category')
    applicant_name = request.POST.get('applicant_name')
    application_type = request.POST.get('application_type')
    address = request.POST.get('address')
    cid = request.POST.get('cid')
    contact_no = request.POST.get('contact_no')
    email = request.POST.get('email')
    focal_person = request.POST.get('focal_person')
    industry_type = request.POST.get('industry_type')
    establishment_type = request.POST.get('establishment_type')
    industry_classification = request.POST.get('industry_classification')
    dzongkhag_code = request.POST.get('dzo_throm')
    gewog_code = request.POST.get('gewog')
    village_code = request.POST.get('vil_chiwog')
    location_name = request.POST.get('location_name')
    industrial_area_acre = request.POST.get('industrial_area_acre')
    state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
    private_area_acre = request.POST.get('private_area_acre')
    others_area_acre = request.POST.get('others_area_acre')
    total_area_acre = request.POST.get('total_area_acre')
    green_area_acre = request.POST.get('green_area_acre')
    production_process_flow = request.POST.get('production_process_flow')
    project_objective = request.POST.get('project_objective')
    project_no_of_workers = request.POST.get('project_no_of_workers')
    project_cost = request.POST.get('project_cost')
    project_duration = request.POST.get('project_duration')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

    if service_id == '1':
        application_details.update(
            application_no=application_no,
            application_type='New',
            project_name=project_name,
            project_category=project_category,
            applicant_name=applicant_name,
            address=address,
            cid=cid,
            contact_no=contact_no,
            email=email,
            focal_person=focal_person,
            industry_type=industry_type,
            establishment_type=establishment_type,
            industry_classification=industry_classification,
            dzongkhag_code=dzongkhag_code,
            gewog_code=gewog_code,
            village_code=village_code,
            location_name=location_name,
            industrial_area_acre=industrial_area_acre,
            state_reserve_forest_acre=state_reserve_forest_acre,
            private_area_acre=private_area_acre,
            others_area_acre=others_area_acre,
            total_area_acre=total_area_acre,
            green_area_acre=green_area_acre,
            production_process_flow=production_process_flow,
            project_objective=project_objective,
            project_no_of_workers=project_no_of_workers,
            project_cost=project_cost,
            project_duration=project_duration,
            )

def submit_renew_application(request):
    data = dict()
    try:
        auth = None
        total_amount = 0
        amount = 0
        ec_reference_no = request.POST.get('ec_reference_no')
        application_no = request.POST.get('application_no')
        initiatives_undertaken = request.POST.get('initiatives_undertaken')
        remarks = request.POST.get('initiatives_undertaken_remarks')

        application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
        renew_details = t_ec_renewal_t1.objects.filter(ec_reference_no=ec_reference_no)
        renew_details_one = t_ec_renewal_t2.objects.filter(ec_reference_no=ec_reference_no)

        renew_details.update(application_status='P',action_date=date.today(),submission_date=date.today())
        renew_details_one.update(application_status='P',action_date=date.today())

        main_application_details = t_payment_details.objects.filter(ec_no=ec_reference_no,account_head_code='131370003')

        for application_details in application_details:
            auth = application_details.ca_authority
            t_ec_renewal_t1.objects.create(application_no=application_no,ec_reference_no=ec_reference_no,proponent_name=application_details.applicant_name,address=application_details.address,initiatives_undertaken=initiatives_undertaken,remarks=remarks,submission_date=date.today(),application_status='P')
            t_workflow_dtls.objects.create(application_no=application_no, 
                                            service_id='10',
                                            application_status='P',
                                            action_date=date.today(),
                                            actor_id=request.session['login_id'],
                                            actor_name=request.session['name'],
                                            assigned_role_id='2',
                                            assigned_role_name='Verifier',
                                            ca_authority=auth,
                                            application_source='ECSS'
                                        )
        fees_details = t_fees_schedule.objects.filter(service_id='10')
        for main_application_details in main_application_details:
            amount = main_application_details.amount
        for fees_details in fees_details:
            total_amount = (fees_details.rate * amount)/100 + fees_details.application_fee

        payment_details = payment_details_master.objects.filter(payment_type='RENEW')
        for pay_details in payment_details:      
            t_payment_details.objects.create(application_no=application_no,
                application_type= 'Renewal',
                application_date=date.today(), 
                proponent_name=request.session['name'],
                amount=total_amount,
                account_head_code=pay_details.account_head_code)
        send_payment_mail(request.session['name'],request.session['email'], total_amount)
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


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

        tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A', application_no__contains='TOR'
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

        report_list = t_report_submission_t1.objects.filter(ca_authority=ca_authority).exclude(report_status='Pending').order_by('submission_date')

        v_application_count = t_workflow_dtls.objects.filter(
            assigned_role_id='2', assigned_role_name='Verifier', ca_authority=ca_authority
        ).count()

        ec_renewal_count = t_ec_industries_t1_general.objects.filter(
            ca_authority=ca_authority, application_status='A', ec_expiry_date__lt=expiry_date_threshold
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
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    
    v_application_count = 0  # Provide default value for v_application_count
    ec_renewal_count = 0  # Provide default value for ec_renewal_count

    if request.session.get('ca_authority') is not None:
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=30)
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
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
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
    login_id = request.session['login_id']

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

# Renewal Details
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
    tor_application_count = t_workflow_dtls.objects.filter(
            application_status='A',application_no__contains='TOR'
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


def view_print_details(request):
    # Retrieve the 'ec_reference_no' parameter from the GET request
    ec_reference_no = request.GET.get('ec_reference_no')
    
    # Retrieve t_ec_industries_t1_general objects with ec_reference_no=ec_reference_no and service_type="Main Activity"
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no, service_type="Main Activity")
    
    # Retrieve t_ec_industries_t11_ec_details objects with ec_reference_no=ec_reference_no
    ec_details = t_ec_industries_t11_ec_details.objects.filter(ec_reference_no=ec_reference_no)
    
    # Count the number of t_application_history objects related to the logged-in user
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
    
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


# dumpyard Details
def add_dumpyard_details(request):
    application_no = request.POST.get('application_no')
    dumpyard_number = request.POST.get('dumpyard_number')
    dumpyard_capacity = request.POST.get('dumpyard_capacity')
    dumpyard_area = request.POST.get('dumpyard_area')
    dumpyard_location =request.POST.get('dumpyard_location')

    t_ec_industries_t13_dumpyard.objects.create(application_no=application_no,dumpyard_number=dumpyard_number,dumpyard_capacity=dumpyard_capacity,dumpyard_area=dumpyard_area,dumpyard_location=dumpyard_location)

    dumpyard_details = t_ec_industries_t13_dumpyard.objects.filter(application_no=application_no).order_by('record_id')
    return render(request, 'dump_yard_details.html', {'dumpyard_details':dumpyard_details})

def update_dumpyard_details(request):
    record_id = request.POST.get('record_id')
    print(record_id)
    application_no = request.POST.get('application_no')
    dumpyard_number = request.POST.get('dumpyard_number')
    dumpyard_capacity = request.POST.get('dumpyard_capacity')
    dumpyard_area = request.POST.get('dumpyard_area')
    dumpyard_location = request.POST.get('dumpyard_location')

    dumpyard = t_ec_industries_t13_dumpyard.objects.filter(record_id=record_id)
    dumpyard.update(dumpyard_number=dumpyard_number,dumpyard_capacity=dumpyard_capacity,dumpyard_area=dumpyard_area,dumpyard_location=dumpyard_location)

    dumpyard_details = t_ec_industries_t13_dumpyard.objects.filter(application_no=application_no).order_by('record_id')
    return render(request, 'dump_yard_details.html', {'dumpyard_details':dumpyard_details})

def delete_dumpyard_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    dumpyard = t_ec_industries_t13_dumpyard.objects.filter(record_id=record_id)
    dumpyard.delete()
    dumpyard_details = t_ec_industries_t13_dumpyard.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'dump_yard_details.html', {'dumpyard_details': dumpyard_details})

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