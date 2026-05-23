from django.contrib.auth.models import User
from ..services import GroupService
from threading import Thread, Barrier
from django.test import TransactionTestCase
from ..models import GroupMember
from django.db import connections

class JoinRaceTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user1 = User.objects.create_user("u1")
        self.user2 = User.objects.create_user("u2")
        self.user3 = User.objects.create_user("u3")
        self.group = GroupService.create_group(owner=self.user1, name="test")

        self.barrier = Barrier(2)
        self.results = []
        self.errors = []

    def join(self, user):
        try:
            self.barrier.wait()

            member = GroupService.join_group(
                group=self.group,
                user=user
            ).member

            self.results.append(member.order)
        except Exception as e:
            self.errors.append(e)
        finally:
            connections.close_all()


    def test_race(self):
        t1 = Thread(target=self.join, args=(self.user2,))
        t2 = Thread(target=self.join, args=(self.user3,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(self.errors), 0)

        queue_orders = list(
            GroupMember.objects
            .filter(group=self.group)
            .values_list("order", flat=True)
        )

        self.assertEqual(len(queue_orders), len(set(queue_orders)))