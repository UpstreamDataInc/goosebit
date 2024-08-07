from fastapi import APIRouter

from goosebit.models import Hardware

router = APIRouter(prefix="/example_plugin")


@router.get("/graph")
async def example_graph():
    compat = await Hardware.all().prefetch_related("firmwares")
    series = []
    labels = []
    for c in compat:
        labels.append(f"{c.model}.{c.revision}")
        series.append(len(c.firmwares))

    return {"series": series, "labels": labels}
