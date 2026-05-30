import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from django.test import Client

from ..services import GroupService
from ..models import GroupMember


User = get_user_model()


@pytest.mark.django_db
def test_reorder_permission_denied():
    owner = User.objects.create_user("owner")
    other = User.objects.create_user("other")
    group = GroupService.create_group(owner=owner, name="test")
    m = GroupMember.objects.get(group=group, user=owner)

    client = APIClient()
    client.force_authenticate(user=other)

    url = reverse("api-group-reorder", kwargs={"code": group.code})
    res = client.post(url, {"new_order": [m.id]})

    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_reorder_success():
    owner = User.objects.create_user("owner")
    group = GroupService.create_group(owner=owner, name="test")
    m1 = GroupMember.objects.get(group=group, user=owner)

    client = APIClient()
    client.force_authenticate(user=owner)

    url = reverse("api-group-reorder", kwargs={"code": group.code})
    res = client.post(url, {"new_order": [m1.id]})

    assert res.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_set_payer_permission_denied():
    owner = User.objects.create_user("owner")
    other = User.objects.create_user("other")
    group = GroupService.create_group(owner=owner, name="test")
    m = GroupMember.objects.get(group=group, user=owner)

    client = APIClient()
    client.force_authenticate(user=other)

    url = reverse("api-group-set-current-payer", kwargs={"code": group.code})
    res = client.post(url, {"member_id":m.id})

    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_set_payer_success():
    owner = User.objects.create_user("owner")
    group = GroupService.create_group(owner=owner, name="test")
    m = GroupMember.objects.get(group=group, user=owner)

    client = APIClient()
    client.force_authenticate(user=owner)

    url = reverse("api-group-set-current-payer", kwargs={"code": group.code})
    res = client.post(url, {"member_id": m.id})

    assert res.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_group_permission_denied():
    owner = User.objects.create_user("owner")
    other = User.objects.create_user("other")
    group = GroupService.create_group(owner=owner, name="test")

    client = Client()
    client.force_login(user=other)

    url = reverse("group-delete", kwargs={"code": group.code})
    res = client.post(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_group_success():
    owner = User.objects.create_user("owner")
    group = GroupService.create_group(owner=owner, name="test")

    client = Client()
    client.force_login(user=owner)

    url = reverse("group-delete", kwargs={"code": group.code})
    res = client.post(url)

    assert res.status_code == status.HTTP_302_FOUND