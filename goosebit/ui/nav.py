from pydantic import BaseModel


class NavigationItem(BaseModel):
    function: str
    text: str
    permissions: list[str]


class Navigation:
    def __init__(self):
        self.items = []

    def route(self, text: str, permissions: list[str] | None = None):
        def decorator(func):
            self.items.append(NavigationItem(function=func.__name__, text=text, permissions=permissions))
            return func

        return decorator

    def get(self):
        return self.items


nav = Navigation()
