from model_bakery import baker
from rest_framework.test import APITestCase

from zq_django_util.logs.models import ExceptionLog, RequestLog


class ModelTestCase(APITestCase):
    def test_request_log_model(self):
        request = baker.prepare(RequestLog)
        self.assertEqual(request.__str__(), request.ip)

    def test_exception_log_model(self):
        exception = baker.prepare(ExceptionLog)
        self.assertEqual(exception.__str__(), exception.exception_type)
