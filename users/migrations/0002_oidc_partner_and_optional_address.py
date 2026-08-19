import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="address",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="address",
                to="addresses.address",
            ),
        ),
        migrations.CreateModel(
            name="OIDCIdentity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(max_length=100)),
                ("subject", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="oidc_identities", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PartnerApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField(max_length=1000)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("approved", "Aprovada"), ("rejected", "Rejeitada")], default="pending", max_length=10)),
                ("review_note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_partner_applications", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="partner_applications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(
            model_name="oidcidentity",
            constraint=models.UniqueConstraint(fields=("provider", "subject"), name="unique_oidc_provider_subject"),
        ),
        migrations.AddConstraint(
            model_name="partnerapplication",
            constraint=models.UniqueConstraint(condition=models.Q(("status", "pending")), fields=("user",), name="unique_pending_partner_application"),
        ),
    ]
