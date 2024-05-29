from django.urls import path
from . import views

urlpatterns = [
    path('new_application', views.new_application, name='new_application'),
    path('new_iee_application', views.new_iee_application, name='new_iee_application'),
    path('new_ea_application', views.new_ea_application, name='new_ea_application'),
    path('new_road_application', views.new_road_application, name='new_road_application'),
    path('new_transmission_application', views.new_transmission_application, name='new_transmission_application'),
    path('new_forestry_application', views.new_forestry_application, name='new_forestry_application'),
    path('new_general_application', views.new_general_application, name='new_general_application'),
    path('new_ground_water_application', views.new_ground_water_application, name='new_ground_water_application'),
    path('new_energy_application', views.new_energy_application, name='new_energy_application'),
    path('new_tourism_application', views.new_tourism_application, name='new_tourism_application'),
     path('new_quarry_application', views.new_quarry_application, name='new_quarry_application'),
    path('new_application_form', views.new_application_form, name='new_application_form'),


    path('add_machine_tool_details', views.add_machine_tool_details, name='add_machine_tool_details'),
    path('update_machine_tool_details', views.update_machine_tool_details, name='update_machine_tool_details'),
    path('delete_machine_tool_details', views.delete_machine_tool_details, name='delete_machine_tool_details'),
    path('add_raw_materials', views.add_raw_materials, name='add_raw_materials'),
    path('update_raw_materials', views.update_raw_materials, name='update_raw_materials'),
    path('delete_raw_materials', views.delete_raw_materials, name='delete_raw_materials'),
    path('add_partner_details', views.add_partner_details, name='add_partner_details'),
    path('update_partner_details', views.update_partner_details, name='update_partner_details'),
    path('delete_partner_details', views.delete_partner_details, name='delete_partner_details'),
    path('add_product_details', views.add_product_details, name='add_product_details'),
    path('get_specific_activity_description', views.get_specific_activity_description,
         name='get_specific_activity_description'),
    path('get_category', views.get_category, name='get_category'),
    path('get_application_service_id',views.get_application_service_id, name='get_application_service_id'),

    #iee_details
    path('load_gewog', views.load_gewog, name='load_gewog'),
    path('load_village', views.load_village, name='load_village'),
    path('save_iee_attachment', views.save_iee_attachment, name='save_iee_attachment'),
    path('save_iee_attachment_details', views.save_iee_attachment_details, name='save_iee_attachment_details'),
    path('save_anc_iee_attachment', views.save_anc_iee_attachment, name='save_anc_iee_attachment'),
    path('save_anc_iee_attachment_details', views.save_anc_iee_attachment_details, name='save_anc_iee_attachment_details'),
    path('save_anc_power_line_details', views.save_anc_power_line_details, name='save_anc_power_line_details'),
    path('update_anc_power_line_details', views.update_anc_power_line_details, name='update_anc_power_line_details'),
    path('delete_anc_power_line_details', views.delete_anc_power_line_details, name='delete_anc_power_line_details'),
    path('save_anc_road_details', views.save_anc_road_details, name='save_anc_road_details'),
    path('update_anc_road_details', views.update_anc_road_details, name='update_anc_road_details'),
    path('delete_anc_road_details', views.delete_anc_road_details, name='delete_anc_road_details'),
    path('add_forestry_produce_details', views.add_forestry_produce_details, name='add_forestry_produce_details'),
    path('update_forestry_produce_details', views.update_forestry_produce_details, name='update_forestry_produce_details'),
    path('delete_forestry_produce_details', views.delete_forestry_produce_details, name='delete_forestry_produce_details'),
    path('save_forest_attachment', views.save_forest_attachment, name='save_forest_attachment'),
    path('save_forest_attachment_details', views.save_forest_attachment_details, name='save_forest_attachment_details'),
    path('save_anc_forest_attachment', views.save_anc_forest_attachment, name='save_anc_forest_attachment'),
    path('save_anc_forest_attachment_details', views.save_anc_forest_attachment_details, name='save_anc_forest_attachment_details'),
    path('save_ground_water_attachment', views.save_ground_water_attachment, name='save_ground_water_attachment'),
    path('save_ground_water_attachment_details', views.save_ground_water_attachment_details, name='save_ground_water_attachment_details'),
    path('save_anc_ground_water_attachment', views.save_anc_ground_water_attachment, name='save_anc_ground_water_attachment'),
    path('save_anc_ground_water_attachment_details', views.save_anc_ground_water_attachment_details, name='save_anc_ground_water_attachment_details'),
    path('save_general_attachment', views.save_general_attachment, name='save_general_attachment'),
    path('save_general_attachment_details', views.save_general_attachment_details, name='save_general_attachment_details'),
    path('save_anc_general_attachment', views.save_anc_general_attachment, name='save_anc_general_attachment'),
    path('save_anc_general_attachment_details', views.save_anc_general_attachment_details, name='save_anc_general_attachment_details'),
    path('add_final_product_details', views.add_final_product_details, name='add_final_product_details'),
    path('update_final_product_details', views.update_final_product_details, name='update_final_product_details'),
    path('delete_final_product_details', views.delete_final_product_details, name='delete_final_product_details'),
    path('save_transmission_attachment', views.save_transmission_attachment, name='save_transmission_attachment'),
    path('save_transmission_attachment_details', views.save_transmission_attachment_details, name='save_transmission_attachment_details'),
    path('save_iee_application', views.save_iee_application, name='save_iee_application'),
    path('save_terrain_baseline_details', views.save_terrain_baseline_details, name='save_terrain_baseline_details'),
    path('save_water_requirement_details', views.save_water_requirement_details, name='save_water_requirement_details'),
    path('save_anc_approach_road_details', views.save_anc_approach_road_details, name='save_anc_approach_road_details'),
    path('save_anc_power_line_form', views.save_anc_power_line_form, name='save_anc_power_line_form'),
    path('save_anc_other_details', views.save_anc_other_details, name='save_anc_other_details'),
    path('save_solid_waste_details', views.save_solid_waste_details, name='save_solid_waste_details'),
    path('save_effluent_details', views.save_effluent_details, name='save_effluent_details'),
    path('save_industry_emission_details', views.save_industry_emission_details, name='save_industry_emission_details'),
    path('save_noise_level_details', views.save_noise_level_details, name='save_noise_level_details'),
    path('save_other_impact_details', views.save_other_impact_details, name='save_other_impact_details'),
    path('submit_iee_application', views.submit_iee_application, name='submit_iee_application'),
    
    #ea_details
    path('save_ea_attachment', views.save_ea_attachment, name='save_ea_attachment'),
    path('save_ea_attachment_details', views.save_ea_attachment_details, name='save_ea_attachment_details'),
    path('save_products_by_products_details', views.save_products_by_products_details, name='save_products_by_products_details'),
    path('update_products_by_products_details', views.update_products_by_products_details, name='update_products_by_products_details'),
    path('delete_products_by_products_details', views.delete_products_by_products_details, name='delete_products_by_products_details'),
    path('save_ea_hazardous_details', views.save_ea_hazardous_details, name='save_ea_hazardous_details'),
    path('update_ea_hazardous_details', views.update_ea_hazardous_details, name='update_ea_hazardous_details'),
    path('delete_ea_hazardous_details', views.delete_ea_hazardous_details, name='delete_ea_hazardous_details'),
    path('save_terrain_baseline_details_one', views.save_terrain_baseline_details_one, name='save_terrain_baseline_details_one'),
    path('save_terrain_baseline_details_two', views.save_terrain_baseline_details_two, name='save_terrain_baseline_details_two'),
    path('submit_ea_application', views.submit_ea_application, name='submit_ea_application'),

    #Ancillary Application Details
    path('industry_ancillary_form', views.industry_ancillary_form, name='industry_ancillary_form'),
    path('ground_water_ancillary_form', views.ground_water_ancillary_form, name='ground_water_ancillary_form'),
    path('forest_ancillary_form', views.forest_ancillary_form, name='forest_ancillary_form'),
    path('general_ancillary_form', views.general_ancillary_form, name='general_ancillary_form'),
    path('transmission_ancillary_form', views.transmission_ancillary_form, name='transmission_ancillary_form'),
    path('save_industry_ancillary_application', views.save_industry_ancillary_application, name='save_industry_ancillary_application'),

    #General Application Details
    path('save_general_info', views.save_general_application, name='save_general_info'),
    path('save_general_water_requirement', views.save_general_water_requirement, name='save_general_water_requirement'),
    path('submit_general_application', views.submit_general_application, name='submit_general_application'),

    #Transmission Details
    path('submit_transmission_application', views.submit_transmission_application, name='submit_transmission_application'),

    #TOR
    path('tor_form', views.tor_form, name='tor_form'),
    path('save_tor_form', views.save_tor_form, name='save_tor_form'),
    path('tor_list', views.tor_list, name='tor_list'),
    path('view_tor_application_details',views.view_tor_application_details, name='view_tor_application_details'),
    path('save_tor_attachment', views.save_tor_attachment, name='save_tor_attachment'),
    path('save_tor_attachment_details', views.save_tor_attachment_details, name='save_tor_attachment_details'),

    #Forest Application Details
    path('save_forest_application', views.save_forest_application, name='save_forest_application'),
    path('submit_forest_application', views.submit_forest_application, name='submit_forest_application'),

    # Ground Water Application Details
    path('save_ground_water_application', views.save_ground_water_application, name='save_ground_water_application'),
    path('save_ground_water_requirement', views.save_ground_water_requirement, name='save_ground_water_requirement'),
    path('submit_ground_water_application', views.submit_ground_water_application, name='submit_ground_water_application'),
    path('save_alternative_analysis', views.save_alternative_analysis, name='save_alternative_analysis'),

    # Quarry Application Details
    path('save_quarry_application', views.save_quarry_application, name='save_quarry_application'),
    path('submit_quarry_application', views.submit_quarry_application, name='submit_quarry_application'),
    path('save_quarry_attachment', views.save_quarry_attachment, name='save_quarry_attachment'),
    path('save_quarry_attachment_details', views.save_quarry_attachment_details, name='save_quarry_attachment_details'),

    #Road Application Details
    path('save_road_application', views.save_road_application, name='save_road_application'),
    path('save_road_attachment', views.save_general_attachment, name='save_road_attachment'),
    path('save_road_attachment_details', views.save_general_attachment_details, name='save_road_attachment_details'),
    path('road_project_details', views.road_project_details, name='road_project_details'),
    path('road_project_details_one', views.road_project_details_one, name='road_project_details_one'),
    path('road_project_details_two', views.road_project_details_two, name='road_project_details_two'),
    path('save_approach_road_details', views.save_approach_road_details, name='save_approach_road_details'),
    path('update_approach_road_details', views.update_approach_road_details, name='update_approach_road_details'),
    path('delete_approach_road_details', views.delete_approach_road_details, name='delete_approach_road_details'),
    path('submit_road_application', views.submit_general_application, name='submit_road_application'),
    path('add_types_of_drain', views.add_types_of_drain, name='add_types_of_drain'),
    path('update_types_of_drain', views.update_types_of_drain, name='update_types_of_drain'),
    path('delete_types_of_drain', views.delete_types_of_drain, name='delete_types_of_drain'),


    #Energy Application Details
    path('save_energy_application', views.save_energy_application, name='save_energy_application'),
    path('submit_energy_application', views.submit_energy_application, name='submit_energy_application'),

    #Tourism Application Details
    path('save_tourism_application', views.save_tourism_application, name='save_tourism_application'),
    path('save_tourism_sewerage_details', views.save_tourism_sewerage_details, name='save_tourism_sewerage_details'),
    path('submit_tourism_application', views.submit_tourism_application, name='submit_tourism_application'),
    path('save_tourism_attachment', views.save_tourism_attachment, name='save_tourism_attachment'),
    path('save_tourism_attachment_details', views.save_tourism_attachment_details, name='save_tourism_attachment_details'),

    # Common 
    path('save_project_details', views.save_project_details, name='save_project_details'),
    path('ec_renewal', views.ec_renewal, name='ec_renewal'),
    path('ec_renewal_details', views.ec_renewal_details, name='ec_renewal_details'),
 
    #Other Modifications
    path('name_change', views.name_change, name='name_change'),
    path('ownership_change', views.ownership_change, name='ownership_change'),
    path('technology_change', views.technology_change, name='technology_change'),
    path('product_change', views.product_change, name='product_change'),
    path('capacity_change', views.capacity_change, name='capacity_change'),
    path('area_change', views.area_change, name='area_change'),
    path('location_change', views.location_change, name='location_change'),
    path('get_other_modification_details', views.get_other_modification_details, name='get_other_modification_details'),
    
    # Draft Application Details
    path('draft_application_list', views.draft_application_list, name='draft_application_list'),
    path('view_draft_application_details', views.view_draft_application_details, name='view_draft_application_details'),
    path('update_draft_application', views.update_draft_application, name='update_draft_application'),
    
    # Renewal Application Details
    path('submit_renew_application', views.submit_renew_application, name='submit_renew_application'),
    
    #Report Submission
    path('report_list', views.report_list, name='report_list'),
    path('view_report_details', views.view_report_details, name='view_report_details'),
    path('viewDraftReport/<str:report_reference_no>', views.viewDraftReport, name='viewDraftReport'),

    path('report_submission_form', views.report_submission_form, name='report_submission_form'),
    path('save_report_submission', views.save_report_submission, name='save_report_submission'),
    path('load_report_submission_details', views.load_report_submission_details, name='load_report_submission_details'),
    path('update_report_submission', views.update_report_submission, name='update_report_submission'),
    path('save_report_details', views.save_report_details, name='save_report_details'),
    path('delete_report_details', views.delete_report_details, name='delete_report_details'),
    path('load_report_attachment_details', views.load_report_attachment_details, name='load_report_attachment_details'),
    path('add_report_file', views.add_report_file, name='add_report_file'),
    path('add_report_file_name', views.add_report_file_name, name='add_report_file_name'),
    path('delete_report_file', views.delete_report_file, name='delete_report_file'),
    path('submit_report_form', views.submit_report_form, name='submit_report_form'),
    path('acknowledge_report', views.acknowledge_report, name='acknowledge_report'),

    #Renewal Details
    path('save_renew_attachment', views.save_renew_attachment, name='save_renew_attachment'),
    path('save_renew_attachment_details', views.save_renew_attachment_details, name='save_renew_attachment_details'),
    path('save_compliance_details', views.save_compliance_details, name='save_compliance_details'),

    #EC PRint
    path('ec_print_list', views.ec_print_list, name='ec_print_list'),
    path('view_print_details', views.view_print_details, name='view_print_details'),

    #Dumpyard Details
    path('add_dumpyard_details', views.add_dumpyard_details, name='add_dumpyard_details'),
    path('update_dumpyard_details', views.update_dumpyard_details, name='update_dumpyard_details'),
    path('delete_dumpyard_details', views.delete_dumpyard_details, name='delete_dumpyard_details'),

    path('delete_application_attachment', views.delete_application_attachment, name='delete_application_attachment'),

    #Payment_part
    path('ecss_payment_update', views.ecss_payment_update, name='ecss_payment_update'),

    #NDI
    path('proof_request/', views.proof_request, name='proof_request'),
    path('proof_request_proponent/', views.proof_request_proponent, name='proof_request_proponent'),
    path('fetch_verified_user_data/', views.fetch_verified_user_data, name='fetch_verified_user_data'),
    path('webhook', views.webhook, name='webhook')

]
