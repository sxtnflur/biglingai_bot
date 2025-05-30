from pydantic import BaseModel


class UserRefInfo(BaseModel):
    ref_link: str
    count_refs: int
    count_paid_refs: int
    got_credits_from_refs: int
    credits_for_ref: int = 50
    credits_for_paid_ref: int = 1000

    paid_refs_percent: int | None = None
    paid_refs_balance: int | None = None
    special_ref_on_moderation: bool = False


class DecodedRefInfo(BaseModel):
    invited_by_id: int
    credits: int | None = None