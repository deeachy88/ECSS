from datetime import date
from django.shortcuts import render, redirect
from proponent.models import t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, t_workflow_dtls, t_ec_industries_t9_products_by_products, t_ec_industries_t10_hazardous_chemicals
from ecs_admin.models import t_bsic_code, t_file_attachment, t_dzongkhag_master, t_gewog_master, t_village_master
# Create your views here.
from django.db.models import Max
from django.utils import timezone
from django.http import JsonResponse


def new_application(request):
    bsic_details = t_bsic_code.objects.all()
    for application_details in bsic_details:
        request.session['ca_authority'] = application_details.competent_authority
        request.session['colour_code'] = application_details.colour_code
        request.session['service_id'] = application_details.service_id
    return render(request, 'new_application.html',{'bsic_details':bsic_details})

def new_ea_application(request):
    service_code = 'EA'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'industry_ea_form.html',
                  {'partner_details': partner_details, 'machine_equipment': machine_equipment,
                   'raw_materials': raw_materials,
                   'project_product': project_product, 'ancillary_road': ancillary_road, 'power_line': power_line,
                   'application_no': application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def new_road_application(request):
    service_code = 'ROA'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'road_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def new_transmission_application(request):
    service_code = 'TRA'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    return render(request, 'transmission_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no})

def new_forestry_application(request):
    service_code = 'FO'
    application_no = get_application_no(request, service_code)
    forest_produce = t_ec_industries_t8_forest_produce.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    return render(request, 'forest_form.html',{'forest_produce':forest_produce,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no})

def new_general_application(request):
    service_code = 'GE'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    return render(request, 'general_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no})

def new_ground_water_application(request):
    service_code = 'GW'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    return render(request, 'ground_water_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no})

def new_industry_application(request):
    service_code = 'GW'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    project_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    return render(request, 'industry_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no})

def get_application_no(request, service_code):
    application_no= t_ec_industries_t1_general.objects.aggregate(Max('application_no'))
    last_application_no= application_no['application_no__max']
    if not last_application_no:
        year=timezone.now().year
        new_application_no = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(last_application_no)[9:13]
        substring = int(substring) + 1
        app_num = str(substring).zfill(4)
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
    application_no = request.POST.get('application_no')

    partner_type_details = t_ec_industries_t2_partner_details.objects.filter(record_id=record_id)
    partner_type_details.delete()
    partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'partner_details.html', {'partner_details': partner_details})


def save_iee_application(request):
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
            application_date=None,
            application_type='N',
            ca_authority=request.session['ca_authority'],
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
            bl_protected_area_name=None,
            bl_protected_area_distance=None,
            bl_migratory_route_name=None,
            bl_migratory_route_distance=None,
            bl_wetland_name=None,
            bl_wetland_distance=None,
            bl_water_bodies_name=None,
            bl_water_bodies_distance=None,
            bl_fmu_name=None,
            bl_fmu_distance=None,
            bl_agricultural_name=None,
            bl_agricultural_distance=None,
            bl_settlement_name=None,
            bl_settlement_distance=None,
            bl_road_name=None,
            bl_road_distance=None,
            bl_public_infra_name=None,
            bl_public_infra_distance=None,
            bl_school_name=None,
            bl_school_distance=None,
            bl_heritage_name=None,
            bl_heritage_distance=None,
            bl_tourist_facility_name=None,
            bl_tourist_facility_distance=None,
            bl_impt_installation_name=None,
            bl_impt_installation_distance=None,
            bl_industries_name=None,
            bl_industries_distance=None,
            bl_others=None,
            bl_others_name=None,
            bl_others_distance=None,
            technology_used=None,
            technology_no=None,
            technology_total_capacity=None,
            energy_source=None,
            energy_source_justification=None,
            water_required=None,
            water_raw_material_source=None,
            water_raw_material_qty_day=None,
            water_raw_material_recycle_day=None,
            water_cleaning_source=None,
            water_cleaning_qty_day=None,
            water_cleaning_recycle_day=None,
            water_process_source=None,
            water_process_qty_day=None,
            water_process_recycle_day=None,
            water_domestic_source=None,
            water_domestic_qty_day=None,
            water_domestic_recycle_day=None,
            water_dust_compression_source=None,
            water_dust_compression_qty_day=None,
            water_dust_compression_recycle_day=None,
            water_others_name=None,
            water_others_source=None,
            water_others_qty_day=None,
            water_others_recycle_day=None,
            water_provide_by_iestate=None,
            water_downstream_users=None,
            water_flow_rate_lean=None,
            water_source_distance=None,
            anc_road_required=None,
            anc_road_length=None,
            anc_road_start_point=None,
            anc_road_end_point=None,
            anc_road_blast_required=None,
            anc_road_blast_type=None,
            anc_road_blast_qty=None,
            anc_road_blast_location=None,
            anc_road_blast_frequency_time=None,
            anc_power_line_required=None,
            anc_power_line_voltage=None,
            anc_power_line_length=None,
            anc_power_line_start_point=None,
            anc_power_line_end_point=None,
            anc_power_line_storing_method=None,
            anc_other_required=None,
            anc_other_crushing_unit=None,
            anc_other_surface_collection=None,
            anc_other_ground_water=None,
            anc_other_mineral=None,
            anc_other_general=None,
            en_impact_allocated_budget=None,
            en_impact_hazardous_waste_list=None,
            en_impact_hazardous_waste_source=None,
            en_impact_hazardous_waste_qty_annum=None,
            en_impact_hazardous_waste_mgt_plan=None,
            en_impact_non_hazardous_waste_list=None,
            en_impact_non_hazardous_waste_source=None,
            en_impact_non_hazardous_waste_qty_annum=None,
            en_impact_non_hazardous_waste_mgt_plan=None,
            en_impact_medical_waste_list=None,
            en_impact_medical_waste_source=None,
            en_impact_medical_waste_qty_annum=None,
            en_impact_medical_waste_mgt_plan=None,
            en_impact_ewaste_list=None,
            en_impact_ewaste_source=None,
            en_impact_ewaste_qty_annum=None,
            en_impact_ewaste_mgt_plan=None,
            en_impact_others_waste_list=None,
            en_impact_others_waste_source=None,
            en_impact_others_waste_qty_annum=None,
            en_impact_others_waste_mgt_plan=None,
            en_waste_water_generate=None,
            waste_water_nh3n_source=None,
            waste_water_nh3n_discharge=None,
            waste_water_nh3n_treatment=None,
            waste_water_nh3n_name_location=None,
            waste_water_arsenic_source=None,
            waste_water_arsenic_discharge=None,
            waste_water_arsenic_treatment=None,
            waste_water_arsenic_name_location=None,
            waste_water_bod_source=None,
            waste_water_bod_discharge=None,
            waste_water_bod_treatment=None,
            waste_water_bod_name_location=None,
            waste_water_boron_source=None,
            waste_water_boron_discharge=None,
            waste_water_boron_treatment=None,
            waste_water_boron_name_location=None,
            waste_water_cadmium_source=None,
            waste_water_cadmium_discharge=None,
            waste_water_cadmium_treatment=None,
            waste_water_cadmium_name_location=None,
            waste_water_cod_source=None,
            waste_water_cod_discharge=None,
            waste_water_cod_treatment=None,
            waste_water_cod_name_location=None,
            waste_water_cloride_source=None,
            waste_water_cloride_discharge=None,
            waste_water_cloride_treatment=None,
            waste_water_cloride_name_location=None,
            waste_water_chromium_source=None,
            waste_water_chromium_discharge=None,
            waste_water_chromium_treatment=None,
            waste_water_chromium_name_location=None,
            waste_water_chromium_hex_source=None,
            waste_water_chromium_hex_discharge=None,
            waste_water_chromium_hex_treatment=None,
            waste_water_chromium_hex_name_location=None,
            waste_water_copper_source=None,
            waste_water_copper_discharge=None,
            waste_water_copper_treatment=None,
            waste_water_copper_name_location=None,
            waste_water_cyanide_source=None,
            waste_water_cyanide_discharge=None,
            waste_water_cyanide_treatment=None,
            waste_water_cyanide_name_location=None,
            waste_water_floride_source=None,
            waste_water_floride_discharge=None,
            waste_water_floride_treatment=None,
            waste_water_floride_name_location=None,
            waste_water_phosphate_source=None,
            waste_water_phosphate_discharge=None,
            waste_water_phosphate_treatment=None,
            waste_water_phosphate_name_location=None,
            waste_water_nitrate_source=None,
            waste_water_nitrate_discharge=None,
            waste_water_nitrate_treatment=None,
            waste_water_nitrate_name_location=None,
            waste_water_iron_source=None,
            waste_water_iron_discharge=None,
            waste_water_iron_treatment=None,
            waste_water_iron_name_location=None,
            waste_water_lead_source=None,
            waste_water_lead_discharge=None,
            waste_water_lead_treatment=None,
            waste_water_lead_name_location=None,
            waste_water_manganese_source=None,
            waste_water_manganese_discharge=None,
            waste_water_manganese_treatment=None,
            waste_water_manganese_name_location=None,
            waste_water_mercury_source=None,
            waste_water_mercury_discharge=None,
            waste_water_mercury_treatment=None,
            waste_water_mercury_name_location=None,
            waste_water_nickel_source=None,
            waste_water_nickel_discharge=None,
            waste_water_nickel_treatment=None,
            waste_water_nickel_name_location=None,
            waste_water_oil_source=None,
            waste_water_oil_discharge=None,
            waste_water_oil_treatment=None,
            waste_water_oil_name_location=None,
            waste_water_ph_source=None,
            waste_water_ph_discharge=None,
            waste_water_ph_treatment=None,
            waste_water_ph_name_location=None,
            waste_water_phenolic_source=None,
            waste_water_phenolic_discharge=None,
            waste_water_phenolic_treatment=None,
            waste_water_phenolic_name_location=None,
            waste_water_selenium_source=None,
            waste_water_selenium_discharge=None,
            waste_water_selenium_treatment=None,
            waste_water_selenium_name_location=None,
            waste_water_so4_source=None,
            waste_water_so4_discharge=None,
            waste_water_so4_treatment=None,
            waste_water_so4_name_location=None,
            waste_water_s_source=None,
            waste_water_s_discharge=None,
            waste_water_s_treatment=None,
            waste_water_s_name_location=None,
            waste_water_tds_source=None,
            waste_water_tds_discharge=None,
            waste_water_tds_treatment=None,
            waste_water_tds_name_location=None,
            waste_water_tss_source=None,
            waste_water_tss_discharge=None,
            waste_water_tss_treatment=None,
            waste_water_tss_name_location=None,
            waste_water_temp_source=None,
            waste_water_temp_discharge=None,
            waste_water_temp_treatment=None,
            waste_water_temp_name_location=None,
            waste_water_tkn_source=None,
            waste_water_tkn_discharge=None,
            waste_water_tkn_treatment=None,
            waste_water_tkn_name_location=None,
            waste_water_residual_cloride_source=None,
            waste_water_residual_cloride_discharge=None,
            waste_water_residual_cloride_treatment=None,
            waste_water_residual_cloride_name_location=None,
            waste_water_zinc_source=None,
            waste_water_zinc_discharge=None,
            waste_water_zinc_treatment=None,
            waste_water_zinc_name_location=None,
            waste_water_ammonia_source=None,
            waste_water_ammonia_discharge=None,
            waste_water_ammonia_treatment=None,
            waste_water_ammonia_name_location=None,
            waste_water_colour_source=None,
            waste_water_colour_discharge=None,
            waste_water_colour_treatment=None,
            waste_water_colour_name_location=None,
            waste_water_treatment_plant_capacity=None,
            waste_water_qty_per_annum=None,
            waste_water_treatment_plant_etp=None,
            waste_water_treatment_sludge_qty=None,
            waste_water_treatment_plant_name_location=None,
            en_industry_emission_generate=None,
            en_spm_emission_expected=None,
            en_so2_emission_expected=None,
            en_nox_emission_expected=None,
            en_co_emission_expected=None,
            en_fluoride_emission_expected=None,
            en_pol_control_device_stack_height=None,
            en_pol_control_device_stack_diameter=None,
            en_pol_control_device_dimension=None,
            en_pol_control_device_volume=None,
            en_pol_control_device_temp=None,
            en_air_pollution_control_device_capacity=None,
            en_air_pollution_control_pcd_dimension=None,
            en_noise_ind_area_day=None,
            en_noise_ind_area_night=None,
            en_noise_ind_area_mgt_plan=None,
            en_noise_sen_area_day=None,
            en_noise_sen_area_night=None,
            en_noise_sen_area_mgt_plan=None,
            en_noise_mixed_area_day=None,
            en_noise_mixed_area_night=None,
            en_noise_mixed_area_mgt_plan=None,
            en_other_impact_odour_source=None,
            en_other_impact_odour_qty=None,
            en_other_impact_odour_mgt_plan=None,
            en_other_impact_fugutive_source=None,
            en_other_impact_fugutive_qty=None,
            en_other_impact_fugutive_mgt_plan=None,
            en_other_impact_slope_source=None,
            en_other_impact_slope_qty=None,
            en_other_impact_slope_mgt_plan=None,
            en_other_impact_aesthetic_source=None,
            en_other_impact_aesthetic_qty=None,
            en_other_impact_aesthetic_mgt_plan=None,
            en_other_impact_mucks_source=None,
            en_other_impact_mucks_qty=None,
            en_other_impact_mucks_mgt_plan=None,
            en_other_impact_sewerage_source=None,
            en_other_impact_sewerage_qty=None,
            en_other_impact_sewerage_mgt_plan=None,
            en_other_impact_erosion_source=None,
            en_other_impact_erosion_qty=None,
            en_other_impact_erosion_mgt_plan=None,
            en_other_impact_storm_water_source=None,
            en_other_impact_storm_water_qty=None,
            en_other_impact_storm_water_mgt_plan=None,
            en_other_impact_habitat_source=None,
            en_other_impact_habitat_qty=None,
            en_other_impact_habitat_mgt_plan=None,
            en_other_impact_socio_source=None,
            en_other_impact_socio_qty=None,
            en_other_impact_socio_mgt_plan=None,
            en_other_impact_water_source_source=None,
            en_other_impact_water_source_qty=None,
            en_other_impact_water_source_mgt_plan=None,
            en_other_impact_other_source=None,
            en_other_impact_other_qty=None,
            en_other_impact_other_mgt_plan=None,
            fee=None,
            assigned_to=None,
            assigned_date=None,
            assigned_by=None,
            inspection_date=None,
            inspection_team=None,
            recommendation=None,
            ec_type=None,
            ec_reference_no=None,
            ec_approve_date=None,
            ec_approval_committee=None,
            fines_penalties=None,
            application_status='P',
            resubmit_remarks=None,
            resubmit_date=None
            )
        t_workflow_dtls.objects.create(application_no=application_no, 
                                        service_id=request.session['service_id'],
                                        application_status='P',
                                        action_date=None,
                                        actor_id=None,
                                        actor_name=None,
                                        assigned_user_id=None,
                                        assigned_role_id=None,
                                        assigned_role_name=None,
                                        result=None,
                                        ca_authority=request.session['ca_authority'],
                                        dzongkhag_thromde_id=dzongkhag_code
                                    )
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
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
        anc_road_length = request.POST.get('anc_road_length')
        anc_road_start_point = request.POST.get('anc_road_start_point')
        anc_road_end_point = request.POST.get('anc_road_end_point')
        anc_road_blast_required = request.POST.get('anc_road_blast_required')
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

        anc_other_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        anc_other_details.update(anc_other_crushing_unit=anc_other_crushing_unit,
                                  anc_other_surface_collection=anc_other_surface_collection,
                                  anc_other_ground_water=anc_other_ground_water,
                                  anc_other_mineral=anc_other_mineral,
                                  anc_other_general=anc_other_general
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
        en_pol_control_device_stack_heicht = request.POST.get('en_pol_control_device_stack_heicht')
        en_pol_control_device_stack_diameter = request.POST.get('en_pol_control_device_stack_diameter')
        en_pol_control_device_dimention = request.POST.get('en_pol_control_device_dimention')
        en_pol_control_device_volume = request.POST.get('en_pol_control_device_volume')
        en_pol_control_device_temp = request.POST.get('en_pol_control_device_temp')
        en_air_pollution_control_device_capacity = request.POST.get('en_air_pollution_control_device_capacity')
        en_air_pollution_control_pcd_dimention = request.POST.get('en_air_pollution_control_pcd_dimention')


        industry_emission_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        industry_emission_details.update(en_industry_emission_generate=en_industry_emission_generate,
                                         en_spm_emission_expected=en_spm_emission_expected,
                                         en_so2_emission_expected=en_so2_emission_expected,
                                         en_nox_emission_expected=en_nox_emission_expected,
                                         en_co_emission_expected=en_co_emission_expected,
                                         en_fluoride_emission_expected=en_fluoride_emission_expected,
                                         en_pol_control_device_stack_heicht=en_pol_control_device_stack_heicht,
                                         en_pol_control_device_stack_diameter=en_pol_control_device_stack_diameter,
                                         en_pol_control_device_dimention=en_pol_control_device_dimention,
                                         en_pol_control_device_volume=en_pol_control_device_volume,
                                         en_pol_control_device_temp=en_pol_control_device_temp,
                                         en_air_pollution_control_device_capacity=en_air_pollution_control_device_capacity,
                                         en_air_pollution_control_pcd_dimention=en_air_pollution_control_pcd_dimention,
                                         )
        data['message'] = "success"
        return JsonResponse(data)
    except:
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
        workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
        workflow_dtls.update(action_date=date.now())
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
    print(broad_activity_code)

    category_details = t_bsic_code.objects.filter(broad_activity_code=broad_activity_code,specific_activity_code=specific_activity_code,category=category)
    for cat_details in category_details:
        data['service_id'] = cat_details.service_id
        data['colour_code'] = cat_details.colour_code
        data['competant_authority'] = cat_details.competent_authority
    return JsonResponse(data)

# IEE DETAILS
def load_gewog(request):
    dzongkhag_id = request.GET.get('dzongkhag_id')
    gewog_list = t_gewog_master.objects.filter(dzongkhag_code=dzongkhag_id).order_by('gewog_name')
    return render(request, 'gewog_list.html', {'gewog_list': gewog_list})

def load_village(request):
    gewog_id = request.GET.get('gewog_id')
    village_list = t_village_master.objects.filter(gewog_code=gewog_id).order_by('village_name')
    return render(request, 'village_list.html', {'village_list': village_list})
def new_iee_application(request):
    service_code = 'IEE'
    application_no = get_application_no(request, service_code)
    partner_details = t_ec_industries_t2_partner_details.objects.all()
    machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
    final_product = t_ec_industries_t4_project_product.objects.all()
    raw_materials = t_ec_industries_t5_raw_materials.objects.all()
    ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
    power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'industry_iee_form.html',{'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
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
    return render('anc_power_line_details.html', {'anc_power_line_details':anc_power_line_details})

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
    return render('anc_power_line_details.html', {'anc_power_line_details':anc_power_line_details})

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

    t_ec_industries_t6_ancillary_road.objects.create(application_no=application_no,line_chainage_from=line_chainage_from,
                                                           line_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                                                           road_width=road_width,row=row,area_required=area_required)
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
    return render('anc_approach_road_details.html', {'anc_road_details':anc_road_details})

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
    road_details.update(application_no=application_no,line_chainage_from=line_chainage_from,
                       line_chainage_to=line_chainage_to,land_type=land_type,terrain=terrain,
                       road_width=road_width,no_of_tower=no_of_tower,row=row,area_required=area_required)
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
    return render('anc_approach_road_details.html', {'anc_road_details':anc_road_details})

def delete_anc_road_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    road_details = t_ec_industries_t6_ancillary_road.objects.filter(record_id=record_id)
    road_details.delete()
    anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'anc_approach_road_details.html', {'anc_road_details': anc_road_details})

def add_forestry_produce_details(request):
    application_no = request.POST.get('application_no')
    produce_name = request.POST.get('produce_name')
    quantity_annum = request.POST.get('quantity_annum')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t8_forest_produce.objects.create(application_no=application_no, produce_name=produce_name,
                                                    qty=qty, storage_method=storage_method)
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
    forestry_produce_details.update(produce_name=produce_name, qty=qty, storage_method=storage_method)
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

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

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

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

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

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def add_final_product_details(request):
    application_no = request.POST.get('application_no')
    product_name = request.POST.get('product_name')
    name_location = request.POST.get('name_location')
    storage_method = request.POST.get('storage_method')

    t_ec_industries_t4_project_product.objects.create(application_no=application_no, product_name=product_name,
                                                    name_location_type=name_location, storage_method=storage_method)
    final_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no).order_by(
        'record_id')
    return render(request, 'final_products.html', {'final_product': final_product})

def update_final_product_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    product_name = request.POST.get('product_name')
    name_location = request.POST.get('name_location')
    storage_method = request.POST.get('storage_method')

    final_product_details = t_ec_industries_t4_project_product.objects.filter(record_id=record_id)
    final_product_details.update(product_name=product_name, name_location_type=name_location, storage_method=storage_method)
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
    return render(request, 'forestry_produce.html', {'forestry_produce': forestry_produce})

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
    general_attach = request.FILES['general_attach']
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

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})


#EA Details
def save_ea_attachment(request):
    data = dict()
    ea_attach = request.FILES['ea_attach']
    file_name = ea_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EA/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ea_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/EA" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_ea_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')
    t_file_attachment.objects.create(application_no=application_no, file_path=file_url, attachment=file_name,attachment_type='EA')
    file_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='EA')

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
    return render(request, 'final_products.html', {'final_product': final_product})

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
        workflow_dtls = t_workflow_dtls.objects.filter(application_no=application_no)
        workflow_dtls.update(action_date=date.now())
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)








