from django.db.models.signals import post_save, post_delete,  pre_delete
from django.dispatch import receiver
from .models import PayingQueueGroup, GroupMember, PayingState
from .utils import normalize_order

@receiver(post_save, sender=PayingQueueGroup)
def create_paying_state_for_group(sender, instance, created, **kwargs):
    if created:
        PayingState.objects.create(group=instance)


@receiver(post_save, sender=GroupMember)
def assign_first_payer(sender, instance, created, **kwargs):
    if created:
        group = instance.group
        paying_state = group.paying_state
        if paying_state.current_paying_member is None:
            paying_state.current_paying_member = instance
            paying_state.save()


@receiver(post_save, sender=PayingQueueGroup)
def add_group_owner_as_member(sender, instance, created, **kwargs):
    if created and instance.owner:
        GroupMember.objects.get_or_create(group=instance, user=instance.owner)


@receiver(pre_delete, sender=GroupMember)
def advance_turn_before_deleting_member(sender, instance, **kwargs):
    group = instance.group
    paying_state = group.paying_state
    if paying_state.current_paying_member == instance:
        paying_state.advance_paying_member()


@receiver(post_delete, sender=GroupMember)
def normalize_queue_after_deleting_member(sender, instance, **kwargs):
    group = instance.group
    normalize_order(group)
