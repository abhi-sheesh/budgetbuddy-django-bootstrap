from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    CATEGORY_TYPES = [
        ('IN', 'Income'),
        ('EX', 'Expense'),
    ]
    category_type = models.CharField(max_length=2, choices=CATEGORY_TYPES)

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.amount} - {self.category} on {self.date}"

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.category.category_type != 'EX':
            raise ValidationError("Budgeting can only be applied to expense categories")

    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.start_date} to {self.end_date})"

    def progress(self):
        expenses = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            date__gte=self.start_date,
            date__lte=self.end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return min((expenses / self.amount) * 100, 100) if self.amount else 0

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    target_date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - Rs {self.current_amount}/Rs {self.target_amount}"

    def progress(self):
        return (self.current_amount / self.target_amount) * 100 if self.target_amount else 0

    def can_add_deposit(self):
        return not self.completed and self.current_amount < self.target_amount

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, 0)
    
    def can_add_deposit(self):
        return not self.completed and self.remaining_amount > 0

class GoalDeposit(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.goal.can_add_deposit():
            raise ValidationError("Cannot add deposit to completed goal")

        super().save(*args, **kwargs)
        self.goal.current_amount += self.amount
        if self.goal.current_amount >= self.goal.target_amount:
            self.goal.completed = True
        self.goal.save()

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, choices=[
        ('GOAL', 'Goal Alert'),
        ('BUDGET', 'Budget Alert'), 
        ('BILL', 'Bill Reminder')
    ])
    last_sent = models.DateTimeField(auto_now_add=True)
    repeat_frequency = models.CharField(max_length=10, choices=[
        ('ONCE', 'Once'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly')
    ], default='ONCE')
    is_active = models.BooleanField(default=True)

class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(max_length=20, blank=True, choices=[
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly')
    ])

    def __str__(self):
        return f"{self.name} - ₹{self.amount} (Due: {self.due_date})"

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    budget_alerts = models.BooleanField(default=True)
    goal_alerts = models.BooleanField(default=True)
    bill_reminders = models.BooleanField(default=True)
    budget_threshold = models.IntegerField(default=90)
    goal_days_prior = models.IntegerField(default=7)
    bill_days_prior = models.IntegerField(default=3)