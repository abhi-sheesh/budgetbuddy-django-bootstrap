from datetime import timedelta
from django.utils import timezone
from .models import Notification, Budget, Goal, Bill

def should_send_notification(notification_type, user, message):
    now = timezone.now()
    threshold = {
        'BUDGET': timedelta(hours=12),
        'GOAL': timedelta(days=1),
        'BILL': timedelta(days=1)
    }.get(notification_type, timedelta(days=1))
    
    existing = Notification.objects.filter(
        user=user,
        notification_type=notification_type,
        message=message,
        is_active=True
    ).order_by('-last_sent').first()
    
    if not existing:
        return True
    
    if existing.repeat_frequency == 'ONCE':
        return False
    elif existing.repeat_frequency == 'DAILY' and (now - existing.last_sent) >= timedelta(days=1):
        return True
    elif existing.repeat_frequency == 'WEEKLY' and (now - existing.last_sent) >= timedelta(weeks=1):
        return True
    
    return False

def create_notification(user, message, notification_type, repeat_frequency='ONCE'):
    if should_send_notification(notification_type, user, message):
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=notification_type,
            repeat_frequency=repeat_frequency
        )

def check_budget_alerts(user):
    budgets = Budget.objects.filter(user=user)
    for budget in budgets:
        progress = budget.progress()
        truncated = int(progress*100)/100
        if progress >= 90:
            create_notification(
                user,
                f"Budget for {budget.category} is at {truncated:.2f}%",
                'BUDGET',
                'DAILY' if progress >= 95 else 'WEEKLY'
            )

def check_goal_alerts(user):
    goals = Goal.objects.filter(user=user, completed=False)
    for goal in goals:
        progress = goal.progress()
        truncated = int(progress*100)/100
        days_left = (goal.target_date - timezone.now().date()).days
        
        if progress >= 90:
            create_notification(
                user,
                f"Goal '{goal.name}' is {truncated:.2f}% complete!",
                'GOAL',
                'DAILY' if progress >= 95 else 'WEEKLY'
            )
        elif days_left <= 7 and days_left > 0:
            freq = 'DAILY' if days_left <= 3 else 'WEEKLY'
            create_notification(
                user,
                f"Goal '{goal.name}' due in {days_left} days",
                'GOAL',
                freq
            )

def check_bill_reminders(user):
    upcoming_bills = Bill.objects.filter(
        user=user,
        is_paid=False,
        due_date__lte=timezone.now().date() + timedelta(days=7)
    )
    
    for bill in upcoming_bills:
        days_until = (bill.due_date - timezone.now().date()).days
        freq = 'DAILY' if days_until <= 3 else 'WEEKLY'
        create_notification(
            user,
            f"Bill '{bill.name}' (Rs {bill.amount}) due {'today' if days_until == 0 else f'in {days_until} days'}",
            'BILL',
            freq
        )