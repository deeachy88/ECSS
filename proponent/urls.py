from django.urls import path
from . import views

urlpatterns = [
    path('new_application', views.new_application, name='new_application'),
    path('new_iee_application', views.new_iee_application, name='new_iee_application'),
    path('new_ea_application', views.new_ea_application, name='new_ea_application'),
    path('new_road_application', views.new_road_application, name='new_road_application'),
    path('new_transmission_application', views.new_transmission_application, name='new_transmission_application'),
    path('new_forest_application', views.new_forest_application, name='new_forest_application'),
    path('new_general_application', views.new_general_application, name='new_general_application'),
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
    path('save_iee_attachment', views.save_iee_attachment, name='save_iee_attachment'),
    path('save_iee_attachment_details', views.save_iee_attachment_details, name='save_iee_attachment_details'),
    path('save_anc_power_line_details', views.save_anc_power_line_details, name='save_anc_power_line_details'),
    path('update_anc_power_line_details', views.save_anc_power_line_details, name='update_anc_power_line_details'),
    path('delete_anc_power_line_details', views.delete_anc_power_line_details, name='delete_anc_power_line_details'),
    path('save_anc_road_details', views.save_anc_road_details, name='save_anc_road_details'),
    path('update_anc_road_details', views.update_anc_road_details, name='update_anc_road_details'),
    path('delete_anc_road_details', views.delete_anc_road_details, name='delete_anc_road_details'),

    #ea_details
    path('save_ea_attachment', views.save_ea_attachment, name='save_ea_attachment'),
    path('save_ea_attachment_details', views.save_ea_attachment_details, name='save_ea_attachment_details'),
]
