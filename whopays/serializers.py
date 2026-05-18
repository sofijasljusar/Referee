from rest_framework import serializers


class ThemeColorSerializer(serializers.Serializer):
    theme_color = serializers.RegexField(
        regex=r"^#[0-9a-fA-F]{6}$"
    )


class ReorderMembersSerializer(serializers.Serializer):
    new_order = serializers.ListField(
        child=serializers.IntegerField()
    )


class SetCurrentPayerSerializer(serializers.Serializer):
    member_id = serializers.IntegerField()
