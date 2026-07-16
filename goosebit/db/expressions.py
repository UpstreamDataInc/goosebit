from typing import Any

from pypika_tortoise.context import SqlContext
from pypika_tortoise.terms import Function as PypikaFunction
from tortoise.expressions import Function


class _PipeConcat(PypikaFunction):
    def __init__(self, *terms: Any, **kwargs: Any) -> None:
        # parent requires a name; get_function_sql never emits it
        super().__init__("", *terms, **kwargs)

    def get_function_sql(self, ctx: SqlContext) -> str:
        return "({})".format(" || ".join(self.get_arg_sql(arg, ctx) for arg in self.args))


class StrConcat(Function):
    """Concatenation via the || operator; CONCAT() needs SQLite >= 3.44."""

    database_func = _PipeConcat
