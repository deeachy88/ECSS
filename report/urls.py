
from django.conf.urls.static import static
from django.urls import path
from . import views
from ECS import settings

urlpatterns = [

#Report
    path('ec_report_form', views.ec_report_form, name='ec_report_form'),
    path('view_ec_list', views.view_ec_list, name='view_ec_list'),
    path('ec_rejected_report_form', views.ec_rejected_report_form, name='ec_rejected_report_form'),
    path('ec_pending_report_form', views.ec_pending_report_form, name='ec_pending_report_form'),
    path('land_use_report_form', views.land_use_report_form, name='land_use_report_form'),
    path('revenue_report_form', views.revenue_report_form, name='revenue_report_form'),

]
