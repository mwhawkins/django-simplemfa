# django-simple-mfa
A simple implementation of basic Multi-Factor Authentication (MFA) functionality for Django applications.

# Overview
The intent of this project is to:
1. Provide basic yet effective MFA functionality for new and existing Django applications.
2. Limit external dependencies wherever feasible by leveraging as much of the Django framework itself as is possible.
3. Simplify the setup and integration of MFA functionality in Django applications.
4. Limit the amount of alteration required in existing codebases to integrate basic MFA functionality.
5. Provide options to integrate more advanced or customized MFA functionality if desired.

At this time only email, phone call, and text message MFA options are supported. Future integrations (such as MS/Google Authenticator apps, OTP keys, WebAuthn, etc.) are possible but only if their integration adheres to the intent of this project as stated above.

## Why It Exists
Upon evaluating various other Django MFA applications, most appeared to fall into one or more of the following categories:
1. Their codebases were deprecated or unsupported.
2. They often required a substantial amount of very specific dependenciesin order to even achieve basic functionality.
3. The often required substantial changes to existing applications to function and integrate properly.

## Basic Requirements
- Django >= version 3.0
- Django-Twilio (if using phone and/or text message MFA)

Twilio is the current integration for phone and text message MFA, but more are planned.
Email MFA leverages the built-in Django email utilities.

# Setup and Use
Coming soon...
