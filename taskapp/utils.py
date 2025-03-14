from .models import Notification  # Adjust based on your app name

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