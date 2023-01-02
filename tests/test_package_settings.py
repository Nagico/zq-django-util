from django.core.signals import setting_changed
from django.test import override_settings
from rest_framework.test import APITestCase

from zq_django_util.utils.package_settings import PackageSettings


class MockTestSetting(PackageSettings):
    setting_name = "TEST_SETTING"
    DEFAULTS = {
        "STR": "STR",
        "INT": 1,
        "FLOAT": 0.1,
        "BOOL": True,
        "LIST": ["STR", 1, 0.1, True],
        "DICT": {
            "STR": "STR",
            "INT": 1,
            "FLOAT": 0.1,
            "BOOL": True,
        },
        "IMPORT_STR": "zq_django_util.utils.package_settings.PackageSettings",
        "IMPORT_LIST": [
            "zq_django_util.utils.package_settings.PackageSettings",
            "zq_django_util.utils.package_settings.PackageSettings",
        ],
        "IMPORT_DICT": {
            "key1": "zq_django_util.utils.package_settings.PackageSettings",
            "key2": "zq_django_util.utils.package_settings.PackageSettings",
        },
    }
    IMPORT_STRINGS = [
        "IMPORT_STR",
        "IMPORT_LIST",
        "IMPORT_DICT",
    ]


test_settings = MockTestSetting()

setting_changed.connect(test_settings.reload_package_settings)


class PackageSettingsTestCase(APITestCase):
    def test_default_value(self):
        self.assertEqual(test_settings.STR, "STR")
        self.assertEqual(test_settings.INT, 1)
        self.assertEqual(test_settings.FLOAT, 0.1)
        self.assertEqual(test_settings.BOOL, True)
        self.assertEqual(test_settings.LIST, ["STR", 1, 0.1, True])
        self.assertEqual(
            test_settings.DICT,
            {
                "STR": "STR",
                "INT": 1,
                "FLOAT": 0.1,
                "BOOL": True,
            },
        )

    def test_import_value(self):
        module = PackageSettings
        self.assertEqual(test_settings.IMPORT_STR, module)
        self.assertEqual(test_settings.IMPORT_LIST, [module, module])
        self.assertEqual(
            test_settings.IMPORT_DICT,
            {
                "key1": module,
                "key2": module,
            },
        )

    def test_override_value(self):
        with override_settings(
            TEST_SETTING={
                "STR": "STR2",
                "INT": 2,
                "FLOAT": 0.2,
                "BOOL": False,
                "LIST": ["STR2", 2, 0.2, False],
                "DICT": {
                    "STR": "STR2",
                    "INT": 2,
                    "FLOAT": 0.2,
                    "BOOL": False,
                },
                "IMPORT_STR": "zq_django_util.utils.package_settings.PackageSettings",
                "IMPORT_LIST": [
                    "zq_django_util.utils.package_settings.PackageSettings",
                    "zq_django_util.utils.package_settings.PackageSettings",
                ],
                "IMPORT_DICT": {
                    "key1": "zq_django_util.utils.package_settings.PackageSettings",
                    "key2": "zq_django_util.utils.package_settings.PackageSettings",
                },
            }
        ):
            self.assertEqual(test_settings.STR, "STR2")
            self.assertEqual(test_settings.INT, 2)
            self.assertEqual(test_settings.FLOAT, 0.2)
            self.assertEqual(test_settings.BOOL, False)
            self.assertEqual(test_settings.LIST, ["STR2", 2, 0.2, False])
            self.assertEqual(
                test_settings.DICT,
                {
                    "STR": "STR2",
                    "INT": 2,
                    "FLOAT": 0.2,
                    "BOOL": False,
                },
            )
            module = PackageSettings
            self.assertEqual(test_settings.IMPORT_STR, module)
            self.assertEqual(test_settings.IMPORT_LIST, [module, module])
            self.assertEqual(
                test_settings.IMPORT_DICT,
                {
                    "key1": module,
                    "key2": module,
                },
            )
