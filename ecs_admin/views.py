from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.utils import timezone

from ecs_admin.models import t_user_master, t_security_question_master, t_role_master, t_forgot_password, \
    t_file_attachment, t_menu_master, t_agency_master, t_proponent_type_master, t_dzongkhag_master, t_village_master,\
    t_gewog_master,t_submenu_master, t_other_details, t_about_us, t_notification_details, t_homepage_master
from ecs_admin.forms import UserForm, RoleForm
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
import string
import random
from django.http import JsonResponse
from datetime import date


# Create your views here.
def home(request):
    proponent_type = t_proponent_type_master.objects.all()
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    security = t_security_question_master.objects.all()
    menu_details = t_menu_master.objects.filter(is_active='Y',is_deleted='N')
    submenu_details = t_submenu_master.objects.filter(is_active='Y',is_deleted='N')
    other_details = t_other_details.objects.filter(is_active='Y',is_deleted='N')
    homepage_details = t_homepage_master.objects.filter()
    file_attachment = t_file_attachment.objects.all()
    home_attachment = t_file_attachment.objects.filter(attachment_type='H')
    return render(request, 'index.html',{'proponent_type':proponent_type,'dzongkhag':dzongkhag,
                                         'gewog':gewog,'village':village,'security':security,'menu_details':menu_details,
                                         'submenu_details':submenu_details, 'other_details':other_details,
                                         'file_attachment':file_attachment, 'homepage_details':homepage_details,
                                         'home_attachment':home_attachment})

def user_login(request):
    return render(request, 'login.html')

def contact_us(request):
    menu_details = t_menu_master.objects.all()
    return render(request,'contact_us.html',{'menu_details':menu_details})

def get_content_details(request):
    menu_id = request.GET.get('menu_id')
    identifier = request.GET.get('identifier')
    file_attachment = t_file_attachment.objects.all()
    if identifier == 'M':
        menu_details = t_menu_master.objects.filter(menu_id=menu_id)
    else:
        menu_details = t_submenu_master.objects.filter(sub_menu_id=menu_id)
    return render(request,'content_details.html',{'menu_details':menu_details,'identifier':identifier,
                                                  'file_attachment':file_attachment})

def login(request):
    _message = 'Please sign in'
    if request.method == 'POST':
        _username = request.POST['username']
        _password = request.POST['password']
        check_user = t_user_master.objects.filter(email_id=_username)
        if check_user is not None:
            for check_user in check_user:
                check_pass = check_password(_password, check_user.password)
                if check_pass:
                    check_user_status = t_user_master.objects.filter(is_active='Y', logical_delete='N')
                    if check_user_status:
                        if not check_user.last_login_date:
                            request.session['login_id'] = check_user.login_id
                            request.session['email'] = check_user.email_id
                            security = t_security_question_master.objects.all()
                            return render(request, 'update_password.html', {'security': security})
                        else:
                            for user_details in check_user_status:
                                if user_details.login_type == 'I':
                                    role_details = t_role_master.objects.filter(role_id=check_user.role_id_id)
                                    for roles in role_details:
                                        request.session['name'] = check_user.name
                                        request.session['role'] = roles.role_name
                                        request.session['email'] = check_user.email_id
                                        request.session['login_type'] = check_user.login_type
                                        return render(request, 'common_dashboard.html')
                                else:
                                    request.session['name'] = check_user.proponent_name
                                    request.session['email'] = check_user.email_id
                                    request.session['login_type'] = check_user.login_type
                                    return render(request, 'common_dashboard.html')

                    else:
                        _message = 'Invalid Account, Please Contact Admin.'
                else:
                    _message = 'User ID or Password Not Matching.'
        else:
            _message = 'Invalid Credentials, Please Try Again.'
    context = {'message': _message}
    return render(request, 'index.html', context)


def add_user(request):
    if request.method == 'POST':
        name = request.POST['name']
        gender = request.POST['gender']
        email = request.POST['email']
        contact_number = request.POST['contact_number']
        role = request.POST['role']
        agency = request.POST['agency']
        password = get_random_password_string(8)
        password_value = make_password(password)
        print(password_value)
        if role == '1':
            t_user_master.objects.create(login_type="I", name=name, gender=gender,
                                         contact_number=contact_number, email_id=email,
                                         password=password_value, is_active="Y",agency_id=None,
                                         logical_delete="N", last_login_date=None, created_by=None,
                                         created_on=None, modified_by=None, modified_on=None, role_id_id=role)
        else:
            t_user_master.objects.create(login_type="I", name=name, gender=gender,
                                         contact_number=contact_number, email_id=email,
                                         password=password_value, is_active="Y",agency_id=agency,
                                         logical_delete="N", last_login_date=None, created_by=None,
                                         created_on=None, modified_by=None, modified_on=None, role_id_id=role)
        details = t_user_master.objects.filter(login_type="I").order_by('login_id')
        sendmail(request, name, email, password)
        return redirect(user_master)

def get_random_password_string(length):
    password_characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(password_characters) for i in range(length))
    return password

def get_random_document_id_string(length):
    doc_id_characters = string.digits
    document_id = ''.join(random.choice(doc_id_characters) for i in range(length))
    return document_id

def load_gewog(request):
    dzongkhag_id = request.GET.get('dzongkhag_id')
    gewog_list = t_gewog_master.objects.filter(dzongkhag_code_id=dzongkhag_id).order_by('gewog_name')
    return render(request, 'gewog_list.html', {'gewog': gewog_list})


def load_village(request):
    gewog_id = request.GET.get('gewog_id')
    village_list = t_village_master.objects.filter(gewog_code_id=gewog_id).order_by('village_name')
    return render(request, 'village_list.html', {'village': village_list})


def check_email_id(request):
    data = dict()
    email = request.POST.get('email')
    message_count = t_user_master.objects.filter(email_id=email).count()
    data['count'] = message_count
    return JsonResponse(data)

def sendmail(request, name, email, password):
    subject = 'USER CREATED'
    message = "Dear " + name + " Login Id has been created for ECS System. Your Login Id is " \
              + email + " And Password is " + password + ""
    recipient_list = [email]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)


def manage_menu(request):
    menu_details = t_menu_master.objects.all()
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    return render(request, 'manage_menu.html',{'menu_details':menu_details,'document_id':document_id,
                                               'file_attachment':file_attachment})

def manage_submenu(request):
    menu_details = t_menu_master.objects.filter(has_sub_menu="Yes",is_active="Y")
    sub_menu_details = t_submenu_master.objects.all()
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    return render(request, 'manage_sub_menu.html',{'menu_details':menu_details,'sub_menu_details':sub_menu_details,
                                                   'document_id':document_id, 'file_attachment':file_attachment})

def add_menu_master(request):
    menu_name = request.POST.get('menu_name')
    has_submenu = request.POST.get('has_submenu')
    has_image = request.POST.get('has_image')
    menu_content = request.POST.get('content')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    document_id = request.POST.get('document_id')
    if has_submenu == 'Yes' and has_image == 'No':
        t_menu_master.objects.create(menu_name=menu_name,menu_content=menu_content,has_sub_menu=has_submenu,is_active='Y')
    else:
        t_menu_master.objects.create(menu_name=menu_name, menu_content=menu_content, has_sub_menu=has_submenu,
                                     is_active='Y',document_id=document_id)
        t_file_attachment.objects.create(document_id=document_id, file_path=file_url,
                                         attachment=file_name)
    return redirect(manage_menu)

def add_submenu_master(request):
    menu_id = request.POST.get('menu_name')
    sub_menu_name = request.POST.get('sub_menu_name')
    sub_menu_content = request.POST.get('content')
    document_id = request.POST.get('document_id')

    t_submenu_master.objects.create(menu_id=menu_id,sub_menu_name=sub_menu_name,sub_menu_content=sub_menu_content,
                                    document_id=document_id,is_active='Y', is_deleted='N')
    return redirect(manage_submenu)

def user_master(request):
    users = t_user_master.objects.filter(login_type='I')
    roles = t_role_master.objects.all().order_by('role_name')
    agency = t_agency_master.objects.all().order_by('agency_name')
    return render(request, 'user_master.html', {'users': users, 'role': roles, 'agency':agency})

def agency_master(request):
    agency_list = t_agency_master.objects.all()
    return render(request, 'agency_master.html', {'agency_list':agency_list})

def proponent_master(request):
    proponent_list = t_proponent_type_master.objects.all()
    return render(request, 'proponent_master.html', {'proponent_list':proponent_list})


def role_master(request):
    role_list = t_role_master.objects.all()
    return render(request, 'role_master.html', {'role':role_list})



def add_agency_master(request):
    agency_name = request.POST.get('agency_name')
    t_agency_master.objects.create(agency_name=agency_name)
    return redirect(agency_master)

def edit_agency_master(request):
    agency_id = request.POST.get('edit_agency_id')
    agency_name = request.POST.get('edit_agency_name')
    agency_details = t_agency_master.objects.filter(agency_id=agency_id)
    agency_details.update(agency_name=agency_name)
    return redirect(agency_master)

def delete_agency_master(request):
    agency_id = request.POST.get('delete_agency_id')
    agency_details = t_agency_master.objects.filter(agency_id=agency_id)
    agency_details.delete()
    return redirect(agency_master)

def add_proponent_master(request):
    proponent_name = request.POST.get('proponent_type_name')
    t_proponent_type_master.objects.create(proponent_type_name=proponent_name)
    return redirect(proponent_master)

def edit_proponent_master(request):
    proponent_id = request.POST.get('edit_proponent_type_id')
    proponent_name = request.POST.get('edit_proponent_type_name')
    agency_details = t_proponent_type_master.objects.filter(proponent_type_id=proponent_id)
    agency_details.update(proponent_type_name=proponent_name)
    return redirect(proponent_master)

def delete_proponent_master(request):
    proponent_id = request.POST.get('delete_proponent_type_id')
    proponent_details = t_proponent_type_master.objects.filter(proponent_type_id=proponent_id)
    proponent_details.delete()
    return redirect(proponent_master)

def manage_user(request):
    data = dict()
    login_id = request.GET.get('login_id')
    email_id = request.GET.get('Email_Id')
    name = request.GET.get('Name')
    identifier = request.GET.get('identifier')

    user_list = t_user_master.objects.filter(login_id=login_id)

    if identifier == "Activate":
        user_list.update(ii_active="Y")
    elif identifier == "Deactivate":
        user_list.update(ii_active="N")
    else:
        password = get_random_password_string(8)
        password_value = make_password(password)
        user_list.update(password=password_value)
        user_list.update(last_login_date=None)
        user_password_reset_mail(name, email_id, password)
    data['identifier'] = identifier
    return JsonResponse(data)


def user_password_reset_mail(Name, Email_Id, password):
    subject = 'PASSWORD RESET'
    message = "Dear " + Name + " Your Password Has Been Reset for Bhutan Bio-Food Security System. Your Login Id is " \
              + Email_Id + " And Password is " + password + ""
    recipient_list = [Email_Id]
    send_mail(subject, message, 'bafrabbfss@moaf.gov.bt', recipient_list, fail_silently=False,
              auth_user='systems@moaf.gov.bt', auth_password='hchqbgeeqvawkceg',
              connection=None, html_message=None)


def logout(request):
    request.session.flush()
    return redirect('/')


def account_setting(request):
    email_id = request.session['email']
    application_details = t_user_master.objects.filter(email_id=email_id)
    return render(request, 'account_setting.html', {'application_details': application_details})

def add_submenu_details(request):
    menu_details = t_menu_master.objects.filter(has_sub_menu='Yes', is_active='Y', is_deleted='N')
    document_id = get_random_document_id_string(5)
    return render(request, 'add_submenu.html', {'menu_details': menu_details, 'document_id':document_id})

def add_menu_details(request):
    document_id = get_random_document_id_string(5)
    return render(request, 'add_menu.html', {'document_id':document_id})

def save_menu_attachment(request):
    data = dict()
    menu_attach = request.FILES['menu_attach']
    file_name = menu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/menu/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, menu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/menu" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_menu_attachment_details(request):
    document_id = request.POST.get('document_id')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')

    t_file_attachment.objects.create(document_id=document_id,file_path=file_url,
                                     attachment=file_name,attachment_type='M')

    file_attach = t_file_attachment.objects.filter(document_id=document_id,attachment_type='M')
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def save_submenu_attachment(request):
    data = dict()
    sub_menu_attach = request.FILES['sub_menu_attach']
    file_name = sub_menu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/submenu/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, sub_menu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/submenu" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_submenu_attachment_details(request):
    document_id = request.POST.get('document_id')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')

    t_file_attachment.objects.create(document_id=document_id,file_path=file_url,
                                     attachment=file_name,attachment_type='SM')

    file_attach = t_file_attachment.objects.filter(document_id=document_id,attachment_type='SM')
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def delete_attachment(request):
    file_id = request.POST.get('file_id')
    identifier = request.POST.get('attachment_type')
    document_id = request.POST.get('document_id')
    print(file_id)
    print(identifier)
    if identifier == 'M':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/menu/")
            fs.delete(str(file_name))
        file.delete()
    elif identifier == 'SM':
        file = t_file_attachment.objects.filter(file_id=file_id)
        for file in file:
            file_name = file.attachment
            fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/submenu/")
            fs.delete(str(file_name))
        file.delete()
    file_attach = t_file_attachment.objects.filter(document_id=document_id)
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})


def save_menu_details(request):
    menu_name = request.POST.get('menu_name')
    has_sub_menu = request.POST.get('has_submenu')
    menu_content = request.POST.get('content')
    document_id = request.POST.get('document_id')

    if has_sub_menu == 'Yes':
        t_menu_master.objects.create(menu_name=menu_name, has_sub_menu=has_sub_menu,is_active='Y',is_deleted='N')
    else:
        t_menu_master.objects.create(menu_name=menu_name, has_sub_menu=has_sub_menu,menu_content=menu_content,
                                     document_id=document_id,is_active='Y',is_deleted='N')
    return redirect(manage_menu)

def update_menu_details(request):
    menu_id = request.POST.get('menu_id')
    menu_name = request.POST.get('menu_name')
    has_sub_menu = request.POST.get('has_submenu')
    menu_content = request.POST.get('content')
    document_id = request.POST.get('document_id')

    menu_details = t_menu_master.objects.filter(menu_id=menu_id)
    if has_sub_menu == 'Yes':
        menu_details.update(menu_name=menu_name, has_sub_menu=has_sub_menu)
    else:
        menu_details.update(menu_name=menu_name, has_sub_menu=has_sub_menu,menu_content=menu_content,
                                     document_id=document_id)
    return redirect(manage_menu)

def manage_menu_details(request):
    menu_id = request.POST.get('menu_id')
    identifier = request.POST.get('identifier')
    menu_details = t_menu_master.objects.filter(menu_id=menu_id)

    if identifier == 'Activate':
        menu_details.update(is_active='Y')
    elif identifier == 'Delete':
        menu_details.update(is_deleted='Y')
    else:
        menu_details.update(is_active='N')
    return redirect(manage_menu)

def update_submenu_details(request):
    sub_menu_id = request.POST.get('sub_menu_id')
    menu_id = request.POST.get('menu_name')
    sub_menu_name = request.POST.get('sub_menu_name')
    sub_menu_content = request.POST.get('content')

    menu_details = t_submenu_master.objects.filter(sub_menu_id=sub_menu_id)
    menu_details.update(menu_id=menu_id, sub_menu_name=sub_menu_name,sub_menu_content=sub_menu_content)
    return redirect(manage_submenu)

def manage_submenu_details(request):
    sub_menu_id = request.POST.get('sub_menu_id')
    identifier = request.POST.get('identifier')
    sub_menu_details = t_submenu_master.objects.filter(sub_menu_id=sub_menu_id)

    if identifier == 'Activate':
        sub_menu_details.update(is_active='Y')
    elif identifier == 'Delete':
        sub_menu_details.update(is_deleted='Y')
    else:
        sub_menu_details.update(is_active='N')
    return redirect(manage_submenu)

def manage_about_us(request):
    about_us_details = t_about_us.objects.filter(is_deleted='N')
    return render(request, 'manage_about_us.html', {'about_us_details': about_us_details })


def about_us(request):
    about_us_details = t_about_us.objects.filter(is_active='Y',is_deleted='N').order_by('about_us_id')
    return render(request, 'about_us.html', {'about_us_details': about_us_details })

def add_about_us(request):
    return render(request, 'add_about_us.html')

def save_about_us(request):
    about_us_title = request.POST.get('about_us_title')
    about_us_content = request.POST.get('about_us_content')
    t_about_us.objects.create(about_us_title=about_us_title,about_us_content=about_us_content,is_active='Y',is_deleted='N')
    return redirect(about_us)

def edit_about_us(request,about_us_id):
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)
    return render(request, 'edit_about_us.html', {'about_us_details': about_us_details})

def update_about_us(request):
    about_us_id = request.POST.get('about_us_id')
    about_us_title = request.POST.get('about_us_title')
    about_us_content = request.POST.get('about_us_content')
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)
    about_us_details.update(about_us_title=about_us_title,about_us_content=about_us_content)
    return redirect(about_us)

def manage_about_us_details(request):
    about_us_id = request.POST.get('about_us_id')
    identifier = request.POST.get('identifier')
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)

    if identifier == 'Activate':
        about_us_details.update(is_active='Y')
    elif identifier == 'Delete':
        about_us_details.update(is_deleted='Y')
    else:
        about_us_details.update(is_active='N')
    return redirect(about_us)

def show_about_us(request):
    about_us_id = request.GET.get('about_us_id')
    about_us_details = t_about_us.objects.filter(about_us_id=about_us_id)
    return render(request, 'view_about_us.html', {'about_us_details': about_us_details})

def track_application(request):
    return render(request, 'track_application.html')

def manage_notification_circulars(request):
    notification_details = t_notification_details.objects.filter(is_deleted='N')
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    return render(request,'manage_notifications_circulars.html', {'notification_details': notification_details,
                                                      'file_attachment':file_attachment,'document_id':document_id})

def notification_circulars(request):
    notification_details = t_notification_details.objects.filter(is_active='Y', is_deleted='N')
    file_attachment = t_file_attachment.objects.all()
    return render(request, 'notification_circulars.html', {'file_attachment': file_attachment,
                                                 'notification_details': notification_details})

def get_notification_details(request):
    notification_id = request.GET.get('notification_id')
    document_id = request.GET.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    notification_details = t_notification_details.objects.filter(notification_id=notification_id)
    return render(request, 'edit_notification_details.html',{'file_attachment':file_attachment,'notification_details':notification_details})


def manage_notification_details(request):
    notification_id = request.POST.get('notification_id')
    identifier = request.POST.get('identifier')
    notification_details = t_notification_details.objects.filter(notification_id=notification_id)

    if identifier == 'Activate':
        notification_details.update(is_active='Y')
    elif identifier == 'Delete':
        notification_details.update(is_deleted='Y')
    else:
        notification_details.update(is_active='N')
    return redirect(manage_notification_circulars)

def add_notification_file(request):
    data = dict()
    attachment_name = request.FILES['notification_document']

    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/notifications")
    if fs.exists(attachment_name.name):
        data['form_is_valid'] = False
    else:
        fs.save(attachment_name.name, attachment_name)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/notifications" + "/" + attachment_name.name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = attachment_name.name
    return JsonResponse(data)

def add_notification_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    notification_title = request.POST.get('notification_title')

    t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id,attachment_type='NC')

    t_notification_details.objects.create(notification_title=notification_title,document_id=document_id,is_active='Y',
                                         is_deleted='N')

    return redirect(manage_notification_circulars)

def delete_notification_attachment(request):
    document_id = request.POST.get('document_id')
    file = t_file_attachment.objects.filter(document_id=document_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/notifications")
        fs.delete(str(file_name))
    file.delete()

    file_attach = t_file_attachment.objects.filter(document_id=document_id)
    notification_details = t_notification_details.objects.filter(document_id=document_id)
    return render(request, 'edit_notification_details.html', {'file_attachment':file_attach,
                                                             'notification_details':notification_details})

def update_notification_file(request):
    data = dict()
    attachment_name = request.FILES['edit_notification_document']
    document_id = request.POST.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)

    if file_attachment.exists():
        data['file_url'] = file_attachment.file_url
        data['file_name'] = file_attachment.attachment
        return JsonResponse(data)
    else:
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/notifications")
        if fs.exists(attachment_name.name):
            data['form_is_valid'] = False
        else:
            fs.save(attachment_name.name, attachment_name)
            file_url = "attachments" + "/" + str(timezone.now().year) + "/notifications" + "/" + attachment_name.name
            data['form_is_valid'] = True
            data['file_url'] = file_url
            data['file_name'] = attachment_name.name
        return JsonResponse(data)

def update_notification_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    notification_title = request.POST.get('notification_title')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    notification_details = t_notification_details.objects.filter(document_id=document_id)
    if file_attachment.exists():
        notification_details.update(notification_title=notification_title)
    else:
        t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id,attachment_type='NC')
        notification_details.update(notification_title=notification_title)
    return redirect(manage_notification_circulars)

def manage_committee_schedule(request):
    return render(request, 'manage_committee_schedule.html')

def manage_eia_related(request):
    return render(request, 'manage_eia_related.html')

def manage_live_statistics(request):
    return render(request, 'manage_live_statistics.html')

def manage_home_page(request):
    home_page_details = t_homepage_master.objects.filter(homepage_id='1')
    file_attachment = t_file_attachment.objects.filter(attachment_type='H')
    return render(request, 'manage_home_page.html', {'home_page_details': home_page_details,
                                                'file_attach': file_attachment})

def update_homepage_details(request):
    homepage_title = request.POST.get('homepage_title')
    content = request.POST.get('content')
    home_page = t_homepage_master.objects.filter(homepage_id=1)
    home_page.update(homepage_title=homepage_title,homepage_content=content)
    home_page_details = t_homepage_master.objects.filter(homepage_id=1)
    file_attach = t_file_attachment.objects.filter(attachment_type='H')
    return render(request, 'manage_home_page.html', {'home_page_details': home_page_details, 'file_attach': file_attach})

def save_homepage_attachment(request):
    data = dict()
    menu_attach = request.FILES['homepage_attach']
    file_name = menu_attach.name
    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/homepage/")
    if fs.exists(file_name):
        data['form_is_valid'] = False
    else:
        fs.save(file_name, menu_attach)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/homepage" + "/" + file_name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = file_name
    return JsonResponse(data)

def save_homepage_attachment_details(request):
    document_id = request.POST.get('document_id')
    file_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')

    t_file_attachment.objects.create(document_id=document_id,file_path=file_url,
                                     attachment=file_name,attachment_type='H')

    file_attach = t_file_attachment.objects.filter(document_id=document_id,attachment_type='H')
    home_page_details = t_homepage_master.objects.filter(homepage_id=1)
    return render(request, 'file_attachment_page.html', {'file_attach': file_attach})

def change_password(request):
    data = dict()
    email_id = request.session['email']
    password_value = make_password(request.POST.get('confirm_password'))
    application_details = t_user_master.objects.filter(email_id=email_id)
    application_details.update(password=password_value)
    data['message'] = "update_successful"
    return JsonResponse(data)


def check_user_password(request):
    data = dict()
    _username = request.session['email']
    _password = request.GET.get('current_password')
    user_details = t_user_master.objects.filter(email_id=_username)
    for user_data in user_details:
        check_pass = check_password(_password, user_data.password)
        if check_pass:
            data['form_is_valid'] = True
        else:
            data['form_is_valid'] = False
        return JsonResponse(data)


def change_mobile_number(request):
    data = dict()
    email_id = request.session['email']
    new_contact_number = request.POST.get('new_contact_number')
    application_details = t_user_master.objects.filter(email_id=email_id)
    application_details.update(mobile_no=new_contact_number)
    data['message'] = "update_successful"
    return JsonResponse(data)


def client_registration(request):
    data = dict()
    proponent_type = request.POST.get('proponent_type')
    proponent_name = request.POST.get('proponent_name')
    address = request.POST.get('proponent_address')
    contact_person = request.POST.get('contact_person')
    email = request.POST.get('email')
    contact_number = request.POST.get('contact_number')
    dzongkhag = request.POST.get('dzongkhag')
    gewog = request.POST.get('gewog')
    village = request.POST.get('village')

    t_user_master.objects.create(login_type='C', proponent_type=proponent_type, proponent_name=proponent_name,
                                 address=address, contact_person=contact_person, email_id=email,
                                 contact_number=contact_number, dzongkhag_code=dzongkhag, gewog_code=gewog,
                                 village_code=village,is_active="N", logical_delete="N",)

    data['message'] = "registration successful"
    return JsonResponse(data)

def new_client_registration(request):
    reg_clients = t_user_master.objects.filter(login_type="C")
    clients = reg_clients.filter(accept_reject=None)
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    proponent_type = t_proponent_type_master.objects.all()
    return render(request, 'new_client_registration.html', {'new_clients': clients,'dzongkhag':dzongkhag,
                                                            'gewog':gewog, 'village':village,
                                                            'proponent_type':proponent_type})

def registered_client(request):
    reg_clients = t_user_master.objects.filter(login_type='C')
    clients = reg_clients.filter(accept_reject='A')
    dzongkhag = t_dzongkhag_master.objects.all()
    gewog = t_gewog_master.objects.all()
    village = t_village_master.objects.all()
    proponent_type = t_proponent_type_master.objects.all()
    return render(request, 'registered_clients.html', {'new_clients': clients,'dzongkhag':dzongkhag,
                                                            'gewog':gewog, 'village':village,
                                                            'proponent_type':proponent_type})


def manage_client(request):
    login_id = request.POST.get('login_id')
    email_id = request.POST.get('email')
    name = request.POST.get('name')
    identifier = request.POST.get('identifier')

    reg_clients = t_user_master.objects.filter(login_id=login_id)
    if identifier == 'Accept':
        password = get_random_password_string(8)
        password_value = make_password(password)
        reg_clients.update(accept_reject="A")
        reg_clients.update(is_active="Y")
        reg_clients.update(password=password_value)
        accept_mail(request, name, email_id, password)
        return redirect(new_client_registration)
    elif identifier == 'Reject':
        reg_clients.update(accept_reject="R")
        reject_mail(request, name, email_id)
        return redirect(new_client_registration)

def accept_mail(request, name, email_id, password):
    subject = 'Client Accepted'
    message = "Dear " + name + " Your Registration for ECS System Is Accepted. Your Login Id is " \
              + email_id + " And Password is " + password + ""
    recipient_list = [email_id]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)

def reject_mail(request, name, email_id):
    subject = 'Client Accepted'
    message = "Dear " + name + " Your Registration for ECS System Has Been Rejected. Your Login Id is " \
                ""
    recipient_list = [email_id]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)

def send_reset_pass_mail(name, email, password):
    subject = 'PASSWORD_RESET'
    message = "Dear " + name + " Your password has been reset for ECS System. Your Login Id is " \
              + email + " And Password is " + password + ""
    recipient_list = [email]
    send_mail(subject, message, 'sparkletechnology2019@gmail.com', recipient_list, fail_silently=False,
              auth_user='sparkletechnology2019@gmail.com', auth_password='ypohpmxhdlmidwgm',
              connection=None, html_message=None)

def update_first_login_details(request):
    login_id = request.POST['login_id']
    confirm_password = request.POST['password']
    security_question = request.POST['security_question']
    security_answer = request.POST['answer']
    today = date.today()

    password = make_password(confirm_password)
    reg_users = t_user_master.objects.filter(pk=login_id)
    reg_users.update(password=password)
    reg_users.update(last_login_date=today)
    t_forgot_password.objects.create(login_id=login_id, security_question_id=security_question, answer=security_answer)
    return redirect(login)

def get_security_answer(request):
    data = dict()
    email_id = request.GET.get('email_id')
    question_id = request.GET.get('questionId')
    details = t_user_master.objects.filter(email_id=email_id)
    for app_details in details:
        login_id = app_details.login_id
        application_details = t_forgot_password.objects.filter(login_id=login_id, security_question_id=question_id)
        for application in application_details:
            data["answer"] = application.answer
    return JsonResponse(data)

def update_password(request):
    data = dict()
    email_id = request.POST.get('email_id')
    password = get_random_password_string(8)
    password_value = make_password(password)
    application_details = t_user_master.objects.filter(email_id=email_id)
    application_details.update(password=password_value)
    data['message'] = "update_successful"
    for details in application_details:
        if details.login_type == 'I':
            send_reset_pass_mail(details.name, email_id, password)
        else:
            send_reset_pass_mail(details.proponent_name, email_id, password)
    return JsonResponse(data)


def load_security_question(request):
    email_id = request.GET.get('email')
    login_details = t_user_master.objects.filter(email_id=email_id)
    for id_details in login_details:
        login_id = id_details.login_id
        details = t_forgot_password.objects.filter(login_id=login_id)
        for security_details in details:
            question_id = security_details.security_question_id
            security = t_security_question_master.objects.filter(question_id=question_id)
    return render(request, 'forgot_pass_list.html', {'security': security})


def manage_publications(request):
    publication_details = t_other_details.objects.filter(is_deleted='N')
    document_id = get_random_document_id_string(5)
    file_attachment = t_file_attachment.objects.all()
    return render(request,'publication_master.html', {'publication_details': publication_details,
                                                      'file_attachment':file_attachment,'document_id':document_id})

def add_publication_file(request):
    data = dict()
    attachment_name = request.FILES['publication_document']

    fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/others")
    if fs.exists(attachment_name.name):
        data['form_is_valid'] = False
    else:
        fs.save(attachment_name.name, attachment_name)
        file_url = "attachments" + "/" + str(timezone.now().year) + "/others" + "/" + attachment_name.name
        data['form_is_valid'] = True
        data['file_url'] = file_url
        data['file_name'] = attachment_name.name
    return JsonResponse(data)

def add_publication_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    title = request.POST.get('title')
    type = request.POST.get('type')

    t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id)

    t_other_details.objects.create(title=title, type=type, document_id=document_id,is_active='Y',
                                         is_deleted='N')

    return redirect(manage_publications)


def get_other_details(request):
    others_id = request.GET.get('others_id')
    document_id = request.GET.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    others_details = t_other_details.objects.filter(others_id=others_id)
    return render(request, 'edit_other_details.html',{'file_attachment':file_attachment,'others_details':others_details})

def get_menu_details(request,menu_id):
    menu_details = t_menu_master.objects.filter(menu_id=menu_id)
    for menu_det in menu_details:
        doc_id = menu_det.document_id
        file_attach = t_file_attachment.objects.filter(document_id=doc_id)
        return render(request, 'edit_menu_details.html',{'menu_details':menu_details,'file_attach':file_attach })

def get_submenu_details(request, sub_menu_id):
    sub_menu_details = t_submenu_master.objects.filter(sub_menu_id=sub_menu_id)
    for sub_menu_det in sub_menu_details:
        doc_id = sub_menu_det.document_id
        file_attach = t_file_attachment.objects.filter(document_id=doc_id)
        menu_list = t_menu_master.objects.all()
        return render(request, 'edit_submenu_details.html', {'sub_menu_details': sub_menu_details, 'file_attach': file_attach,
                                                             'menu_list':menu_list})

def delete_publication_attachment(request):
    document_id = request.POST.get('document_id')
    file = t_file_attachment.objects.filter(document_id=document_id)
    for file in file:
        file_name = file.attachment
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/publications")
        fs.delete(str(file_name))
    file.delete()

    file_attach = t_file_attachment.objects.filter(document_id=document_id)
    publication_details = t_other_details.objects.filter(document_id=document_id)
    return render(request, 'edit_other_details.html', {'file_attachment':file_attach,
                                                             'publication_details':publication_details})

def update_publication_file(request):
    data = dict()
    attachment_name = request.FILES['edit_publication_document']
    document_id = request.POST.get('document_id')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)

    if file_attachment.exists():
        data['file_url'] = file_attachment.file_url
        data['file_name'] = file_attachment.attachment
        return JsonResponse(data)
    else:
        fs = FileSystemStorage("attachments" + "/" + str(timezone.now().year) + "/others")
        if fs.exists(attachment_name.name):
            data['form_is_valid'] = False
        else:
            fs.save(attachment_name.name, attachment_name)
            file_url = "attachments" + "/" + str(timezone.now().year) + "/others" + "/" + attachment_name.name
            data['form_is_valid'] = True
            data['file_url'] = file_url
            data['file_name'] = attachment_name.name
        return JsonResponse(data)

def update_publication_attach(request):
    document_id = request.POST.get('document_id')
    attachment_name = request.POST.get('filename')
    file_url = request.POST.get('file_url')
    title = request.POST.get('title')
    type = request.POST.get('type')

    file_attachment = t_file_attachment.objects.filter(document_id=document_id)
    publication_details = t_other_details.objects.filter(document_id=document_id)
    if file_attachment.exists():
        publication_details.update(title=title)
        publication_details.update(type=type)
    else:

        t_file_attachment.objects.create(file_path=file_url,attachment=attachment_name,document_id=document_id)
        publication_details.update(title=title)
        publication_details.update(type=type)
    return redirect(manage_publications)

def manage_publication_details(request):
    others_id = request.POST.get('publication_id')
    identifier = request.POST.get('identifier')
    publication_details = t_other_details.objects.filter(others_id=others_id)

    if identifier == 'Activate':
        publication_details.update(is_active='Y')
    elif identifier == 'Delete':
        publication_details.update(is_deleted='Y')
    else:
        publication_details.update(is_active='N')
    return redirect(manage_publications)

def publications(request):
    publication_details = t_other_details.objects.filter(is_active='Y',is_deleted='N')
    file_attachment = t_file_attachment.objects.all()
    return render(request, 'publications.html', {'file_attachment': file_attachment,
                                                 'publication_details': publication_details})

