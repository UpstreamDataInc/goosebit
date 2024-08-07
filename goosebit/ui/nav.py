class Navigation:
    def __init__(self):
        self.items = []

    def add(self, text: str, permissions: str = None):
        def decorator(func):
            self.items.append({"function": func.__name__, "text": text, "permissions": permissions})
            return func

        return decorator


NAVIGATION = Navigation()
