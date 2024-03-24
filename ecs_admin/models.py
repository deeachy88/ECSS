from django.core.files.storage import FileSystemStorage
from django.db import models

fs = FileSystemStorage()


# Create your models here.
class t_role_master(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100)
    is_active = models.CharField(max_length=3)

    def __str__(self):
        return self.role_name

class t_country_master(models.Model):
    country_id = models.AutoField(primary_key=True)
    country_name = models.CharField(max_length=100)


class t_app_status_master(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=100)
    status_type = models.CharField(max_length=20)
    status_type_short_desc = models.CharField(max_length=200)


class t_security_question_master(models.Model):
    question_id = models.AutoField(primary_key=True)
    question = models.CharField(max_length=100)

    def __str__(self):
        return self.question


class t_agency_master(models.Model):
    agency_id = models.AutoField(primary_key=True)
    agency_code = models.CharField(max_length=100)
    agency_name = models.CharField(max_length=100)
    agency_type = models.CharField(max_length=50)

class t_thromde_master(models.Model):
    thromde_id = models.AutoField(primary_key=True)
    thromde_name = models.CharField(max_length=100)


class t_proponent_type_master(models.Model):
    proponent_type_id = models.AutoField(primary_key=True)
    proponent_type_name = models.CharField(max_length=250)

class t_dzongkhag_master(models.Model):
    dzongkhag_code = models.AutoField(primary_key=True)
    dzongkhag_name = models.CharField(max_length=100,default=None)

    def __str__(self):
        return self.Dzongkhag_Name


class t_gewog_master(models.Model):
    gewog_code = models.AutoField(primary_key=True)
    gewog_name = models.CharField(max_length=100,default=None)
    dzongkhag_code = models.ForeignKey(t_dzongkhag_master, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.gewog_name


class t_village_master(models.Model):
    village_code = models.AutoField(primary_key=True)
    village_name = models.CharField(max_length=100,default=None)
    gewog_code = models.ForeignKey(t_gewog_master, on_delete=models.CASCADE, null=True, blank=True)
    village_name_dzo = models.CharField(max_length=100, default=None,blank=True,null=True)

    def __str__(self):
        return self.village_name

class t_section_master(models.Model):
    section_id = models.AutoField(primary_key=True)
    section_name = models.CharField(max_length=100)
    division_id = models.CharField(max_length=20)

class t_service_master(models.Model):
    service_id = models.AutoField(primary_key=True)
    service_name = models.CharField(max_length=100)

class t_fees_schedule(models.Model):
    fees_id = models.AutoField(primary_key=True)
    service_id = models.IntegerField()
    service_name = models.CharField(max_length=100)
    parameter = models.CharField(max_length=250)
    rate = models.IntegerField()
    application_fee = models.IntegerField()

class t_bsic_code(models.Model):
    bsic_id = models.AutoField(primary_key=True)
    broad_activity_code = models.CharField(max_length=10)
    activity_description = models.CharField(max_length=250)
    specific_activity_code = models.CharField(max_length=10)
    specific_activity_description = models.TextField()
    classification = models.CharField(max_length=10)
    category = models.TextField()
    colour_code = models.CharField(max_length=10)
    competent_authority = models.CharField(max_length=250)
    entry_point = models.CharField(max_length=10)
    service_id = models.IntegerField()
    has_tor = models.CharField(max_length=3,default=None, blank=True, null=True)


class t_competant_authority_master(models.Model):
    competent_authority_id = models.AutoField(primary_key=True)
    competent_authority = models.CharField(max_length=100)
    dzongkhag_code = models.ForeignKey(t_dzongkhag_master, on_delete=models.CASCADE, null=True, blank=True)
    remarks = models.CharField(max_length=250, default=None, blank=True, null=True)

class t_location_field_office_mapping(models.Model):
    location_code = models.AutoField(primary_key=True)
    location_name = models.CharField(max_length=100)
    dzongkhag_code = models.ForeignKey(t_dzongkhag_master, on_delete=models.CASCADE, null=True, blank=True)
    competent_authority_id = models.IntegerField(default=None, blank=True, null=True)

class t_user_type_master(models.Model):
    user_type_id = models.AutoField(primary_key=True)
    user_type = models.CharField(max_length=250)

class t_user_role_mapping(models.Model):
    user_role_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=20)
    role_id = models.IntegerField(default=None, blank=True, null=True)

class t_user_master(models.Model):
    login_id = models.AutoField(primary_key=True)
    login_type = models.TextField(default=None, blank=True, null=True)
    name = models.CharField(max_length=200, default=None, blank=True, null=True)
    agency_type = models.CharField(max_length=50, default=None, blank=True, null=True)
    agency_code = models.IntegerField(default=None, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    contact_number = models.IntegerField(default=None, blank=True, null=True)
    email_id = models.EmailField(default=None, blank=True, null=True)
    password = models.TextField(default=None, blank=True, null=True)
    cid = models.BigIntegerField(default=None, blank=True, null=True)
    role_id = models.ForeignKey(t_role_master, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.CharField(max_length=1, default=None, blank=True, null=True)
    logical_delete = models.CharField(max_length=1, default=None, blank=True, null=True)
    last_login_date = models.DateTimeField(default=None, blank=True, null=True)
    created_by = models.CharField(max_length=250, default=None, blank=True, null=True)
    created_on = models.DateField(default=None, blank=True, null=True)
    modified_by = models.CharField(max_length=250, default=None, blank=True, null=True)
    modified_on = models.DateField(default=None, blank=True, null=True)
    accept_reject = models.CharField(max_length=1, default=None, blank=True, null=True)
    dzongkhag_code = models.IntegerField(default=None, blank=True, null=True)
    gewog_code = models.IntegerField(default=None, blank=True, null=True)
    village_code = models.IntegerField(default=None, blank=True, null=True)
    i_dzongkhag = models.CharField(max_length=100, default=None, blank=True, null=True)
    i_gewog = models.CharField(max_length=100, default=None, blank=True, null=True)
    i_village = models.CharField(max_length=100, default=None, blank=True, null=True)
    proponent_type = models.IntegerField(default=None, blank=True, null=True)
    proponent_name = models.CharField(max_length=255, default=None, blank=True, null=True)
    contact_person = models.CharField(max_length=255, default=None, blank=True, null=True)
    address = models.TextField(max_length=250, default=None, blank=True, null=True)


class t_forgot_password(models.Model):
    forgot_pass_id = models.AutoField(primary_key=True)
    login_id = models.IntegerField()
    security_question_id = models.IntegerField()
    answer = models.CharField(max_length=250)


class t_menu_master(models.Model):
    menu_id = models.AutoField(primary_key=True)
    menu_name = models.CharField(max_length=250, default=None, blank=True, null=True)
    menu_content = models.TextField(default=None, blank=True, null=True)
    is_active = models.CharField(max_length=3, default=None, blank=True, null=True)
    has_sub_menu = models.CharField(max_length=3, default=None, blank=True, null=True)
    document_id = models.IntegerField(blank=True, null=True)
    is_deleted = models.CharField(max_length=3, default=None, blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)

class t_submenu_master(models.Model):
    sub_menu_id = models.AutoField(primary_key=True)
    menu_id = models.IntegerField(blank=True, null=True)
    sub_menu_name = models.CharField(max_length=250, default=None, blank=True, null=True)
    sub_menu_content = models.TextField(max_length=250, default=None, blank=True, null=True)
    is_active = models.CharField(max_length=3, default=None, blank=True, null=True)
    document_id = models.IntegerField(blank=True, null=True)
    is_deleted = models.CharField(max_length=3, default=None, blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)

class t_homepage_master(models.Model):
    homepage_id = models.AutoField(primary_key=True)
    homepage_title = models.CharField(max_length=250, default=None, blank=True, null=True)
    homepage_content = models.TextField(max_length=250, default=None, blank=True, null=True)
    is_active = models.CharField(max_length=3, default=None, blank=True, null=True)
    document_id = models.IntegerField(blank=True, null=True)
    is_deleted = models.CharField(max_length=3, default=None, blank=True, null=True)

class t_file_attachment(models.Model):
    file_id = models.AutoField(primary_key=True)
    application_no = models.CharField(max_length=100, default=None, blank=True, null=True)
    file_path = models.CharField(max_length=250)
    attachment = models.FileField(storage=fs)
    attachment_type = models.CharField(max_length=100, blank=True, null=True)
    document_id = models.IntegerField(blank=True, null=True)


class t_other_details(models.Model):
    others_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255, default=None, blank=True, null=True)
    title = models.CharField(max_length=255, default=None, blank=True, null=True)
    document_id = models.BigIntegerField(blank=True, null=True)
    is_active = models.CharField(max_length=3, default=None, blank=True, null=True)
    is_deleted = models.CharField(max_length=3, default=None, blank=True, null=True)

class t_error_log(models.Model):
    error_code = models.AutoField(primary_key=True)
    error_detail = models.CharField(max_length=255, default=None, blank=True, null=True)
    created_by = models.CharField(max_length=100, default=None, blank=True, null=True)
    created_date = models.DateField(default=None, blank=True, null=True)

class t_about_us(models.Model):
    about_us_id = models.AutoField(primary_key=True)
    about_us_title = models.CharField(max_length=100, default=None, blank=True, null=True)
    about_us_content = models.TextField(default=None, blank=True, null=True)
    is_active = models.CharField(max_length=3, default=None, blank=True, null=True)
    is_deleted = models.CharField(max_length=3, default=None, blank=True, null=True)

class t_notification_details(models.Model):
    notification_id = models.AutoField(primary_key=True)
    notification_title = models.CharField(max_length=100, default=None, blank=True, null=True)
    notification_content = models.TextField(default=None, blank=True, null=True)
    document_id = models.BigIntegerField(blank=True, null=True)
    is_active = models.CharField(max_length=3, default=None, blank=True, null=True)
    is_deleted = models.CharField(max_length=3, default=None, blank=True, null=True)
    notification_date = models.CharField(max_length=10, default=None, blank=True, null=True)

class payment_details_master(models.Model):
    record_id = models.AutoField(primary_key=True)
    account_head_name = models.CharField(max_length=250, default=None, blank=True, null=True)
    account_head_code = models.BigIntegerField(default=None, blank=True, null=True)
    payment_type = models.CharField(max_length=250, default=None, blank=True, null=True)