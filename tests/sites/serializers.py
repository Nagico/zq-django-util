from django.utils.timezone import now
from rest_framework import serializers

from tests.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "groups"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["time"] = now()
        return data
