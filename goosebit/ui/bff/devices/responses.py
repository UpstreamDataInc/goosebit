from __future__ import annotations

from typing import Callable

from pydantic import BaseModel, Field
from tortoise.queryset import QuerySet

from goosebit.schema.devices import DeviceSchema
from goosebit.ui.bff.common.requests import DataTableRequest


class BFFDeviceResponse(BaseModel):
    data: list[DeviceSchema]
    draw: int
    records_total: int = Field(serialization_alias="recordsTotal")
    records_filtered: int = Field(serialization_alias="recordsFiltered")

    @classmethod
    async def convert(cls, dt_query: DataTableRequest, query: QuerySet, search_filter: Callable):
        total_records = await query.count()
        if dt_query.search.value:
            query = query.filter(search_filter(dt_query.search.value))

        if dt_query.order_query:
            query = query.order_by(dt_query.order_query)

        filtered_records = await query.count()
        devices = await query.offset(dt_query.start).limit(dt_query.length).all()
        data = [DeviceSchema.model_validate(d) for d in devices]

        return cls(data=data, draw=dt_query.draw, records_total=total_records, records_filtered=filtered_records)
