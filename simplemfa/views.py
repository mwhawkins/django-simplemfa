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
        next_url = request.GET.get("next", None)
        context = self.get_context_data()
        initial = {"user_id": request.user.id, "next": next_url}
        context['form'] = self.form_class(initial=initial)
        context['next'] = next_url

        # if this session key is not set, we send a code - this prevents new codes being generated on page refresh
        if not request.session.get("_simplemfa_code_sent", False):

            try:
                # delete old codes (if any) for this user
                AuthCode.delete_all_codes_for_user(request.user.id)

                # the selected mode for the user to get the code, eventually get this from a profile setting
                mode = "EMAIL"

                # create the new MFA auth object
                code = AuthCode.create_code_for_user(request.user.id, sent_via=mode)

                # if code is good, process it
                if code is not None:
                    request.session['_simplemfa_code_sent'] = True

                    # eventually replace this with send_mfa_code(request, code, mode) where mode is how it is to be sent
                    send_mfa_code(request, code, mode)

                    # for testing in development
                    if settings.DEBUG:
                        print("MFA CODE: " + code)

                else:
                    raise Exception

            except Exception:
                AuthCode.delete_all_codes_for_user(request.user.id)
                request.session['_simplemfa_code_sent'] = False
                messages.add_message(request, messages.ERROR,
                                     "Something went wrong. A code was not created. Try again.")

        return render(request, self.get_template_names(), context)

    def post(self, request, *args, **kwargs):
        form_data = self.form_class(request.POST)
        next_url = request.GET.get("next", None)

        # the form authenticates the code provided, returns True if it checks out
        if form_data.authenticate():

            # replace the original next_url with data from the form (if any)
            next_url = form_data.cleaned_data.get("next", request.GET.get("next", None))

            # this authenticates the user, letting the middleware know they have passed verification
            request.session['_simplemfa_authenticated'] = True

            if next_url is not None:
                return redirect(next_url, request)
            else:
                # where do we go after being authenticated if not set in next_url?
                redirect_view = settings.LOGIN_REDIRECT_URL if hasattr(settings, 'LOGIN_REDIRECT_URL') else "home"
                return redirect(reverse(redirect_view), request)
        else:
            context = {"form": form_data, "form_errors": form_data.errors, "next": next_url}
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
        # variables
        mode = request.GET.get("sent_via", "EMAIL")

        # start doing some work
        response = {}
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

            # the result is good, code is created and sent
            response['code_created'] = True

        except:
            # something went wrong, let them know no new code was issued
            AuthCode.delete_all_codes_for_user(request.user.id)
            response['code_created'] = False
            messages.add_message(request, messages.ERROR, "Something went wrong. A code was not created. Try again.")

        if request.is_ajax():
            return JsonResponse(response)
        else:
            messages.add_message(request, messages.SUCCESS, "A new code has been sent.")
            return redirect(reverse("simplemfa:mfa-login"), request)

    def post(self, request, *args, **kwargs):
        # request must be AJAX
        if not request.is_ajax():
            raise HttpResponseBadRequest

        # POST variables
        mode = request.POST.get("sent_via", request.GET.get("sent_via", "EMAIL"))
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
            send_mfa_code(request, code)

            # for testing in development
            if settings.DEBUG:
                print("MFA CODE: " + code)

            # the result is good
            response['code_created'] = True
            response['message'] = "A new code was created and has been sent."

        except:
            # something went wrong, let them know no new code was issued or sent
            AuthCode.delete_all_codes_for_user(request.user.id)
            response['code_created'] = False
            response['message'] = "Something went wrong and we were unable to generate a new code. Try again."

        return JsonResponse(response)
