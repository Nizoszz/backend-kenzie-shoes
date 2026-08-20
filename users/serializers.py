from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from addresses.models import Address
from addresses.serializers import AddressSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
    )

    def validate_password(self, value):
        user = self.instance or User(
            username=self.initial_data.get("username", ""),
            email=self.initial_data.get("email", ""),
            first_name=self.initial_data.get("first_name", ""),
            last_name=self.initial_data.get("last_name", ""),
        )
        try:
            validate_password(value, user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    def create(self, validated_data: dict) -> User:
        address_create = validated_data.pop("address")
        address = Address.objects.create(**address_create)
        user = User.objects.create_user(address=address, **validated_data)
        return user

    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        address = validated_data.pop("address", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if address is not None:
            if instance.address is None:
                instance.address = Address.objects.create(**address)
            else:
                for key, value in address.items():
                    setattr(instance.address, key, value)
                instance.address.save()
        if password is not None:
            instance.set_password(password)

        instance.save()

        return instance

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "is_superuser",
            "is_seller",
            "image_user",
            "address",
            "user_cart",
        ]

        read_only_fields = ["id", "is_superuser", "is_seller", "user_cart"]
        extra_kwargs = {"password": {"write_only": True}}
