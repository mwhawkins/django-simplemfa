# django-simplemfa
An easy-to-integrate implementation of essential Multi-Factor Authentication (MFA) functionality for Django applications.

[Available on PyPI](https://pypi.org/project/django-simplemfa/) (`pip install django-simplemfa`)

# Overview
The intent of this project is to:
1. Provide essential MFA functionality for new and existing Django applications.
2. Limit external (outside Django) dependencies wherever feasible.
3. Simplify the setup and integration of MFA functionality in Django applications.

## Why It Exists
Upon evaluating various other Django MFA applications, most appeared to be one or more of the following:
1. Their codebases were deprecated or unsupported.
2. They often required a substantial amount of very specific dependencies in order to achieve even basic functionality.
3. They often required substantial changes to existing applications to function and integrate properly.

## Basic Requirements
- Django >= version 3.0
- Django-Twilio (if using phone and/or text message MFA, not required for just email)

Twilio is the current integration for phone and text message MFA, but more are planned.
Email MFA leverages the built-in Django email utilities.

# Setup
Download or clone the `simplemfa` package here into your Django application or install from PyPi with `pip install django-simplemfa`.

## Templates (`templates/simplemfa`)

Create a new directory called 'simplemfa' and in it place or create the following template:
- `simplemfa/auth.html` (the MFA login screen template)

The following templates are optional if you want to override the default content for each:
- `simplemfa/mfa_email.html` (the MFA email message template)
- `simplemfa/mfa_text.html` (the MFA text message template)
- `simplemfa/mfa_voice.html` (plain text file with the message you want to say via phone call)

Examples and defaults are provided in the package's `templates` directory (`simplemfa/templates`).

## URLs (`urls.py`)

Add `path('mfa/', include('simplemfa.urls', namespace="simplemfa"))` to your routes, making sure to include the namespace as shown.

## Settings (`settings.py`)

### Required Settings

- Required: `REQUIRE_MFA = True` (global setting which activates MFA for all users)
- Required: Ensure the Django [email system is configured properly](https://docs.djangoproject.com/en/3.0/topics/email/) 
- Required: ```INSTALLED_APPS = [
                                  ...
                                  'simplemfa'
                              ]```
- Required:  ```MIDDLEWARE = [
                                  ...
                            'simplemfa.middleware.ValidateMFAMiddleware'
                            ]```
                            
**If using Twilio (text and voice):**

- Required: Install and set up [djang-twilio](https://django-twilio.readthedocs.io/en/latest/)
- Required: `MFA_USER_PHONE_ATTRIBUTE` (the attribute of `request.user` that has the phone number for the user in the format `+12345678900`, e.g. `profile.phone` resolves to `request.user.profile.phone`)

### Optional Settings
- Optional: `APP_NAME = "My App Name"` (application name which is provided in the messages to the user)
- Optional: `MFA_CODE_LENGTH` (default is 6)
- Optional: `MFA_COOKIE_EXPIRATION_DAYS` (the default "remember me" period, default is 7)
- Optional: `MFA_CODE_EXPIRATION` (default is 900 seconds (15 minutes))
- Optional: `MFA_CODE_DELIVERY_DEFAULT` (default is "EMAIL")
- Optional: `MFA_USER_MODE_ATTRIBUTE` (the attribute of `request.user` that has the user's default way of receiving the MFA code, e.g. `profile.mfa_mode` resolves to `request.user.profile.mfa_mode` which must be one of the choices from `simplemfa.models.AUTH_CODE_DELIVERY_CHOICES` - currently "EMAIL", "TEXT", and "PHONE")

### Migrations and Running
Once those items are complete, run `makemigrations` and `migrate` for your project, then run your project. That's it!

It should allow you to access all public (login exempt) pages. After you log in, however, it will automatically redirect you to the MFA verification page where you will request and then enter an MFA code. If the code passes, you will be allowed to proceed as any normal authenticated user would in your application.

# Notes

A project example is coming shortly.

As of right now, MFA is applied globablly in the `settings.py` file. We are working on changing that to track in a User's settings as part of an `MFAProfile` model attached to the User object.

MFA codes sent to users are stored as one-way hashed objects using Django's built-in hashers. It is treated as a password field in the application. The hashes are created and verified using Django's own `make_password()` and `check_password()` functions, respectively. The ONLY time a plain-text MFA code is created in the application is during the sending of the user message to the Twilio API or via email.



