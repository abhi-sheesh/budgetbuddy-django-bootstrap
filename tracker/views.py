from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from .forms import SignUpForm, TransactionForm, CategoryForm, BudgetForm, GoalForm, BillForm, NotificationPreferenceForm, GoalDepositForm
from .models import Transaction, Category, Budget, Goal, Bill, Notification, NotificationPreference
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from .filters import TransactionFilter
from django.core.paginator import Paginator
from django.views.generic import ListView
from django.contrib import messages
from django.http import JsonResponse
import json
from .utils import check_budget_alerts, check_goal_alerts, check_bill_reminders
from django.contrib import messages
import logging
from .mining import detect_spending_patterns
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dashboard(request):
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]
    
    budgets = Budget.objects.filter(user=request.user, end_date__gte=timezone.now())
    
    goals = Goal.objects.filter(user=request.user, completed=False)
    
    today = timezone.now()
    month_start = today.replace(day=1)
    month_end = month_start + timedelta(days=32)
    month_end = month_end.replace(day=1) - timedelta(days=1)
    
    income = Transaction.objects.filter(
        user=request.user,
        category__category_type='IN',
        date__gte=month_start,
        date__lte=month_end
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    expenses = Transaction.objects.filter(
        user=request.user,
        category__category_type='EX',
        date__gte=month_start,
        date__lte=month_end
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    savings = income - expenses
    
    expense_categories = Category.objects.filter(user=request.user, category_type='EX')
    expense_data = []
    for category in expense_categories:
        total = Transaction.objects.filter(
            user=request.user,
            category=category,
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        if total > 0:
            expense_data.append({
                'category': category.name,
                'amount': float(total)
            })
    
    context = {
        'recent_transactions': recent_transactions,
        'budgets': budgets,
        'goals': goals,
        'income': income,
        'expenses': expenses,
        'savings': savings,
        'expense_data': json.dumps(expense_data),
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transactions')
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'tracker/add_transaction.html', {'form': form})

@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    
    transaction_filter = TransactionFilter(request.GET, queryset=transactions, user=request.user)
    transactions = transaction_filter.qs
    
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter': transaction_filter,
    }
    return render(request, 'tracker/transaction_list.html', context)

@login_required
def income_list(request):
    incomes = Transaction.objects.filter(
        user=request.user,
        category__category_type='IN'
    ).order_by('-date')
    
    transaction_filter = TransactionFilter(request.GET, queryset=incomes, user=request.user)
    incomes = transaction_filter.qs
    
    context = {
        'incomes': incomes,
        'filter': transaction_filter,
    }
    return render(request, 'tracker/income_list.html', context)

@login_required
def expense_list(request):
    expenses = Transaction.objects.filter(
        user=request.user,
        category__category_type='EX'
    ).order_by('-date')
    
    transaction_filter = TransactionFilter(request.GET, queryset=expenses, user=request.user)
    expenses = transaction_filter.qs
    
    context = {
        'expenses': expenses,
        'filter': transaction_filter,
    }
    return render(request, 'tracker/expense_list.html', context)

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('categories')
    else:
        form = CategoryForm()
    return render(request, 'tracker/add_category.html', {'form': form})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'tracker/category_list.html', {'categories': categories})

@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('budgets')
    else:
        form = BudgetForm(user=request.user)
    return render(request, 'tracker/add_budget.html', {'form': form})

@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user)
    return render(request, 'tracker/budget_list.html', {'budgets': budgets})

@login_required
def add_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('goals')
    else:
        form = GoalForm()
    return render(request, 'tracker/add_goal.html', {'form': form})

@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tracker/goal_list.html', {'goals': goals})

@login_required
def add_goal_deposit(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    if not goal.can_add_deposit():
        messages.error(request, "Cannot add deposit - goal already completed!")
        return redirect('goals')
    
    if request.method == 'POST':
        form = GoalDepositForm(request.POST, goal=goal)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.goal = goal
            try:
                deposit.save()
                messages.success(request, f'Deposit of Rs {deposit.amount} added to {goal.name}')
                return redirect('goals')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = GoalDepositForm(goal=goal)
    
    return render(request, 'tracker/add_deposit.html', {
        'form': form,
        'goal': goal
    })

@login_required
def goal_deposit_history(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    deposits = goal.deposits.all().order_by('-deposit_date')
    return render(request, 'tracker/deposit_history.html', {
        'goal': goal,
        'deposits': deposits
    })

@login_required
def reports(request):
    return render(request, 'tracker/reports.html')

@login_required
def chart_data(request):
    time_range = request.GET.get('range', 'monthly')
    user = request.user
    
    today = datetime.now().date()
    if time_range == 'yearly':
        start_date = today - timedelta(days=365)
    elif time_range == 'quarterly':
        start_date = today - timedelta(days=90)
    else:  
        start_date = today - timedelta(days=30)
    
    transactions = Transaction.objects.filter(
        user=user,
        date__range=[start_date, today]
    ).values('date', 'category__category_type').annotate(amount=Sum('amount'))
    
    expenses = Transaction.objects.filter(
        user=user,
        category__category_type='EX',
        date__range=[start_date, today]
    ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    incomes = Transaction.objects.filter(
        user=user,
        category__category_type='IN', 
        date__range=[start_date, today]
    ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    return JsonResponse({
        'monthly': {
            'labels': [t['date'].strftime('%b %d') for t in transactions],
            'income': [float(t['amount']) for t in transactions if t['category__category_type'] == 'IN'],
            'expenses': [float(t['amount']) for t in transactions if t['category__category_type'] == 'EX']
        },
        'expenses': {
            'labels': [e['category__name'] for e in expenses],
            'data': [float(e['total']) for e in expenses]
        },
        'income': {
            'labels': [i['category__name'] for i in incomes],
            'data': [float(i['total']) for i in incomes]
        }
    })

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('transactions')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'tracker/edit_transaction.html', {'form': form})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transactions')
    return render(request, 'tracker/delete_transaction.html', {'transaction': transaction})

@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('categories')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'tracker/edit_category.html', {'form': form})

@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        return redirect('categories')
    return render(request, 'tracker/delete_category.html', {'category': category})

@login_required
def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('budgets')
    else:
        form = BudgetForm(instance=budget, user=request.user)
    return render(request, 'tracker/edit_budget.html', {'form': form})

@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        return redirect('budgets')
    return render(request, 'tracker/delete_budget.html', {'budget': budget})

@login_required
def edit_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            return redirect('goals')
    else:
        form = GoalForm(instance=goal)
    return render(request, 'tracker/edit_goal.html', {'form': form})

@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        return redirect('goals')
    return render(request, 'tracker/delete_goal.html', {'goal': goal})

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transactions')

def bills(request):
    bills = Bill.objects.filter(user=request.user).order_by('due_date')
    context = {
        'bills': bills,
        'overdue': bills.filter(is_paid=False, due_date__lt=timezone.now().date()),
        'due_soon': bills.filter(is_paid=False, due_date__range=[
            timezone.now().date(), 
            timezone.now().date() + timedelta(days=3)
        ])
    }
    return render(request, 'tracker/bills.html', context)

def mark_paid(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, user=request.user)
    bill.is_paid = True
    bill.save()
    
    if request.POST.get('create_transaction'):
        Transaction.objects.create(
            user=request.user,
            amount=-bill.amount,
            category=bill.category,
            date=timezone.now().date(),
            description=f"Payment for {bill.name}"
        )
    
    return redirect('bills')

@login_required
def edit_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, user=request.user)
    
    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, "Bill updated successfully!")
            return redirect('bill_list')
    else:
        form = BillForm(instance=bill)
    
    return render(request, 'tracker/edit_bill.html', {'form': form, 'bill': bill})

@login_required
def delete_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, user=request.user)
    
    if request.method == 'POST':
        bill.delete()
        messages.success(request, "Bill deleted successfully!")
        return redirect('bill_list')
    
    return render(request, 'tracker/delete_bill.html', {'bill': bill})

@login_required
def delete_bill_from_history(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, user=request.user)
    
    if request.method == 'POST':
        bill.delete()
        messages.success(request, "Bill deleted successfully!")
        return redirect('bill_history')
    
    return render(request, 'tracker/delete_bill_history.html', {'bill': bill})

def notifications(request):
    notifications = Notification.objects.filter(user=request.user)
    unread = notifications.filter(is_read=False)
    for notification in unread:
        notification.is_read = True
        notification.save()
    
    return render(request, 'tracker/notifications.html', 
                 {'notifications': notifications})

@login_required
def bill_list(request):
    bills = Bill.objects.filter(
        user=request.user,
        is_paid = False,
        recurring = False
    ).order_by('due_date')

    bills = Bill.objects.filter(user=request.user).order_by('due_date')
    return render(request, 'tracker/bill_list.html', {'bills': bills})

@login_required
def bill_history(request):
    all_bills = Bill.objects.filter(user=request.user).order_by('-due_date')
    return render(request, 'tracker/bill_history.html', {'bills': all_bills})

@login_required
def add_bill(request):
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.user = request.user
            bill.save()
            return redirect('bill_list')
    else:
        form = BillForm()
    return render(request, 'tracker/add_bill.html', {'form': form})

@login_required
def mark_bill_paid(request, bill_id):
    bill = Bill.objects.get(id=bill_id, user=request.user)
    bill.is_paid = True
    bill.save()
    
    if bill.recurring:
        new_due_date = calculate_next_due_date(bill.due_date, bill.recurring_frequency)
        Bill.objects.create(
            user=request.user,
            name=bill.name,
            amount=bill.amount,
            due_date=new_due_date,
            recurring=True,
            recurring_frequency=bill.recurring_frequency,
            is_paid=False 
        )
    
    return redirect('bill_list')

def calculate_next_due_date(current_date, frequency):
    if frequency == 'WEEKLY':
        return current_date + timedelta(weeks=1)
    elif frequency == 'MONTHLY':
        return current_date + relativedelta(months=1)
    elif frequency == 'YEARLY':
        return current_date + relativedelta(years=1)
    return current_date

@login_required
def notifications(request):
    if request.method == 'POST':
        pass
    
    check_budget_alerts(request.user)
    check_goal_alerts(request.user)
    check_bill_reminders(request.user)
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'tracker/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

logger = logging.getLogger(__name__)

@login_required
def clear_notifications(request):
    if request.method == 'POST':
        try:
            count = Notification.objects.filter(user=request.user).count()
            
            Notification.objects.filter(user=request.user).delete()
            
            messages.success(request, f"Successfully deleted {count} notifications")
        except Exception as e:
            messages.error(request, "Failed to delete notifications")
            logger.exception("Notification deletion failed")
    
    return redirect('notifications')

@login_required
def notification_settings(request):
    prefs = NotificationPreference.objects.get_or_create(user=request.user)[0]
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            return redirect('notifications')
    else:
        form = NotificationPreferenceForm(instance=prefs)
    
    return render(request, 'tracker/notification_settings.html', {'form': form})

def spending_patterns(request):
    patterns = detect_spending_patterns(request.user)
    return render(request, 'tracker/patterns.html', {'patterns': patterns})
