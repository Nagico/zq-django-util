import pytest


@pytest.fixture
def meili_client(mocker):
    mocker.patch("meilisearch.Client")
    patcher_meili = mocker.patch("zq_django_util.utils.meili")

    yield patcher_meili.meili_client

    mocker.stopall()
