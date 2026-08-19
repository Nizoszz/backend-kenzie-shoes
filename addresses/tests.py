import pytest

from addresses.serializers import AddressSerializer


@pytest.mark.django_db
def test_address_serializer_validates_required_fields():
    serializer = AddressSerializer(data={"street": "Rua A"})
    assert not serializer.is_valid()
    assert {"number", "zipcode", "city", "state"}.issubset(serializer.errors)


# Create your tests here.
