from django import template
from django.core.mail import send_mail
from django.template.loader import get_template
from django.conf import settings
from django.shortcuts import reverse
from twilio.twiml.voice_response import VoiceResponse, Say
from twilio.rest import Client


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


def get_message_context(request, code):
    context = {
        'username': request.user.username,
        'request': request,
        'app_name': settings.APP_NAME if hasattr(settings, "APP_NAME") else f"{request.META.get('HTTP_HOST')}",
        'code': code,
        'url': request.build_absolute_uri(location=reverse('mfa:mfa-login'))
    }
    return context


def get_twilio_client():
    if hasattr(settings, "TWILIO_ACCOUNT_SID") and hasattr(settings, "TWILIO_AUTH_TOKEN") and \
            hasattr(settings, "TWILIO_NUMBER"):
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return None


def send_mfa_code_email(request, code):
    html_template = get_template('simplemfa/auth_email.html')
    context = get_message_context(request, code)
    msg = html_template.render(context)
    subject = f"{context['app_name']} Verification Code"
    default_from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "user@localhost"
    send_mail(subject, msg, default_from_email, [request.user.email], fail_silently=False)


def send_mfa_code_text(request, code):
    template = get_template('simplemfa/auth_text.html')
    context = get_message_context(request, code)
    msg = str(template.render(context))
    client = get_twilio_client()
    if hasattr(settings, "MFA_USER_PHONE_ATTRIBUTE") and client is not None:
        phone_object_string = f"request.user.{settings.MFA_USER_PHONE_ATTRIBUTE}"
        try:
            recipient = eval(phone_object_string)
            if recipient is not None:
                client.messages.create(to=recipient,
                                       from_=settings.TWILIO_NUMBER,
                                       body=msg)
                return True
        except:
            return False
    return False


def send_mfa_code_phone(request, code):
    template = get_template('simplemfa/auth_voice.html')
    context = get_message_context(request, code)
    msg = str(template.render(context)) + ","
    client = get_twilio_client()
    if hasattr(settings, "MFA_USER_PHONE_ATTRIBUTE") and client is not None:
        phone_object_string = f"request.user.{settings.MFA_USER_PHONE_ATTRIBUTE}"
        try:
            recipient = eval(phone_object_string)
            if recipient is not None:
                response = VoiceResponse()
                say = Say()
                say.p(f",,,{msg},,,")
                for char in code:
                    say.say_as(f",,,,,{char},,,,,", interpret_as="spell-out")
                say.p(f",,,Again, {msg},,,")
                for char in code:
                    say.say_as(f",,,,,{char},,,,,", interpret_as="spell-out")
                say.p(f",,,Again, {msg},,,")
                for char in code:
                    say.say_as(f",,,,,{char},,,,,", interpret_as="spell-out")
                say.p(",,,Goodbye!")
                response.append(say)
                print(response.to_xml())
                client.calls.create(to=recipient,
                                    from_=settings.TWILIO_NUMBER,
                                    twiml=str(response.to_xml()))
                return True
        except:
            return False
    return False


def get_user_mfa_mode(request):
    if hasattr(settings, "MFA_USER_MODE_ATTRIBUTE"):
        mode_attr_string = f"request.user.{settings.MFA_USER_MODE_ATTRIBUTE}"
        return eval(mode_attr_string) if eval(mode_attr_string) is not None else "EMAIL"
    else:
        return "EMAIL"


def send_mfa_code(request, code, mode=None):
    if mode is None:
        mode = get_user_mfa_mode(request)

    if mode == "TEXT":
        result = send_mfa_code_text(request, code)
        if not result:
            return send_mfa_code_email(request, code)
    elif mode == "PHONE":
        result = send_mfa_code_phone(request, code)
        if not result:
            return send_mfa_code_email(request, code)
    else:
        return send_mfa_code_email(request, code)

