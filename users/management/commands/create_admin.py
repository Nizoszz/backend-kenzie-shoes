from django.core.management.base import BaseCommand, CommandError
from users.models import User
from addresses.models import Address


class Command(BaseCommand):
    help = "Create admin users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Define o username",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Define o email",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Define o password",
        )

    def handle(self, *args, **kwargs):
        username = kwargs.get("username")
        email = kwargs.get("email")
        password = kwargs.get("password")
        address = kwargs.get("address")

        if not username:
            username = "admin"
        if not email:
            email = username + "@kenzieshoes.com"
        if not password:
            raise CommandError(
                "Password is required. Use --password or a protected secret."
            )
        if not address:
            address_create = {
                "street": "Rua admin",
                "number": 1,
                "city": "Cidade admin",
                "state": "Estado admin",
                "zipcode": "...",
            }

        user_obj = User.objects.filter(username=username)
        if user_obj:
            raise CommandError(f"Username `{username}` already taken.")

        email_obj = User.objects.filter(email=email)
        if email_obj:
            raise CommandError(f"Email `{email}` already taken.")

        address = Address.objects.create(**address_create)
        User.objects.create_superuser(
            username=username, email=email, password=password, address=address
        )

        self.stdout.write(
            self.style.SUCCESS(f"Admin `{username}` successfully created!")
        )
