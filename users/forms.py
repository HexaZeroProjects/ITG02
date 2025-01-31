from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'address')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address']
            )
        return user

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email", max_length=254)

class CustomSetPasswordForm(SetPasswordForm):
    pass


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']