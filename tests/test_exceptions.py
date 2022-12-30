from django.test import TestCase, override_settings

from zq_django_util.exceptions import ApiException
from zq_django_util.response import ResponseType


class ApiExceptionTestCase(TestCase):
    EID_REX = r"[0-9a-z]{6}"

    def test_gen_exp_id(self):
        eid = ApiException.get_exp_id()
        self.assertRegex(eid, f"^{self.EID_REX}$")

    def test_get_exp_info(self):
        msg = "msg"
        try:
            raise ValueError(msg)
        except ValueError:
            info = ApiException.get_exception_info()
            self.assertEqual(info["type"], "<class 'ValueError'>")
            self.assertEqual(info["msg"], msg)
            self.assertRegex(
                info["info"], r"    raise ValueError\(msg\)\nValueError: msg$"
            )
            self.assertRegex(
                info["stack"][-1], r'"stack": traceback.format_stack()'
            )

    @override_settings(DEBUG=True)
    def test_exception_data_debug(self):
        data = {"a": 1}

        exc = ApiException(ResponseType.ServerError)
        exc.exc_data = data

        res = exc.exception_data

        self.assertEqual(res["eid"], exc.eid)
        self.assertEqual(res["time"], exc.time)
        self.assertDictEqual(res["exception"], data)

    @override_settings(DEBUG=False)
    def test_exception_data_not_debug(self):
        data = {"a": 1}

        exc = ApiException(ResponseType.ServerError)
        exc.exc_data = data

        res = exc.exception_data

        self.assertEqual(res["eid"], exc.eid)
        self.assertEqual(res["time"], exc.time)
        self.assertNotIn("exception", res)

    def test_inner_exception(self):
        inner = ValueError("inner msg")
        exc = ApiException(ResponseType.ServerError, inner=inner)
        self.assertEqual(exc.inner, inner)

    # region response type
    def test_response_type_not_record_default(self):
        exc = ApiException(ResponseType.NotLogin)
        self.assertEqual(exc.response_type, ResponseType.NotLogin)
        self.assertFalse(exc.record)

    def test_response_type_not_record_force(self):
        exc = ApiException(ResponseType.ServerError, record=False)
        self.assertEqual(exc.response_type, ResponseType.ServerError)
        self.assertFalse(exc.record)

    def test_response_type_record_default(self):
        exc = ApiException(ResponseType.ServerError)
        self.assertEqual(exc.response_type, ResponseType.ServerError)
        self.assertTrue(exc.record)

    def test_response_type_record_force(self):
        exc = ApiException(ResponseType.NotLogin, record=True)
        self.assertEqual(exc.response_type, ResponseType.NotLogin)
        self.assertTrue(exc.record)

    # endregion

    # region msg
    def test_msg_not_record_default(self):
        exc = ApiException(ResponseType.NotLogin)
        self.assertEqual(exc.msg, ResponseType.NotLogin.detail)

    def test_msg_not_record_custom(self):
        msg = "custom"

        exc = ApiException(ResponseType.NotLogin, msg=msg)
        self.assertEqual(exc.msg, msg)

    def test_msg_record_default(self):
        exc = ApiException(ResponseType.ServerError)
        self.assertRegex(
            exc.msg, f"^{ApiException.RECORD_MSG_TEMPLATE}{self.EID_REX}$"
        )

    def test_msg_record_custom(self):
        msg = "custom"

        exc = ApiException(ResponseType.ServerError, msg=msg)
        self.assertRegex(
            exc.msg,
            f"^{ApiException.RECORD_MSG_TEMPLATE}{self.EID_REX}, {msg}$",
        )

    # endregion

    # region detail
    def test_detail_not_record_default(self):
        exc = ApiException(ResponseType.NotLogin)
        self.assertEqual(exc.detail, ResponseType.NotLogin.detail)

    def test_detail_not_record_custom(self):
        detail = "custom"

        exc = ApiException(ResponseType.NotLogin, detail=detail)
        self.assertEqual(exc.detail, detail)

    def test_detail_record_default(self):
        exc = ApiException(ResponseType.ServerError)
        self.assertRegex(
            exc.detail, f"^{ResponseType.ServerError.detail}, {self.EID_REX}$"
        )

    def test_detail_record_custom(self):
        detail = "custom"

        exc = ApiException(ResponseType.ServerError, detail=detail)
        self.assertRegex(exc.detail, f"^{detail}, {self.EID_REX}$")

    # endregion

    def test_response_data(self):
        try:
            inner = ValueError("inner msg")
            raise ApiException(
                ResponseType.LoginFailed,
                msg="msg",
                detail="detail",
                inner=inner,
                record=True,
            )
        except ApiException as e:
            response = e.response_data
            self.assertEqual(response["code"], ResponseType.LoginFailed.code)
            self.assertEqual(response["msg"], e.msg)
            self.assertEqual(response["detail"], e.detail)
            self.assertDictEqual(response["data"], e.exception_data)
