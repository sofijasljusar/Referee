from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import PayingQueueGroup

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


class EditGroupForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=None,
        label="Group owner",
        widget=forms.Select(attrs={
            "class": "input-box",
        }),
        empty_label=None
    )

    class Meta:
        model = PayingQueueGroup
        fields = ["emoji", "name", "owner"]
        help_texts = {
            "emoji": None,
            "name": None,
            "owner": None,
        }
        widgets = {
            "emoji": forms.TextInput(attrs={
                "class": "input-box",
                "placeholder": "Emoji",
            }),
            "name": forms.TextInput(attrs={
                "class": "input-box",
                "placeholder": "Name",
            }),
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        if group:
            member_users = User.objects.filter(pk__in=group.members.values_list('user_id', flat=True))
            self.fields["owner"].queryset = member_users


