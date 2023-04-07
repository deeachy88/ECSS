from django.http import JsonResponse
from django.shortcuts import redirect, render
from ecs_admin.views import bsic_master
from proponent.models import t_ec_industries_t10_hazardous_chemicals, t_ec_industries_t11_ec_details, t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, t_ec_industries_t9_products_by_products, t_fines_penalties, t_payment_details, t_workflow_dtls
from ecs_admin.models import t_bsic_code, t_dzongkhag_master, t_file_attachment, t_gewog_master, t_role_master, t_service_master, t_thromde_master, t_user_master, t_village_master
from ecs_main.models import t_inspection_monitoring_t1
from django.utils import timezone
from datetime import date
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage

# Create your views here.
def verify_application_list(request):
    application_list = t_workflow_dtls.objects.filter(application_status='P', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='DEC', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='AL', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all()
    return render(request, 'application_list.html',{'application_list':application_list, 'service_details':service_details, 'payment_details':payment_details})

def client_application_list(request):
    application_list = t_workflow_dtls.objects.filter(application_status='ALR', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='ALA', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='EATC', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='RS', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='LU', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all()
    return render(request, 'application_list.html',{'application_list':application_list, 'service_details':service_details, 'payment_details':payment_details})

def reviewer_application_list(request):
    application_list = t_workflow_dtls.objects.filter(application_status='R', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='ALS', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='FEATC', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='RSS', action_date__isnull=False) | t_workflow_dtls.objects.filter(application_status='LUS', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all()
    return render(request, 'application_list.html', {'application_list':application_list, 'service_details':service_details, 'payment_details':payment_details})

def payment_list(request):
    payment_details = t_payment_details.objects.filter(transaction_no__isnull=True)
    return render(request, 'payment_details.html', {'payment_details': payment_details})

def view_application_details(request):
    application_no = request.POST.get('application_no')
    service_id = request.POST.get('service_id')
    application_source = request.POST.get('application_source')
    status = None

    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    for work_details in workflow_details:
        status = work_details.application_status
        
    if service_id == '1':
        if application_source == 'IBLS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.all()
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
            project_product = t_ec_industries_t4_project_product.objects.all()
            raw_materials = t_ec_industries_t5_raw_materials.objects.all()
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
            power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
            forest_produce = t_ec_industries_t8_forest_produce
            products_by_products = t_ec_industries_t9_products_by_products
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            
            return render(request, 'draft/ea_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials, 'status':status,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                        'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details,'ancillary_details':ancillary_details})
        else:
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.all()
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
            project_product = t_ec_industries_t4_project_product.objects.all()
            raw_materials = t_ec_industries_t5_raw_materials.objects.all()
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
            power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
            forest_produce = t_ec_industries_t8_forest_produce
            products_by_products = t_ec_industries_t9_products_by_products
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            
            return render(request, 'draft/iee_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                        'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                        'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '2':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/energy_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog,
                                                     'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '3':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/road_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '4':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/transmission_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '5':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/tourism_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '6':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/ground_water_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '7':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/forest_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '8':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/quarry_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '9':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        ec_details = t_ec_industries_t11_ec_details.objects.all()
        
        return render(request, 'draft/general_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details})
    elif service_id == '10':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        reviewer_list = t_user_master.objects.filter(role_id='3')
        return render(request, 'renewal_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals, 'reviewer_list':reviewer_list})
    elif service_id == '11':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        reviewer_list = t_user_master.objects.filter(role_id='3')
        return render(request, 'name_change_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals, 'reviewer_list':reviewer_list})
    elif service_id == '12':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        reviewer_list = t_user_master.objects.filter(role_id='3')
        return render(request, 'ownwership_change_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,
                                                     'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals, 'reviewer_list':reviewer_list})

    elif service_id == '0':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        reviewer_list = t_user_master.objects.filter(role_id='3')

        return render(request, 'tor_form_details.html', {'application_no':application_no,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'reviewer_list':reviewer_list})

def forward_application(request):
    application_no = request.POST.get('application_no')
    forwardTo = request.POST.get('forwardTo')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(assigned_to=forwardTo, assigned_date=date.today(), assigned_by=request.session['email'])
    user_details = t_user_master.objects.filter(login_id=forwardTo)
    for users in user_details:
        role_id = users.role_id
        role_details = t_role_master.objects.filter(role_id=role_id)
        for role in role_details:
            role_name = role.role_name
        workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
        workflow_details.update(assigned_user_id=forwardTo)
        workflow_details.update(assigned_role_id=role_id)
        workflow_details.update(assigned_role_name=role_name)
        workflow_details.update(action_date=date.today())
        workflow_details.update(actor_id=request.session['login_id'])
        workflow_details.update(actor_name=request.session['name'])
    return redirect(verify_application_list)

def approve_application(request):
    application_no = request.POST.get('application_no')
    ec_no = get_ec_no(request)

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(ec_no=ec_no, ec_approve_date=date.today(),application_status='A')
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
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
            for email_id in application_details:
                emailId = email_id.email
                send_ec_approve_email(ec_no, emailId, application_no, service_name)
    return redirect(verify_application_list)

def resubmit_application(request):
    application_no = request.POST.get('application_no')
    remarks = request.POST.get('resubmit_remarks')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
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
    payment_details = t_payment_details.objects.filter(application_no=application_no)
    payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                               instrument_no=instrument_no, transaction_date=transaction_date)
    return redirect(payment_list)

def get_ec_no(request):
    agency_code = request.session['agency_code']
    last_ec_no = t_ec_industries_t1_general.objects.aggregate(Max('ec_reference_no'))
    lastECNo = last_ec_no['ec_reference_no__max']
    if not lastECNo:
        year = timezone.now().year
        newECNo = agency_code + "-" + "EC" + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastECNo)[13:17]
        substring = int(substring) + 1
        ecNo = str(substring).zfill(4)
        year = timezone.now().year
        newECNo = agency_code + "-" + "EC" + "-" + str(year) + "-" + ecNo
    return newECNo

def send_ec_approve_email(ec_no, email, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " And EC Clearance No is:" + ec_no + \
              " Please Make Payment. Visit The Nearest EC Office For Payment " 
    recipient_list = [email]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)
    
def send_ec_resubmission_email(email, application_no, service_name):
    subject = 'APPLICATION RESUBMISSION'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Having" \
              " Application No " + application_no + " Has Been Sent For Resubmission. Please Check The Application And Resubmit It."
    recipient_list = [email]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)
    
def save_eatc_attachment(request):
    data = dict()
    eatc_attach = request.FILES['eatc_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + eatc_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EATC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, eatc_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/EATC" + "/" + file_name
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

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def forward_application(request):
    application_no = request.POST.get('application_no')
    identifier = request.POST.get('identifier')

    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    if identifier == 'R':
        forward_to = request.POST.get('forward_to')
        workflow_details.update(application_status='R', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=forward_to, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(reviewer_application_list)
    elif identifier == 'AL':
        workflow_details.update(application_status='AL', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='2',assigned_role_name='Verifier')
        return redirect(reviewer_application_list)
    elif identifier == 'ALA':
        workflow_details.update(application_status='ALA', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id=None,assigned_role_name=None)
        return redirect(verify_application_list)
    elif identifier == 'ALR':
        workflow_details.update(application_status='ALA', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id=None,assigned_role_name=None)
        return redirect(verify_application_list)
    elif identifier == 'ALS':
        workflow_details.update(application_status='ALS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(verify_application_list)
    elif identifier == 'EATC':
        workflow_details.update(application_status='EATC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(verify_application_list)
    elif identifier == 'FEATC':
        workflow_details.update(application_status='FEATC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(client_application_list)
    elif identifier == 'RS':
        workflow_details.update(application_status='RS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(verify_application_list)
    elif identifier == 'RSS':
        workflow_details.update(application_status='RSS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(client_application_list)
    elif identifier == 'LU':
        workflow_details.update(application_status='LU', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(verify_application_list)
    elif identifier == 'LUS':
        workflow_details.update(application_status='LUS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(verify_application_list)
    elif identifier == 'DEC':
        workflow_details.update(application_status='DEC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(reviewer_application_list)
    elif identifier == 'A':
        workflow_details.update(application_status='A', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
        return redirect(verify_application_list)

def save_draft_ec_attachment(request):
    data = dict()
    draft_ec_attach = request.FILES['draft_ec_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + draft_ec_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, draft_ec_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/EC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_draft_ec_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='DEC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='DEC')

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def save_lu_attachment(request):
    data = dict()
    lu_attach = request.FILES['lu_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + lu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/LU/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, lu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/LU" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_lu_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='LU')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})


# Inspection Report
def inspection_list(request):
    inspection_list = t_inspection_monitoring_t1.objects.filter(record_status='Active').order_by('inspection_date')
    user_list = t_user_master.objects.all()
    ec_details = t_ec_industries_t1_general.objects.all()
    return render(request, 'inspection.html', {'inspection_list':inspection_list, 'user_list':user_list, 'ec_details':ec_details})

def load_ec_details(request):
    data = dict()
    ec_reference_no = request.GET.get('ec_reference_no')
    ec_detail_list = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
    for ec_detail_list in ec_detail_list:
        data["applicant_name"],data["project_name"],data["address"] = ec_detail_list.applicant_name, ec_detail_list.project_name, ec_detail_list.address
    return JsonResponse(data)

def add_inspection(request):
    inspection_type = request.GET.get('inspection_type')
    inspection_date = request.GET.get('inspection_date')
    inspection_reason = request.GET.get('inspection_reason')
    ec_clearance_no = request.GET.get('ec_clearance_no')
    proponent_name = request.GET.get('proponent_name')
    project_name = request.GET.get('project_name')
    address = request.GET.get('address')
    observation = request.GET.get('observation')
    team_leader = request.GET.get('team_leader')
    team_members = request.GET.get('team_members')
    remarks = request.GET.get('remarks')
    fines_penalties = request.GET.get('fines_penalties')
    inspection_status = request.GET.get('inspection_status')

    t_inspection_monitoring_t1.objects.create(inspection_type=inspection_type, inspection_date=inspection_date,
                                              inspection_reason=inspection_reason, ec_clearance_no=ec_clearance_no,
                               login_id=login_id, project_name=project_name, proponent_name=proponent_name,
                               address=address, observation=observation, team_leader=team_leader,
                               team_members=team_members, remarks=remarks, fines_penalties=fines_penalties,
                               status=inspection_status, updated_by_ca=request.session['login_id'], record_status='Active')
    return redirect(inspection_list)

def get_inspection_details(request, record_id):
    inspection_details = t_inspection_monitoring_t1.objects.filter(record_id=record_id)
    ec_details = t_ec_industries_t1_general.objects.all()
    return render(request, 'edit_inspection.html', {'inspection_details': inspection_details, 'ec_details':ec_details})

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

    inspection_details = t_inspection_monitoring_t1.objects.filter(record_id=edit_record_id)
    inspection_details.update(inspection_type=edit_inspection_type, inspection_date=edit_inspection_date,
                              inspection_reason=edit_inspection_reason, ec_clearance_no=edit_ec_clearance_no,
                              proponent_name=edit_proponent_name, project_name=edit_project_name, address=edit_address,
                              observation=edit_observation, team_leader=edit_team_leader, team_members=edit_team_members,
                              remarks=edit_remarks, fines_penalties=edit_fines_penalties,
                              status=edit_inspection_status, updated_by_ca=request.session['login_id']
                              )
    return redirect(inspection_list)

def delete_inspection(request):
    delete_bsic_id = request.POST.get('bsic_id')
    bsic_details = t_bsic_code.objects.filter(bsic_id=delete_bsic_id)
    bsic_details.delete()
    return redirect(bsic_master)

def get_fines_penalties_details(request):
    ec_ref_no = request.GET.get('ec_ref_no')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=ec_ref_no) | t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_ref_no)
    
    return render(request, 'fines_penalties_details.html', {'application_details':application_details})

def save_fines_penalties(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        fines_penalties_type = request.POST.get('fines_penalty_type')
        ec_no = request.POST.get('ec_ref_no')
        proponent_name = request.POST.get('ec_ref_no')
        address = request.POST.get('address')
        validity = request.POST.get('ec_expiry_date')
        amount = request.POST.get('fines_and_penalties')
        

        t_fines_penalties.objects.create(application_no=application_no,
                                        fines_penalties_type=fines_penalties_type,
                                        fines_date=date.now(),
                                        ec_no=ec_no,
                                        proponent_name=proponent_name,
                                        address=address,
                                        validity=validity,
                                        amount=amount,
                                        fines_status='P'
                                        )
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)


#TOR Details
def tor_to_verifier(request):
    application_no = request.POST.get('application_no')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
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

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
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
                tor_submit_email(emailId, application_no, service_name)
    return redirect(verify_application_list)

def tor_submit_email(email_id, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your TOR Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " . " 
    recipient_list = [email_id]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)

