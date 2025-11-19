from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "mt-3 input-box", "placeholder": "Username"}))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={"class": "mt-3 input-box", "placeholder": "Email"}))
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "mt-3 input-box", "placeholder": "Password"}))
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "mt-3 input-box", "placeholder": "Confirm Password"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class LogInForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "mt-3 input-box", "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "mt-3 input-box", "placeholder": "Password"}))


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]
        help_texts = {
            "username": None,
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "input-box",
                "placeholder": "Username"
            })
        }


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "mt-3 input-box",
                   "placeholder": "Email"}
        )
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "mt-3 input-box",
                   "placeholder": "New Password"}
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "mt-3 input-box",
                   "placeholder": "Confirm Password"}
        )
    )
