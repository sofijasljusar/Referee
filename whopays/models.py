from django.db import models
from django.contrib.auth import get_user_model
import regex
from django.core.exceptions import ValidationError

User = get_user_model()


def validate_single_emoji(value):
    if len(regex.findall(r'\X', value)) != 1:
        raise ValidationError("Please enter exactly one emoji.")


class PayingQueueGroup(models.Model):
    CODE_LENGTH = 8
    code = models.CharField(max_length=CODE_LENGTH, unique=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    emoji = models.CharField(
        max_length=15,
        blank=True,
        default="👥",
        validators=[validate_single_emoji],
        help_text="Add an emoji to represent this group."
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


class GroupMember(models.Model):
    group = models.ForeignKey(PayingQueueGroup, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="unique_member_per_group"),
            models.UniqueConstraint(fields=["group", "order"], name="unique_order_per_group")
        ]

    def __str__(self):
        return self.user.username


class PayingState(models.Model):
    group = models.OneToOneField(PayingQueueGroup, on_delete=models.CASCADE, related_name="paying_state")
    current_paying_member = models.ForeignKey(GroupMember, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.group.code} - {self.current_paying_member}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme_color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"{self.user.username} Profile"
