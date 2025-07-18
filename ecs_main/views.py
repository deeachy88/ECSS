import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
import requests
from ecs_admin.views import bsic_master, get_auth_token
from proponent.models import t_ec_industries_t10_hazardous_chemicals, t_ec_industries_t11_ec_details, t_ec_industries_t13_dumpyard, t_ec_industries_t1_general, t_ec_industries_t2_partner_details, t_ec_industries_t3_machine_equipment, t_ec_industries_t4_project_product, t_ec_industries_t5_raw_materials, t_ec_industries_t6_ancillary_road, t_ec_industries_t7_ancillary_power_line, t_ec_industries_t8_forest_produce, t_ec_industries_t9_products_by_products, t_ec_renewal_t1, t_ec_renewal_t2, t_fines_penalties, t_payment_details, t_workflow_dtls, t_workflow_dtls_audit
from ecs_admin.models import payment_details_master, t_bsic_code, t_dzongkhag_master, t_file_attachment, t_gewog_master, t_role_master, t_service_master, t_thromde_master, t_user_master, t_village_master
from ecs_main.models import t_application_history, t_inspection_monitoring_t1
from django.utils import timezone
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage
from django.db.models import Max
from datetime import datetime, timedelta, date
from datetime import date
from django.db.models import Count, Subquery, OuterRef
from django.utils.timezone import now
from django.db.models import Q

# Create your views here.
def verify_application_list(request):
    # Get session data with defaults
    ca_authority = request.session.get('ca_authority')
    login_id = request.session.get('login_id')
    
    # Base query filters
    base_filters = {
        'assigned_role_id': '2',
        'action_date__isnull': False,
        'ca_authority': ca_authority
    }
    
    # Optimized application list query using Q objects
    application_query = Q(**base_filters) & (
        Q(application_status='P') | 
        Q(application_status='DEC') | 
        Q(application_status='AL') | 
        Q(application_status='FT') |
        Q(application_status='V', assigned_user_id=login_id)
    )
    
    application_list = t_workflow_dtls.objects.filter(application_query)
    
    # Count for V applications (optimized)
    v_application_count = t_workflow_dtls.objects.filter(
        Q(application_status='V', assigned_user_id=login_id) & 
        Q(**base_filters)
    ).count()
    
    # Optimized service and payment queries
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.exclude(service_type='AP')
    pay_details = t_payment_details.objects.exclude(service_type="TOR")
    
    # EC renewal count (optimized)
    ec_renewal_count = 0
    if ca_authority:
        expiry_date_threshold = datetime.now().date() + timedelta(days=30)
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(
            ca_authority=ca_authority,
            application_status='A',
            ec_expiry_date__lt=expiry_date_threshold
        ).count()
    
    # Create response with no-cache headers
    context = {
        'application_details': application_list,
        'v_application_count': v_application_count,
        'service_details': service_details,
        'payment_details': payment_details,
        'ec_renewal_count': ec_renewal_count,
        'pay_details': pay_details
    }
    
    response = render(request, 'application_list.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
    

def client_application_list(request):
    login_id = request.session.get('login_id', None)
    applicant_id = request.session.get('email', None)
    application_list = t_workflow_dtls.objects.filter(application_status='ALR', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='EATC', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='RS', action_date__isnull=False,assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='LU', action_date__isnull=False,assigned_user_id=login_id)| t_workflow_dtls.objects.filter(application_status='ALA', action_date__isnull=False,assigned_user_id=login_id)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(service_type='AP')
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=login_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    response = render(request, 'application_list.html',{'application_details':application_list,'cl_application_count':cl_application_count,'app_hist_count':app_hist_count, 'service_details':service_details, 'payment_details':payment_details,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def reviewer_application_list(request):
    r_application_count = 0
    ca_authority = request.session.get('ca_authority', None)
    login_id = request.session.get('login_id', None)
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(service_type='AP')
    
    application_list = []  # Initialize application_list outside the if block
    
    if ca_authority is not None:
        application_list = t_workflow_dtls.objects.filter(application_status='R', assigned_role_id='3', action_date__isnull=False, ca_authority=ca_authority, assigned_user_id=login_id) | t_workflow_dtls.objects.filter(application_status='ALS', assigned_role_id='3', action_date__isnull=False, ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='FEATC', assigned_role_id='3', action_date__isnull=False, ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='RSS', assigned_role_id='3', action_date__isnull=False, ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='LUS', assigned_role_id='3', action_date__isnull=False, ca_authority=ca_authority) | t_workflow_dtls.objects.filter(application_status='APP', assigned_role_id='3', action_date__isnull=False, ca_authority=ca_authority)
        r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
    
    response = render(request, 'application_list.html', {'application_details': application_list, 'r_application_count': r_application_count, 'service_details': service_details, 'payment_details': payment_details})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# APPLICATION LISTS FORM IBLS
def ibls_application_list(request):
    role_id = request.session['role_id']
    verifier_list = t_user_master.objects.filter(role_id='2')
    service_details = t_service_master.objects.all()
    payment_details = t_payment_details.objects.all().exclude(service_type='AP')
    application_list = t_workflow_dtls.objects.filter(application_status='P', assigned_role_id=role_id, action_date__isnull=False)
    client_application_count = t_user_master.objects.filter(
                accept_reject__isnull=True,
                login_type='C'
            ).count()
    response = render(request, 'application_list.html',{'application_details':application_list,'client_application_count':client_application_count,'verifier_list':verifier_list,'service_details':service_details,'payment_details':payment_details})
    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# def payment_list(request):
#     login_id = request.session['login_id']
#     payment_details = t_payment_details.objects.filter(transaction_no__isnull=True)
#     service_details = t_service_master.objects.all()
#     return render(request, 'payment_list.html', {'payment_details': payment_details,'service_details':service_details})

def payment_list(request):
    applicant_id = request.session.get('email', None)
    assigned_user_id = request.session.get('login_id', None)
    payment_details = t_payment_details.objects.filter(
        receipt_no__isnull=True,
        ref_no__in=t_ec_industries_t1_general.objects.filter(applicant_id=applicant_id).values('application_no')
    )
    service_details = t_service_master.objects.all()
    app_hist_count = t_application_history.objects.filter(applicant_id=applicant_id).count()
    cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=assigned_user_id).count()
    t1_general_subquery = t_ec_industries_t1_general.objects.filter(
        tor_application_no=OuterRef('application_no')
    ).values('tor_application_no')

    # Query to count approved applications that are not in t1_general
    tor_application_count = t_ec_industries_t1_general.objects.filter(
            application_status='A',
            application_no__contains='TOR',applicant_id=applicant_id
        ).exclude(
            application_no__in=Subquery(t1_general_subquery)
        ).count()
    
    response = render(request, 'payment_list.html',
                  {'payment_details': payment_details,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'service_details': service_details,'tor_application_count':tor_application_count})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def view_application_details(request):
    application_no = request.GET.get('application_no')
    print(application_no)
    service_id = request.GET.get('service_id')
    application_source = request.GET.get('application_source')
    status = None
    ca_auth = None
    assigned_role_id = None
    result = t_ec_industries_t1_general.objects.filter(application_no=application_no,application_no__contains='TOR')
    workflow_details = t_workflow_dtls.objects.filter(application_no=application_no)
    for work_details in workflow_details:
        status = work_details.application_status
        ca_auth = work_details.ca_authority
        assigned_role_id = work_details.assigned_role_id
    if result.exists():
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        dzongkhag = t_dzongkhag_master.objects.all()
        gewog = t_gewog_master.objects.all()
        village = t_village_master.objects.all()
        thromde = t_thromde_master.objects.all()
        reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
        file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOR')
        tor_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')
        return render(request, 'tor_form_details.html', {'application_details':application_details,'file_attach':file_attach,'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village, 'thromde':thromde, 'reviewer_list':reviewer_list,'assigned_role_id':assigned_role_id, 'status':status,'tor_attach':tor_attach})
    else:
        if service_id == '1':
            if application_source == 'IBLS':
                role_id = request.session['role_id']
                verifier_list = t_user_master.objects.filter(role_id='2')
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
                ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
                file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEA')
                anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
                for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
                gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
                ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
                ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
                reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
                eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
                lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
                rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
                ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'ea_application_details.html', {
                    'reviewer_list': reviewer_list,
                    'application_details': application_details,
                    'partner_details': partner_details,
                    'machine_equipment': machine_equipment,
                    'raw_materials': raw_materials,
                    'status': status,
                    'anc_road_details': anc_road_details,
                    'anc_power_line_details': anc_power_line_details,
                    'project_product': project_product,
                    'application_no': application_no,
                    'dzongkhag': dzongkhag,
                    'gewog': gewog,
                    'village': village,
                    'file_attach': file_attach,
                    'anc_file_attach': anc_file_attach,
                    'for_anc_file_attach': for_anc_file_attach,
                    'gw_anc_file_attach': gw_anc_file_attach,
                    'ind_anc_file_attach': ind_anc_file_attach,
                    'forest_produce': forest_produce,
                    'app_hist_count': app_hist_count,
                    'cl_application_count': cl_application_count,
                    'products_by_products': products_by_products,
                    'hazardous_chemicals': hazardous_chemicals,
                    'ec_details': ec_details,
                    'ancillary_details': ancillary_details,
                    'eatc_attach': eatc_attach,
                    'lu_attach': lu_attach,
                    'rev_lu_attach': rev_lu_attach,
                    'role':role_id,
                    'verifier_list':verifier_list
                })
            else:
                application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
                ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
                file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEA')
                anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
                for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
                gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
                ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
                ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
                reviewer_list = t_user_master.objects.filter(role_id='3',agency_code=ca_auth)
                eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
                lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
                rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
                ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
                app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
                cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
                return render(request, 'iee_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                            'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                            'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '2':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ENR')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'energy_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'village':village,'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '3':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ROA')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'road_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '4':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TRA')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'transmission_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '5':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='TOU')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'tourism_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '6':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWA')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'ground_water_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '7':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FOR')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count() 
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count() 
            return render(request, 'forest_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '8':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='QUA')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no,service_type='Main Activity')
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'quarry_application_details.html',{'reviewer_list':reviewer_list,'ai_attach':ai_attach,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'project_product':project_product,'anc_road_details':anc_road_details, 'anc_power_line_details':anc_power_line_details, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count, 'products_by_products': products_by_products,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '9':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Main Activity')
            ancillary_details = t_ec_industries_t1_general.objects.filter(application_no=application_no,service_type='Ancillary')
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
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GEN')
            anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GENANC')
            for_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='FORANC')
            gw_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='GWANC')
            ind_anc_file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='IEEANC')
            dumpyard_details = t_ec_industries_t13_dumpyard.objects.filter(application_no=application_no).order_by('record_id')
            ec_details = t_ec_industries_t11_ec_details.objects.filter(application_no=application_no)
            reviewer_list = t_user_master.objects.filter(role_id='3', agency_code=ca_auth)
            eatc_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='EATC')
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'general_application_details.html',{'reviewer_list':reviewer_list,'application_details':application_details,'partner_details':partner_details,'machine_equipment':machine_equipment,'raw_materials':raw_materials,'status':status,'anc_road_details':anc_road_details,'anc_power_line_details':anc_power_line_details,
                                                        'final_product':project_product,'ancillary_road':ancillary_road, 'power_line':power_line, 'application_no':application_no, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village,'dumpyard_details':dumpyard_details,'file_attach':file_attach,'anc_file_attach':anc_file_attach,'anc_file_attach':anc_file_attach,'for_anc_file_attach':for_anc_file_attach,'gw_anc_file_attach':gw_anc_file_attach,'ind_anc_file_attach':ind_anc_file_attach,
                                                        'forest_produce':forest_produce,'ai_attach':ai_attach, 'products_by_products': products_by_products,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'hazardous_chemicals':hazardous_chemicals,'ec_details':ec_details, 'ancillary_details':ancillary_details,'eatc_attach':eatc_attach, 'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})
        elif service_id == '10':
            renewal_details_one = t_ec_renewal_t1.objects.filter(application_no=application_no)
            for renewal_details_one in renewal_details_one:
                application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no=renewal_details_one.ec_reference_no,service_type='Main Activity')
            renewal_details_two = t_ec_renewal_t2.objects.filter(application_no=application_no)
            file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='ECR')
            reviewer_list = t_user_master.objects.filter(role_id='3')
            dzongkhag = t_dzongkhag_master.objects.all()
            gewog = t_gewog_master.objects.all()
            village = t_village_master.objects.all()
            lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='LU')
            rev_lu_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RLU')
            ai_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='AI')
            app_hist_count = t_application_history.objects.filter(applicant_id=request.session['email']).count()
            cl_application_count = t_workflow_dtls.objects.filter(assigned_user_id=request.session['login_id']).count()
            return render(request, 'renewal_application_details.html',{'application_details':application_details,'renewal_details_one':renewal_details_one,'status':status,
                                                                    'dzongkhag':dzongkhag,'gewog':gewog,'village':village,'ai_attach':ai_attach,'app_hist_count':app_hist_count,'cl_application_count':cl_application_count,'renewal_details_two':renewal_details_two,'reviewer_list':reviewer_list,'file_attach':file_attach ,'lu_attach':lu_attach,'rev_lu_attach':rev_lu_attach})


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
    service_id = None
    fine_details = t_payment_details.objects.filter(ref_no=application_no, service_type='Fines And Penalties')
    if fine_details.exists():
        fine_details.update(transaction_no=transaction_no, amount=amount,
                               instrument_no=instrument_no, transaction_date=transaction_date)
        work_details = t_fines_penalties.objects.filter(application_no=application_no)
        work_details.update(fines_status='FPP') # Fines Paid
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        for app_det in application_details:
            applicant = app_det.applicant_id
            service_id = app_det.service_id
            ca_auth = app_det.ca_authority
            t_application_history.objects.create(application_no=application_no,
                    application_status='FPP',
                    action_date=date.today(),
                    actor_id=request.session['login_id'], 
                    actor_name=request.session['name'],
                    applicant_id=applicant,
                    remarks='Fines Payment Made',
                    service_id=service_id,
                    ca_authority=ca_auth)
    else:
        payment_details = t_payment_details.objects.filter(ref_no=application_no, service_type='AP')
        if payment_details.exists():
            payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                                instrument_no=instrument_no, transaction_date=transaction_date)
            work_details = t_workflow_dtls.objects.filter(application_no=application_no)
            work_details.update(application_status='APP')
            work_details.update(assigned_role_id='3')
            work_details.update(assigned_role_name='Reviewer')
            work_details.update(action_date=date.today())
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no, service_type='Main Activity')
            application_details.update(application_status='APP')
            application_details.update(action_date=date.today())
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
                ca_auth = app_det.ca_authority
            t_application_history.objects.create(application_no=application_no,
                    application_status='P',
                    action_date=date.today(),
                    actor_id=request.session['login_id'], 
                    actor_name=request.session['name'],
                    applicant_id=applicant,
                    remarks='Additional Payment Made',
                    service_id=service_id,
                    ca_authority=ca_auth)
        else:
            payment_details = t_payment_details.objects.filter(ref_no=application_no)
            payment_details.update(payment_type=payment_type, transaction_no=transaction_no, amount=amount,
                                    instrument_no=instrument_no, transaction_date=transaction_date)
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
                ca_auth = app_det.ca_authority
            t_application_history.objects.create(application_no=application_no,
                    application_status='P',
                    action_date=date.today(),
                    actor_id=request.session['login_id'], 
                    actor_name=request.session['name'],
                    applicant_id=applicant,
                    remarks='Payment Made',
                    service_id=service_id,
                    ca_authority=ca_auth)
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

def get_tor_clearance_no(request,service_id):
    service_name = None
    last_cl_no = t_ec_industries_t1_general.objects.aggregate(Max('tor_clearance_no'))
    lastClearnaceNo = last_cl_no['tor_clearance_no__max']

    if service_id == '1':
        service_name='IEE'
    elif service_id == '2':
        service_name='ENE'
    elif service_id == '3':
        service_name='ROA'
    elif service_id == '4':
        service_name='TRA'
    elif service_id == '5':
        service_name='TOU'
    elif service_id == '6':
        service_name='GWA'
    elif service_id == '7':
        service_name='FOR'
    elif service_id == '8':
        service_name='QUA'
    else:
        service_name='GEN'    

    if not lastClearnaceNo:
        year = timezone.now().year
        newClearanceNo = "TOR" + "-" + str(service_name) + "-" + str(year) + "-" + "0001"
    else:
        substring = str(lastClearnaceNo)[13:17]
        substring = int(substring) + 1
        ecNo = str(substring).zfill(4)
        year = timezone.now().year
        newClearanceNo ="TOR" + "-" + str(service_name) + "-" + str(year) + "-" + ecNo
    return newClearanceNo

def send_ec_ap_email(ec_no, email, application_no, service_name, addtional_payment_amount):
    subject = 'ADDITIONAL PAYMENT'
    message = "Dear Sir," \
              "" \
              "Your EC Application For " + service_name + " Has Additional Payment. Your " \
              " Amount is " + str(addtional_payment_amount) + " Please Make Payment To Proceed Further"\
              " . " 
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
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
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    
def send_tor_approve_email(email, application_no, service_name,tor_clearance_no):
    print("send_tor_approve_email")
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir/Madam," \
              "" \
              "Your TOR Application For" + service_name + " Has Been Approved. Draft TOR Has been attached for your reference. " \
              " Your Application No is " + application_no + " And Tor Clearance No is" + tor_clearance_no + " Thank You"\
              " . " 
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    
    
def send_ec_resubmission_email(email, application_no, service_name):
    subject = 'APPLICATION RESUBMISSION'
    message = "Dear Sir," \
              "" \
              "Your EC Application For" + service_name + "Having" \
              " Application No " + application_no + " Has Been Sent For Resubmission. Please Check The Application And Resubmit It."
    recipient_list = [email]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
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
        if identifier == 'V':
            workflow_details.update(action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=forward_to, assigned_role_id='2',assigned_role_name='Verifier')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_no=application_no,
                        application_status='P',
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
                        remarks='To Verifier',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "ibls_application_list"
        elif identifier == 'R':
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
                        remarks='Addtional Info Rejected',
                        service_id=service_id)
            data['message'] = "success"
            data['redirect_to'] = "verify_application_list"
        elif identifier == 'ALS':
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
            account_head_code = request.POST.get('account_head')
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='AP')
            for app_det in application_details:
                applicant = app_det.applicant_id
                service_id = app_det.service_id
            t_application_history.objects.create(application_status='AP',application_no=application_no,
                        action_date=date.today(),
                        actor_id=request.session['login_id'], 
                        actor_name=request.session['name'],
                        applicant_id=applicant,
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
                            service_type='AP',
                            application_date=date.today(), 
                            proponent_name=request.session['name'],
                            amount=addtional_payment_amount,
                            account_head_code=account_head_code)

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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
                        remarks='Legal Undertaking attached',
                        service_id=service_id)
            workflow_details.update(application_status='LUS', action_date=date.today(), actor_id=request.session['login_id'], actor_name=request.session['name'], assigned_user_id=None, assigned_role_id='3',assigned_role_name='Reviewer')
            data['message'] = "success"
            data['redirect_to'] = "client_application_list"
        elif identifier == 'DEC':
            # 1. Update application status to 'DEC'
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
            application_details.update(application_status='DEC')

            # 2. Get applicant and service ID (assuming at least one record exists)
            app_det = application_details.first()
            applicant = app_det.applicant_id
            service_id = app_det.service_id

            # 3. Record in application history
            t_application_history.objects.create(
                application_status='DEC',
                application_no=application_no,
                action_date=date.today(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks='Drafted EC',
                service_id=service_id
            )

            # 4. Update workflow details
            workflow_details.update(
                application_status='DEC',
                action_date=date.today(),
                actor_id=request.session['login_id'],
                actor_name=request.session['name'],
                assigned_user_id=None,
                assigned_role_id='2',
                assigned_role_name='Verifier'
            )

            # 5. Initialize date tracker
            dates = {
                'approval': None,    # LUS
                'submission': None,   # P
                'ai': None,          # ALR
                'resubmit': None      # RSS
            }

            # 6. Extract dates from application history
            for app_details in t_application_history.objects.filter(application_no=application_no):
                if app_details.application_status == 'LUS':
                    print("LUS:", app_details.action_date)
                    dates['approval'] = app_details.action_date
                elif app_details.application_status == 'P':
                    print("P:", app_details.action_date)
                    dates['submission'] = app_details.application_date
                elif app_details.application_status == 'ALR':
                    print("ALR:", app_details.action_date)
                    dates['ai'] = app_details.action_date
                elif app_details.application_status == 'RSS':
                    print("RSS:", app_details.action_date)
                    dates['resubmit'] = app_details.action_date

            # 7. Calculate TAT (with None checks)
            tat = 0  # Default if dates are missing

            # Case 1: Only submission + approval dates exist
            if dates['submission'] and dates['approval'] and not dates['ai'] and not dates['resubmit']:
                tat = (dates['approval'] - dates['submission']).days

            # Case 2: All dates exist (with AI + Resubmission)
            elif dates['submission'] and dates['approval'] and dates['ai'] and dates['resubmit']:
                total_days = (dates['approval'] - dates['submission']).days
                ai_resubmit_days = (dates['ai'] - dates['resubmit']).days
                tat = max(total_days - ai_resubmit_days, 0)  # Prevent negative TAT

            # 8. Update TAT in DB (if valid)
            if tat > 0:
                application_details.update(tat=tat)
            else:
                application_details.update(tat=tat)

            # 9. Return response
            data['message'] = "success"
            data['redirect_to'] = "reviewer_application_list"
        elif identifier == 'A':
            ec_expiry_date = request.POST.get('ec_expiry_date')
            tat = request.POST.get('tat')
            ec_no = get_ec_no(request)
            application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)

            # Update common fields in application details
            application_details.update(
                ec_approve_date=now(),
                application_status='A',
                tat=tat,
                ec_expiry_date=ec_expiry_date
            )

            for app_det in application_details:
                service_type = app_det.service_type
                if service_type in ['NC', 'OC']:
                    # Update workflow details
                    workflow_details.update(
                        assigned_user_id=None,
                        assigned_role_id=None,
                        assigned_role_name=None,
                        action_date=now(),
                        actor_id=request.session['login_id'],
                        actor_name=request.session['name'],
                        application_status='A'
                    )
                    
                    service_id = app_det.service_id
                    service_details = t_service_master.objects.filter(service_id=service_id).first()
                    if service_details:
                        service_name = service_details.service_name

                        for email_id in application_details:
                            send_ec_approve_email(ec_no, email_id.email, application_no, service_name)
                else:
                    app_det.ec_reference_no = ec_no
                    app_det.save()
                    
                    t_application_history.objects.create(
                        application_status='A',
                        application_no=application_no,
                        action_date=now(),
                        actor_id=request.session['login_id'],
                        actor_name=request.session['name'],
                        applicant_id=app_det.applicant_id,
                        remarks='Approved',
                        service_id=app_det.service_id
                    )
                    
                    t_ec_industries_t11_ec_details.objects.filter(application_no=application_no).update(ec_reference_no=ec_no)
                    
                    workflow_details.update(
                        assigned_user_id=None,
                        assigned_role_id=None,
                        assigned_role_name=None,
                        action_date=now(),
                        actor_id=request.session['login_id'],
                        actor_name=request.session['name'],
                        application_status='A'
                    )

                    service_details = t_service_master.objects.filter(service_id=app_det.service_id).first()
                    if service_details:
                        service_name = service_details.service_name
                        
                        for email_id in application_details:
                            send_ec_approve_email(ec_no, email_id.email, application_no, service_name)
                            
                        token = get_auth_token()
                        
                        # Prepare the data to be sent in the request body
                        post_data = {
                            "applicationNo": application_no,
                            "cleareanceNo": ec_no,
                            "status": True,  # Boolean True, not string "True"
                            "message": "ok",
                            "rejectionMessage": "notok",
                            "issueDate":now().strftime("%Y-%m-%d"),
                            "expiryDate":ec_expiry_date
                        }

                        # Headers with authorization token
                        headers = {
                            'Authorization': f"Bearer {token}",
                            'Content-Type': 'application/json'  # Ensure the content-type is set to application/json
                        }

                        # Send the POST request
                        res = requests.post(
                            'https://datahub-apim.tech.gov.bt/update_to_ibls_application/1.0.0/nectoibls',
                            json=post_data,  # Send as JSON, not as a string
                            headers=headers,
                            verify=False  # This disables SSL verification, use with caution in production
                        )

                        # Print the response text for debugging
                        print(f"Status Code: {res.status_code}")
                        print(f"Response Text: {res.text}")

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
                        applicant_id=applicant,
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
                        applicant_id=applicant,
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
                        tor_clearance_no = get_tor_clearance_no(request,service_id)
                        send_tor_approve_email(emailId, application_no, service_name,tor_clearance_no)
                        application_details.update(tor_clearance_no=tor_clearance_no)
                        data['message'] = "success"
                        data['redirect_to'] = "verify_application_list"
    except Exception as e: 
        print('An error occurred:', e)
        error_msg = str(e)
        data['error'] = str(error_msg.split("\n")[0])
    return JsonResponse(data)

def days_between(start_date, end_date):
    if start_date and end_date:
        # Ensure both are date objects, otherwise parse them
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        return abs((end_date - start_date).days)
    return 0

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

# TOR ATTACHMENTS
def save_rev_tor_attachment(request):
    data = dict()
    lu_attach = request.FILES['rev_tor_attach']
    app_no = request.POST.get('application_no')
    file_name = str(app_no)[0:3] + "_" + str(app_no)[4:8] + "_" + str(app_no)[9:13] + "_" + lu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RTOR/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, lu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/RTOR" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_rev_tor_attachment_details(request):
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    application_no = request.POST.get('application_no')

    t_file_attachment.objects.create(application_no=application_no,file_path=file_url, attachment=file_name,attachment_type='RTOR')
    file_attach = t_file_attachment.objects.filter(application_no=application_no,attachment_type='RTOR')

    return render(request, 'tor_attachment_page.html', {'tor_attach': file_attach})

def delete_rev_tor_attachment(request):
    file_id = request.POST.get('file_id')
    application_no = request.POST.get('application_no')
    
    file = t_file_attachment.objects.filter(file_id=file_id)
    for file in file:
        file_name = str(application_no)[0:3] + "_" + str(application_no)[4:8] + "_" + str(application_no)[9:13] + "_" + str(file.attachment)
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/RTOR")
        fs.delete(str(file_name))
    file.delete()

    tor_attach = t_file_attachment.objects.filter(application_no=application_no, attachment_type='RTOR')
    return render(request, 'tor_attachment_page.html', {'tor_attach':tor_attach})

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
    v_application_count = 0
    r_application_count = 0
    ec_renewal_count = 0
    client_application_count = t_user_master.objects.filter(accept_reject__isnull=True, login_type='C').count()
    ca_authority = request.session.get('ca_authority', None)

    ec_details = t_ec_industries_t1_general.objects.all()
    
    if ca_authority is not None: 
        v_application_count = t_workflow_dtls.objects.filter(assigned_role_id='2', assigned_role_name='Verifier', ca_authority=request.session['ca_authority']).count()
        r_application_count = t_workflow_dtls.objects.filter(assigned_role_id='3', assigned_role_name='Reviewer', ca_authority=request.session['ca_authority']).count()
        expiry_date_threshold = datetime.now().date() + timedelta(days=30)
        ec_renewal_count = t_ec_industries_t1_general.objects.filter(ca_authority=request.session['ca_authority'],
                                                                                  application_status='A',
                                                                                  ec_expiry_date__lt=expiry_date_threshold).count()
    
    response = render(request, 'inspection/inspection.html', {
        'client_application_count': client_application_count,
        'inspection_list': inspection_list,
        'ec_renewal_count': ec_renewal_count,
        'v_application_count': v_application_count,
        'r_application_count': r_application_count, 
        'user_list': user_list, 
        'ec_details': ec_details
    })
    return response

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
    

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
def get_birms_token():
    """
    get an auth token
    """
    credentials = {'username': 'ECSS',
                   'password': 'ECSs@2024!'
                   }

    headers = {'Accept': 'application/json'}

    try:
        # Send POST request to authenticate
        res = requests.post('https://birmsstagging.drc.gov.bt/api-services/core-module/api/v1/auth/external-users/logMeIn',
                            json=credentials, headers=headers, verify=False)

        # Check if request was successful (status code 200)
        if res.status_code == 200:
            # Extract access token from response JSON
            #print("Response content:", res.text)
            json_data = res.json()
            access_token = json_data['content']['tokenDto']['accessToken']
            return access_token
        else:
            print("Authentication failed. Status code:", res.status_code)
    except Exception as e:
        print("An error occurred:", e)

def get_fines_penalties_details(request):
    ec_ref_no = request.GET.get('ec_ref_no')

    application_details = t_ec_industries_t1_general.objects.filter(application_no=ec_ref_no) | t_ec_industries_t1_general.objects.filter(ec_reference_no=ec_ref_no)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    return render(request, 'fines_penalties_details.html', {'application_details':application_details, 'dzongkhag':dzongkhag, 'gewog':gewog, 'village':village})

def save_fines_penalties(request):
    data = dict()
    try:
        application_no = request.POST.get('application_no')
        fines_penalties_type = request.POST.get('fines_penalty_type')
        ec_no = request.POST.get('ec_ref_no')
        proponent_name = request.POST.get('proponent_name')
        address = request.POST.get('address')
        validity = request.POST.get('ec_expiry_date')
        amount = request.POST.get('fines_and_penalties')
        
        parsed_date = datetime.strptime(validity, "%d-%m-%Y")
        formatted_date = parsed_date.strftime("%Y-%m-%d")

        t_fines_penalties.objects.create(application_no=application_no,
                                        fines_penalties_type=fines_penalties_type,
                                        fines_date=date.today(),
                                        ec_no=ec_no,
                                        proponent_name=proponent_name,
                                        address=address,
                                        validity=formatted_date,
                                        amount=amount,
                                        fines_status='P'
                                        )
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        for app_det in application_details:
            applicant = app_det.applicant_id
            service_id = app_det.service_id
            ca_auth = app_det.ca_authority
            cid_no = app_det.cid
            mob_no = app_det.contact_no
            app_name = app_det.app_name
            t_application_history.objects.create(application_no=application_no,
                application_status='FP',
                application_date=date.today(),
                action_date=date.today(),
                actor_id=request.session['login_id'], 
                actor_name=request.session['name'],
                applicant_id=applicant,
                remarks='Fines Payment Pending',
                service_id=service_id,
                ca_authority=ca_auth)
            
            token = get_birms_token()
            #print("Token:", token)

            url = "https://birmsstagging.drc.gov.bt/api-services/moenr-service/api/v1/paymentdetails/create"
            today_date_str = date.today().isoformat()

            payload = {
                "platform": "Environment Clearance Services System",
                "refNo": application_no,
                "taxPayerNo": "11303003082",
                "taxPayerDocumentNo": "11303003082",
                "paymentRequestDate": today_date_str,
                "agencyCode": "DTH1552",
                "payerEmail": request.session['email'],
                "mobileNo": mob_no,
                "totalPayableAmount": amount,
                "paymentDueDate": None,
                "taxPayerName": app_name,
                "code": "moenr",
                "paymentLists": [
                    {
                        "serviceCode": "100125",
                        "description": "ec_renewal",
                        "payableAmount": amount
                    }
                ]
            }

            headers = {'Authorization': "Bearer {}".format(token)}
            
            try:
                response = requests.post(url, headers=headers, json=payload, verify=False)
                print(payload)
                print("Response Status Code:", response.status_code)
                print("Response Content:", response.text)

                # Check if the response content is empty
                if response.status_code == 200:
                    try:
                        data = response.json()  # Parse response JSON
                        paymentAdviceNo = data['content']['paymentAdviceNo']
                        insert_app_payment_details(request, application_no, "fines_penalties", amount, "fines_penalties", paymentAdviceNo)
                       
                        t_payment_details.objects.create(
                            ref_no=application_no,
                            payment_request_date=date.today(),
                            tax_payer_name=request.session['name'],
                            agency_code="DTH1552",
                            tax_payer_document_no=cid_no,
                            mobile_no=mob_no,
                            payer_email=request.session['email'],
                            description="fines_and_penalties",
                            total_payable_amount=amount,
                            service_type="FINE",
                            payment_advice_no=paymentAdviceNo
                        )
                    except ValueError as e:
                        print("Failed to parse JSON response:", e)
                
                else:
                    print("Payment request failed with status code:", response.status_code)
                    print("Response text:", response.text)
            except requests.exceptions.RequestException as e:
                print("HTTP Request failed:", e)
            #insert_payment_details(request, application_no,pay_details.account_head_code,proponent_name,amount,ec_no)
        application_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
        for application_details in application_details:
            fines_penalties_email(application_details.email, application_no, amount)
        data['message'] = "success"
    except Exception as e:
        print('An error occurred:', e)
        data['message'] = "failure"
    return JsonResponse(data)

def insert_app_payment_details(request, application_no, description, total_amount, service_type, paymentAdviceNo):
    print("insert_app_payment_details")
    cid_no = None
    mob_no = None
    identifier = None
    
    app_details = t_ec_industries_t1_general.objects.filter(application_no=application_no)
    
    if description == "NEW GENERAL APPLICATION":
        identifier = "new_general_application"
    elif description == "NEW IEE APPLICATION":
        identifier = "new_iee_application"
    elif description == "NEW EA APPLICATION":
        identifier = "new_ea_application"
    elif description == "NEW FOREST APPLICATION":
        identifier = "new_forestry_application"
    elif description == "NEW GW APPLICATION":
        identifier = "new_ground_water_application"
    elif description == "NEW QUARRY APPLICATION":
        identifier = "new_quarry_application"
    elif description == "NEW ENERGY APPLICATION":
        identifier = "new_energy_application"
    elif description == "NEW TOURISM APPLICATION":
        identifier = "new_tourism_application"
    elif description == "NEW TRANSMISSION APPLICATION":
        identifier = "new_transmission_application"
    elif description == "NEW ROAD APPLICATION":
        identifier = "new_road_application"
    else:
        identifier = "tor_form"
    
    for app_det in app_details:
        cid_no = app_det.cid
        mob_no = app_det.contact_no
    
    if 'new' in identifier or 'tor' in identifier or 'ec_renewal' in identifier or 'fines' in identifier:
        t_payment_details.objects.create(
            ref_no=application_no,
            payment_request_date=date.today(),
            tax_payer_name=request.session['name'],
            agency_code="DTH1552",
            tax_payer_document_no="11303003082",
            mobile_no=mob_no,
            payer_email=request.session['email'],
            description=identifier,
            total_payable_amount=total_amount,
            service_type=service_type,
            payment_advice_no=paymentAdviceNo
        )
    
    return redirect(identifier)

def fines_penalties_email(email_id, application_no, amount):
    subject = 'FINES AND PENALTY'
    message = "Dear Sir," \
              "" \
              "Your Application No" + application_no + "Has Has Fines and Penalty " \
              " of Nu. " + amount + " . Please Pay To Further Proceess Your Application." 
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
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
                tor_clearance_no = get_tor_clearance_no(request,service_id)
                send_tor_approve_email(emailId, application_no, service_name, tor_clearance_no)
                application_details.update(tor_clearance_no=tor_clearance_no)
    return redirect(verify_application_list)

def tor_submit_email(email_id, application_no, service_name):
    subject = 'APPLICATION APPROVED'
    message = "Dear Sir," \
              "" \
              "Your TOR Application For" + service_name + "Has Been Approved. Your " \
              " Application No is " + application_no + " . " 
    recipient_list = [email_id]
    send_mail(subject, message, 'systems@moenr.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moenr.gov.bt', auth_password='wdiigzpprtutwmdc',
              connection=None, html_message=None)
    
def fines_penalties(request):
    application_details = t_ec_industries_t1_general.objects.filter(ec_reference_no__isnull=False)
    response = render(request, 'fines_penalties.html',{'application_details':application_details})

    # Set cache-control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def insert_payment_details(request,application_no,account_head, proponent_name,total_amount,ec_no):
    t_payment_details.objects.create(application_no=application_no,
            service_type='Fines And Penalties',
            application_date=date.today(), 
            proponent_name=proponent_name,
            amount=total_amount,
            account_head_code=account_head,
            ec_no=ec_no)
    return redirect(fines_penalties)

def ec_expired_list(request):
    current_date = timezone.now().date()
    expired_list = t_ec_industries_t1_general.objects.filter(ec_expiry_date__lt=current_date, application_status='A',is_revoked__isnull=True)
    service_details = t_service_master.objects.all()
    return render(request,'expired_list.html',{'expired_list':expired_list, 'service_details':service_details})

