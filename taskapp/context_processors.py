def notification_processor(request):
    context = {
        'unread_notifications_count': 0,
        'recent_notifications': []
    }
    
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.all()[:5]
        #print(f"Unread count: {unread_count}")
        #print(f"Recent notifications: {list(recent_notifications)}")
        
        context.update({
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        })
    
    return context 