from django.shortcuts import render, redirect, reverse
from django.views.generic import TemplateView, View
from simplemfa.forms import MFAAuth
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from simplemfa.models import AuthCode
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from simplemfa.helpers import send_mfa_code, get_user_mfa_mode, get_user_phone, parse_phone, set_cookie, get_cookie_expiration, \
    sanitize_email, sanitize_phone, template_fallback, build_mfa_request_url


class MFALoginView(LoginRequiredMixin, TemplateView):
    template_name = "simplemfa/auth.html"
    form_class = MFAAuth

    def get(self, request, *args, **kwargs):
        next_url = request.GET.get("next", None)
        context = self.get_context_data()
        initial = {"user_id": request.user.id, "next": next_url}
        context['form'] = self.form_class(initial=initial)
        context['next'] = next_url
        context['mfa_code_sent'] = request.session.get("_simplemfa_code_sent", False)
        context['default_mode'] = get_user_mfa_mode(request)
        context['trusted_device_days'] = get_cookie_expiration()
        context['request_url'] = build_mfa_request_url(request)

        email = request.user.email
        context['sanitized_email'] = sanitize_email(email)

        phone = sanitize_phone(get_user_phone(request))
        context['sanitized_phone'] = phone

        return render(request, self.get_template_names(), context)

    def post(self, request, *args, **kwargs):
        form_data = self.form_class(request.POST)
        if form_data.authenticate():
            next_url = form_data.cleaned_data.get("next", request.GET.get("next", None))
            request.session['_simplemfa_authenticated'] = True
            if next_url is not None:
                response = redirect(next_url, request)
            else:
                redirect_view = settings.LOGIN_REDIRECT_URL if hasattr(settings, 'LOGIN_REDIRECT_URL') else "index"
                response = redirect(reverse(redirect_view), request)
            if form_data.cleaned_data.get("trusted_device").upper() == "TRUE":
                set_cookie(response, "_simplemfa_trusted_device", timezone.now())
            return response
        else:
            request.session['_simplemfa_authenticated'] = False
            context = self.get_context_data()
            context['mfa_code_sent'] = request.session.get("_simplemfa_code_sent", False)
            context['userid'] = request.user.id
            context['next'] = form_data.cleaned_data.get("next", request.GET.get("next", None))
            context['form'] = form_data
            context['default_mode'] = get_user_mfa_mode(request)
            context['trusted_device_days'] = get_cookie_expiration()
            context['request_url'] = build_mfa_request_url(request)

            email = request.user.email
            context['sanitized_email'] = sanitize_email(email)

            phone = sanitize_phone(get_user_phone(request))
            context['sanitized_phone'] = phone

            messages.add_message(request, messages.ERROR, "We were unable to authenticate the code provided")
            return render(request, self.get_template_names(), context)

    def get_template_names(self):
        return template_fallback([self.template_name, "simplemfa/auth.html", "simplemfa/mfa_auth.html"])


"""
An AJAX view to request a new MFA code
INPUT: user_id, request, mode via POST
OUTPUT: JSON response (result)
"""


class MFARequestView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        reset = request.GET.get("reset", None)
        response = {}
        if reset is not None and reset.upper() == "TRUE":
            AuthCode.delete_all_codes_for_user(request.user.id)
            request.session['_simplemfa_code_sent'] = False
        else:
            # variables
            mode = request.GET.get("sent_via", get_user_mfa_mode(request))

            try:
                # delete old codes (if any) for this user
                AuthCode.delete_all_codes_for_user(request.user.id)

                # create the new MFA auth object
                code = AuthCode.create_code_for_user(request.user.id, sent_via=mode)

                # send email or text to the user, depending on selected mode
                send_mfa_code(request, code, mode=mode)

                # for testing in development
                if settings.DEBUG:
                    print("MFA CODE: " + code)

                if code is not None:
                    messages.add_message(request, messages.SUCCESS, "A new code has been sent.")
                    request.session['_simplemfa_code_sent'] = True
                    # the result is good, code is created and sent
                    response['code_created'] = True
            except:
                # something went wrong, let them know no new code was issued
                AuthCode.delete_all_codes_for_user(request.user.id)
                response['code_created'] = False
                request.session['_simplemfa_code_sent'] = False
                messages.add_message(request, messages.ERROR,
                                     "Something went wrong. A code was not created. Try again.")

        if request.is_ajax():
            return JsonResponse(response)
        else:
            next_url = request.GET.get("next", None)
            url = reverse("mfa:mfa-login")
            if next_url is not None:
                url += f"?next={next_url}"
            return redirect(url, request)

    def post(self, request, *args, **kwargs):
        # request must be AJAX
        if not request.is_ajax():
            raise HttpResponseBadRequest

        # POST variables
        mode = request.POST.get("sent_via", request.GET.get("sent_via", get_user_mfa_mode(request)))
        user_id = request.POST.get("user_id", None)

        # verify the user is who they say they are
        # here we check the request data against a variable set in the POST data
        if user_id is None or request.user.id != user_id:
            raise PermissionDenied

        # start doing some work
        response = {}

        try:
            # delete any existing codes before issuing a new one
            AuthCode.delete_all_codes_for_user(request.user.id)

            # create the new MFA auth object
            code = AuthCode.create_code_for_user(request.user.id, sent_via=mode)

            # send code to the user, depending on selected mode
            send_mfa_code(request, code, mode=mode)

            # for testing in development
            if settings.DEBUG:
                print("MFA CODE: " + code)

            if code is not None:
                request.session['_simplemfa_code_sent'] = True
                # the result is good
                response['code_created'] = True
                response['message'] = "A new code was created and has been sent."

        except:
            # something went wrong, let them know no new code was issued or sent
            AuthCode.delete_all_codes_for_user(request.user.id)
            response['code_created'] = False
            request.session['_simplemfa_code_sent'] = False
            response['message'] = "Something went wrong and we were unable to generate a new code. Try again."

        return JsonResponse(response)
