# ecs_admin/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging

from proponent.models import t_ec_additional_information, t_ec_ai_remainder

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_additional_info_reminder(self):
    """
    Runs daily at 8 AM (via Celery Beat).
    Sends ONE reminder per month to applicants whose:
      - additional_info_due_date is set and not yet passed
      - additional_info_proponent is still empty (no response submitted yet)
      - applicant_id (email) is available
      - last_reminder_sent is NULL or was more than 30 days ago
    Logs every sent reminder to t_ec_ai_remainder.
    """

    today = timezone.localdate()
    one_month_ago = today - timedelta(days=30)

    #  Core business logic filter
    pending_records = t_ec_additional_information.objects.filter(
        additional_info_due_date__isnull=False,       # Due date must be set
        additional_info_due_date__gte=today,           # Due date not yet passed
        applicant_id__isnull=False,                    # Email must exist
        additional_info_proponent__isnull=True,        # Proponent has NOT responded yet
    ).filter(
        Q(last_reminder_sent__isnull=True) |           # Never reminded before
        Q(last_reminder_sent__lte=one_month_ago)       # OR last reminded 30+ days ago
    )

    success_count = 0
    fail_count = 0

    for record in pending_records:
        applicant_email = record.applicant_id
        due_date = record.additional_info_due_date
        app_no = record.application_no or "N/A"
        ca_request = record.additional_info_ca or "Please refer to the portal for details."
        ca_date = record.additional_info_ca_date
        precord_id = record.record_id

        try:
            #  Send reminder email
            send_mail(
                subject=f"[DECC] Reminder: Additional Information Required – Application No. {app_no}",
                message=build_email_body(app_no, ca_request, ca_date, due_date),
                from_email=None,          # Uses EMAIL_HOST_USER from settings.py
                recipient_list=[applicant_email],
                fail_silently=False,
            )

            #  Update last_reminder_sent on the source record
            record.last_reminder_sent = today
            record.save(update_fields=['last_reminder_sent'])

            #  Log to t_ec_ai_remainder history table
            t_ec_ai_remainder.objects.create(
                application_no=app_no,
                applicant_id=applicant_email,
                reminder_sent=today,
                precord_id=precord_id,
            )

            success_count += 1
            logger.info(
                f" Reminder sent | App: {app_no} | To: {applicant_email} | Date: {today}"
            )

        except Exception as exc:
            fail_count += 1
            logger.error(
                f" Failed to send | App: {app_no} | To: {applicant_email} | Error: {exc}"
            )
            # Retry up to 3 times with a 5-minute delay
            raise self.retry(exc=exc, countdown=300)

    logger.info(
        f"📬 Reminder Task Complete → Success: {success_count} | Failed: {fail_count}"
    )
    return {
        "date": str(today),
        "success": success_count,
        "failed": fail_count,
    }


def build_email_body(app_no, ca_request, ca_date, due_date):
    """
    Builds a clean plain-text reminder email body.
    """
    ca_date_str = ca_date.strftime('%d %B %Y') if ca_date else "N/A"
    due_date_str = due_date.strftime('%d %B %Y') if due_date else "N/A"

    return f"""
Dear Applicant,

This is a reminder from the Department of Environment & Climate Change (DECC).

You have a pending request for Additional Information regarding your application.

  Application No       : {app_no}
  Information Requested: {ca_request}
  Date of Request      : {ca_date_str}
  Submission Due Date  : {due_date_str}

Please log in to the DECC portal and submit the required information 
before the due date. Failure to do so may affect the processing of your application.

If you have already submitted the information, please disregard this email.

For any queries, contact the DECC office.

Regards,
DECC Portal
Department of Environment & Climate Change
    """.strip()
