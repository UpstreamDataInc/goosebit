from pydantic import RootModel


class SoftwareDeleteRequest(RootModel[list[int]]):
    pass
