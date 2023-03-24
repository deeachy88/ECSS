from django.conf.urls.static import static
from django.urls import path
from . import views
from ECS import settings

urlpatterns = [
    path('verify_application_list', views.verify_application_list, name='verify_application_list'),
    path('reviewer_application_list', views.reviewer_application_list, name='reviewer_application_list'),
    path('approver_application_list', views.approver_application_list, name='approver_application_list'),
    path('resubmit_application_list', views.resubmit_application_list, name='resubmit_application_list'),
    path('view_application_details', views.view_application_details, name='view_application_details'),
    path('forward_application', views.forward_application, name='forward_application'),
    path('approve_application', views.approve_application, name='approve_application'),
    path('resubmit_application', views.resubmit_application, name='resubmit_application'),
    path('update_payment_details', views.update_payment_details, name='update_payment_details'),
    path('validate_receipt_no', views.validate_receipt_no, name='validate_receipt_no'),

#InspectionMonitoring
    path('inspection_list', views.inspection_list, name='inspection_list'),
    path('add_inspection', views.add_inspection, name='add_inspection'),
    path('get_inspection_details/<int:record_id>', views.get_inspection_details, name='get_inspection_details'),
    path('load_ec_details', views.load_ec_details, name='load_ec_details'),
    path('edit_inspection', views.edit_inspection, name='edit_inspection'),
    path('delete_inspection', views.delete_inspection, name='delete_inspection'),


]