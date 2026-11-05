from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este e-mail já está cadastrado.")
        return value

    def validate(self, attrs):
        try:
            password_validation.validate_password(attrs["password"], User(name=attrs["name"], email=attrs["email"]))
        except ValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError({"email": ["Este e-mail já está cadastrado."]})


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate(self, attrs):
        user = authenticate(request=self.context["request"],
                            email=User.objects.normalize_email(attrs["email"]), password=attrs["password"])
        if user is None:
            raise serializers.ValidationError({"detail": "E-mail ou senha inválidos."})
        return {"user": user}
