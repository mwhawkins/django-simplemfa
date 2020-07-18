from django.conf import settings
from django.shortcuts import redirect, reverse


class ValidateMFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        mfa_required = settings.REQUIRE_MFA if hasattr(settings, "REQUIRE_MFA") else False
        mfa_authenticated = request.session.get("_simplemfa_authenticated", False)

        if getattr(view_func, 'login_exempt', False):
            return None

        if 'simplemfa' in request.resolver_match.namespaces:
            return None

        if request.path in [reverse("simplemfa:mfa-login"), reverse("simplemfa:mfa-request")]:
            return None

        if request.user.is_authenticated and mfa_required and not mfa_authenticated:
            url = f"{reverse('simplemfa:mfa-login')}?next={request.path}"
            return redirect(url, request)

        return None
