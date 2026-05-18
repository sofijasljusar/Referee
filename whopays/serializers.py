from rest_framework import serializers


class ThemeColorSerializer(serializers.Serializer):
    theme_color = serializers.RegexField(
        regex=r"^#[0-9a-fA-F]{6}$"
    )
