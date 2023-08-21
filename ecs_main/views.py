from django.http import JsonResponse
from django.shortcuts import redirect, render
from ecs_admin.views import bsic_master
from proponent.models import t_ec_industries_t10_hazardous_chemicals, t_ec_industries_t11_ec_details, t_ec_industries_t13_dumpyard, t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, t_ec_industries_t9_products_by_products, t_ec_renewal_t1, t_ec_renewal_t2, t_fines_penalties, t_payment_details, t_workflow_dtls, t_workflow_dtls_audit
from ecs_admin.models import t_bsic_code, t_dzongkhag_master, t_file_attachment, t_gewog_master, t_role_master, t_service_master, t_thromde_master, t_user_master, t_village_master
from ecs_main.models import t_application_history, t_inspection_monitoring_t1
from django.utils import timezone
from datetime import date
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from datetime import datetime, timedelta

# Create your views here.
def verify_application_list(request):
    ca_authority = request.session['ca_authority']
    application_list = t_workflow_dtls.objects.filter(application_status='P', assigned_role_id='2', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='DEC',assigned_role_id='2', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='AL',assigned_role_id='2', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='FT',assigned_role_id='2', action_date__isnull=False,ca_authority=ca_authority)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(application_type='AP')
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=ca_authority,
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'application_list.html',{'application_details':application_list,'v_application_count':v_application_count, 'service_details':service_details, 'payment_details':payment_details,'ec_renewal_count':ec_renewal_count})

def client_application_list(request):
    login_id = request.session['login_id']
    application_list = t_workflow_dtls.objects.filter(application_status='ALR', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='ALA', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='EATC', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='RS', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='LU', action_date__isnull=False,assigned_user_id=login_id)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(application_type='AP')
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=login_id).count()
    return render(request, 'application_list.html',{'application_details':application_list,'cl_application_count':cl_application_count,'app_hist_count':app_hist_count, 'service_details':service_details, 'payment_details':payment_details})

def reviewer_application_list(request):
    ca_authority = request.session['ca_authority']
    login_id = request.session['login_id']
    application_list = t_workflow_dtls.objects.filter(application_status='R',assigned_role_id='3', action_date__isnull=False,ca_authority=ca_authority,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='ALS',assigned_role_id='3', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='FEATC',assigned_role_id='3', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='RSS',assigned_role_id='3', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='LUS',assigned_role_id='3', action_date__isnull=False,ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='APP',assigned_role_id='3', action_date__isnull=False,ca_authority=ca_authority)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(application_type='AP')
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    return render(request, 'application_list.html', {'application_details':application_list,'r_application_count':r_application_count, 'service_details':service_details, 'payment_details':payment_details})

# def payment_list(request):
#     login_id = request.session['login_id']
#     payment_details = t_payment_details.objects.filter(transaction_no__isnull=True)
#     service_details = t_service_master.objects.all()
#     return render(request, 'payment_list.html', {'payment_details': payment_details,'service_details':service_details})

def payment_list(request):
    login_id = request.session['email']
    print(login_id)
    payment_details = t_payment_details.objects.filter(
        transaction_no__isnull=True,
        application_no__in=t_ec_industries_t1_general.objects.filter(applicant_id=login_id).values('application_no')
    )
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
    return render(request, 'payment_list.html',
                  {'payment_details': payment_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'service_details': service_details})

def view_application_details(request):
    application_no = request.GET.get('application_no')
    service_id = request.GET.get('service_id')
    application_source = request.GET.get('application_source')
    status = None
    ca_auth = None

    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    for work_details in workflow_details:
        status = work_details.application_status
        ca_auth = work_details.ca_authority
        assigned_role_id = work_details.assigned_role_id

        if service_id == '1':
            if application_source == 'IBLS':
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
                ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
                anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
                anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
                anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
                for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
                gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
                ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
                ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
                reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
                eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
                lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
                rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'ea_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials, 'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                            'project_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details,'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach, 'rev_lu_attach':rev_lu_attach})
            else:
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
                ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
                partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
                machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
                project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
                raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
                anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
                anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
                forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
                products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
                hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
                dzongkhag = t_dzongkhag_master.objects.all()
                gewog = t_gewog_master.objects.all()
                village = t_village_master.objects.all()
                file_attach = t_file_attachment.objects.filter(attachment_type='IEE')
                anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
                for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
                gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
                ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
                ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
                reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
                eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
                lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
                rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'iee_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                            'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '2':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='ENR')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'energy_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '3':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            ec_details = t_ec_industries_t11_ec_details.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'road_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '4':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'transmission_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '5':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'tourism_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '6':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'ground_water_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '7':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count() 
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count() 
            return render(request, 'forest_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '8':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.filter(application_no=application_no).order_by('record_id')
            products_by_products = t_ec_industries_t9_products_by_products.filter(application_no=application_no).order_by('record_id')
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.filter(application_no=application_no).order_by('record_id')
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by('record_id')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='QUA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no,form_type='Main Activity')
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'quarry_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '9':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,form_type='Ancillary')
            partner_details = t_ec_industries_t2_partner_details.objects.filter(application_no=application_no)
            machine_equipment = t_ec_industries_t3_machine_equipment.objects.filter(application_no=application_no)
            project_product = t_ec_industries_t4_project_product.objects.filter(application_no=application_no)
            raw_materials = t_ec_industries_t5_raw_materials.objects.filter(application_no=application_no)
            ancillary_road = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no)
            power_line = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no)
            forest_produce = t_ec_industries_t8_forest_produce.objects.filter(application_no=application_no)
            products_by_products = t_ec_industries_t9_products_by_products.objects.filter(application_no=application_no)
            hazardous_chemicals = t_ec_industries_t10_hazardous_chemicals.objects.filter(application_no=application_no)
            anc_road_details = t_ec_industries_t6_ancillary_road.objects.filter(application_no=application_no).order_by('record_id')
            anc_power_line_details = t_ec_industries_t7_ancillary_power_line.objects.filter(application_no=application_no).order_by('record_id')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            file_attach = t_file_attachment.objects.filter(attachment_type='IEA')
            anc_file_attach = t_file_attachment.objects.filter(attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(attachment_type='IEEANC')
            dumpyard_details = t_ec_industries_t13_dumpyard.objects.filter(application_no=application_no).order_by('record_id')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'general_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'dumpyard_details':dumpyard_details,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce, 'products_by_products': products_by_products,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '10':
            renewal_details_one = t_ec_renewal_t1.objects.filter(application_no=application_no)
            for renewal_details_one in renewal_details_one:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=renewal_details_one.ec_reference_no,form_type='Main Activity')
            renewal_details_two = t_ec_renewal_t2.objects.filter(application_no=application_no)
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ECR')
            reviewer_list = t_user_master.objects.filter(role_id='3')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'renewal_application_details.html',{'application_details':application_details,'renewal_details_one':renewal_details_one,'status':status,
                                                                       'dzongkhag':dzongkhag,'gewog':gewog,'village':village,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'renewal_details_two':renewal_details_two,'reviewer_list':reviewer_list,'file_attach':file_attach ,'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '0':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            thromde = t_thromde_master.objects.all()
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            file_attach = t_file_attachment.objects.filter(attachment_type='TOR')

            return render(request, 'tor_form_details.html', {'application_details':application_details,'file_attach':file_attach,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'reviewer_list':reviewer_list,'assigned_role_id':assigned_role_id, 'status':status})


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
    return redirect(reviewer_application_list)



def validate_receipt_no(request):
    data = dict()
    receipt_no = request.GET.get('receipt_no')
    receipt_no_count = t_payment_details.objects.filter(transaction_no=receipt_no).count()

    if receipt_no_count > 0:
        data['status'] = "Exists"
    else:
        data['status'] = "No Exists"
    return JsonResponse(data)


def update_payment_details(request):
    application_no = request.POST.get('application_no')
    payment_type = request.POST.get('payment_type')
    transaction_no = request.POST.get('transaction_no')
    amount = request.POST.get('amount')
    instrument_no = request.POST.get('instrument_no')
    transaction_date = request.POST.get('transaction_date')
    applicant = None
    payment_details = t_payment_details.objects.filter(application_no=application_no, application_type='AP')
    if payment_details.exists():
        payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                               instrument_no=instrument_no, transaction_date=transaction_date)
        work_details = t_workflow_dtls.objects.filter(application_no=application_no)
        work_details.update(application_status='APP')
        work_details.update(assigned_role_id='3')
        work_details.update(assigned_role_name='Reviewer')
        work_details.update(action_date=date.today())
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, form_type='Main Activity')
        application_details.update(application_status='APP')
        application_details.update(action_date=date.today())
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        for app_det in application_details:
            applicant = app_det.applicant_id
            service_id = app_det.service_id
            ca_auth = app_det.ca_authorty
        t_application_history.objects.create(application_no=application_no,
                application_status='APP',
                action_date=date.today(),
                actor_id=request.session['login_id'], 
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks='Additional Payment Made',
                service_id=service_id,
                ca_authorty=ca_auth)
    else:
        payment_details = t_payment_details.objects.filter(application_no=application_no)
        payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                                instrument_no=instrument_no, transaction_date=transaction_date)
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        for app_det in application_details:
            applicant = app_det.applicant_id
            service_id = app_det.service_id
            ca_auth = app_det.ca_authorty
        t_application_history.objects.create(application_no=application_no,
                application_status='PAY',
                action_date=date.today(),
                actor_id=request.session['login_id'], 
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks='Payment Made',
                service_id=service_id,
                ca_authorty=ca_auth)
    return redirect(payment_list)

def get_ec_no(request):
    last_ec_no = t_ec_industries_t1_general.objects.aggregate(Max('ec_reference_no'))
    lastECNo = last_ec_no['ec_reference_no__max']
    if not lastECNo:
        year = timezone.now().year
        newECNo = "EC" + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastECNo)[9:12]
        substring = int(substring) + 1
        ecNo = str(substring).zfill(4)
        year = timezone.now().year
        newECNo ="EC" + "-" + str(year) + "-" + ecNo
    return newECNo

def send_ec_ap_email(ec_no, email, application_no, service_name, addtional_payment_amount):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Has Additional Payment. Your " \
              " Amount is " + str(addtional_payment_amount) + " Please Make Payment To Proceed Further"\
              " . " 
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    

def send_ec_approve_email(ec_no, email, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " And EC Clearance No is:" + ec_no + \
              " . " 
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
def send_tor_approve_email(ec_no, email, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your TOR Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + \
              " . " 
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
    
def send_ec_resubmission_email(email, application_no, service_name):
    subject = 'APPLICATION RESUBMISSION'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Having" \
              " Application No " + application_no + " Has Been Sent For Resubmission. Please Check The Application And Resubmit It."
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
def save_eatc_attachment(request):
    data = dict()
    eatc_attach = request.FILES['eatc_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + eatc_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/EATC/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, eatc_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/EATC" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)
    

def save_eatc_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='EATC')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')

    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def forward_application(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        identifier = request.POST.get('identifier')
        forward_to = request.POST.get('forward_to')
        applicant = None
        
        workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
        if identifier == 'R':
            workflow_details.update(application_status='R', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=forward_to, assigned_role_id='3',assigned_role_name='Reviewer')
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='R')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_no=application_no,
                        application_status='R',
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='To Reviewer',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'AL':
            additional_info_letter = request.POST.get('additional_info_letter')
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(additional_info_letter=additional_info_letter,application_status='AL')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='AL',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Addtional Info Required',
                        service_id=service_id)
            workflow_details.update(application_status='AL', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='2',assigned_role_name='Verifier')
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'ALA':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(ai_date=date.today(),application_status='ALA')
            for app_details in application_details:
                app_id = app_details.applicant_id
                applicant = app_details.applicant_id
                service_id = app_details.service_id
                user_details = t_user_master.objects.filter(email_id=app_id)
                for user_details in user_details:
                    login_id = user_details.login_id
                    workflow_details.update(application_status='ALA', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='ALA',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Addtional Info Approved',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'ALR':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(ai_date=date.today(),application_status='ALR')
            for app_details in application_details:
                app_id = app_details.applicant_id
                applicant = app_details.applicant_id
                service_id = app_details.service_id
                user_details = t_user_master.objects.filter(email_id=app_id)
                for user_details in user_details:
                    login_id = user_details.login_id
                    workflow_details.update(application_status='ALR', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='ALR',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Addtional Info Rejected',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'ALS':
            additional_info = request.POST.get('additional_info')
            application_details.update(resubmit_date=date.today())
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(additional_info=additional_info,application_status='ALS')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='ALS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Addtional Info Submitted',
                        service_id=service_id)
            workflow_details.update(application_status='ALS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'EATC':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='EATC')
            for app_details in application_details:
                app_id = app_details.applicant_id
                applicant = app_details.applicant_id
                service_id = app_details.service_id
                user_details = t_user_master.objects.filter(email_id=app_id)
                for user_details in user_details:
                    login_id = user_details.login_id
                    workflow_details.update(application_status='EATC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='EATC',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='EATC Attach Requested',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'FEATC':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='FEATC')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='FEATC',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='EATC Attachment Made',
                        service_id=service_id)
            workflow_details.update(application_status='FEATC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'RS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='RS')
            for app_details in application_details:
                app_id = app_details.applicant_id
                applicant = app_details.applicant_id
                service_id = app_details.service_id
                user_details = t_user_master.objects.filter(email_id=app_id)
                for user_details in user_details:
                    login_id = user_details.login_id
                    workflow_details.update(application_status='RS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='RS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Resumit Application For Clearification',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'RSS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='RSS')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='RSS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Application Resubmitted',
                        service_id=service_id)
            resubmit_remarks = request.POST.get('resubmit_remarks')
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(resubmit_remarks=resubmit_remarks)
            application_details.update(resubmit_date=date.today())
            workflow_details.update(application_status='RSS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'AP':
            addtional_payment_amount = request.POST.get('addtional_payment_amount')
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='AP')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='AP',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Additional Payment Required',
                        service_id=service_id)
            workflow_details.update(assigned_user_id=None)
            workflow_details.update(assigned_role_id=None)
            workflow_details.update(assigned_role_name=None)
            workflow_details.update(action_date=date.today())
            workflow_details.update(actor_id=request.session['login_id'])
            workflow_details.update(actor_name=request.session['name'])
            workflow_details.update(application_status='AP')

            t_payment_details.objects.create(application_no=application_no,
                            application_type='AP',
                            application_date=date.today(), 
                            proponent_name=request.session['name'],
                            amount=addtional_payment_amount,
                            account_head_code='131370080')

            for work_details in workflow_details:
                service_id = work_details.service_id
                service_details = t_service_master.objects.filter(service_id=service_id)
                for service in service_details:
                    service_name = service.service_name
                    for email_id in application_details:
                        emailId = email_id.email
                        send_ec_ap_email(ec_no, emailId, application_no, service_name,addtional_payment_amount)
                        data['message'] = "success"
                        data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'LU':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='LU')
            for app_details in application_details:
                app_id = app_details.applicant_id
                applicant = app_details.applicant_id
                service_id = app_details.service_id
                user_details = t_user_master.objects.filter(email_id=app_id)
                for user_details in user_details:
                    login_id = user_details.login_id
                    workflow_details.update(application_status='LU', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=login_id, assigned_role_id=None,assigned_role_name=None)
            t_application_history.objects.create(application_status='LU',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Legal Undertaking Request',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'LUS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='LUS')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='LUS',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Legal Undertaking attached',
                        service_id=service_id)
            workflow_details.update(application_status='LUS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'DEC':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='DEC')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='DEC',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Drafted EC',
                        service_id=service_id)
            workflow_details.update(application_status='DEC', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='2',assigned_role_name='Verifier')

            app_history = t_application_history.objects.filter(application_no=application_no)

            application_approval_date = None
            application_submission_date = None
            application_ai_date = None
            application_resubmit_date = None

            for app_details in app_history:
                if app_details.application_status == 'LUS':
                    application_approval_date = app_details.action_date
                elif app_details.application_status == 'P':
                    application_submission_date = app_details.application_date
                elif app_details.application_status == 'ALR':
                    application_ai_date = app_details.action_date
                elif app_details.application_status == 'RSS':
                    application_resubmit_date = app_details.action_date

            # Calculate TAT (Turnaround Time) based on the conditions
            if application_approval_date and application_submission_date and application_ai_date is None and application_resubmit_date is None:
                tat = days_between(application_submission_date,application_approval_date)
            else:
                day_one = days_between(application_submission_date,application_approval_date)
                day_two = days_between( application_resubmit_date, application_ai_date)
                tat = day_one - day_two

            # Update the application details with TAT
          
            application_details.update(tat=tat)
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'A':
            ec_expiry_date = request.POST.get('ec_expiry_date')
            tat = request.POST.get('tat')
            ec_no = get_ec_no(request)

            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(ec_reference_no=ec_no, ec_approve_date=date.today(),application_status='A',tat=tat,ec_expiry_date=ec_expiry_date)
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='DEC',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='Approved',
                        service_id=service_id)
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            ec_details.update(ec_reference_no=ec_no)
            
            payment_details = t_payment_details.objects.filter(application_no=application_no)
            payment_details.update(ec_no=ec_no)

            workflow_details.update(assigned_user_id=None)
            workflow_details.update(assigned_role_id=None)
            workflow_details.update(assigned_role_name=None)
            workflow_details.update(action_date=date.today())
            workflow_details.update(actor_id=request.session['login_id'])
            workflow_details.update(actor_name=request.session['name'])
            workflow_details.update(application_status='A')
            for work_details in workflow_details:
                service_id = work_details.service_id
                service_details = t_service_master.objects.filter(service_id=service_id)
                for service in service_details:
                    service_name = service.service_name
                    for email_id in application_details:
                        emailId = email_id.email
                        send_ec_approve_email(ec_no, emailId, application_no, service_name)
                        data['message'] = "success"
                        data['redirect_to'] = "verify_application_list"
        elif identifier == 'FT': # forward TOR form
            tor_remarks = request.POST.get('tor_remarks')
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(tor_remarks=tor_remarks,application_status='FT')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id=app_det.service_id
            t_application_history.objects.create(application_status='FT',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='TOR Forwared',
                        service_id=service_id)
            workflow_details.update(application_status='FT', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='2',assigned_role_name='Verifier')
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'AT': # Approve TOR form
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(tor_approve_date=date.today(),application_status='A')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id=app_det.service_id
            t_application_history.objects.create(application_status='FT',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        application_id=applicant,
                        remarks='TOR Approved',
                        service_id=service_id)
            workflow_details.update(assigned_user_id=None)
            workflow_details.update(assigned_role_id=None)
            workflow_details.update(assigned_role_name=None)
            workflow_details.update(action_date=date.today())
            workflow_details.update(actor_id=request.session['login_id'])
            workflow_details.update(actor_name=request.session['name'])
            workflow_details.update(application_status='A')
            for work_details in workflow_details:
                service_id = work_details.service_id
                service_details = t_service_master.objects.filter(service_id=service_id)
                for service in service_details:
                    service_name = service.service_name
                    for email_id in application_details:
                        emailId = email_id.email
                        send_tor_approve_email(ec_no, emailId, application_no, service_name)
                        data['message'] = "success"
                        data['redirect_to'] = "verify_application_list"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def days_between(date1, date2):
    return (date2 - date1).days

def save_lu_attachment(request):
    data = dict()
    lu_attach = request.FILES['lu_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + lu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/LU/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, lu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/LU" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_lu_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='LU')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')

    return render(request, 'lu_attachment_page.html', {'lu_attach': file_attach})

def save_rev_lu_attachment(request):
    data = dict()
    lu_attach = request.FILES['rev_lu_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + lu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RLU/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, lu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/RLU" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_rev_lu_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='RLU')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')

    return render(request, 'rev_lu_attachment_page.html', {'rev_lu_attach': file_attach})

def delete_rev_lu_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RLU")
        fs.delete(str(file_name))
    file.delete()

    rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RLU')
    return render(request, 'rev_lu_attachment_page.html', {'rev_lu_attach':rev_lu_attach})

def save_ai_attachment(request):
    data = dict()
    ai_attach = request.FILES['ai_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + ai_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/AI/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, ai_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/AI" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_ai_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='AI')
    ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')

    return render(request, 'ai_attachment_page.html', {'ai_attach': ai_attach})

def delete_ai_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/AI")
        fs.delete(str(file_name))
    file.delete()

    rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='AI')
    return render(request, 'rev_lu_attachment_page.html', {'rev_lu_attach':rev_lu_attach})

def delete_lu_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')

    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/LU")
        fs.delete(str(file_name))
    file.delete()

    lu_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RLU')
    return render(request, 'lu_attachment_page.html', {'lu_attach':lu_attach})

def save_draft_ec_details(request):
    application_no = request.POST.get('application_no')
    ec_type = request.POST.get('ec_type')
    ec_heading = request.POST.get('ec_heading')
    ec_terms = request.POST.get('ec_terms')

    t_ec_industries_t11_ec_details.objects.create(application_no=application_no,ec_type=ec_type, ec_heading=ec_heading, ec_terms=ec_terms)
    ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no).order_by('record_id')

    return render(request, 'ec_draft_details.html', {'ec_details':ec_details})

def update_draft_ec_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')
    ec_type = request.POST.get('ec_type')
    ec_heading = request.POST.get('ec_heading')
    ec_terms = request.POST.get('ec_terms')

    ec_details = t_ec_industries_t11_ec_details.objects.filter(record_id=record_id)
    ec_details.update(ec_type=ec_type,ec_heading=ec_heading, ec_terms=ec_terms)
    ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no).order_by('record_id')

    return render(request, 'ec_draft_details.html', {'ec_details':ec_details})

def delete_draft_ec_details(request):
    record_id = request.POST.get('record_id')
    application_no = request.POST.get('application_no')

    ec_details = t_ec_industries_t11_ec_details.objects.filter(record_id=record_id)
    ec_details.delete()
    ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no).order_by('record_id')

    return render(request, 'ec_draft_details.html', {'ec_details':ec_details})

# Inspection Report
def inspection_list(request):
    inspection_list = t_inspection_monitoring_t1.objects.filter(record_status='Active').order_by('inspection_date')
    user_list = t_user_master.objects.all()
    ec_details = t_ec_industries_t1_general.objects.all()
    v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    expiry_date_threshold = datetime.now().date() + timedelta(days=30)
    ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    return render(request, 'inspection/inspection.html', {'inspection_list':inspection_list,'ec_renewal_count':ec_renewal_count,'v_application_count':v_application_count,'r_application_count':r_application_count, 'user_list':user_list, 'ec_details':ec_details})

def view_inspection_details(request):
    inspection_reference_no = request.GET.get('inspection_reference_no')
    inspection_details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=inspection_reference_no)
    file_attach = t_file_attachment.objects.filter(application_no=inspection_reference_no)
    return render(request, 'inspection/inspection_details.html',
                  {'inspection_details':inspection_details, 'file_attach':file_attach})

def inspection_submission_form(request):
    applicant = request.session['email']
    ec_details = t_ec_industries_t1_general.objects.filter(ec_reference_no__isnull=False)
    r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    return render(request, 'inspection/inspection_submission.html', {'ec_details': ec_details,'r_application_count':r_application_count})

def load_ec_details(request):
    data = dict()
    ec_reference_no = request.GET.get('ec_reference_no')
    ec_detail_list = t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_reference_no)
    for ec_detail_list in ec_detail_list:
        data["applicant_name"],data["project_name"],data["address"],data["ca_authority"],data["applicant_id"] = ec_detail_list.applicant_name, ec_detail_list.project_name, ec_detail_list.address, ec_detail_list.ca_authority, ec_detail_list.applicant_id
    return JsonResponse(data)

def add_inspection(request):
    data = dict()
    service_code = 'ins'
    reference_no = get_inspection_submission_ref_no(request, service_code)
    inspection_type = request.POST.get('inspection_type')
    inspection_date = request.POST.get('inspection_date')
    inspection_reason = request.POST.get('inspection_reason')
    ec_clearance_no = request.POST.get('ec_clearance_no')
    proponent_name = request.POST.get('proponent_name')
    project_name = request.POST.get('project_name')
    address = request.POST.get('address')
    observation = request.POST.get('observation')
    team_leader = request.POST.get('team_leader')
    team_members = request.POST.get('team_members')
    remarks = request.POST.get('remarks')
    fines_penalties = request.POST.get('fines_penalties')
    inspection_status = request.POST.get('inspection_status')
    applicant_id = request.POST.get('applicant_id')
    
    t_inspection_monitoring_t1.objects.create(inspection_type=inspection_type, inspection_date=inspection_date,
                                              inspection_reference_no=reference_no, inspection_reason=inspection_reason,
                                              ec_clearance_no=ec_clearance_no, project_name=project_name,
                                              proponent_name=proponent_name, address=address, observation=observation,
                                              team_leader=team_leader, team_members=team_members, remarks=remarks,
                                              fines_penalties=fines_penalties, status=inspection_status,
                                              login_id=applicant_id,
                                              updated_by_ca=request.session['login_id'], record_status='Active')
    data['ref_no'] = reference_no
    return JsonResponse(data)

def load_inspection_attachment_details(request):
    referenceNo = request.GET.get('attachment_refNo')
    print(referenceNo)
    attachment_details = t_file_attachment.objects.filter(application_no=referenceNo)
    return render(request, 'inspection/inspection_file_attachment.html',
                  {'file_attach': attachment_details})

def get_inspection_details(request, record_id):
    file_attach = t_file_attachment.objects.filter(application_no=record_id)
    inspection_details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=record_id)
    ec_details = t_ec_industries_t1_general.objects.filter(ec_reference_no__isnull=False)
    return render(request, 'inspection/edit_inspection.html', {'inspection_details': inspection_details,
                                                               'file_attach': file_attach, 'ec_details': ec_details})

def get_formatted_date(date):
    if not date:
        return ''  # handle case when date is empty or None

    formatted_date = date.strftime('%d/%m/%Y')
    return formatted_date

def edit_inspection(request):
    edit_record_id = request.POST.get('record_id')
    edit_inspection_type = request.POST.get('inspection_type')
    edit_inspection_date = request.POST.get('inspection_date')
    edit_inspection_reason = request.POST.get('inspection_reason')
    edit_ec_clearance_no = request.POST.get('ec_clearance_no')
    edit_proponent_name = request.POST.get('proponent_name')
    edit_project_name = request.POST.get('project_name')
    edit_address = request.POST.get('address')
    edit_observation = request.POST.get('observation')
    edit_team_leader = request.POST.get('team_leader')
    edit_team_members = request.POST.get('team_members')
    edit_remarks = request.POST.get('remarks')
    edit_fines_penalties = request.POST.get('fines_penalties')
    edit_inspection_status = request.POST.get('inspection_status')
    inspection_details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=edit_record_id)
    inspection_details.update(inspection_type=edit_inspection_type, inspection_date=edit_inspection_date,
                              inspection_reason=edit_inspection_reason, ec_clearance_no=edit_ec_clearance_no,
                              proponent_name=edit_proponent_name, project_name=edit_project_name, address=edit_address,
                              observation=edit_observation, team_leader=edit_team_leader, team_members=edit_team_members,
                              remarks=edit_remarks, fines_penalties=edit_fines_penalties,
                              status=edit_inspection_status, updated_by_ca=request.session['login_id']
                              )

    return redirect(inspection_list)

def delete_inspection(request):
    delete_record_id = request.POST.get('record_id')
    inspection_details = t_inspection_monitoring_t1.objects.filter(record_id=delete_record_id)
    inspection_details.update(record_status='Deleted', updated_by_ca=request.session['login_id'])
    return redirect(inspection_list)

def get_inspection_submission_ref_no(request, service_code):
    last_reference_no = t_inspection_monitoring_t1.objects.aggregate(Max('inspection_reference_no'))
    lastRefNo = last_reference_no['inspection_reference_no__max']
    if not lastRefNo:
        year = timezone.now().year
        newRefNo = service_code + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastRefNo)[9:13]
        substring = int(substring) + 1
        RefNo = str(substring).zfill(4)
        year = timezone.now().year
        newRefNo = service_code + "-" + str(year) + "-" + RefNo
    return newRefNo

def submit_inspection_form(request):
    reference_no = request.POST.get('record_id')
    created_on = datetime.now()
    details = t_inspection_monitoring_t1.objects.filter(inspection_reference_no=reference_no)
    details.update(updated_on=created_on)

# EndInspection

def get_fines_penalties_details(request):
    ec_ref_no = request.GET.get('ec_ref_no')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=ec_ref_no) | t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_ref_no)
    
    return render(request, 'fines_penalties_details.html', {'application_details':application_details})

def save_fines_penalties(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        fines_penalties_type = request.POST.get('fines_penalty_type')
        ec_no = request.POST.get('ec_ref_no')
        proponent_name = request.POST.get('ec_ref_no')
        address = request.POST.get('address')
        validity = request.POST.get('ec_expiry_date')
        amount = request.POST.get('fines_and_penalties')
        

        t_fines_penalties.objects.create(application_no=application_no,
                                        fines_penalties_type=fines_penalties_type,
                                        fines_date=date.now(),
                                        ec_no=ec_no,
                                        proponent_name=proponent_name,
                                        address=address,
                                        validity=validity,
                                        amount=amount,
                                        fines_status='P'
                                        )
        insert_payment_details(request, application_no,'131379010',proponent_name,amount,fines_penalties_type)
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        for application_details in application_details:
            fines_penalties_email(application_details.email, application_no, amount)
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def fines_penalties_email(email_id, application_no, amount):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your Application No" + application_no + "Has Has Fines and Penalty " \
              " of Nu. " + amount + " . Please Pay To Further Proceess Your Application." 
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
#TOR Details
def tor_to_verifier(request):
    application_no = request.POST.get('application_no')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(application_status='V') #Tor Submitted to Verifier/approver
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    workflow_details.update(assigned_user_id=None)
    workflow_details.update(assigned_role_id='3')
    workflow_details.update(assigned_role_name='Verifier')
    workflow_details.update(action_date=date.today())
    workflow_details.update(actor_id=request.session['login_id'])
    workflow_details.update(actor_name=request.session['name'])
    workflow_details.update(application_status='V')
    
    return redirect(reviewer_application_list)

def approve_tor_application(request):
    application_no = request.POST.get('application_no')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    application_details.update(application_status='A') #Tor Submitted to Verifier/approver
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    workflow_details.update(assigned_user_id=None)
    workflow_details.update(assigned_role_id='3')
    workflow_details.update(assigned_role_name='Verifier')
    workflow_details.update(action_date=date.today())
    workflow_details.update(actor_id=request.session['login_id'])
    workflow_details.update(actor_name=request.session['name'])
    workflow_details.update(application_status='A')
    for work_details in workflow_details:
        service_id = work_details.service_id
        service_details = t_service_master.objects.filter(service_id=service_id)
        for service in service_details:
            service_name = service.service_name
            for email_id in application_details:
                emailId = email_id.email
                tor_submit_email(emailId, application_no, service_name)
    return redirect(verify_application_list)

def tor_submit_email(email_id, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your TOR Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " . " 
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='aqjsbjamnzxtadvl',
              connection=None, html_message=None)
    
def fines_penalties(request):
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no__isnull=False)
    return render(request, 'fines_penalties.html',{'application_details':application_details})

def insert_payment_details(request,application_no,account_head, proponent_name,total_amount,application_type):
    t_payment_details.objects.create(application_no=application_no,
            application_type=application_type,
            application_date=date.today(), 
            proponent_name=proponent_name,
            amount=total_amount,
            account_head_code=account_head)
    return redirect(fines_penalties)