from typing import Optional

from ninja import Schema


class ParserSchema(Schema):
    meta: dict
    header: str
    left: str
    right: str
    ok: Optional[bool]
