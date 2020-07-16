from django import template
from django.core.mail import send_mail
from django.template.loader import get_template
from django.conf import settings
from django.urls import resolve
import sys
from django.shortcuts import reverse


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def template_exists(value):
    try:
        template.loader.get_template(value)
        return True
    except template.TemplateDoesNotExist:
        return False


def template_fallback(values):
    for value in values:
        if template_exists(value):
            return value
    raise template.TemplateDoesNotExist


def send_mfa_code_email(request, code):
    html_template = get_template('simplemfa/auth_email.html')
    context = {
        'username': request.user.username,
        'request': request,
        'app_name': settings.APP_NAME if hasattr(settings, "APP_NAME") else f"the application at "
                                                                            f"{request.build_absolute_uri(location=reverse('mfa:mfa-login'))}",
        'code': code,
        'url': request.build_absolute_uri(location=reverse('mfa:mfa-login'))
    }
    msg = html_template.render(context)
    subject = f"{context['app_name']} Verification Code"
    default_from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "user@localhost"
    send_mail(subject, msg, default_from_email, [request.user.email], fail_silently=False)


def send_mfa_code(request, code):
    # add more options here later
    return send_mfa_code_email(request, code)
