import string
import random
from django.db import models
from django.contrib.auth import get_user_model
import regex
from django.core.exceptions import ValidationError
from django.db import transaction
from .exceptions import EmptyGroupError, InvalidPayingStateError

User = get_user_model()

GROUP_CODE_LENGTH = 8

def validate_single_emoji(value):
    if len(regex.findall(r'\X', value)) != 1:
        raise ValidationError("Please enter exactly one emoji.")


def generate_group_code(length=GROUP_CODE_LENGTH):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


class PayingQueueGroup(models.Model):
    code = models.CharField(max_length=GROUP_CODE_LENGTH, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    emoji = models.CharField(
        max_length=15,
        blank=True,
        default="👥",
        validators=[validate_single_emoji],
        help_text="Add an emoji to represent this group."
    )

    @classmethod
    def create_group(cls, owner, name, **kwargs):
        with transaction.atomic():
            group = cls.objects.create(
                owner=owner,
                name=name,
                code=generate_group_code(),
                **kwargs
            )

            member = GroupMember.objects.create(group=group, user=owner)

            PayingState.objects.create(
                group=group,
                current_paying_member=member
            )
            return group

    def normalize_member_order(self):
        members = self.members.order_by("order")
        for index, member in enumerate(members, start=1):
            if member.order != index:
                member.order = index
        GroupMember.objects.bulk_update(members, ["order"])

    def remove_member(self, member):
        with transaction.atomic():
            is_owner = (self.owner == member.user)

            remaining_members = list(self.members.exclude(id=member.id))
            if not remaining_members:
                self.close_group()
                return {"group_deleted": True}

            paying_state = self.paying_state
            if paying_state.current_paying_member_id == member.id:
                paying_state.advance_paying_member()

            member.delete()

            self.normalize_member_order()
            if is_owner:
                self.owner = remaining_members[0].user
                self.save()
            owner_member_id = self.members.get(user=self.owner).id
            return {
                "group_deleted": False,
                "current_payer_id": paying_state.current_paying_member_id,
                "owner_member_id": owner_member_id
            }

    def close_group(self):
        self.paying_state.delete()
        self.delete()

    def __str__(self):
        return f"Paying Queue Group '{self.name}' with code: {self.code}."


class GroupMember(models.Model):
    group = models.ForeignKey(PayingQueueGroup, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="unique_member_per_group"),
            models.UniqueConstraint(fields=["group", "order"], name="unique_order_per_group")
        ]

    def save(self, *args, **kwargs):
        if self._state.adding and self.order is None:
            last_order = GroupMember.objects.filter(group=self.group).aggregate(models.Max("order"))["order__max"]
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class PayingState(models.Model):
    group = models.OneToOneField(PayingQueueGroup, on_delete=models.CASCADE, related_name="paying_state")
    current_paying_member = models.ForeignKey(GroupMember, on_delete=models.PROTECT)

    def advance_paying_member(self):
        members = list(self.group.members.order_by("order"))
        if not members:
            raise EmptyGroupError(
                "Cannot advance turn: group has no members."
            )

        if self.current_paying_member not in members:
            raise InvalidPayingStateError(
                "Cannot advance turn: current payer is not a member of this group."
            )

        current_index = members.index(self.current_paying_member)
        next_index = (current_index + 1) % len(members)
        self.current_paying_member = members[next_index]
        self.save()

    def __str__(self):
        return f"Current paying member in group {self.group.code}: {self.current_paying_member.user.username}."


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme_color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"{self.user.username} Profile"
