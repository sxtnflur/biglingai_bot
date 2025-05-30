from pydantic import BaseModel


class CreditsPack(BaseModel):
    id: int
    credits: int
    price: int
    sale: int | None = None


class Sub(BaseModel):
    id: int
    name: str
    days: int
    price: int
    sale: int | None = None