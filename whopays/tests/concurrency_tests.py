from django.contrib.auth.models import User
from ..services import GroupService
from ..models import GroupMember, PayingQueueGroup
from .utils import ConcurrentTestCase
from ..exceptions import GroupClosed


class JoinRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.user1 = User.objects.create_user("u1")
        self.user2 = User.objects.create_user("u2")
        self.user3 = User.objects.create_user("u3")
        self.group = GroupService.create_group(owner=self.user1, name="test")

    def test_concurrent_join_for_duplicated_order(self):
        def f1():
            GroupService.join_group(group=self.group, user=self.user2)
        def f2():
            GroupService.join_group(group=self.group, user=self.user3)

        errors = self.run_concurrently([f1, f2])
        self.assertFalse(errors)

        queue_orders = list(
            GroupMember.objects
            .filter(group=self.group)
            .values_list("order", flat=True)
        )
        self.assertEqual(len(queue_orders), len(set(queue_orders)))


class LeaveRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("u1")
        self.user = User.objects.create_user("u2")
        self.group = GroupService.create_group(
            owner=self.owner,
            name="test"
        )
        self.member = GroupService.join_group(
            group=self.group,
            user=self.user
        ).member

    def test_concurrent_leave_for_stale_remaining(self):
        def f1():
            GroupService.leave_group(
                group=self.group,
                member=self.group.members.get(user=self.owner)
            )

        def f2():
            GroupService.leave_group(
                group=self.group,
                member=self.member
            )

        errors = self.run_concurrently([f1, f2])
        self.assertFalse(errors)
        self.assertFalse(GroupMember.objects.filter(group=self.group).exists())
        self.assertFalse(PayingQueueGroup.objects.filter(id=self.group.id).exists())


class CloseJoinRaceTest(ConcurrentTestCase):
    """
        Tests race condition between group closing and user joining.

        Expected outcomes:
        - if join wins the race - both succeed sequentially
        - if close wins the race - join fails with GroupClosed
        - no IntegrityError in close or DoesNotExist exception in join
    """

    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("owner")
        self.new_user = User.objects.create_user("new_user")
        self.group = GroupService.create_group(owner=self.owner, name="test")

    def test_concurrent_close_join(self):
        def f1():
            GroupService.close_group(self.group)

        def f2():
            GroupService.join_group(
                group=self.group,
                user=self.new_user
            )

        errors = self.run_concurrently([f1, f2])
        self.assertTrue(
            not errors or all(isinstance(e, GroupClosed) for e in errors),
            msg=f"Unexpected errors: {errors}"
        )


class CloseLeaveRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("owner")
        self.group = GroupService.create_group(owner=self.owner, name="test")
        self.user = User.objects.create_user("user")
        self.member = GroupService.join_group(
            group=self.group,
            user=self.user
        ).member

    def test_concurrent_close_leave(self):
        def f1():
            GroupService.close_group(self.group)

        def f2():
            GroupService.leave_group(
                group=self.group,
                member=self.member
            )

        errors = self.run_concurrently([f1, f2])
        self.assertTrue(
            not errors or all(isinstance(e, GroupClosed) for e in errors),
            msg=f"Unexpected errors: {errors}"
        )


class CloseAdvanceRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("owner")
        self.group = GroupService.create_group(owner=self.owner, name="test")
        self.user = User.objects.create_user("user")
        GroupService.join_group(
            group=self.group,
            user=self.user
        )

    def test_concurrent_close_advance(self):
        def f1():
            GroupService.close_group(self.group)

        def f2():
            GroupService.advance_paying_member(self.group)

        errors = self.run_concurrently([f1, f2])
        self.assertTrue(
            not errors or all(isinstance(e, GroupClosed) for e in errors),
            msg=f"Unexpected errors: {errors}"
        )


class JoinAdvanceRaceTest(ConcurrentTestCase):
    reset_sequences = True

    def setUp(self):
        self.owner = User.objects.create_user("u1")
        self.new_user = User.objects.create_user("u2")
        self.group = GroupService.create_group(
            owner=self.owner,
            name="test"
        )

    def test_concurrent_join_advance(self):
        def f1():
            GroupService.join_group(
                group=self.group,
                user=self.new_user
            )

        def f2():
            GroupService.advance_paying_member(self.group)

        errors = self.run_concurrently([f1, f2])
        self.assertFalse(errors)

        group = PayingQueueGroup.objects.get(id=self.group.id)
        self.assertEqual(group.members.count(), 2)
        self.assertIn(
            group.paying_state.current_paying_member,
            group.members.all()
        )