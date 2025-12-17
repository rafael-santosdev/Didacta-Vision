from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class NomeOrEmailBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')

        if username is None or password is None:
            return None

        try:
            user = User.objects.filter(nome_completo__iexact=username).first()
            if not user:
                user = User.objects.filter(email__iexact=username).first()
            if not user:
                user = User.objects.filter(username__iexact=username).first()
            if not user:
                return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

