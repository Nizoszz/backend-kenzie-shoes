import pytest


@pytest.mark.django_db
def test_health_check(api_client):
    response = api_client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_api_documentation_is_restricted_outside_debug(api_client, settings):
    settings.DEBUG = False
    assert api_client.get("/api/schema/").status_code in {401, 403}


@pytest.mark.django_db
def test_admin_can_access_api_documentation(authenticated_client, make_user):
    admin = make_user(is_staff=True, is_superuser=True)
    assert authenticated_client(admin).get("/api/schema/").status_code == 200
