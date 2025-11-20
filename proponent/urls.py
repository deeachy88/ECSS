from django.urls import path

from proponent import views

urlpatterns = [
    path('new_application', views.new_application, name='new_application'),
    path('get_application_service_id',views.get_application_service_id, name='get_application_service_id'),
    path('application_form', views.application_form, name='application_form'),
    path('save_general_details', views.save_general_details, name='save_general_details'),
    path('save_general_attachment', views.save_general_attachment, name='save_general_attachment'),
    path('save_general_attachment_details', views.save_general_attachment_details, name='save_general_attachment_details'),
    path('submit_general_application', views.submit_general_application, name='submit_general_application'),
    path('check_file_attachment', views.check_file_attachment, name='check_file_attachment'),
    path('delete_application_attachment', views.delete_application_attachment, name='delete_application_attachment'),

    # DRAFT DETAILS
    path('draft_application_list', views.draft_application_list, name='draft_application_list'),
    path('view_draft_application_details', views.view_draft_application_details, name='view_draft_application_details'),
    
    # EC RENEWAL
    path('ec_renewal', views.ec_renewal, name='ec_renewal'),

    # OTHER MODIFICATION DETAILS
    path('name_change', views.name_change, name='name_change'),
    path('ownership_change', views.ownership_change, name='ownership_change'),
    path('technology_change', views.technology_change, name='technology_change'),
    path('product_change', views.product_change, name='product_change'),
    path('capacity_change', views.capacity_change, name='capacity_change'),
    path('area_change', views.area_change, name='area_change'),
    path('location_change', views.location_change, name='location_change'),
    path('get_other_modification_details', views.get_other_modification_details, name='get_other_modification_details'),

    #TOR DETAILS
    path('tor_list', views.tor_list, name='tor_list'),


    #Report Submission
    path('report_list', views.report_list, name='report_list'),

    #EC PRint
    path('ec_print_list', views.ec_print_list, name='ec_print_list'),

    #NDI
    path('proof_request/', views.proof_request, name='proof_request'),
    path('proof_request_employee/', views.proof_request_employee, name='proof_request_employee'),
    path('proof_request_proponent/', views.proof_request_proponent, name='proof_request_proponent'),
    path('fetch_verified_user_data/', views.fetch_verified_user_data, name='fetch_verified_user_data'),
    path('webhook', views.webhook, name='webhook'),
    path('ndi_dash/', views.ndi_dash, name='ndi_dash'),
    path('ndi_dash_eid/', views.ndi_dash_eid, name='ndi_dash_eid'),
    path('update_password_ndi/', views.update_password_ndi, name='update_password_ndi'),
    path('issuance_call/', views.issuance_call, name='issuance_call'),
    path('fetch_relationship_data/', views.fetch_relationship_data, name='fetch_relationship_data'),
    path('revoke_ec', views.revoke_ec, name='revoke_ec')

]
