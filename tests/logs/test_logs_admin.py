from django.contrib.auth import get_user_model
from django.test import override_settings
from model_bakery import baker
from rest_framework.test import APITestCase

from zq_django_util.logs.admin import RequestLogAdmin
from zq_django_util.logs.models import ExceptionLog, RequestLog

User = get_user_model()


class RequestLogAdminTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin", password="admin"
        )
        self.client.login(username="admin", password="admin")

        baker.make(RequestLog, _quantity=10)
        baker.make(ExceptionLog, _quantity=10)

    def test_request_log_admin(self):
        response = self.client.get("/admin/logs/requestlog/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cl"].result_count, 20)

    def test_request_log_admin_export_select(self):
        response = self.client.post(
            "/admin/logs/requestlog/",
            {
                "action": "export_as_csv",
                "_selected_action": [1, 2, 3],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"],
            "attachment; filename=logs.requestlog.csv",
        )

    def test_request_log_admin_object(self):
        response = self.client.get("/admin/logs/requestlog/1/change/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["object_id"], "1")

    def test_request_log_admin_object_export(self):
        response = self.client.get(
            "/admin/logs/requestlog/1/change/?export=true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"],
            "attachment; filename=logs.requestlog.csv",
        )

    def test_request_log_api_admin_performance(self):
        response = self.client.get(
            "/admin/logs/requestlog/?api_performance=slow"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cl"].result_count, 0)

        response = self.client.get(
            "/admin/logs/requestlog/?api_performance=fast"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cl"].result_count, 0)

    @override_settings(
        DRF_LOGGER={
            "ADMIN_SLOW_API_ABOVE": 0.1,
        }
    )
    def test_ADMIN_SLOW_API_ABOVE_error(self):
        with self.assertRaises(
            ValueError,
            msg="DRF_LOGGER__ADMIN_SLOW_API_ABOVE must be an integer.",
        ):
            self.client.get("/admin/logs/requestlog/?api_performance=slow")

    @override_settings(
        DRF_LOGGER={
            "ADMIN_TIMEDELTA": 1,
        }
    )
    def test_request_log_admin_add_on_time(self):
        admin = RequestLogAdmin(RequestLog, None)
        obj = RequestLog.objects.first()
        self.assertIsNotNone(admin.added_on_time(obj))
