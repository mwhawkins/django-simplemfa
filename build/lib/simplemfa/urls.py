try:
    from django.urls import path as url
except:
     from django.conf.urls import  url
from simplemfa.views import MFALoginView, MFARequestView

urlpatterns = [
    url(r'mfa_auth/', MFALoginView.as_view(), name="mfa-login"),
    url(r'mfa_request/', MFARequestView.as_view(), name="mfa-request"),
    ]

app_name = "simplemfa"