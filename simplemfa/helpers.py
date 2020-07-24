from django import template
from django.core.mail import send_mail
from django.template.loader import get_template
from django.conf import settings
from django.shortcuts import reverse
from twilio.twiml.voice_response import VoiceResponse, Say
from twilio.rest import Client
from django.utils import timezone


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
    default_from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else \
        f"no-reply@{request.META.get('HTTP_HOST')}"
    return send_mail(subject, msg, default_from_email, [request.user.email], fail_silently=False)


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
                recipient = parse_phone(recipient)
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
            code_list = [str(i) for i in str(code)]
            if recipient is not None:
                recipient = parse_phone(recipient)
                response = VoiceResponse()
                say = Say()
                say.p(f",,,,,,,,,{msg},,,,,,,,,...")
                for char in code_list:
                    say.say_as(f",,,,,,,,...{str(char)},,,,,,,,...", interpret_as="spell-out")
                say.p(f",,,,,,,,,...Again, {msg},,,,,,,,,")
                for char in code_list:
                    say.say_as(f",,,,,,,,...{str(char)},,,,,,,,...", interpret_as="spell-out")
                say.p(",,,,,,Goodbye!")
                response.append(say)
                print(response.to_xml())
                client.calls.create(to=recipient,
                                    from_=settings.TWILIO_NUMBER,
                                    twiml=str(response.to_xml()))
                return True
        except:
            return False
    return False


def parse_phone(phone):
    result = phone
    if "+" not in result:
        result = "+" + result
    return result.replace("-","").replace("(","").replace(")","").replace(" ","")


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
        if not send_mfa_code_text(request, code):
            return send_mfa_code_email(request, code)
        else:
            return True
    elif mode == "PHONE":
        if not send_mfa_code_phone(request, code):
            return send_mfa_code_email(request, code)
        else:
            return True
    else:
        return send_mfa_code_email(request, code)


def get_user_phone(request):
    if hasattr(settings, "MFA_USER_PHONE_ATTRIBUTE"):
        mode_attr_string = f"request.user.{settings.MFA_USER_PHONE_ATTRIBUTE}"
        return eval(mode_attr_string) if eval(mode_attr_string) is not None else None
    return None


def get_cookie_expiration():
    if hasattr(settings, "MFA_COOKIE_EXPIRATION_DAYS"):
        return settings.MFA_COOKIE_EXPIRATION_DAYS
    else:
        return 7


def set_cookie(response, key, value, days_expire=get_cookie_expiration()):
    if days_expire is None:
        max_age = 7 * 24 * 60 * 60  # seven days
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = timezone.datetime.strftime(timezone.now() + timezone.timedelta(seconds=max_age),
                                         "%a, %d-%b-%Y %H:%M:%S UTC")
    response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)


def sanitize_email(email):
    if email is not None:
        email_parts = email.split("@")
        domain_parts = email_parts[1].split('.')

        email_result = ""
        for i in range(len(email_parts[0])):
            if i == len(email_parts[0]) - 1 or i == 0:
                email_result += email_parts[0][i]
            else:
                email_result += "*"
        email = email_result

        domain_result = ""
        for i in range(len(domain_parts[0])):
            if i == len(domain_parts[0]) - 1 or i == 0:
                domain_result += domain_parts[0][i]
            else:
                domain_result += "*"
        domain = f"{domain_result}.{domain_parts[1]}"

        return f"{email}@{domain}"
    return None


def sanitize_phone(phone):
    if phone is not None:
        phone = parse_phone(phone).replace("+", "")
        phone_result = ""
        for i in range(len(phone)):
            if i < len(phone) - 4:
                phone_result += "*"
            else:
                phone_result += phone[i]
        return phone_result
    return None


def build_mfa_request_url(request):
    next_url = request.GET.get("next", None)
    request_url = reverse("simplemfa:mfa-request")
    request_url += "?reset=true"
    if next_url is not None:
        request_url += f"&next={next_url}"
    return request_url
