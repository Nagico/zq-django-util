"""
将错误码表格中 code、详情、备注、状态码、ResponseType 五列
(无需拷贝 00000 的三行)拷贝至 error.ini 文件中，运行该程序更新 ResponseType
"""


def prepare_context(path: str) -> (str, str):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    above = []
    below = []
    above_finished = False
    below_started = False

    for line in lines:
        if not above_finished:
            above.append(line)

        if not above_finished and line == "# region ResponseType\n":
            above_finished = True
        if above_finished and line == "# endregion\n":
            below_started = True

        if below_started:
            below.append(line)

    return "".join(above), "".join(below)


def write_file(
    path: str, above: str, content: list[tuple[str, str]], below: str
) -> None:
    if path.endswith("py"):
        lines = [
            "@unique",
            "class ResponseType(ResponseTypeEnum):",
            '    """API状态类型"""',
            "",
        ]
        lines += [f"    {line[0]}{line[1]}" for line in content]
    elif path.endswith("pyi"):
        lines = [
            "class ResponseType(ResponseTypeEnum):",
        ]
        lines += [f"    {line[0]}..." for line in content]
    else:
        raise ValueError("path must be a python file")

    with open(path, "w", encoding="utf-8") as f:
        f.write(above)
        f.write("\n".join(lines) + "\n")
        f.write(below)


def get_new_content() -> list[tuple[str, str]]:
    content = [("Success = ", '("00000", "", 200)')]
    with open("error.ini", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            tmp = line.strip("\n").split("\t")
            code = tmp[0]
            detail = tmp[1]
            status = int(tmp[3])
            name = tmp[4]
            content.append((f"{name} = ", f'("{code}", "{detail}", {status})'))

    return content


def main():
    py_path = "../../zq_django_util/response/__init__.py"

    # read
    py_st, py_ed = prepare_context(py_path)

    # parse
    content = get_new_content()

    # write
    write_file(py_path, py_st, content, py_ed)


if __name__ == "__main__":
    main()
