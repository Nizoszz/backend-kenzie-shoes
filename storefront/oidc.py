from authlib.integrations.django_client import OAuth
from django.conf import settings

oauth = OAuth()


def oidc_client():
    if not all((settings.OIDC_SERVER_METADATA_URL, settings.OIDC_CLIENT_ID)):
        return None
    client = oauth.create_client("oidc")
    if client is None:
        client = oauth.register(
            name="oidc",
            client_id=settings.OIDC_CLIENT_ID,
            client_secret=settings.OIDC_CLIENT_SECRET,
            server_metadata_url=settings.OIDC_SERVER_METADATA_URL,
            client_kwargs={
                "scope": settings.OIDC_SCOPES,
                "code_challenge_method": "S256",
                "token_endpoint_auth_method": (
                    "client_secret_basic" if settings.OIDC_CLIENT_SECRET else "none"
                ),
            },
        )
    return client
