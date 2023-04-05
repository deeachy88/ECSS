from django.conf.urls.static import static
from django.urls import path
from . import views
from ECS import settings

urlpatterns = [
    path('verify_application_list', views.verify_application_list, name='verify_application_list'),
    path('client_application_list', views.client_application_list, name='client_application_list'),
    path('reviewer_application_list', views.reviewer_application_list, name='reviewer_application_list'),
    path('view_application_details', views.view_application_details, name='view_application_details'),
    path('forward_application', views.forward_application, name='forward_application'),
    path('approve_application', views.approve_application, name='approve_application'),
    path('resubmit_application', views.resubmit_application, name='resubmit_application'),
    path('update_payment_details', views.update_payment_details, name='update_payment_details'),
    path('validate_receipt_no', views.validate_receipt_no, name='validate_receipt_no'),
    path('save_eatc_attachment', views.save_eatc_attachment, name='save_eatc_attachment'),
    path('save_eatc_attachment_details', views.save_eatc_attachment_details, name='save_eatc_attachment_details'),
    path('save_draft_ec_attachment', views.save_draft_ec_attachment, name='save_draft_ec_attachment'),
    path('save_draft_ec_attachment_details', views.save_draft_ec_attachment_details, name='save_draft_ec_attachment_details'),
    path('save_lu_attachment', views.save_lu_attachment, name='save_lu_attachment'),
    path('save_lu_attachment_details', views.save_lu_attachment_details, name='save_lu_attachment_details'),

#InspectionMonitoring
    path('inspection_list', views.inspection_list, name='inspection_list'),
    path('add_inspection', views.add_inspection, name='add_inspection'),
    path('get_inspection_details/<int:record_id>', views.get_inspection_details, name='get_inspection_details'),
    path('load_ec_details', views.load_ec_details, name='load_ec_details'),
    path('edit_inspection', views.edit_inspection, name='edit_inspection'),
    path('delete_inspection', views.delete_inspection, name='delete_inspection'),

#fines and penalties
    path('get_fines_penalties_details', views.get_fines_penalties_details, name='get_fines_penalties_details'),
    path('save_fines_penalties', views.save_fines_penalties, name='save_fines_penalties'),
    
#TOR Details
    path('tor_to_verifier',views.tor_to_verifier, name='tor_to_verifier'),
    path('approve_tor_application', views.approve_tor_application, name='approve_tor_application')

]