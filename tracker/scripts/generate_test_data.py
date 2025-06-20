import os
import sys
import django
import random
from datetime import timedelta
from django.utils import timezone

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_tracker.settings')
django.setup()

from tracker.models import Transaction, Category
from django.contrib.auth.models import User

def generate_test_expense_data(user, days=365):
    expense_category, _ = Category.objects.get_or_create(
        name="Groceries",
        category_type="EX",
        user=user
    )

    start_date = timezone.now().date() - timedelta(days=days)
    count = 0

    for i in range(days):
        date = start_date + timedelta(days=i)
        if random.random() > 0.8:
            continue
        amount = round(random.uniform(100, 1000), 2)
        Transaction.objects.create(
            user=user,
            category=expense_category,
            amount=amount,
            date=date,
            description="Auto-generated test data"
        )
        count += 1

    print(f"✅ Generated {count} expense transactions for user {user.username}")

if __name__ == '__main__':
    user = User.objects.get(username='abhishesh')
    generate_test_expense_data(user)
