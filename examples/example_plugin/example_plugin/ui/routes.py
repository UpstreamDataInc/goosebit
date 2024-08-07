from fastapi import APIRouter
from fastapi.requests import Request

from goosebit.ui.nav import NAVIGATION
from goosebit.ui.templates import TEMPLATES

router = APIRouter(prefix="/example_plugin")


@router.get("/graph")
@NAVIGATION.add("Graph")
async def graph_ui(request: Request):
    return TEMPLATES.handler.TemplateResponse(request, "example_plugin/graph.html", context={"title": "Graph"})
