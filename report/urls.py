
from django.conf.urls.static import static
from django.urls import path
from . import views
from ECS import settings

urlpatterns = [

#Report
    path('ec_report_form', views.ec_report_form, name='ec_report_form'),
    path('view_ec_list', views.view_ec_list, name='view_ec_list'),
    path('ec_reject_report_form', views.ec_reject_report_form, name='ec_reject_report_form'),
    path('view_ec_reject_list', views.view_ec_reject_list, name='view_ec_reject_list'),
    path('ec_pending_report_form', views.ec_pending_report_form, name='ec_pending_report_form'),
    path('ec_pending_list', views.ec_pending_list, name='ec_pending_list'),
    path('land_use_report_form', views.land_use_report_form, name='land_use_report_form'),
    path('land_use_report', views.land_use_report, name='land_use_report'),
    path('revenue_report_form', views.revenue_report_form, name='revenue_report_form'),
    path('revenue_report', views.revenue_report, name='revenue_report'),

#Application Status
    path('application_status_list', views.application_status_list, name='application_status_list'),
    path('application_status', views.application_status, name='application_status'),

#Application Status
    path('application_history', views.application_history, name='application_history'),

]
