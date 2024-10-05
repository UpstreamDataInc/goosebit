from typing import Callable

from pydantic import BaseModel, Field
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from goosebit.schema.software import SoftwareSchema
from goosebit.ui.bff.common.requests import DataTableOrderDirection, DataTableRequest


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

        filtered_records = await query.count()

        if len(dt_query.order) > 0 and dt_query.order[0].name == "version":
            # ordering cannot be delegated to database as semantic versioning sorting is not supported
            software = await query.all()
            reverse = dt_query.order[0].dir == DataTableOrderDirection.DESCENDING
            software.sort(key=lambda s: s.parsed_version, reverse=reverse)

            # in-memory paging
            if dt_query.length is None:
                software = software[dt_query.start :]
            else:
                software = software[dt_query.start : dt_query.start + dt_query.length]

        else:
            # if no ordering is specified, database-side paging can be used
            if dt_query.length is not None:
                query = query.limit(dt_query.length)

            software = await query.offset(dt_query.start).all()

        data = [SoftwareSchema.model_validate(s) for s in software]

        return cls(data=data, draw=dt_query.draw, records_total=total_records, records_filtered=filtered_records)
