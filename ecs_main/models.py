from django.core.files.storage import FileSystemStorage
from django.db import models

fs = FileSystemStorage()

class t_inspection_monitoring_t1(models.Model):
    record_id = models.AutoField(primary_key=True)
    inspection_type = models.CharField(max_length=100,default=None, blank=True, null=True)
    inspection_date = models.DateField(default=None, blank=True, null=True)
    inspection_reason = models.CharField(max_length=100,default=None, blank=True, null=True)
    ec_clearance_no = models.CharField(max_length=100,default=None, blank=True, null=True)
    login_id = models.CharField(max_length=100,default=None, blank=True, null=True)
    proponent_name = models.CharField(max_length=250,default=None, blank=True, null=True)
    project_name = models.TextField(max_length=250, default=None, blank=True, null=True)
    address = models.TextField(max_length=500, default=None, blank=True, null=True)
    observation = models.TextField(max_length=500,default=None, blank=True, null=True)
    team_leader = models.CharField(max_length=100,default=None, blank=True, null=True)
    team_members = models.CharField(max_length=500,default=None, blank=True, null=True)
    remarks = models.CharField(max_length=500,default=None, blank=True, null=True)
    fines_penalties = models.CharField(max_length=100,default=None, blank=True, null=True)
    status = models.CharField(max_length=100,default=None, blank=True, null=True)
    updated_by_ca = models.CharField(max_length=100,default=None, blank=True, null=True)
    record_status = models.CharField(max_length=10,default=None, blank=True, null=True)
    inspection_reference_no = models.CharField(max_length=100, default=None, blank=True, null=True)
    updated_on = models.DateField(default=None, blank=True, null=True)

class t_application_history(models.Model):
    record_id = models.AutoField(primary_key=True)
    application_no = models.CharField(max_length=100, default=None, blank=True, null=True)
    application_date = models.DateField(default=None, blank=True, null=True)
    applicant_id = models.CharField(max_length=100, default=None, blank=True, null=True)
    ca_authority = models.CharField(max_length=100, default=None, blank=True, null=True)
    service_id = models.IntegerField(default=None, blank=True, null=True)
    application_status = models.CharField(max_length=10, default=None, blank=True, null=True)
    action_date = models.DateField(default=None, blank=True, null=True)
    actor_id = models.IntegerField(default=None, blank=True, null=True)
    actor_name = models.CharField(max_length=100, default=None, blank=True, null=True)
    remarks = models.TextField(default=None, blank=True, null=True)
    status = models.CharField(max_length=100, default=None, blank=True, null=True)

