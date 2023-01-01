from typing import TypedDict


class TokenVO(TypedDict, total=True):
    id: int
    username: str
    access: str
    refresh: str
