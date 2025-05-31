from django import forms
from .models import Transaction, Category, Budget, Goal, Bill, NotificationPreference, GoalDeposit
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class TransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
    
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type']

class BudgetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['category'].queryset = Category.objects.filter(user=self.user, category_type = 'EX')
            
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'current_amount', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }

class GoalDepositForm(forms.ModelForm):
    class Meta:
        model = GoalDeposit
        fields = ['amount', 'deposit_date', 'notes']
        widgets = {
            'deposit_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={
                'min': '0.01',
                'step': '0.01',
                'max': ''  
            })
        }

    def __init__(self, *args, **kwargs):
        self.goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
        
        if self.goal:
            remaining = self.goal.target_amount - self.goal.current_amount
            self.fields['amount'].widget.attrs['max'] = f"{remaining:.2f}"

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not self.goal:
            return amount
            
        if amount <= 0:
            raise forms.ValidationError("Deposit amount must be positive")
            
        remaining = self.goal.target_amount - self.goal.current_amount
        if amount > remaining:
            raise forms.ValidationError(
                f"Amount exceeds remaining goal need by ₹{(amount - remaining):.2f}. "
                f"Maximum deposit: ₹{remaining:.2f}"
            )
        return amount

    def clean(self):
        cleaned_data = super().clean()
        if self.goal and not self.goal.can_add_deposit():
            raise forms.ValidationError("Cannot add deposit to completed goal")
        return cleaned_data


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['name', 'amount', 'due_date', 'recurring', 'recurring_frequency']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        widgets = {
            'user': forms.HiddenInput()
        }