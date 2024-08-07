from fastapi import APIRouter

from goosebit.models import Hardware

router = APIRouter(prefix="/example_plugin")


@router.get("/graph")
async def example_graph():
    compat = await Hardware.all().prefetch_related("devices")
    series = []
    labels = []
    for c in compat:
        labels.append(f"{c.model}.{c.revision}")
        series.append(len(c.devices))

    return {"series": series, "labels": labels}
