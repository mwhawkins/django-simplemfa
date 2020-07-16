from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect, reverse


class ValidateMFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(view_func, 'login_exempt', False):
            return None

        if 'mfa' in request.resolver_match.namespaces:
            return None

        if request.path in [reverse("simplemfa:mfa-login"), reverse("simplemfa:mfa-request"), reverse('login'), reverse('logout')]:
            return None

        if request.user.is_authenticated and settings.REQUIRE_MFA and not request.session.get("_simple_mfa_authenticated", False):
            mfa_url = reverse("simplemfa:mfa-login")
            url = f"{mfa_url}?next={request.path}"
            return redirect(url, request)
        else:
            return None
