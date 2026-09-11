from django import forms
from django.core.validators import RegexValidator
from allauth.account.forms import (
    SignupForm, LoginForm, ResetPasswordForm, 
    ResetPasswordKeyForm, ChangePasswordForm, 
    SetPasswordForm, AddEmailForm, ConfirmEmailVerificationCodeForm
)
# Import Unfold Widgets
from unfold.widgets import (
    UnfoldAdminTextInputWidget, 
    UnfoldAdminEmailInputWidget,
)
from django.forms.widgets import PasswordInput as UnfoldAdminPasswordInputWidget

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div

# --- Custom Widget Base Classes ---

class Input():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['class'] = 'input'

class TextInput(Input, UnfoldAdminTextInputWidget):
    pass
        
class EmailInput(Input, UnfoldAdminEmailInputWidget):
    pass

class PasswordInput(Input, UnfoldAdminPasswordInputWidget):
    pass

phone_number_validator = RegexValidator(
    regex=r'^(?:\+88|88)?01[3-9]\d{8}$',
    message="Enter a valid Bangladeshi phone number."
)

# --- Forms Implementation ---

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True, widget=TextInput())
    last_name = forms.CharField(max_length=30, required=True, widget=TextInput())
    phone = forms.CharField(
        validators=[phone_number_validator], 
        max_length=15, 
        required=True, 
        widget=TextInput(attrs={"placeholder": "01x...", "type": "text"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Column('first_name'),
                Column('last_name'),
                css_class="grid grid-cols-2 gap-4"
            ),
            'email',
            'phone',
            'password1',
            'password2',
            Submit('submit', 'Signup', css_class='btn btn-primary w-full')
        )
        self.fields['email'].widget = EmailInput()
        self.fields['password1'].widget = PasswordInput()
        if 'password2' in self.fields:
            self.fields['password2'].widget = PasswordInput()

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone'] 
        user.save()
        return user


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'login',
            'password',
            Div('remember', css_class="flex justify-start"),
            Submit('submit', 'Login', css_class='btn btn-primary w-full')
        )
        self.fields['login'].widget = TextInput()
        self.fields['password'].widget = PasswordInput()


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'email',
            Submit('submit', 'Reset Password', css_class='btn btn-primary w-full')
        )
        self.fields['email'].widget = EmailInput()


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'password1',
            'password2',
            Submit('submit', 'Set New Password', css_class='btn btn-primary w-full')
        )
        self.fields['password1'].widget = PasswordInput()
        self.fields['password2'].widget = PasswordInput()


class CustomChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'oldpassword',
            'password1',
            'password2',
            Submit('submit', 'Change Password', css_class='btn btn-primary w-full')
        )
        self.fields['oldpassword'].widget = PasswordInput()
        self.fields['password1'].widget = PasswordInput()
        self.fields['password2'].widget = PasswordInput()


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'password1',
            'password2',
            Submit('submit', 'Set Password', css_class='btn btn-primary w-full')
        )
        self.fields['password1'].widget = PasswordInput()
        self.fields['password2'].widget = PasswordInput()


class CustomAddEmailForm(AddEmailForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'email',
            Submit('submit', 'Add Email', css_class='btn btn-primary w-full')
        )
        self.fields['email'].widget = EmailInput()


class CustomConfirmEmailVerificationCodeForm(ConfirmEmailVerificationCodeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'code',
            Submit('submit', 'Confirm', css_class='btn btn-primary w-full')
        )
        self.fields['code'].widget = TextInput()