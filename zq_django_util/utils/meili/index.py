from typing import Any, Type

from django.db.models import Model, QuerySet
from django.db.models.signals import post_delete, post_save
from meilisearch import Client
from meilisearch.index import Index as MeiliIndex
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from zq_django_util.utils.meili import meili_client
from zq_django_util.utils.meili.response import SearchResult

PK = int | str


class BaseIndex(MeiliIndex):
    index_uid: str
    primary_key: str | None = None
    client: Client = meili_client

    class_settings: bool = True

    # global
    displayed_attributes: list[str] = ["*"]
    searchable_attributes: list[str] = ["*"]
    filterable_attributes: list[str] = []
    sortable_attributes: list[str] = []
    ranking_rules: list[str] = [
        "typo",
        "words",
        "proximity",
        "attribute",
        "sort",
        "exactness",
    ]
    stop_words: list[str] = []
    synonyms: dict[str, list[str]] = {}
    distinct_attribute: str | None = None

    # faceting
    max_values_per_facet: int = 100

    # pagination
    max_total_hits: int = 1000

    _instance: "BaseIndex" = None

    class Meta:
        abstract = True

    def __init__(self) -> None:
        assert (
            self.index_uid is not None and self.index_uid != ""
        ), "index_uid is required"
        assert self.client is not None, "client is required"

        super().__init__(
            self.client.config, uid=self.index_uid, primary_key=self.primary_key
        )

        if self.class_settings:
            self.update_settings(self._class_settings)

    def __new__(cls, *args, **kwargs):
        """
        singleton
        """
        if cls._instance is None:
            cls._instance = super(BaseIndex, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _validate_string_list(
        name: str, value: list[str], allow_empty: bool = True
    ):
        assert isinstance(value, list), f"{name} must be a list"
        assert allow_empty or len(value) > 0, f"{name} must not be empty"
        assert all(
            isinstance(item, str) for item in value
        ), f"{name} must be a list of string"

    def _validate_class_settings(self):
        self._validate_string_list(
            "displayedAttributes", self.displayed_attributes, allow_empty=False
        )
        self._validate_string_list(
            "searchableAttributes",
            self.searchable_attributes,
            allow_empty=False,
        )
        self._validate_string_list(
            "filterableAttributes", self.filterable_attributes
        )
        self._validate_string_list(
            "sortableAttributes", self.sortable_attributes
        )
        self._validate_string_list(
            "rankingRules", self.ranking_rules, allow_empty=False
        )
        self._validate_string_list("stopWords", self.stop_words)

        assert isinstance(self.synonyms, dict), "synonyms must be a dict"
        assert all(
            isinstance(key, str) for key in self.synonyms.keys()
        ), "synonyms keys must be a string"
        assert all(
            isinstance(value, list) for value in self.synonyms.values()
        ), "synonyms values must be a list of string"
        assert all(
            isinstance(item, str)
            for value in self.synonyms.values()
            for item in value
        ), "synonyms values must be a list of string"

        assert self.distinct_attribute is None or isinstance(
            self.distinct_attribute, str
        ), "distinctAttribute must be a string or None"

    @property
    def _class_settings(self) -> dict[str, Any]:
        self._validate_class_settings()
        return {
            "displayedAttributes": self.displayed_attributes,
            "searchableAttributes": self.searchable_attributes,
            "filterableAttributes": self.filterable_attributes,
            "sortableAttributes": self.sortable_attributes,
            "rankingRules": self.ranking_rules,
            "stopWords": self.stop_words,
            "synonyms": self.synonyms,
            "distinctAttribute": self.distinct_attribute,
            "faceting": {"maxValuesPerFacet": self.max_values_per_facet},
            "pagination": {"maxTotalHits": self.max_total_hits},
        }


class BaseIndexHelper:
    queryset: QuerySet
    serializer_class: Type[BaseSerializer]
    index_class: Type[BaseIndex]

    class Meta:
        abstract = True

    def __init__(self):
        self.model = self.queryset.model
        self.index = self.index_class()

        post_save.connect(self.model_save_receiver, sender=self.model)
        post_delete.connect(self.model_delete_receiver, sender=self.model)

    def upsert_index(
        self,
        objs: Model | PK | list[Model | PK] | QuerySet,
        ignore_default_query_set: bool = False,
    ):
        """
        创建或更新索引

        https://docs.meilisearch.com/reference/api/documents.html#add-or-replace-documents

        :param objs: id、对象、id列表、对象列表、QuerySet
        :param ignore_default_query_set: 忽略默认的query_set限制，默认为False
        :return:
        """
        if not isinstance(objs, list):
            # 将单个对象转换为列表
            objs = [objs]

        if isinstance(objs, QuerySet) and not ignore_default_query_set:
            # 限制QuerySet
            objs = objs & self.queryset

        if len(objs) > 0 and isinstance(objs[0], PK):
            if ignore_default_query_set:
                objs = self.model.objects.filter(pk__in=objs)
            else:
                objs = self.queryset.filter(pk__in=objs)

        if len(objs) == 0:
            return

        serializer = self.serializer_class(objs, many=True)
        data = serializer.data
        self.index.add_documents(data)

    def delete_index(
        self,
        ids: Model | PK | list[Model | PK] | QuerySet,
        ignore_default_query_set: bool = True,
    ):
        """
        删除索引

        https://docs.meilisearch.com/reference/api/documents.html#delete-documents-by-batch

        :param ids: 对象
        :param ignore_default_query_set: 忽略默认的query_set限制，默认为True
        :return:
        """
        if not isinstance(ids, list) and not isinstance(ids, QuerySet):
            # 将单个对象转换为列表
            ids = [ids]

        if isinstance(ids, QuerySet) and not ignore_default_query_set:
            # 限制QuerySet
            ids = ids & self.queryset

        if len(ids) > 0 and not isinstance(ids[0], PK):
            # 将对象列表转换为id列表
            ids = [i.pk for i in ids]

        if len(ids) == 0:
            return

        self.index.delete_documents(ids)

    def rebuild_index(self):
        """
        重建索引

        https://docs.meilisearch.com/reference/api/documents.html#delete-all-documents

        :return:
        """
        self.index.delete_all_documents()

        self.index.add_documents(
            self.serializer_class(
                self.queryset,
                many=True,
            ).data
        )

    def search(
        self,
        query: str,
        page: int = 1,
        hits_per_page: int = 20,
        filter: str | list | None = None,
        facets: list[str] | None = None,
        attributes_to_retrieve: list[str] | None = None,
        attributes_to_crop: list[str] | None = None,
        crop_length: int | None = None,
        crop_marker: str | None = None,
        attributes_to_highlight: list[str] | None = None,
        highlight_pre_tag: str | None = None,
        highlight_post_tag: str | None = None,
        show_match_positions: bool | None = None,
        sort: list[str] | None = None,
        matching_strategy: str | None = None,
    ) -> SearchResult:
        """
        搜索

        https://docs.meilisearch.com/reference/api/search.html

        :param filter:
        :param query: 关键词
        :param page:
        :param hits_per_page:
        :param filter:
        :param facets:
        :param attributes_to_retrieve:
        :param attributes_to_crop:
        :param crop_length:
        :param crop_marker:
        :param attributes_to_highlight:
        :param highlight_pre_tag:
        :param highlight_post_tag:
        :param show_match_positions:
        :param sort:
        :param matching_strategy:
        :return:
        """
        query_params = {
            "page": page,
            "hitsPerPage": hits_per_page,
        }
        filter and query_params.update({"filter": filter})
        facets and query_params.update({"facetsDistribution": facets})
        attributes_to_retrieve and query_params.update(
            {"attributesToRetrieve": attributes_to_retrieve}
        )
        attributes_to_crop and query_params.update(
            {"attributesToCrop": attributes_to_crop}
        )
        crop_length and query_params.update({"cropLength": crop_length})
        crop_marker and query_params.update({"cropMarker": crop_marker})
        attributes_to_highlight and query_params.update(
            {"attributesToHighlight": attributes_to_highlight}
        )
        highlight_pre_tag and query_params.update(
            {"highlightPreTag": highlight_pre_tag}
        )
        highlight_post_tag and query_params.update(
            {"highlightPostTag": highlight_post_tag}
        )
        show_match_positions and query_params.update(
            {"showMatchPositions": show_match_positions}
        )
        sort and query_params.update({"sort": sort})
        matching_strategy and query_params.update(
            {"matchingStrategy": matching_strategy}
        )

        return SearchResult(self.index.search(query, query_params))

    def search_with_request(
        self, query: str, request: Request, **kwargs
    ) -> SearchResult:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        return self.search(query, page=page, hits_per_page=page_size, **kwargs)

    def model_save_receiver(self, instance, **kwargs):
        self.upsert_index(instance)

    def model_delete_receiver(self, instance, **kwargs):
        self.delete_index(instance)
