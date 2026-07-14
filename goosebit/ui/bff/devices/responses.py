from __future__ import annotations

from enum import IntEnum
from typing import Any, Callable

from pydantic import BaseModel, Field
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from goosebit.db.models import UpdateModeEnum, UpdateStateEnum
from goosebit.schema.devices import DeviceSchema
from goosebit.ui.bff.common.requests import DataTableRequest

# Integer-enum columns displayed as text: search the term against the enum names, not the column.
ENUM_SEARCH_COLUMNS: dict[str, type[IntEnum]] = {
    "last_state": UpdateStateEnum,
    "update_mode": UpdateModeEnum,
}


def _enum_search_query(name: str, enum_cls: type[IntEnum], value: str) -> Q:
    # Substring match on enum display names ("err" -> ERROR); no match -> empty __in -> no rows.
    value = value.casefold()
    matches = [int(member) for member in enum_cls if value in str(member).casefold()]
    return Q(**{f"{name}__in": matches})


class BFFDeviceResponse(BaseModel):
    data: list[DeviceSchema]
    draw: int
    records_total: int = Field(serialization_alias="recordsTotal")
    records_filtered: int = Field(serialization_alias="recordsFiltered")

    @classmethod
    async def convert(
        cls, dt_query: DataTableRequest, query: QuerySet[Any], search_filter: Callable[[str], Any]
    ) -> "BFFDeviceResponse":
        total_records = await query.count()
        if dt_query.search.value:
            query = query.filter(search_filter(dt_query.search.value))

        for column in dt_query.columns:
            enum_cls = ENUM_SEARCH_COLUMNS.get(column.name)
            if enum_cls is not None and column.search.value is not None:
                column_query = _enum_search_query(column.name, enum_cls, column.search.value)
            else:
                column_query = column.query
            query = query.filter(column_query)

        filtered_records = await query.count()

        if dt_query.order_query:
            query = query.order_by(dt_query.order_query)

        if dt_query.length is not None:
            query = query.limit(dt_query.length)

        devices = await query.offset(dt_query.start).all()
        data = [DeviceSchema.model_validate(d) for d in devices]

        return cls(data=data, draw=dt_query.draw, records_total=total_records, records_filtered=filtered_records)
