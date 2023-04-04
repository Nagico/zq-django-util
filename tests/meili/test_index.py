from unittest import mock

from zq_django_util.utils.meili.index import BaseIndex


class UserIndex(BaseIndex):
    index_uid = "users"
    primary_key = "id"

    searchable_attributes = ["title", "content"]
    displayed_attributes = ["title", "content"]
    ranking_rules = [
        "typo",
        "words",
        "proximity",
        "attribute",
        "wordsPosition",
        "exactness",
    ]
    stop_words = ["the", "a", "an"]
    synonyms = {"wolverine": ["xmen", "logan"]}
    filterable_attributes = ["title"]
    sortable_attributes = ["title"]
    distinct_attribute = "title"
    max_values_per_facet = 10
    max_total_hits = 100


def test_index_settings(meili_client):
    UserIndex.update_settings = mock.Mock()

    UserIndex()

    UserIndex.update_settings.assert_called_once()

    assert UserIndex.update_settings.call_args[0][0] == {
        "searchableAttributes": ["title", "content"],
        "displayedAttributes": ["title", "content"],
        "rankingRules": [
            "typo",
            "words",
            "proximity",
            "attribute",
            "wordsPosition",
            "exactness",
        ],
        "stopWords": ["the", "a", "an"],
        "synonyms": {"wolverine": ["xmen", "logan"]},
        "filterableAttributes": ["title"],
        "sortableAttributes": ["title"],
        "distinctAttribute": "title",
        "faceting": {"maxValuesPerFacet": 10},
        "pagination": {"maxTotalHits": 100},
    }
