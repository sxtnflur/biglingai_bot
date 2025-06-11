from schemas.subs import CreditsPack, Sub


class SubsService:
    def get_credits_packs(self):
        return [
            CreditsPack(
                id=1, credits=50, price=490, sale=None
            ),
            CreditsPack(
                id=2, credits=200, price=990, sale=10
            ),
            CreditsPack(
                id=3, credits=500, price=1490, sale=20
            )
        ]

    def get_credits_pack_by_id(self, id: int):
        return self.get_credits_packs()[id-1]

    def get_subs(self):
        return [
            Sub(
                id=1, name='Турист', days=1, price=49
            ),
            Sub(
                id=2, name='Лингвист', days=30, price=190
            ),
            Sub(
                id=4, name='Носитель', days=90, price=490
            )
        ]

    def get_sub(self, id: int):
        return self.get_subs()[id-1]