from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str | None = None
    first_name: str
    last_name: str | None = None
    credits: int
    sub_end: datetime | None = None
    paid_refs_percent: int | None = None

    class Config:
        from_attributes = True

    @property
    def full_name(self):
        name = [self.first_name]
        if self.last_name:
            name.append(self.last_name)
        return ' '.join(name)