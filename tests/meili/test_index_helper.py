from unittest import mock

import pytest
from model_bakery import baker
from rest_framework import serializers
from rest_framework.fields import DateTimeField

from tests.models import User
from zq_django_util.utils.meili.index import BaseIndexHelper


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "is_active", "create_time"]


class UserIndexHelper(BaseIndexHelper):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    index_class = mock.Mock()


@pytest.fixture
def helper(db):
    User.objects.all().delete()
    res = UserIndexHelper()
    res.index.reset_mock()
    yield res
    res.index.reset_mock()
    User.objects.all().delete()


@pytest.fixture
def helper_no_auto(db):
    User.objects.all().delete()
    res = UserIndexHelper(auto_update=False)
    res.index.reset_mock()
    yield res
    res.index.reset_mock()
    User.objects.all().delete()


def test_helper_upsert__single_obj(db, helper_no_auto):
    user = baker.prepare(User, is_active=True)
    helper_no_auto.upsert_index(user)

    fun = helper_no_auto.index.add_documents

    assert fun.call_count == 1
    assert fun.call_args[0][0][0] == {
        "id": user.pk,
        "username": user.username,
        "is_active": user.is_active,
        "create_time": user.create_time,
    }


def test_helper_upsert__multi_obj(db, helper_no_auto):
    users = baker.prepare(User, is_active=True, _quantity=3)

    helper_no_auto.upsert_index(users)

    fun = helper_no_auto.index.add_documents

    assert fun.call_count == 1
    assert len(fun.call_args[0][0]) == 3


def test_helper_upsert__single_pk(db, helper_no_auto):
    user = baker.make(User, is_active=True)

    fun = helper_no_auto.index.add_documents

    helper_no_auto.upsert_index(user.pk)

    assert fun.call_count == 1
    assert fun.call_args[0][0][0] == {
        "id": user.pk,
        "username": user.username,
        "is_active": user.is_active,
        "create_time": DateTimeField().to_representation(user.create_time),
    }


def test_helper_upsert__multi_pk(db, helper_no_auto):
    users = baker.make(User, is_active=True, _quantity=3)

    fun = helper_no_auto.index.add_documents

    helper_no_auto.upsert_index([user.pk for user in users])

    assert fun.call_count == 1
    assert len(fun.call_args[0][0]) == 3


def test_helper_upsert__multi_pk_ignore_default_query_set(db, helper_no_auto):
    baker.make(User, is_active=True, is_staff=True, _quantity=3)
    baker.make(User, is_active=True, is_staff=False, _quantity=6)
    baker.make(User, is_active=False, is_staff=True, _quantity=10)
    queryset = User.objects.filter(is_staff=True)

    fun = helper_no_auto.index.add_documents

    helper_no_auto.upsert_index(
        [user.pk for user in queryset], ignore_default_query_set=True
    )

    assert fun.call_count == 1
    assert len(fun.call_args[0][0]) == 13


def test_helper_upsert__queryset(db, helper_no_auto):
    baker.make(User, is_active=True, is_staff=True, _quantity=3)
    baker.make(User, is_active=True, is_staff=False, _quantity=6)
    baker.make(User, is_active=False, is_staff=True, _quantity=10)
    queryset = User.objects.filter(is_staff=True)

    fun = helper_no_auto.index.add_documents

    helper_no_auto.upsert_index(queryset)

    assert fun.call_count == 1
    assert len(fun.call_args[0][0]) == 3


def test_helper_upsert__queryset_ignore_default_query_set(db, helper_no_auto):
    baker.make(User, is_active=True, is_staff=True, _quantity=3)
    baker.make(User, is_active=True, is_staff=False, _quantity=6)
    baker.make(User, is_active=False, is_staff=True, _quantity=10)
    queryset = User.objects.filter(is_staff=True)

    fun = helper_no_auto.index.add_documents

    helper_no_auto.upsert_index(queryset, ignore_default_query_set=True)

    assert fun.call_count == 1
    assert len(fun.call_args[0][0]) == 13


def test_helper_upsert__empty(db, helper_no_auto):
    fun = helper_no_auto.index.add_documents

    helper_no_auto.upsert_index([])

    assert fun.call_count == 0


def test_helper_delete__single_obj(db, helper_no_auto):
    user = baker.make(User, is_active=True)

    fun = helper_no_auto.index.delete_documents

    helper_no_auto.delete_index(user)

    assert fun.call_count == 1
    assert fun.call_args[0][0] == [user.pk]


def test_helper_delete__multi_obj(db, helper_no_auto):
    users = baker.make(User, is_active=True, _quantity=3)

    fun = helper_no_auto.index.delete_documents

    helper_no_auto.delete_index(users)

    assert fun.call_count == 1
    assert fun.call_args[0][0] == [user.pk for user in users]


def test_helper_delete__single_pk(db, helper_no_auto):
    user = baker.make(User, is_active=True)

    fun = helper_no_auto.index.delete_documents

    helper_no_auto.delete_index(user.pk)

    assert fun.call_count == 1
    assert fun.call_args[0][0] == [user.pk]


def test_helper_delete__multi_pk(db, helper_no_auto):
    users = baker.make(User, is_active=True, _quantity=3)

    fun = helper_no_auto.index.delete_documents

    helper_no_auto.delete_index([user.pk for user in users])

    assert fun.call_count == 1
    assert not set(fun.call_args[0][0]) ^ set(
        [user.pk for user in users]
    )  # the same lists but in different order


def test_helper_delete__queryset(db, helper_no_auto):
    baker.make(User, is_active=True, is_staff=True, _quantity=3)
    baker.make(User, is_active=True, is_staff=False, _quantity=6)
    baker.make(User, is_active=False, is_staff=True, _quantity=10)
    queryset = User.objects.filter(is_staff=True)

    fun = helper_no_auto.index.delete_documents

    helper_no_auto.delete_index(queryset)

    assert fun.call_count == 1
    assert not set(fun.call_args[0][0]) ^ set(
        [user.pk for user in queryset]
    )  # the same lists but in different order


def test_helper_delete__empty(db, helper_no_auto):
    fun = helper_no_auto.index.delete_documents

    helper_no_auto.delete_index([])

    assert fun.call_count == 0


def test_helper_rebuild_index(db, helper_no_auto):
    baker.make(User, is_active=True, is_staff=True, _quantity=3)
    baker.make(User, is_active=True, is_staff=False, _quantity=6)
    baker.make(User, is_active=False, is_staff=True, _quantity=10)

    fun = helper_no_auto.index.add_documents

    helper_no_auto.rebuild_index()

    assert fun.call_count == 1
    assert len(fun.call_args[0][0]) == 9


def test_helper__search(helper_no_auto):
    baker.make(User, is_active=True, is_staff=True, _quantity=3)
    baker.make(User, is_active=True, is_staff=False, _quantity=6)
    baker.make(User, is_active=False, is_staff=True, _quantity=10)

    fun = helper_no_auto.index.search

    fun.return_value = {
        "hits": [
            {"objectID": 1},
            {"objectID": 2},
            {"objectID": 3},
        ],
        "page": 1,
        "totalPages": 5,
        "hitsPerPage": 3,
        "totalHits": 14,
        "processingTimeMs": 1,
        "query": "keyword",
    }

    res = helper_no_auto.search(
        query="keyword",
        page=1,
        hits_per_page=3,
        filter="filter",
        facets=["facets"],
        attributes_to_retrieve=["attributes_to_retrieve"],
        attributes_to_crop=["attributes_to_crop"],
        crop_length=10,
        crop_marker="crop_marker",
        attributes_to_highlight=["attributes_to_highlight"],
        highlight_pre_tag="highlight_pre_tag",
        highlight_post_tag="highlight_post_tag",
        show_match_positions=True,
        sort=["sort"],
        matching_strategy="matching_strategy",
    )

    assert fun.call_count == 1
    assert fun.call_args[0][0] == "keyword"
    assert fun.call_args[0][1] == {
        "page": 1,
        "hitsPerPage": 3,
        "filter": "filter",
        "facetsDistribution": ["facets"],
        "attributesToRetrieve": ["attributes_to_retrieve"],
        "attributesToCrop": ["attributes_to_crop"],
        "cropLength": 10,
        "cropMarker": "crop_marker",
        "attributesToHighlight": ["attributes_to_highlight"],
        "highlightPreTag": "highlight_pre_tag",
        "highlightPostTag": "highlight_post_tag",
        "showMatchPositions": True,
        "sort": ["sort"],
        "matchingStrategy": "matching_strategy",
    }

    assert len(res) == 3


def test_helper__search__no_results(helper_no_auto):
    fun = helper_no_auto.index.search

    fun.return_value = {
        "hits": [],
        "page": 1,
        "totalPages": 0,
        "hitsPerPage": 0,
        "totalHits": 0,
        "processingTimeMs": 1,
        "query": "keyword",
    }

    res = helper_no_auto.search("keyword")

    assert fun.call_count == 1
    assert fun.call_args[0][0] == "keyword"
    assert fun.call_args[0][1] == {
        "page": 1,
        "hitsPerPage": 20,
    }

    assert len(res) == 0


def test_helper__search_with_request(helper_no_auto):
    request = mock.Mock()
    request.query_params = {
        "page": 1,
        "page_size": 3,
    }

    fun = helper_no_auto.index.search

    fun.return_value = {
        "hits": [],
        "page": 1,
        "totalPages": 0,
        "hitsPerPage": 0,
        "totalHits": 0,
        "processingTimeMs": 1,
        "query": "keyword",
    }

    helper_no_auto.search_with_request("keyword", request)

    assert fun.call_count == 1
    assert fun.call_args[0][0] == "keyword"
    assert fun.call_args[0][1] == {
        "page": 1,
        "hitsPerPage": 3,
    }


def test_helper__auto_upsert(helper):
    fun = helper.index.add_documents
    user = baker.make(User, is_active=True)

    user.is_active = False
    user.save()

    assert fun.call_count == 2

    assert fun.call_args_list[0][0][0][0] == {
        "id": user.pk,
        "username": user.username,
        "is_active": True,
        "create_time": DateTimeField().to_representation(user.create_time),
    }
    assert fun.call_args_list[1][0][0][0] == {
        "id": user.pk,
        "username": user.username,
        "is_active": False,
        "create_time": DateTimeField().to_representation(user.create_time),
    }


def test_helper__auto_delete(helper):
    fun = helper.index.delete_documents
    user = baker.make(User, is_active=True)
    pk = user.pk
    user.delete()

    assert fun.call_count == 1
    assert fun.call_args[0][0] == [pk]
