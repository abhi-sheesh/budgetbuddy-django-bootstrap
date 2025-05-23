from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

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

    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"

    def progress(self):
        return (self.current_amount / self.target_amount) * 100 if self.target_amount else 0
