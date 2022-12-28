"""
将错误码表格中 code、详情、备注、状态码、ResponseType 五列
(无需拷贝 00000 的三行)拷贝至 error.ini 文件中，运行该程序更新 ResponseType
"""
program_path = "../zq_django_util/response/__init__.py"


def prepare_context() -> (str, str):
    with open(program_path, "r", encoding="utf-8") as f:
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


def write_file(above: str, content: list[str], below: str) -> None:
    lines = [
        "@unique",
        "class ResponseType(ResponseTypeEnum):",
        '    """API状态类型"""',
        "",
    ]
    lines += [f"    {line}" for line in content]

    with open(program_path, "w", encoding="utf-8") as f:
        f.write(above)
        f.write("\n".join(lines) + "\n")
        f.write(below)


def get_new_content() -> list[str]:
    content = ['Success = ("00000", "", 200)']
    with open("error.ini", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            tmp = line.strip("\n").split("\t")
            code = tmp[0]
            detail = tmp[1]
            status = int(tmp[3])
            name = tmp[4]
            content.append(f'{name} = ("{code}", "{detail}", {status})')

    return content


if __name__ == "__main__":
    st, ed = prepare_context()
    write_file(st, get_new_content(), ed)
