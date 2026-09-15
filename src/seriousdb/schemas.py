from typing import Annotated

from pydantic import BaseModel, Field

KeyField = Annotated[str, Field(description="The key associated with the value.", examples=["name"])]
ValueField = Annotated[str, Field(description="The value associated with the key.", examples=["Alice"])]


class KeyRequest(BaseModel):
    key: KeyField
    value: ValueField


class KeyQuery(BaseModel):
    key: KeyField