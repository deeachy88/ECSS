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
    path('validate_receipt_no', views.validate_receipt_no, name='validate_receipt_no')
]