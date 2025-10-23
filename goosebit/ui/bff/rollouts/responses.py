from typing import Any, Callable

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
    async def convert(
        cls, dt_query: DataTableRequest, query: QuerySet[Any], search_filter: Callable[[str], Any]
    ) -> "BFFRolloutsResponse":
        total_records = await query.count()
        if dt_query.search.value:
            query = query.filter(search_filter(dt_query.search.value))

        for column in dt_query.columns:
            query = query.filter(column.query)

        filtered_records = await query.count()

        if dt_query.order_query:
            query = query.order_by(dt_query.order_query)

        if dt_query.length is not None:
            query = query.limit(dt_query.length)

        rollouts = await query.offset(dt_query.start).all()
        data = [RolloutSchema.model_validate(r) for r in rollouts]

        return cls(data=data, draw=dt_query.draw, records_total=total_records, records_filtered=filtered_records)
