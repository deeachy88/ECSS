from django import forms

from ecs_admin.models import t_user_master, t_role_master

class UserForm(forms.ModelForm):
    class Meta:
        model = t_user_master
        fields = '__all__'

class RoleForm(forms.ModelForm):
    class Meta:
        model = t_role_master
        fields = '__all__'