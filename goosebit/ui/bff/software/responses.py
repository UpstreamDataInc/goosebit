from typing import Callable

from pydantic import BaseModel, Field
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from goosebit.schema.software import SoftwareSchema
from goosebit.ui.bff.common.requests import DataTableRequest


class BFFSoftwareResponse(BaseModel):
    data: list[SoftwareSchema]
    draw: int
    records_total: int = Field(serialization_alias="recordsTotal")
    records_filtered: int = Field(serialization_alias="recordsFiltered")

    @classmethod
    async def convert(cls, dt_query: DataTableRequest, query: QuerySet, search_filter: Callable, alt_filter: Q):
        total_records = await query.count()
        query = query.filter(alt_filter)
        if dt_query.search.value:
            query = query.filter(search_filter(dt_query.search.value))

        if dt_query.order_query:
            query = query.order_by(dt_query.order_query)

        filtered_records = await query.count()

        query = query.offset(dt_query.start)

        if not dt_query.length == 0:
            query = query.limit(dt_query.length)

        software = await query.all()
        data = [SoftwareSchema.model_validate(s) for s in software]

        return cls(data=data, draw=dt_query.draw, records_total=total_records, records_filtered=filtered_records)
