from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from simplemfa.models import AuthCode
from django.utils import timezone


class MFAAuth(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    auth_code = forms.CharField(required=True, widget=forms.TextInput())
    next = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        auth_code = cleaned_data.get("auth_code", None)
        user_id = cleaned_data.get("user_id", None)
        user = None

        try:
            User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            self.add_error("user_id", "Your account was not found.")
        else:
            user = User.objects.get(id=user_id, is_active=True)

        try:
            now = timezone.now()
            AuthCode.objects.get(user=user)
        except [AuthCode.DoesNotExist, AuthCode.MultipleObjectsReturned]:
            self.add_error("auth_code", "Your code was not found. Please request a new one.")
        else:
            auth = AuthCode.objects.get(user=user)
            if auth.expires <= now:
                self.add_error("auth_code", "Your code has expired. Please request a new one.")
                auth.delete()
            elif not check_password(auth_code, auth.code):
                self.add_error("auth_code", "An invalid code was provided. Please request a new one.")

    def authenticate(self):
        if self.is_valid():
            try:
                auths = AuthCode.objects.filter(user_id=self.cleaned_data.get("user_id")).all()
                for auth in auths:
                    auth.delete()
                return True
            except [AuthCode.DoesNotExist, AuthCode.MultipleObjectsReturned]:
                self.add_error("auth_code", "We are unable to authenticate the code provided. "
                                            "Request a new one and try again.")
                return False
        return False
