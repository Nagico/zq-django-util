import importlib
from unittest.mock import patch

from django.test import override_settings
from rest_framework.test import APITestCase

from zq_django_util.utils import meili
from zq_django_util.utils.meili.constant.task import TaskStatus, TaskType
from zq_django_util.utils.meili.error import Error


class MeiliTestCase(APITestCase):
    @override_settings(
        MEILI_URL="http://localhost:7700",
        MEILI_MASTER_KEY="masterKey",
    )
    def setUp(self):
        self.patcher_meili = patch("meilisearch.Client")
        self.mock_meili = self.patcher_meili.start()

        importlib.reload(meili)

    def tearDown(self):
        self.patcher_meili.stop()

    def test_meili(self):
        self.assertTrue(meili.meili_client)
        self.mock_meili.assert_called_once_with(
            "http://localhost:7700",
            "masterKey",
        )


class MeiliUtilTestCase(APITestCase):
    def test_error(self):
        from zq_django_util.utils.meili.error import Error

        error = Error(
            {
                "message": "test",
                "errorCode": "test",
                "errorType": "auth",
                "errorLink": "test",
            }
        )
        self.assertEqual(error.message, "test")
        self.assertEqual(error.code, "test")
        self.assertEqual(error.type, "auth")
        self.assertEqual(error.link, "test")

    def test_exception(self):
        from zq_django_util.utils.meili.error import Error
        from zq_django_util.utils.meili.exceptions import (
            MeiliSearchTaskError,
            MeiliSearchTaskFail,
            MeiliSearchTaskTimeoutError,
        )

        error = Error(
            {
                "message": "test",
                "errorCode": "test",
                "errorType": "auth",
                "errorLink": "test",
            }
        )
        self.assertEqual(
            str(MeiliSearchTaskError("test")), "MeiliSearchTaskError, test"
        )
        self.assertEqual(
            str(MeiliSearchTaskTimeoutError("test")),
            "MeiliSearchTaskTimeoutError, test",
        )
        self.assertEqual(
            str(MeiliSearchTaskFail(error)), "MeiliSearchTaskPendingError, test"
        )

    def test_response(self):
        from zq_django_util.utils.meili.response import SearchResult

        response = {
            "hits": [
                {
                    "id": "test",
                    "title": "test",
                    "content": "test",
                    "created_at": "test",
                    "updated_at": "test",
                },
                {
                    "id": "test2",
                    "title": "test2",
                    "content": "test2",
                    "created_at": "test2",
                    "updated_at": "test2",
                },
            ],
            "page": 1,
            "hitsPerPage": 20,
            "totalPages": 5,
            "totalHits": 100,
            "processingTimeMs": 1,
            "query": "test",
        }

        search_result = SearchResult(response)

        self.assertEqual(search_result.page, 1)
        self.assertEqual(search_result.hits_per_page, 20)
        self.assertEqual(search_result.total_pages, 5)
        self.assertEqual(search_result.count, 100)
        self.assertEqual(search_result.processing_time_ms, 1)
        self.assertEqual(search_result.query, "test")
        self.assertEqual(len(search_result), 2)
        self.assertEqual(search_result[0].id, "test")
        self.assertEqual(search_result[0].title, "test")
        self.assertEqual(search_result[0].content, "test")
        self.assertEqual(search_result[0].created_at, "test")
        self.assertEqual(search_result[0].updated_at, "test")
        self.assertEqual(search_result[1]["id"], "test2")
        self.assertEqual(search_result[1]["title"], "test2")
        self.assertEqual(search_result[1]["content"], "test2")
        self.assertEqual(search_result[1]["created_at"], "test2")
        self.assertEqual(search_result[1]["updated_at"], "test2")

        for hit in search_result:
            self.assertEqual(hit.id, "test")
            self.assertEqual(hit.title, "test")
            self.assertEqual(hit.content, "test")
            self.assertEqual(hit.created_at, "test")
            self.assertEqual(hit.updated_at, "test")
            break

    def test_task(self):
        from zq_django_util.utils.meili.task import AsyncTask

        patcher_meili_task = patch("meilisearch.models.task.Task")
        mock_meili_task = patcher_meili_task.start()

        mock_meili_task.return_value.uid = "uid"
        mock_meili_task.return_value.index_uid = "index_uid"
        mock_meili_task.return_value.status = "enqueued"
        mock_meili_task.return_value.type = "documentAdditionOrUpdate"
        mock_meili_task.return_value.details = {}
        mock_meili_task.return_value.error = {
            "message": "test",
            "errorCode": "test",
            "errorType": "auth",
            "errorLink": "test",
        }

        mock_meili_task.return_value.duration = None
        mock_meili_task.return_value.enqueued_at = None
        mock_meili_task.return_value.started_at = None
        mock_meili_task.return_value.finished_at = None

        meili_task = mock_meili_task()

        task = AsyncTask(meili_task)

        self.assertEqual(task.uid, "uid")
        self.assertEqual(task.index_uid, "index_uid")
        self.assertEqual(task.status, TaskStatus.ENQUEUED)
        self.assertEqual(task.type, TaskType.DOCUMENT_ADDITION_OR_UPDATE)
        self.assertDictEqual(task.details, {})
        self.assertDictEqual(
            task.error.__dict__,
            Error(
                {
                    "message": "test",
                    "errorCode": "test",
                    "errorType": "auth",
                    "errorLink": "test",
                }
            ).__dict__,
        )
        self.assertFalse(task.is_processing)
        self.assertFalse(task.is_succeeded)
        self.assertFalse(task.is_failed)
        self.assertFalse(task.is_canceled)
        self.assertFalse(task.is_finished)
        self.assertTrue(task.is_enqueued)
