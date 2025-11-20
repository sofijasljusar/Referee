import string
import random
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .utils import validate_single_emoji

GROUP_CODE_LENGTH = 8


def generate_group_code(length=GROUP_CODE_LENGTH):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class PayingQueueGroup(models.Model):
    code = models.CharField(max_length=10, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    emoji = models.CharField(
        max_length=15,
        blank=True,
        default="👥",
        validators=[validate_single_emoji],
        help_text="Add an emoji to represent this group."
    )

    def save(self, *args, **kwargs):
        if not self.code:
            new_code = generate_group_code()
            while PayingQueueGroup.objects.filter(code=new_code).exists():
                new_code = generate_group_code()
            self.code = new_code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paying Queue Group '{self.name}' with code: {self.code}."


class GroupMember(models.Model):
    group = models.ForeignKey(PayingQueueGroup, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="unique_member_per_group")
        ]

    def clean(self):
        if GroupMember.objects.filter(group=self.group, user=self.user).exclude(pk=self.pk).exists():
            raise ValidationError(f"{self.user.username} is already a member of this group.")

    def save(self, *args, **kwargs):
        self.clean()
        if self._state.adding and self.order == 0:
            last_order = GroupMember.objects.filter(group=self.group).aggregate(models.Max("order"))["order__max"]
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __repr__(self):
        return f"Member of a group {self.group.code}: {self.user.username}."

    def __str__(self):
        return self.user.username


class PayingState(models.Model):
    group = models.OneToOneField(PayingQueueGroup, on_delete=models.CASCADE, related_name="paying_state")
    current_paying_member = models.ForeignKey(GroupMember, on_delete=models.SET_NULL, null=True, blank=True)

    def advance_paying_member(self):
        members = list(self.group.members.all())
        current_index = members.index(self.current_paying_member)
        next_index = (current_index + 1) % len(members)
        self.current_paying_member = members[next_index]
        self.save()

    def __str__(self):
        if self.current_paying_member:
            return f"Current paying member in group {self.group.code}: {self.current_paying_member.user.username}."
        return f"Currently group {self.group.code} has no paying member set."


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme_color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"{self.user.username} Profile"
