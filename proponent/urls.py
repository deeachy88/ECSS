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

    # Update OLD EC
    path('old_ec_application', views.old_ec_application, name='old_ec_application'),
    path('old_ec_application_form', views.old_ec_application_form, name='old_ec_application_form'),
    path('save_old_ec_general_details', views.save_old_ec_general_details, name='save_old_ec_general_details'),
    path('submit_old_ec_general_application', views.submit_old_ec_general_application, name='submit_old_ec_general_application'),
    path('check_old_ec', views.check_old_ec, name='check_old_ec'),

    # PENDING OLD DETAILS
    path('view_pending_old_ec_details', views.view_pending_old_ec_details, name='view_pending_old_ec_details'),


    # EC RENEWAL
    path('ec_renewal', views.ec_renewal, name='ec_renewal'),
    path('ec_renewal_details', views.ec_renewal_details, name='ec_renewal_details'),
    path('submit_renew_application', views.submit_renew_application, name='submit_renew_application'),
    path('save_renew_attachment', views.save_renew_attachment, name='save_renew_attachment'),
    path('save_renew_attachment_details', views.save_renew_attachment_details, name='save_renew_attachment_details'),
    path('save_compliance_details', views.save_compliance_details, name='save_compliance_details'),

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
    path('tor_form', views.tor_form, name='tor_form'),
    path('save_tor_form', views.save_tor_form, name='save_tor_form'),
    path('tor_list', views.tor_list, name='tor_list'),
    path('view_tor_application_details',views.view_tor_application_details, name='view_tor_application_details'),
    path('save_tor_attachment', views.save_tor_attachment, name='save_tor_attachment'),
    path('save_tor_attachment_details', views.save_tor_attachment_details, name='save_tor_attachment_details'),

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

    #EC PRint
    path('ec_print_list', views.ec_print_list, name='ec_print_list'),
    path('view_print_details', views.view_print_details, name='view_print_details'),

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
    path('revoke_ec', views.revoke_ec, name='revoke_ec'),

    #Payment_part
    path('ecss_payment_update', views.ecss_payment_update, name='ecss_payment_update'),
    path('ecss_payment_reversal', views.ecss_payment_reversal, name='ecss_payment_reversal')

]
