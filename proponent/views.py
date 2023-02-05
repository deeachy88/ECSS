from django.shortcuts import render
from proponent.models import t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line
# Create your views here.
from django.db.models import Max
from django.utils import timezone

def new_iee_application(request):
    service_code = 'IEE'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    return render(request, 'industry_iee_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no})


def get_application_no(request, service_code):
    application_no= t_ec_industries_t1_general.objects.aggregate(Max('application_no'))
    last_application_no= application_no['application_no__max']
    if not last_application_no:
        year=timezone.now().year
        new_application_no = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastAppNo)[9:13]
        substring = int(substring) + 1
        app_num = str(substring).zfill(4)
        year =  timezone.now().year
        new_application_no =  service_code + "-" + str(year) + "-" + app_num
    return new_application_no

def add_machine_tool_details(request):
    application_no = application_no,
    machine_tool = request.POST.get('machine_tool')
    machine_tool_qty = request.POST.get('machine_tool_qty')
    machine_tool_installed_capacity = request.POST.get('machine_tool_installed_capacity')

    t_ec_industries_t3_machine_equipment.objects.create(application_no= application_no,machine_name= machine_tool,
                                                        qty=machine_tool_qty,installed_capacity=machine_tool_installed_capacity)
    machine_equipment=application_no, t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no).order_by('record_id')
    return render(request, 'details_machine_equipment_tool.html',{'machine_equipment':machine_equipment})

def add_project_product(request):
    application_no = request.POST.get('application_no')
    product_name = request.POST.get('product_name')
    installed_capacity = request.POST.get('installed_capacity')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t4_project_product.objects.create(application_no= application_no, product_name= application_no,
                                                        installed_capacity= application_no,storage_method= application_no)
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
    application_no = request.POST.get('application_no'),
    machine_tool = request.POST.get('machine_tool')
    machine_tool_qty = request.POST.get('machine_tool_qty')
    machine_tool_installed_capacity = request.POST.get('machine_tool_installed_capacity')

    machine_equipment_details = t_ec_industries_t3_machine_equipment.objects.filter(record_id=record_id)
    machine_equipment_details.update(machine_name=machine_tool,qty=machine_tool_qty,installed_capacity= machine_tool_installed_capacity)
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
    application_no = application_no,

    partner_type_details = t_ec_industries_t2_partner_details.objects.filter(record_id=record_id)
    partner_type_details.delete()
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'partner_details.html', {'partner_details': partner_details})


def save_iee_application(request):
    application_no = request.POST.get('application_no')
    application_type = request.POST.get('application_type')
    ca_authority = request.POST.get('ca_authority')
    applicant_id = request.POST.get('applicant_id')
    applicant_type = request.POST.get('applicant_type')
    colour_code = request.POST.get('colour_code')
    project_name = request.POST.get('project_name')
    project_category = request.POST.get('project_category')
    applicant_name = request.POST.get('applicant_name')
    address = request.POST.get('address')
    cid = request.POST.get('cid')
    contact_no = request.POST.get('contact_no')
    email = request.POST.get('email')
    focal_person = request.POST.get('focal_person')
    industry_type = request.POST.get('industry_type')
    industry_classification = request.POST.get('industry_classification')
    thromde_id = request.POST.get('thromde_id')
    dzongkhag_code = request.POST.get('dzongkhag_code')
    gewog_code = request.POST.get('gewog_code')
    village_code = request.POST.get('village_code')
    location_name = request.POST.get('location_name')
    industrial_area_acre = request.POST.get('industrial_area_acre')
    state_reserve_forest_acre = request.POST.get('state_reserve_forest_acre')
    private_area_acre = request.POST.get('private_area_acre')
    others_area_acre = request.POST.get('others_area_acre')
    green_area_acre = request.POST.get('green_area_acre')
    proposed_location_justification = request.POST.get('proposed_location_justification')
    terrain_elevation = request.POST.get('terrain_elevation')
    terrain_slope = request.POST.get('terrain_slope')
    project_objective = request.POST.get('project_objective')
    project_no_of_workers = request.POST.get('project_no_of_workers')
    project_cost = request.POST.get('project_cost')
    project_duration = request.POST.get('project_duration')

    t_ec_industries_t1_general.objects.create(
        application_no=application_no,
        application_date=date.today(),
        application_type=application_type,
        ca_authority=ca_authority,
        applicant_id=applicant_id,
        applicant_type=applicant_type,
        colour_code=colour_code,
        project_name=project_name,
        project_category=project_category,
        applicant_name=applicant_name,
        address=address,
        cid=cid,
        contact_no=contact_no,
        email=email,
        focal_person=focal_person,
        industry_type=industry_type,
        industry_classification=industry_classification,
        thromde_id=thromde_id,
        dzongkhag_code=dzongkhag_code,
        gewog_code=gewog_code,
        village_code=village_code,
        location_name=location_name,
        industrial_area_acre=industrial_area_acre,
        state_reserve_forest_acre=state_reserve_forest_acre,
        private_area_acre=private_area_acre,
        others_area_acre=others_area_acre,
        green_area_acre=green_area_acre,
        proposed_location_justification=proposed_location_justification,
        terrain_elevation=terrain_elevation,
        terrain_slope=terrain_slope,
        project_objective=project_objective,
        project_no_of_workers=project_no_of_workers,
        project_cost=project_cost,
        project_duration=project_duration,
        )
    data['success'] = "success"
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

def new_ea_application(request):
    return render(request, 'industry_ea_form.html')
