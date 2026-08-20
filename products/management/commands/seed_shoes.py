from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from products.models import Category, Product
from users.models import User

SHOES = (
    {
        "name": "Tênis Urban Pulse",
        "value": Decimal("249.90"),
        "category": Category.TENIS,
        "stock": 24,
        "description": "Tênis casual leve, com cabedal respirável e solado confortável.",
        "image_product": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tênis Street Classic",
        "value": Decimal("289.90"),
        "category": Category.TENIS,
        "stock": 18,
        "description": "Modelo versátil para compor looks urbanos no dia a dia.",
        "image_product": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tênis Runner Flow",
        "value": Decimal("399.90"),
        "category": Category.TENIS_CORRIDA,
        "stock": 15,
        "description": "Amortecimento responsivo e estrutura leve para treinos diários.",
        "image_product": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Tênis Sprint Pro",
        "value": Decimal("449.90"),
        "category": Category.TENIS_CORRIDA,
        "stock": 12,
        "description": "Tênis de corrida com boa tração e suporte para ritmos intensos.",
        "image_product": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Bota Adventure Trail",
        "value": Decimal("379.90"),
        "category": Category.BOTAS,
        "stock": 10,
        "description": "Bota resistente com solado tratorado para trilhas e uso urbano.",
        "image_product": "https://images.unsplash.com/photo-1542838687-2b3e12dbf9d1?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Bota Chelsea Couro",
        "value": Decimal("429.90"),
        "category": Category.BOTAS,
        "stock": 8,
        "description": "Bota Chelsea elegante, com acabamento clássico e ajuste lateral.",
        "image_product": "https://images.unsplash.com/photo-1520639888713-7851133b1ed0?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chuteira Field Control",
        "value": Decimal("329.90"),
        "category": Category.CHUTEIRAS,
        "stock": 16,
        "description": "Chuteira de campo desenvolvida para controle e estabilidade.",
        "image_product": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chuteira Speed Match",
        "value": Decimal("359.90"),
        "category": Category.CHUTEIRAS,
        "stock": 14,
        "description": "Modelo leve com travas distribuídas para mudanças rápidas de direção.",
        "image_product": "https://images.unsplash.com/photo-1511886929837-354d827aae26?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Sapatênis Essential",
        "value": Decimal("219.90"),
        "category": Category.SAPATENIS,
        "stock": 22,
        "description": "Conforto casual com visual discreto para diferentes ocasiões.",
        "image_product": "https://images.unsplash.com/photo-1491553895911-0055eca6402d?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Sapatênis City Line",
        "value": Decimal("259.90"),
        "category": Category.SAPATENIS,
        "stock": 20,
        "description": "Design contemporâneo e palmilha macia para jornadas prolongadas.",
        "image_product": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Sandália Summer Comfort",
        "value": Decimal("139.90"),
        "category": Category.CHINELOS_SANDALIAS,
        "stock": 28,
        "description": "Sandália leve com tiras ajustáveis e base anatômica.",
        "image_product": "https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=900&q=80",
    },
    {
        "name": "Chinelo Beach Soft",
        "value": Decimal("79.90"),
        "category": Category.CHINELOS_SANDALIAS,
        "stock": 35,
        "description": "Chinelo macio e resistente à água para lazer e descanso.",
        "image_product": "https://images.unsplash.com/photo-1603487742131-4160ec999306?auto=format&fit=crop&w=900&q=80",
    },
)


class Command(BaseCommand):
    help = "Popula o catálogo com calçados de demonstração e imagens remotas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seller",
            default="demo-seller",
            help="Username do vendedor proprietário dos produtos.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["seller"]
        seller, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@example.invalid",
                "first_name": "Loja",
                "last_name": "Demonstração",
                "is_seller": True,
            },
        )

        if created:
            seller.set_unusable_password()
            seller.save(update_fields=("password",))
        elif not seller.is_seller:
            raise CommandError(
                f"O usuário '{username}' existe, mas não possui perfil de vendedor."
            )

        created_count = 0
        skipped_count = 0
        for shoe in SHOES:
            _, was_created = Product.objects.get_or_create(
                name=shoe["name"], defaults={**shoe, "user": seller}
            )
            created_count += was_created
            skipped_count += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo populado: {created_count} criados, "
                f"{skipped_count} já existentes. Vendedor: {seller.username}."
            )
        )
