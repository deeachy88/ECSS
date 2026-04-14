from django.contrib import admin

# Register your models here.

from django.contrib import admin
from proponent.models import t_ec_ai_remainder


@admin.register(t_ec_ai_remainder)
class AIReminderAdmin(admin.ModelAdmin):

    list_display = [
        'record_id',
        'application_no',
        'applicant_id',
        'reminder_sent',
    ]

    search_fields = [
        'application_no',
        'applicant_id',
    ]

    list_filter = [
        'reminder_sent',
    ]

    ordering = ['-reminder_sent']

    # ✅ Prevent editing of log records
    readonly_fields = [
        'record_id',
        'application_no',
        'applicant_id',
        'reminder_sent',
    ]
