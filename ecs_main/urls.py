from django.conf.urls.static import static
from django.urls import path
from . import views
from ECS import settings

urlpatterns = [
    path('verify_application_list', views.verify_application_list, name='verify_application_list'),
    path('client_application_list', views.client_application_list, name='client_application_list'),
    path('reviewer_application_list', views.reviewer_application_list, name='reviewer_application_list'),
    #IBLS APPLICATION LIST
    path('ibls_application_list', views.ibls_application_list, name='ibls_application_list'),

    path('view_application_details', views.view_application_details, name='view_application_details'),
    path('forward_application', views.forward_application, name='forward_application'),
    path('resubmit_application', views.resubmit_application, name='resubmit_application'),
    path('update_payment_details', views.update_payment_details, name='update_payment_details'),
    path('validate_receipt_no', views.validate_receipt_no, name='validate_receipt_no'),
    path('save_eatc_attachment', views.save_eatc_attachment, name='save_eatc_attachment'),
    path('save_eatc_attachment_details', views.save_eatc_attachment_details, name='save_eatc_attachment_details'),
    path('save_draft_ec_details', views.save_draft_ec_details, name='save_draft_ec_details'),
    path('update_draft_ec_details', views.update_draft_ec_details, name='update_draft_ec_details'),
    path('delete_draft_ec_details', views.delete_draft_ec_details, name='delete_draft_ec_details'),
    path('save_lu_attachment', views.save_lu_attachment, name='save_lu_attachment'),
    path('save_lu_attachment_details', views.save_lu_attachment_details, name='save_lu_attachment_details'),
    path('save_rev_lu_attachment', views.save_rev_lu_attachment, name='save_rev_lu_attachment'),
    path('save_rev_lu_attachment_details', views.save_rev_lu_attachment_details, name='save_rev_lu_attachment_details'),
    path('delete_rev_lu_attachment', views.delete_rev_lu_attachment, name='delete_rev_lu_attachment'),
    path('delete_lu_attachment', views.delete_lu_attachment, name='delete_lu_attachment'),
    path('save_ai_attachment', views.save_ai_attachment, name='save_ai_attachment'),
    path('save_ai_attachment_details', views.save_ai_attachment_details, name='save_ai_attachment_details'),
    path('delete_ai_attachment', views.delete_ai_attachment, name='delete_ai_attachment'),
    path('save_rev_tor_attachment', views.save_rev_tor_attachment, name='save_rev_tor_attachment'),
    path('save_rev_tor_attachment_details', views.save_rev_tor_attachment_details, name='save_rev_tor_attachment_details'),
    path('delete_rev_tor_attachment', views.delete_rev_tor_attachment, name='delete_rev_tor_attachment'),

#InspectionMonitoring
    path('inspection_submission_form', views.inspection_submission_form, name='inspection_submission_form'),
    path('view_inspection_details', views.view_inspection_details, name='view_inspection_details'),
    path('inspection_list', views.inspection_list, name='inspection_list'),
    path('add_inspection', views.add_inspection, name='add_inspection'),
    path('get_inspection_details/<str:record_id>', views.get_inspection_details, name='get_inspection_details'),
    path('load_inspection_attachment_details', views.load_inspection_attachment_details, name='load_inspection_attachment_details'),
    path('load_ec_details', views.load_ec_details, name='load_ec_details'),
    path('edit_inspection', views.edit_inspection, name='edit_inspection'),
    path('delete_inspection', views.delete_inspection, name='delete_inspection'),
    path('submit_inspection_form', views.submit_inspection_form, name='submit_inspection_form'),


#fines and penalties
    path('fines_penalties', views.fines_penalties, name='fines_penalties'),
    path('get_fines_penalties_details', views.get_fines_penalties_details, name='get_fines_penalties_details'),
    path('save_fines_penalties', views.save_fines_penalties, name='save_fines_penalties'),
    
#TOR Details
    path('tor_to_verifier',views.tor_to_verifier, name='tor_to_verifier'),
    path('approve_tor_application', views.approve_tor_application, name='approve_tor_application'),

# Payment Details
    path('payment_list', views.payment_list, name='payment_list'),

# EC Expired List
    path('ec_expired_list', views.ec_expired_list, name='ec_expired_list'),
]