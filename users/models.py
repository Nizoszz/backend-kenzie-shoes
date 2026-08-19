from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=127, unique=True)
    is_seller = models.BooleanField(default=False, null=True, blank=True)
    image_user = models.URLField(max_length=200, null=True, blank=True)

    address = models.OneToOneField(
        "addresses.Address",
        on_delete=models.CASCADE,
        related_name="address",
        null=True,
        blank=True,
    )

    product = models.ManyToManyField(
        "products.Product", through="cart.Cart", related_name="cart"
    )

    @property
    def profile_complete(self):
        return self.address_id is not None


class OIDCIdentity(models.Model):
    provider = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="oidc_identities"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "subject"), name="unique_oidc_provider_subject"
            )
        ]

    def __str__(self):
        return f"{self.provider}:{self.subject}"


class PartnerApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovada"
        REJECTED = "rejected", "Rejeitada"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="partner_applications"
    )
    message = models.TextField(max_length=1000)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_partner_applications",
    )
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=models.Q(status="pending"),
                name="unique_pending_partner_application",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.get_status_display()}"
