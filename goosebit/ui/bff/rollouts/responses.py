from typing import Callable

from pydantic import BaseModel, Field
from tortoise.queryset import QuerySet

from goosebit.schema.rollouts import RolloutSchema
from goosebit.ui.bff.common.requests import DataTableRequest


class BFFRolloutsResponse(BaseModel):
    data: list[RolloutSchema]
    draw: int
    records_total: int = Field(serialization_alias="recordsTotal")
    records_filtered: int = Field(serialization_alias="recordsFiltered")

    @classmethod
    async def convert(cls, dt_query: DataTableRequest, query: QuerySet, search_filter: Callable):
        total_records = await query.count()
        if dt_query.search.value:
            query = query.filter(search_filter(dt_query.search.value))

        filtered_records = await query.count()

        if dt_query.order_query:
            query = query.order_by(dt_query.order_query)

        if dt_query.length is not None:
            query = query.limit(dt_query.length)

        rollouts = await query.offset(dt_query.start).all()
        data = [RolloutSchema.model_validate(r) for r in rollouts]

        return cls(data=data, draw=dt_query.draw, records_total=total_records, records_filtered=filtered_records)
