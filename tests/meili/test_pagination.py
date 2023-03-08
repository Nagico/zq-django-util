import pytest
from django.core.paginator import EmptyPage

from zq_django_util.utils.meili.pagination import MeiliPaginator
from zq_django_util.utils.meili.response import SearchResult


def test_pagination():
    # Arrange
    search_result = SearchResult(
        {
            "hits": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "page": 1,
            "hitsPerPage": 10,
            "totalPages": 10,
            "totalHits": 100,
            "processingTimeMs": 1,
            "query": "test",
        }
    )
    paginator = MeiliPaginator(search_result, 10)
    # Act
    page = paginator.page(1)
    # Assert
    assert page.number == 1
    assert page.paginator == paginator
    assert len(page.object_list) == 10
    assert page.has_next() is True
    assert page.has_previous() is False
    assert page.has_other_pages() is True
    assert page.next_page_number() == 2
    with pytest.raises(EmptyPage):
        page.previous_page_number()
    assert page.start_index() == 1
    assert page.end_index() == 10
    assert page.paginator.count == 100
    assert page.paginator.num_pages == 10
    assert page.paginator.per_page == 10
