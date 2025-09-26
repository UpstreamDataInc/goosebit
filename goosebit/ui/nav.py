from typing import Any, Callable

from pydantic import BaseModel


class NavigationItem(BaseModel):
    function: str
    text: str
    permissions: list[str] | None
    show: bool


class Navigation:
    def __init__(self) -> None:
        self.items: list[NavigationItem] = []

    def route(
        self, text: str, permissions: list[str] | None = None, show: bool = True
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.items.append(NavigationItem(function=func.__name__, text=text, permissions=permissions, show=show))
            return func

        return decorator

    def get(self) -> list[NavigationItem]:
        return self.items


nav = Navigation()
