import random
import time
from typing import Tuple


def split_file_name(file_name: str) -> Tuple[str, str]:
    """
    获取文件名与扩展名

    :param file_name: 文件全名

    :return: 文件名，扩展名
    """
    if "." in file_name:  # 文件存在扩展名
        ext = file_name.split(".")[-1]  # 文件扩展名
        name = ".".join(file_name.split(".")[0:-1])
    else:
        ext = ""
        name = file_name

    return name, ext


def get_random_name(file_name: str) -> str:
    """
    获取随机文件名

    :param file_name: 原文件名

    :return:
    """
    name, ext = split_file_name(file_name)

    new_name = time.strftime("%Y%m%d%H%M%S")  # 定义文件名，年月日时分秒随机数
    new_name = (
        new_name
        + "_%04d" % random.randint(0, 10000)
        + (("." + ext) if ext != "" else "")
    )

    return new_name

