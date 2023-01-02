import importlib
import sys
from typing import Type
from unittest.mock import MagicMock, patch

import oss2
from django import VERSION
from django.core.exceptions import SuspiciousOperation
from django.core.files.temp import TemporaryFile
from django.test import override_settings
from django.utils.timezone import now
from rest_framework.test import APITestCase

from zq_django_util.utils.oss.backends import (
    OssFile,
    OssMediaStorage,
    OssStaticStorage,
    OssStorage,
)
from zq_django_util.utils.oss.exceptions import OssError


class OssStorageTestCase(APITestCase):
    access_key_id = "access_key_id"
    access_key_secret = "access_key_secret"
    bucket_name = "bucket"
    endpoint = "https://oss-cn-shanghai.aliyuncs.com"

    @override_settings(
        ALIYUN_OSS={
            "ACCESS_KEY_ID": access_key_id,
            "ACCESS_KEY_SECRET": access_key_secret,
            "ENDPOINT": endpoint,
            "BUCKET_NAME": bucket_name,
            "URL_EXPIRE_SECOND": 60 * 60 * 24 * 30,
            "TOKEN_EXPIRE_SECOND": 60,
            "MAX_SIZE_MB": 100,
        }
    )
    def setUp(self) -> None:
        self.patcher_auth = patch("oss2.Auth")
        self.mock_auth = self.patcher_auth.start()
        self.patcher_service = patch("oss2.Service")
        self.mock_service = self.patcher_service.start()
        self.patcher_bucket = patch("oss2.Bucket")
        self.mock_bucket = self.patcher_bucket.start()

        self.storage = OssStorage()
        self.storage.base_dir = "/base/"

    def tearDown(self) -> None:
        self.patcher_auth.stop()
        self.patcher_service.stop()
        self.patcher_bucket.stop()

    def test_init(self):
        self.mock_auth.assert_called_once_with(
            self.access_key_id, self.access_key_secret
        )
        self.mock_service.assert_called_once_with(
            self.mock_auth.return_value, self.endpoint
        )
        self.mock_bucket.assert_called_once_with(
            self.mock_auth.return_value, self.endpoint, self.bucket_name
        )
        self.mock_bucket.return_value.get_bucket_acl.assert_called_once()

    def mock_exc(self, exc_type: Type) -> oss2.exceptions.OssError:
        return exc_type(
            status=404,
            headers={},
            body=b"",
            details={
                "Code": str(exc_type),
            },
        )

    def test_init_no_bucket(self):
        self.mock_bucket.return_value.get_bucket_acl.side_effect = (
            self.mock_exc(oss2.exceptions.NoSuchBucket)
        )
        with self.assertRaises(SuspiciousOperation):
            OssStorage()

    def test__normalize_endpoint_no_protocol(self):
        endpoint = "oss-cn-shanghai.aliyuncs.com"
        self.assertEqual(
            self.storage._normalize_endpoint(endpoint),
            f"http://{endpoint}",
        )

    def test__get_key_name_file(self):
        self.storage.base_dir = "/base1/base2/"
        self.assertEqual(
            self.storage._get_key_name("file"),
            "base1/base2/file",
        )

        self.storage.base_dir = "/base1/base2"
        self.assertEqual(
            self.storage._get_key_name("file"),
            "base1/base2/file",
        )

        self.storage.base_dir = "base1/base2"
        self.assertEqual(
            self.storage._get_key_name("file"),
            "base1/base2/file",
        )

    def test__get_key_dir(self):
        self.assertEqual(
            self.storage._get_key_name("dir/"),
            "base/dir/",
        )

    def test__open(self):
        file = TemporaryFile()
        file.write(b"test")
        file.seek(0)
        file.content_length = 4
        file.request_id = "request_id"

        self.mock_bucket.return_value.get_object.return_value = file
        res = self.storage._open("file")

        self.mock_bucket.return_value.get_object.assert_called_once_with(
            "base/file"
        )
        self.assertEqual(res.read(), b"test")
        self.assertEqual(res.name, "base/file")

    def test__open_no_verify_copy(self):
        file = TemporaryFile()
        file.write(b"test")
        file.seek(0)
        file.content_length = None
        file.request_id = "request_id"

        self.mock_bucket.return_value.get_object.return_value = file
        res = self.storage._open("file")

        self.assertEqual(res.read(), b"test")

    def test__open_mode_invalid(self):
        with self.assertRaises(ValueError):
            self.storage._open("file", mode="invalid")

    def test__open_no_such_key(self):
        self.mock_bucket.return_value.get_object.side_effect = self.mock_exc(
            oss2.exceptions.NoSuchKey
        )
        with self.assertRaises(OssError):
            self.storage._open("file")

    def test__open_error(self):
        self.mock_bucket.return_value.get_object.side_effect = Exception()
        with self.assertRaises(OssError):
            self.storage._open("file")

    def test__save(self):
        content = b"test"
        res = self.storage._save("file", content)

        self.mock_bucket.return_value.put_object.assert_called_once_with(
            "base/file", content
        )
        self.assertEqual(res, "file")

    def test_create_dir(self):
        self.storage.create_dir("dir")

        self.mock_bucket.return_value.put_object.assert_called_once_with(
            "base/dir/", ""
        )

    def test_create_dir_with_slash(self):
        self.storage.create_dir("dir/dir/")

        self.mock_bucket.return_value.put_object.assert_called_once_with(
            "base/dir/dir/", ""
        )

    def test_exists(self):
        self.mock_bucket.return_value.object_exists.return_value = True
        self.assertTrue(self.storage.exists("file"))
        self.mock_bucket.return_value.object_exists.assert_called_once_with(
            "base/file"
        )

        self.mock_bucket.return_value.object_exists.return_value = False
        self.assertFalse(self.storage.exists("file"))
        self.mock_bucket.return_value.object_exists.assert_called_with(
            "base/file"
        )

    def test_get_file_meta(self):
        self.mock_bucket.return_value.get_object_meta.return_value = {
            "Content-Length": 4,
            "Content-Type": "text/plain",
            "Last-Modified": "2020-01-01 00:00:00",
        }
        res = self.storage.get_file_meta("file")

        self.mock_bucket.return_value.get_object_meta.assert_called_once_with(
            "base/file"
        )
        self.assertEqual(
            res, self.mock_bucket.return_value.get_object_meta.return_value
        )

    @patch("zq_django_util.utils.oss.backends.OssStorage.get_file_meta")
    def test_size(self, mock_meta: MagicMock):
        mock_meta.return_value.content_length = 4
        self.assertEqual(self.storage.size("file"), 4)
        mock_meta.assert_called_once_with("file")

    @patch("zq_django_util.utils.oss.backends.OssStorage.get_file_meta")
    def test_modified_time(self, mock_meta: MagicMock):
        time = now()
        mock_meta.return_value.last_modified = time.timestamp()
        self.assertEqual(
            self.storage.modified_time("file").timestamp(), time.timestamp()
        )

    @patch("zq_django_util.utils.oss.backends.OssStorage.get_file_meta")
    def test_get_modified_time(self, mock_meta: MagicMock):
        time = now()
        mock_meta.return_value.last_modified = time.timestamp()
        self.assertEqual(
            self.storage.get_modified_time("file").timestamp(), time.timestamp()
        )
        self.assertEqual(
            self.storage.get_modified_time("file").tzinfo, time.tzinfo
        )

    @override_settings(USE_TZ=False)
    @patch("zq_django_util.utils.oss.backends.OssStorage.get_file_meta")
    def test_get_modified_time_no_tz(self, mock_meta: MagicMock):
        time = now()
        mock_meta.return_value.last_modified = time.timestamp()
        self.assertEqual(
            self.storage.get_modified_time("file").timestamp(), time.timestamp()
        )
        self.assertIsNone(self.storage.get_modified_time("file").tzinfo)

    def test_content_type(self):
        self.mock_bucket.return_value.head_object.return_value.content_type = (
            "text/plain"
        )
        self.assertEqual(self.storage.content_type("file"), "text/plain")
        self.mock_bucket.return_value.head_object.assert_called_once_with(
            "base/file"
        )

    def test_listdir(self):
        class MockFile:
            def __init__(self, key: str):
                self.key = key

            def is_prefix(self):
                return self.key.endswith("/")

            def __eq__(self, other):
                return self.key == other.key or self.key == other

        self.mock_bucket.return_value.list_objects.return_value.object_list = [
            MockFile("base/dir/file"),
            MockFile("base/dir/dd/"),
            MockFile("base/dir/dd/ffile"),
        ]
        self.mock_bucket.return_value.list_objects.return_value.is_truncated = (
            False
        )

        res = self.storage.listdir("dir")
        self.mock_bucket.return_value.list_objects.assert_called_once_with(
            prefix="base/dir/",
            delimiter="/",
            marker="",
            max_keys=100,
            headers={},
        )
        self.assertEqual(res[0], ["base/dir/dd/"])
        self.assertEqual(res[1], ["base/dir/dd/ffile", "base/dir/file"])

    def test_listdir_dot(self):
        class MockFile:
            def __init__(self, key: str):
                self.key = key

            def is_prefix(self):
                return self.key.endswith("/")

            def __eq__(self, other):
                return self.key == other.key or self.key == other

        self.mock_bucket.return_value.list_objects.return_value.object_list = [
            MockFile("base/file"),
            MockFile("base/dd/"),
            MockFile("base/dd/ffile"),
        ]
        self.mock_bucket.return_value.list_objects.return_value.is_truncated = (
            False
        )

        self.storage.listdir(".")
        self.mock_bucket.return_value.list_objects.assert_called_once_with(
            prefix="base/",
            delimiter="/",
            marker="",
            max_keys=100,
            headers={},
        )

    def test_url_private(self):
        self.storage.bucket_acl = oss2.BUCKET_ACL_PRIVATE
        self.mock_bucket.return_value.sign_url.return_value = "url"

        self.assertEqual(self.storage.url("file"), "url")

    def test_url_public(self):
        self.storage.bucket_acl = oss2.BUCKET_ACL_PUBLIC_READ
        self.mock_bucket.return_value.sign_url.return_value = (
            "https:%2F%2Furl?token=token"
        )

        self.assertEqual(self.storage.url("file"), "https://url")

    def test_delete(self):
        self.storage.delete("file")
        self.mock_bucket.return_value.delete_object.assert_called_once_with(
            "base/file"
        )

    def test_delete_dir_without_slash(self):
        self.storage.delete_dir("dir")
        self.mock_bucket.return_value.delete_object.assert_called_once_with(
            "base/dir/"
        )

    def test_delete_dir_with_slash(self):
        self.storage.delete_dir("dir/")
        self.mock_bucket.return_value.delete_object.assert_called_once_with(
            "base/dir/"
        )


class OssOtherStorageTestCase(APITestCase):
    access_key_id = "access_key_id"
    access_key_secret = "access_key_secret"
    bucket_name = "bucket"
    endpoint = "https://oss-cn-shanghai.aliyuncs.com"

    @override_settings(
        ALIYUN_OSS={
            "ACCESS_KEY_ID": access_key_id,
            "ACCESS_KEY_SECRET": access_key_secret,
            "ENDPOINT": endpoint,
            "BUCKET_NAME": bucket_name,
            "URL_EXPIRE_SECOND": 60 * 60 * 24 * 30,
            "TOKEN_EXPIRE_SECOND": 60,
            "MAX_SIZE_MB": 100,
        }
    )
    def setUp(self) -> None:
        self.patcher_auth = patch("oss2.Auth")
        self.mock_auth = self.patcher_auth.start()
        self.patcher_service = patch("oss2.Service")
        self.mock_service = self.patcher_service.start()
        self.patcher_bucket = patch("oss2.Bucket")
        self.mock_bucket = self.patcher_bucket.start()

        self.storage = OssStorage()

    def tearDown(self) -> None:
        self.patcher_auth.stop()
        self.patcher_service.stop()
        self.patcher_bucket.stop()

    @override_settings(MEDIA_URL="/media/")
    def test_media(self):
        storage = OssMediaStorage()
        self.assertEqual(storage.base_dir, "/media/")

    @override_settings(STATIC_URL="/static/")
    def test_static(self):
        storage = OssStaticStorage()
        self.assertEqual(storage.base_dir, "/static/")


class OssFileTestCase(APITestCase):
    @patch("django.core.files.base.File.open")
    def test_open(
        self,
        mock_django_file_open: MagicMock,
    ):
        mock_storage = MagicMock(name="mock_storage")
        mock_file = MagicMock(name="mock_file")
        mock_file.closed = True
        oss_file = OssFile(mock_file, "file", mock_storage)
        oss_file.open()

        mock_storage.open.assert_called_once_with("file", "rb")
        mock_django_file_open.assert_called_once_with("rb")


class OssBackendImportTestCase(APITestCase):
    def setUp(self) -> None:
        if "zq_django_util.utils.oss.backends" in sys.modules:
            del sys.modules["zq_django_util.utils.oss.backends"]

        self.django_version_patcher = patch("django.VERSION")

    def tearDown(self) -> None:
        patch.stopall()

        if "zq_django_util.utils.oss.backends" in sys.modules:
            del sys.modules["zq_django_util.utils.oss.backends"]
        importlib.import_module("zq_django_util.utils.oss.backends")

    def test_dj3_import(self):
        version = VERSION[0]
        self.mock_django_version = self.django_version_patcher.start()
        self.mock_django_version.__getitem__.return_value = 3

        if version < 4:  # test django 3 import under actual env of django 3
            module = importlib.import_module(
                "zq_django_util.utils.oss.backends"
            )
            self.assertEqual(
                module.__name__, "zq_django_util.utils.oss.backends"
            )
        else:  # test django 3 import under actual env of django 4
            with self.assertRaises(ImportError):
                importlib.import_module("zq_django_util.utils.oss.backends")

    def test_dj4_import(self):
        version = VERSION[0]
        self.mock_django_version = self.django_version_patcher.start()
        self.mock_django_version.__getitem__.return_value = 4

        if version < 4:  # test django 4 import under actual env of django 3
            with self.assertRaises(ImportError):
                importlib.import_module("zq_django_util.utils.oss.backends")
        else:  # test django 4 import under actual env of django 4
            module = importlib.import_module(
                "zq_django_util.utils.oss.backends"
            )
            self.assertEqual(
                module.__name__, "zq_django_util.utils.oss.backends"
            )
