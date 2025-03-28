from .models import Notification  # Adjust based on your app name
from django.core.mail import send_mail
from django.conf import settings

def send_task_email(subject, message, recipient_email):
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,  # Sender email (from settings)
        [recipient_email],
        fail_silently=False,
    )


def create_notification(user, notification_type, title, message, project=None, task=None):
    try:
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_project=project,
            related_task=task
        )
        print(f"Created notification: {notification}")
        return notification
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None 