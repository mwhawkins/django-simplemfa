# django-simple-mfa
A simple implementation of basic Multi-Factor Authentication (MFA) functions in Django.

# Overview
The intent of this application is to:
1. Provide basic MFA functionality via email, phone, or text message
2. Leverage as much of the Django application itself as possible without external dependencies when feasible
3. Provide a simplified mechanism for setup that does not require major changes to existing projects

## Why It Exists
Upon testing various other Django MFA applications, most fell into one or more of the following categories:
1. Codebase was deprecated or didn't support recent Django versions
2. Required a large amount of very specific dependencies
3. Required substantial changes to existing application structure to function properly

## Basic Requirements
- Django >= version 3.0
- Django-Twilio (if using phone and/or text message MFA)

Twilio is the only current integration for phone and text message, but more are planned.
Email MFA is provided using the Django built-in email utilities.

# Setup and Use
Coming soon...
