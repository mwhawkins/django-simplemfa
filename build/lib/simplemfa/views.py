from django.shortcuts import render, redirect, reverse
from django.views.generic import TemplateView, View
from simplemfa.forms import MFAAuth
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from simplemfa.models import AuthCode
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.http import HttpResponse, JsonResponse
from simplemfa.helpers import template_fallback
from django.contrib import messages
from simplemfa.helpers import send_mfa_code


class MFALoginView(LoginRequiredMixin, TemplateView):
    template_name = "simplemfa/auth.html"
    form_class = MFAAuth

    def get(self, request, *args, **kwargs):
        next = request.GET.get("next", None)
        context = self.get_context_data()
        initial = {"user_id": request.user.id, "next": next}
        context['form'] = self.form_class(initial=initial)
        context['next'] = next

        # delete old codes (if any) for this user
        AuthCode.delete_all_codes_for_user(request.user.id)

        # create the new MFA auth object
        new_auth = AuthCode.objects.create(user=request.user, sent_via="EMAIL")

        # create_code() return a plain-text code
        # a hashed version is stored in the database - this is the ONLY time a plain text code will be issued
        code = new_auth.create_code()

        # send email or text to the user, depending on selected mode (only email right now)
        send_mfa_code(request, code)
        if settings.DEBUG:
            print("MFA CODE: " + code)

        return render(request, self.get_template_names(), context)

    def post(self, request, *args, **kwargs):
        form_data = self.form_class(request.POST)
        if form_data.authenticate():
            next = form_data.cleaned_data.get("next", request.GET.get("next", None))
            request.session['_simple_mfa_authenticated'] = True
            if next is not None:
                return redirect(next, request)
            else:
                redirect_view = settings.LOGIN_REDIRECT_URL if hasattr(settings, 'LOGIN_REDIRECT_URL') else "index"
                return redirect(reverse(redirect_view), request)
        else:
            context = {"form": form_data, "form_errors": form_data.errors}
            return render(request, self.get_template_names(), context)

    def get_template_names(self):
        return template_fallback([self.template_name, "simplemfa/mfa_auth.html", "simplemfa/mfa.html"])


"""
An AJAX view to request a new MFA code
INPUT: user_id, request, mode via POST
OUTPUT: JSON response (result)
"""

class MFARequestView(LoginRequiredMixin, View):

    def delete_codes(self, request):
        if AuthCode.objects.filter(user_id=request.user.id).exists():
            for ac in AuthCode.objects.filter(user_id=request.user.id).all():
                ac.delete()
        return True

    def get(self, request, *args, **kwargs):
        # variables
        mode = "EMAIL"

        # delete any existing codes before issuing a new one
        self.delete_codes(request)

        # start doing some work
        response = {}
        try:
            # delete old codes (if any) for this user
            AuthCode.delete_all_codes_for_user(request.user.id)

            # create the new MFA auth object
            new_auth = AuthCode.objects.create(user=request.user, sent_via=mode)

            # create_code() return a plain-text code
            # a hashed version is stored in the database - this is the ONLY time a plain text code will be issued
            code = new_auth.create_code()

            # send email or text to the user, depending on selected mode
            send_mfa_code(request, code)
            if settings.DEBUG:
                print("MFA CODE: " + code)
            # the result is good
            response['code_created'] = True
        except:
            # something went wrong, let them know no new code was issued
            response['code_created'] = False

        if request.is_ajax():
            return JsonResponse(response)
        else:
            messages.add_message(request, messages.SUCCESS, "A new code has been sent.")
            return redirect(reverse("mfa:mfa-login"), request)

    def post(self, request, *args, **kwargs):
        # request must be AJAX
        if not request.is_ajax():
            raise HttpResponseBadRequest

        # POST variables
        mode = request.POST.get("mode", "EMAIL")
        user_id = request.POST.get("user_id", None)

        # verify the user is who they say they are
        # here we check the request data against a variable set in the POST data
        if request.user.id != user_id:
            raise PermissionDenied

        # delete any existing codes before issuing a new one
        self.delete_codes(request)

        # start doing some work
        response = {}
        try:
            # delete old codes (if any) for this user
            AuthCode.delete_all_codes_for_user(request.user.id)

            # create the new MFA auth object
            new_auth = AuthCode.objects.create(user=request.user, sent_via=mode)

            # create_code() return a plain-text code
            # a hashed version is stored in the database - this is the ONLY time a plain text code will be issued
            code = new_auth.create_code()

            # send email or text to the user, depending on selected mode
            send_mfa_code(request, code)
            if settings.DEBUG:
                print("MFA CODE: " + code)
            # the result is good
            response['code_created'] = True
        except:
            # something went wrong, let them know no new code was issued
            response['code_created'] = False

        return JsonResponse(response)
