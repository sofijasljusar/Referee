from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PayingQueueGroup, GroupMember, PayingState


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

