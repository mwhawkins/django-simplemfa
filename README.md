# django-simplemfa
An implementation of basic Multi-Factor Authentication (MFA) functionality for Django applications (phone call, text message, and email).

[Now available on PyPI](https://pypi.org/project/django-simplemfa/) (`pip install django-simplemfa`)

# Overview
The intent of this project is to:
1. Provide basic yet effective MFA functionality for new and existing Django applications.
2. Limit external (outside Django) dependencies wherever feasible.
3. Simplify the setup and integration of MFA functionality in Django applications.
4. Limit the amount of alteration required in existing codebases to integrate basic MFA functionality.
5. Provide options to integrate more advanced or customized MFA functionality if desired.

At this time only email, phone call, and text message MFA options are supported. Future integrations (such as MS/Google Authenticator apps, OTP keys, WebAuthn, etc.) are possible.

## Why It Exists
Upon evaluating various other Django MFA applications, most appeared to be one or more of the following:
1. Their codebases were deprecated or unsupported.
2. They often required a substantial amount of very specific dependencies in order to achieve even basic functionality.
3. They often required substantial changes to existing applications to function and integrate properly.

## Basic Requirements
- Django >= version 3.0
- Django-Twilio (if using phone and/or text message MFA)

Twilio is the current integration for phone and text message MFA, but more are planned.
Email MFA leverages the built-in Django email utilities.

# Setup and Use
Download or clone the `simplemfa` package here or install from PyPi with `pip install django-simplemfa`.

**In your `templates` directory, create a new directory called 'simplemfa' and in it place or create the following templates:**
- `simplemfa/mfa_email.html` (the MFA email message template)
- `simplemfa/mfa_text.html` (the MFA text message template)
- `simplemfa/mfa_voice.html` (plain text file with the message you want to send via phone call)
- `simplemfa/auth.html` (the MFA login screen template)

Examples are provided in the package's `templates` directory (`simplemfa/templates`).

**In your `urls.py` add:**
`path('mfa/', include('simplemfa.urls', namespace="simplemfa"))`

Make sure to include the namespace as above.

**In your `settings.py`:**

Required Settings:
- Required: `REQUIRE_MFA = True` (global setting which activates MFA for all users)
- Required: `DEFAULT_FROM_EMAIL = "myemail@provider.com"` (the email address you want MFA messages to come from)
- Required: ```INSTALLED_APPS = [
                                  ...
                                  'simplemfa'
                              ]```

- Required:  ```MIDDLEWARE = [
                                  ...
                            'simplemfa.middleware.ValidateMFAMiddleware'
                            ]```
                            
If using Twilio (text and voice):
- Required: `TWILIO_AUTH_TOKEN` (your Twilio Auth Token)
- Required: `TWILIO_ACCOUNT_SID` (your Twilio account SID)
- Required: `TWILIO_NUMBER` (your Twilio phone number you want MFA codes sent from)
- Required: `MFA_USER_PHONE_ATTRIBUTE` (the attribute of `request.user` that has the phone number for the user in the format `+12345678900`, e.g. `profile.phone` resolves to `request.user.profile.phone`)
- Required: `MFA_USER_MODE_ATTRIBUTE` (the attribute of `request.user` that has the user's default way of receiving the MFA code, e.g. `profile.mfa_mode` resolves to `request.user.profile.mfa_mode` which must be one of the choices from `simplemfa.models.AUTH_CODE_DELIVERY_CHOICES` - currently "EMAIL", "TEXT", and "PHONE")

Optional Settings:
- Optional: `APP_NAME = "My App Name"` (application name which is provided in the messages to the user)
- Optional: `LOGIN_REDIRECT_URL = 'my_view_name'` (the default view users are sent to after they authenticate)
- Optional: `MFA_CODE_LENGTH` (default is 6)
- Optional: `MFA_CODE_EXPIRATION` (default is 900 seconds (15 minutes))
- Optional: `MFA_CODE_DELIVERY_DEFAULT` (default is "EMAIL")

If using Twilio (for phone call or text message), you will need to install and set up [djang-twilio](https://django-twilio.readthedocs.io/en/latest/) according to the instructions for that package.

For email, ensure that your [email is configured properly](https://docs.djangoproject.com/en/3.0/topics/email/) in your Django settings. 

Once those items are complete, run `makemigrations` then `migrate` for your project. 

Run your project. It should allow you to access all public (login exempt) pages. After you log in, however, it will automatically redirect you to the MFA verification page where you will request and then enter an MFA code. If the code passes, you will be allowed to proceed as any normal authenticated user would in your application.

That's it!

# Notes

A project example is coming shortly.

As of right now, MFA is applied globablly in the `settings.py` file. We are working on changing that to track in a User's settings as part of an `MFAProfile` model attached to the User object.

MFA codes sent to users are stored as one-way hashed objects using Django's built-in hashers. It is treated as a password field in the application. The hashes are created and verified using Django's own `make_password()` and `check_password()` functions, respectively. The ONLY time a plain-text MFA code is created in the application is during the sending of the user message to the Twilio API or via email. At no other time are MFA codes rendered or stored as plain text. All MFA codes are destroyed immediately after use or upon expiration (`MFA_CODE_EXPIRATION`).



