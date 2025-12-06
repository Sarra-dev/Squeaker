from .models import Notification

def create_notification(recipient, sender, notification_type, meep=None, comment=None):
    """
    Create a notification for a user action
    Don't create notification if user is interacting with their own content
    """
    if recipient == sender:
        return None
    
    # Avoid duplicate notifications for the same action
    if notification_type == 'like' and meep:
        existing = Notification.objects.filter(
            recipient=recipient,
            sender=sender,
            notification_type='like',
            meep=meep
        ).exists()
        if existing:
            return None
    
    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        meep=meep,
        comment=comment
    )
    return notification