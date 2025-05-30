from django.utils.deprecation import MiddlewareMixin
from .utils import check_budget_alerts, check_goal_alerts, check_bill_reminders
from .models import NotificationPreference

class NotificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            prefs = NotificationPreference.objects.get_or_create(user=request.user)[0]
            
            if prefs.budget_alerts:
                check_budget_alerts(request.user)
            if prefs.goal_alerts:
                check_goal_alerts(request.user)
            if prefs.bill_reminders:
                check_bill_reminders(request.user)