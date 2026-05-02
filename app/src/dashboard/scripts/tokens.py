from rest_framework.authtoken.models import Token

from authentication.models import User


def run():
    for user in User.objects.all():
        Token.objects.get_or_create(user=user)
