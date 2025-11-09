import logging
from rest_framework.test import APIRequestFactory, force_authenticate, APITestCase
from whopays.models import PayingQueueGroup, GroupMember
from django.contrib.auth.models import User
from whopays.api_views import ReorderQueueAPIView


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ReorderQueueTests(APITestCase):
    def setUp(self):
        self.users = [
            User.objects.create_user(username="babyshark", password="tudu"),
            User.objects.create_user(username="mummyshark", password="tudutudu"),
            User.objects.create_user(username="daddyshark", password="tudutudutudu"),
        ]
        self.group = PayingQueueGroup.objects.create(name="Sharks", owner=self.users[0])
        for user in self.users[1:]:
            GroupMember.objects.create(group=self.group, user=user)

    def test_reorder_queue(self):
        before_order = [(m.id, m.user.username) for m in self.group.members.all()]
        logger.info(f"Before reorder: {before_order}")

        new_order = [m.id for m in reversed(self.group.members.all())]
        factory = APIRequestFactory()
        request = factory.post(
            f'/group/{self.group.code}/reorder/',
            {'new_order': new_order},
            format='json'
        )
        force_authenticate(request, user=self.users[0])
        view = ReorderQueueAPIView.as_view()
        response = view(request, code=self.group.code)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        after_order = [(m.id, m.user.username) for m in self.group.members.all()]
        logger.info(f"After reorder: {after_order}")

        ordered_numbers = list(self.group.members.all())
        for i in range(len(ordered_numbers)):
            self.assertEqual(ordered_numbers[i].id, new_order[i])
