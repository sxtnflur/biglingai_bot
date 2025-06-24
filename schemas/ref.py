from pydantic import BaseModel


class UserRefInfo(BaseModel):
    ref_link: str
    count_refs: int
    count_paid_refs: int

    paid_refs_percent: int | None = None
    paid_refs_balance: int | None = None
    special_ref_on_moderation: bool = False


class DecodedRefInfo(BaseModel):
    invited_by_id: int