from django.urls import path
from . import views

urlpatterns = [
    path('new_iee_application', views.new_iee_application, name='new_iee_application'),
    path('new_ea_application', views.new_ea_application, name='new_ea_application'),
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

]
