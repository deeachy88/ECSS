from django.http import JsonResponse
from django.shortcuts import redirect, render
from proponent.models import t_ec_industries_t10_hazardous_chemicals, t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, t_ec_industries_t9_products_by_products, t_payment_details, t_workflow_dtls
from ecs_admin.models import t_dzongkhag_master, t_gewog_master, t_role_master, t_service_master, t_user_master, t_village_master
from django.utils import timezone
from datetime import date
from django.core.mail import send_mail

# Create your views here.
def verify_application_list(request):
    application_list = t_workflow_dtls.objects.all(application_status='P', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    return render(request, application_list.html,{'application_list':application_list, 'service_details':service_details})

def reviewer_application_list(request):
    application_list = t_workflow_dtls.objects.all(application_status='P', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    return render(request, application_list.html,{'application_list':application_list, 'service_details':service_details})

def approver_application_list(request):
    application_list = t_workflow_dtls.objects.all(application_status='P', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    return render(request, application_list.html,{'application_list':application_list, 'service_details':service_details})

def resubmit_application_list(request):
    application_list = t_workflow_dtls.objects.all(application_status='P', action_date__isnull=False)
    service_details = t_service_master.objects.all()
    return render(request, application_list.html,{'application_list':application_list, 'service_details':service_details})

def payment_list(request):
    payment_details = t_payment_details.objects.filter(receipt_no__isnull=True)
    return render(request, 'payment_details.html', {'payment_details': payment_details})

def view_application_details(request):
    application_no = request.POST.get('application_no')
    service_id = request.POST.get('service_id')

    if service_id == '1':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()

        return render(request, 'industry_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '2':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'energy_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '3':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'road_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '4':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'transmission_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '5':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'tourism_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '6':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'ground_water_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '7':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'forest_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '8':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'quarry_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '9':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'general_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '10':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'renewal_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '11':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'name_change_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})
    elif service_id == '12':
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        partner_details = t_ec_industries_t2_partner_details.objects.all()
        machine_equipment = t_ec_industries_t3_machine_equipment.objects.all()
        project_product = t_ec_industries_t4_project_product.objects.all()
        raw_materials = t_ec_industries_t5_raw_materials.objects.all()
        ancillary_road = t_ec_industries_t6_ancillary_road.objects.all()
        power_line = t_ec_industries_t7_ancillary_power_line.objects.all()
        forest_produce = t_ec_industries_t8_forest_produce
        products_by_products = t_ec_industries_t9_products_by_products
        hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        return render(request, 'ownwership_change_application_details.html',{'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,
                                                     'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'forest_produce':forest_produce, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals})


def forward_application(request):
    application_no = request.POST.get('application_no')
    forwardTo = request.POST.get('forwardTo')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(assigned_to=forwardTo, assigned_date=date.today(), assigned_by=request.session['email'])
    user_details = t_user_master.objects.filter(login_id=forwardTo)
    for users in user_details:
        role_id = users.role_id
        role_details = t_role_master.objects.filter(role_id=role_id)
        for role in role_details:
            role_name = role.role_name
        workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
        workflow_details.update(assigned_user_id=forwardTo)
        workflow_details.update(assigned_role_id=role_id)
        workflow_details.update(assigned_role_name=role_name)
        workflow_details.update(action_date=date.today())
        workflow_details.update(actor_id=request.session['login_id'])
        workflow_details.update(actor_name=request.session['name'])
    return redirect(verify_application_list)

def approve_application(request):
    application_no = request.POST.get('application_no')
    ec_no = get_ec_no(request)

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(ec_no=ec_no, ec_approve_date=date.today(),application_status='A')
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    workflow_details.update(assigned_user_id=None)
    workflow_details.update(assigned_role_id=None)
    workflow_details.update(assigned_role_name=None)
    workflow_details.update(action_date=date.today())
    workflow_details.update(actor_id=request.session['login_id'])
    workflow_details.update(actor_name=request.session['name'])
    workflow_details.update(status_id='A')
    for work_details in workflow_details:
        service_id = work_details.service_id
        service_details = t_service_master.objects.filter(service_id=service_id)
        for service in service_details:
            service_name = service.service_name
            for email_id in application_details:
                emailId = email_id.email
                send_ec_approve_email(ec_no, emailId, application_no, service_name)
                insert_payment_details(application_no, ec_no, service_name)
    return redirect(approver_application_list)

def resubmit_application(request):
    application_no = request.POST.get('application_no')
    remarks = request.POST.get('resubmit_remarks')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(resubmit_remarks=remarks)
    application_details.update(resubmit_date=date.today())

    for details in application_details:
        email = details.applicant_id
        user_details = t_user_master.objects.filter(email_id=email)
        for users in user_details:
            login_id = users.login_id
        workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
        workflow_details.update(assigned_user_id=login_id)
        workflow_details.update(assigned_role_id=None)
        workflow_details.update(assigned_role_name=None)
        workflow_details.update(action_date=date.today())
        workflow_details.update(actor_id=request.session['login_id'])
        workflow_details.update(actor_name=request.session['name'])
        for work_details in workflow_details:
            service_id = work_details.service_id
            service_details = t_service_master.objects.filter(service_id=service_id)
            for service in service_details:
                service_name = service.service_name
                send_ec_resubmission_email(email, application_no, service_name)
    return redirect(resubmit_application_list)

def insert_payment_details(application_no, ec_no):
    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    for application in application_details:
        application_details.update(
            application_type= application.application_type,
            application_no=application_no,
            application_date=application.application_date, 
            proponent_name=application.applicant_name,
            ec_no=ec_no 
        )
    return redirect(approver_application_list)

def validate_receipt_no(request):
    data = dict()
    receipt_no = request.GET.get('receipt_no')
    receipt_no_count = t_payment_details.objects.filter(receipt_no=receipt_no).count()

    if receipt_no_count > 0:
        data['status'] = "Exists"
    else:
        data['status'] = "No Exists"
    return JsonResponse(data)


def update_payment_details(request):
    Application_No = request.POST.get('application_no')
    payment_type = request.POST.get('payment_type')
    transaction_no = request.POST.get('transaction_no')
    amount = request.POST.get('amount')
    instrument_no = request.POST.get('instrument_no')
    transaction_date = request.POST.get('transaction_date')
    payment_details = t_payment_details.objects.filter(application_no=Application_No)
    payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                               instrument_no=instrument_no, transaction_date=transaction_date)
    return redirect(payment_list)

def get_ec_no(request):
    agency_code = request.session['agency_code']
    last_ec_no = t_ec_industries_t1_general.objects.aggregate(Max('ec_reference_no'))
    lastECNo = last_ec_no['ec_reference_no__max']
    if not lastECNo:
        year = timezone.now().year
        newECNo = agency_code + "-" + "EC" + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastECNo)[13:17]
        substring = int(substring) + 1
        ecNo = str(substring).zfill(4)
        year = timezone.now().year
        newECNo = agency_code + "-" + "EC" + "-" + str(year) + "-" + ecNo
    return newECNo

def send_ec_approve_email(ec_no, email, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " And EC Clearance No is:" + ec_no + \
              " Please Make Payment. Visit The Nearest EC Office For Payment " 
    recipient_list = [email]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)
    
def send_ec_resubmission_email(email, application_no, service_name):
    subject = 'APPLICATION RESUBMISSION'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Having" \
              " Application No " + application_no + " Has Been Sent For Resubmission. Please Check The Application And Resubmit It."
    recipient_list = [email]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)
