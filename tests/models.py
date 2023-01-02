from django.db import models

from zq_django_util.utils.user.models import AbstractUser


class AbstractTestModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = "tests"
        abstract = True


class User(AbstractUser, AbstractTestModel):
    openid = models.CharField(
        max_length=64, unique=True, verbose_name="微信openid"
    )

    class Meta:
        app_label = "tests"
        db_table = "te_user"
        ordering = ["-id"]
