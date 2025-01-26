from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User  # Изменено на стандартную модель User
        fields = ('username', 'email')  # Убраны поля phone и address, так как их больше нет

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email", max_length=254)

class CustomSetPasswordForm(SetPasswordForm):
    pass
