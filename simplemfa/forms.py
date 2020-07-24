from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from simplemfa.models import AuthCode
from django.utils import timezone
from simplemfa.constants import MessageConstants


class MFAAuth(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    auth_code = forms.CharField(required=True, widget=forms.TextInput())
    next = forms.CharField(widget=forms.HiddenInput())
    trusted_device = forms.CharField(widget=forms.CheckboxInput())

    def clean(self):
        cleaned_data = super().clean()
        auth_code = cleaned_data.get("auth_code", None)
        user_id = cleaned_data.get("user_id", None)
        user = None

        try:
            User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            self.add_error("user_id", MessageConstants.ACCOUNT_NOT_FOUND)
        else:
            user = User.objects.get(id=user_id, is_active=True)

        try:
            now = timezone.now()
            auth = AuthCode.objects.get(user=user)
        except [AuthCode.DoesNotExist, AuthCode.MultipleObjectsReturned]:
            self.add_error("auth_code", MessageConstants.MFA_CODE_NOT_FOUND)
        else:
            if auth.expires <= now:
                self.add_error("auth_code", MessageConstants.MFA_CODE_EXPIRED)
                auth.delete()
            elif not check_password(auth_code.upper(), auth.code):
                self.add_error("auth_code", MessageConstants.MFA_CODE_NOT_AUTHENTICATED)

    def authenticate(self):
        if self.is_valid():
            try:
                auths = AuthCode.objects.filter(user_id=self.cleaned_data.get("user_id")).all()
                for auth in auths:
                    auth.delete()
                return True
            except:
                self.add_error("auth_code", MessageConstants.MFA_CODE_NOT_AUTHENTICATED)
                return False
        return False
