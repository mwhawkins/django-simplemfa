from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import random
from random import randint
import string
from django.contrib.auth.hashers import make_password


CODE_STRING_LENGTH = settings.MFA_CODE_LENGTH if hasattr(settings, 'MFA_CODE_LENGTH') else 6
CODE_EXPIRATION_LENGTH = settings.MFA_CODE_EXPIRATION if hasattr(settings, 'MFA_CODE_EXPIRATION') else 15*60
CODE_DELIVERY_DEFAULT = settings.MFA_CODE_DELIVERY_DEFAULT if hasattr(settings, 'MFA_CODE_DELIVERY_DEFAULT') else "EMAIL"
AUTH_CODE_DELIVERY_CHOICES = [
    ('TEXT', "Text Message"),
    ('PHONE', "Phone Call"),
    ('EMAIL', "Email")
]


def random_string(string_length=CODE_STRING_LENGTH, all_uppercase=True, all_lowercase=False, mixed_case=False,
                  include_numbers=True, only_numbers=False):

    if only_numbers:
        range_start = 10 ** (string_length - 1)
        range_end = (10 ** string_length) - 1
        return str(randint(range_start, range_end))

    letters = string.ascii_letters
    if include_numbers:
        letters += string.octdigits

    if all_uppercase:
        return ''.join(random.choice(letters.upper()) for i in range(string_length))
    elif all_lowercase:
        return ''.join(random.choice(letters.lower()) for i in range(string_length))
    elif mixed_case:
        return ''.join(random.choice(letters) for i in range(string_length))
    else:
        return ''.join(random.choice(letters.upper()) for i in range(string_length))


def hash_this(input):
    try:
        return make_password(input)
    except:
        print("Caught error making hash")
        return input


def generate_code(code=random_string()):
    return hash_this(code)


def get_expiration(seconds=CODE_EXPIRATION_LENGTH):
    return timezone.now() + timezone.timedelta(seconds=seconds)


class AuthCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    expires = models.DateTimeField(default=get_expiration)
    code = models.CharField(max_length=255, default=generate_code)
    sent_via = models.CharField(max_length=15, choices=AUTH_CODE_DELIVERY_CHOICES, default=CODE_DELIVERY_DEFAULT)

    class Meta:
        verbose_name = "MFA Authentication Code"
        verbose_name_plural = "MFA Authentication Codes"

    def __str__(self):
        return f"User: {self.user.username} | Created: {self.created} | Sent Via: {self.sent_via}"

    @classmethod
    def delete_all_codes_for_user(cls, user_id):
        auths = cls.objects.filter(user_id=user_id)
        for auth in auths.all():
            auth.delete()

    @classmethod
    def create_code_for_user(cls, user_id, sent_via="EMAIL"):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        else:
            obj = cls.objects.create(user=user, sent_via=sent_via)
            return obj.create_code()

    def create_code(self):
        code = random_string(only_numbers=True)
        self.code = generate_code(code=code)
        self.expires = get_expiration()
        self.save()
        return code
