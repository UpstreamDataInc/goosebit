from fastapi import APIRouter
from fastapi.requests import Request

from goosebit.ui.templates import templates

router = APIRouter(prefix="/example_plugin")


@router.get("/graph")
async def firmware_ui(request: Request):
    return templates.TemplateResponse(request, "graph.html", context={"title": "Graph"})
