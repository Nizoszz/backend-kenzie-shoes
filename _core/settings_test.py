from .settings import *  # noqa: F403

SECRET_KEY = "test-secret-key-with-at-least-thirty-two-bytes"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@example.com"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("TEST_POSTGRES_DB", "commerce_test"),  # noqa: F405
        "USER": os.getenv("TEST_POSTGRES_USER", "commerce"),  # noqa: F405
        "PASSWORD": os.getenv("TEST_POSTGRES_PASSWORD", "commerce"),  # noqa: F405
        "HOST": os.getenv("TEST_POSTGRES_HOST", "localhost"),  # noqa: F405
        "PORT": os.getenv("TEST_POSTGRES_PORT", "5433"),  # noqa: F405
    }
}
