import pytest
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.core.cache import cache


def test_argon2_uses_a_unique_random_salt_with_expected_length():
    first_hash = make_password("SamePassword123!")
    second_hash = make_password("SamePassword123!")

    assert first_hash != second_hash
    assert first_hash.startswith("argon2$")

    salt = identify_hasher(first_hash).decode(first_hash)["salt"]
    assert 15 <= len(salt) <= 25


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",
        "lowercase1!",
        "UPPERCASE1!",
        "NoNumbers!",
        "NoSpecial123",
    ],
)
def test_password_policy_rejects_weak_passwords(password):
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        validate_password(password)


@pytest.mark.django_db
def test_registration_hashes_password_and_creates_address(api_client):
    response = api_client.post(
        "/api/users/",
        {
            "username": "new-user",
            "email": "new@example.com",
            "password": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
            "address": {
                "street": "Rua Nova",
                "number": 10,
                "zipcode": "01000-000",
                "city": "São Paulo",
                "state": "SP",
            },
        },
        format="json",
    )
    assert response.status_code == 201
    assert "password" not in response.data
    from users.models import User

    user = User.objects.get(username="new-user")
    assert check_password("StrongPass123!", user.password)
    assert user.password.startswith("argon2$")
    assert user.address.street == "Rua Nova"


@pytest.mark.django_db
def test_api_registration_applies_password_policy(api_client):
    response = api_client.post(
        "/api/users/",
        {
            "username": "weak-password",
            "email": "weak@example.com",
            "password": "12345678",
            "first_name": "Weak",
            "last_name": "Password",
            "address": {
                "street": "Rua Nova",
                "number": 10,
                "zipcode": "01000-000",
                "city": "São Paulo",
                "state": "SP",
            },
        },
        format="json",
    )

    assert response.status_code == 400
    assert "password" in response.data


@pytest.mark.django_db
def test_registration_cannot_self_promote_to_seller(api_client):
    payload = {
        "username": "attacker",
        "email": "attacker@example.com",
        "password": "StrongPass123!",
        "first_name": "Attack",
        "last_name": "User",
        "is_seller": True,
        "address": {
            "street": "Rua A",
            "number": 1,
            "zipcode": "01000-000",
            "city": "São Paulo",
            "state": "SP",
        },
    }
    assert api_client.post("/api/users/", payload, format="json").status_code == 201
    from users.models import User

    assert User.objects.get(username="attacker").is_seller is False


def test_admin_command_requires_explicit_password():
    from django.core.management.base import CommandError

    from users.management.commands.create_admin import Command

    with pytest.raises(CommandError, match="Password is required"):
        Command().handle(username="admin", email="admin@example.com", password=None)


@pytest.mark.django_db
def test_login_returns_jwt(api_client, buyer):
    response = api_client.post(
        "/api/users/login/", {"username": buyer.username, "password": "StrongPass123!"}
    )
    assert response.status_code == 200
    assert {"access", "refresh"}.issubset(response.data)


@pytest.mark.django_db
def test_refresh_token_rotates_and_logout_blacklists_it(api_client, buyer):
    login = api_client.post(
        "/api/users/login/",
        {"username": buyer.username, "password": "StrongPass123!"},
    )
    refresh = api_client.post(
        "/api/users/token/refresh/", {"refresh": login.data["refresh"]}
    )
    assert refresh.status_code == 200
    assert refresh.data["refresh"] != login.data["refresh"]
    assert (
        api_client.post(
            "/api/users/logout/", {"refresh": refresh.data["refresh"]}
        ).status_code
        == 200
    )
    assert (
        api_client.post(
            "/api/users/token/refresh/", {"refresh": refresh.data["refresh"]}
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_jwt_login_blocks_brute_force_by_ip(api_client, buyer):
    cache.clear()
    responses = [
        api_client.post(
            "/api/users/login/",
            {"username": f"unknown-{attempt}", "password": "wrong"},
            REMOTE_ADDR="198.51.100.10",
        )
        for attempt in range(5)
    ]
    assert responses[-1].status_code == 429


@pytest.mark.django_db
def test_storefront_login_blocks_distributed_brute_force_by_username(client, buyer):
    responses = [
        client.post(
            "/login/",
            {"username": buyer.username, "password": "wrong"},
            REMOTE_ADDR=f"198.51.100.{attempt}",
        )
        for attempt in range(1, 6)
    ]

    assert responses[-1].status_code == 429
    assert (
        client.post(
            "/login/",
            {"username": buyer.username, "password": "StrongPass123!"},
            REMOTE_ADDR="203.0.113.20",
        ).status_code
        == 429
    )


@pytest.mark.django_db
def test_successful_login_resets_previous_failures(client, buyer):
    for _ in range(2):
        assert (
            client.post(
                "/login/",
                {"username": buyer.username, "password": "wrong"},
                REMOTE_ADDR="198.51.100.20",
            ).status_code
            == 200
        )

    assert (
        client.post(
            "/login/",
            {"username": buyer.username, "password": "StrongPass123!"},
            REMOTE_ADDR="198.51.100.20",
        ).status_code
        == 302
    )
    client.post("/logout/")

    for _ in range(4):
        assert (
            client.post(
                "/login/",
                {"username": buyer.username, "password": "wrong"},
                REMOTE_ADDR="198.51.100.20",
            ).status_code
            == 200
        )


@pytest.mark.django_db
def test_admin_login_is_protected(client, make_user):
    admin = make_user(is_staff=True, is_superuser=True)
    responses = [
        client.post(
            "/admin/login/",
            {"username": admin.username, "password": "wrong"},
            REMOTE_ADDR="198.51.100.30",
        )
        for _ in range(5)
    ]

    assert responses[-1].status_code == 429


@pytest.mark.django_db
def test_only_owner_can_retrieve_or_update_user(authenticated_client, buyer, make_user):
    other = make_user()
    client = authenticated_client(buyer)
    assert client.get(f"/api/users/{buyer.id}/").status_code == 200
    assert client.get(f"/api/users/{other.id}/").status_code == 403
    response = client.patch(
        f"/api/users/{buyer.id}/",
        {"password": "ChangedPass123!", "address": {"street": "Rua Alterada"}},
        format="json",
    )
    assert response.status_code == 200
    buyer.refresh_from_db()
    assert buyer.check_password("ChangedPass123!")
    assert buyer.address.street == "Rua Alterada"


@pytest.mark.django_db
def test_user_update_cannot_bypass_password_policy(authenticated_client, buyer):
    response = authenticated_client(buyer).patch(
        f"/api/users/{buyer.id}/", {"password": "abcdefgh"}, format="json"
    )

    assert response.status_code == 400
    assert "password" in response.data
    buyer.refresh_from_db()
    assert buyer.check_password("StrongPass123!")
