from axes.signals import user_locked_out
from django.dispatch import receiver
from rest_framework.exceptions import Throttled


@receiver(user_locked_out, dispatch_uid="users.raise_api_login_throttled")
def raise_api_login_throttled(sender, request, **kwargs):
    if request.path_info.startswith("/api/"):
        raise Throttled(
            detail="Muitas tentativas de login. Tente novamente mais tarde."
        )
