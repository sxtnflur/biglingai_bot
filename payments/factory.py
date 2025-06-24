from typing_extensions import Literal
from .base import PaymentData, AbstractPaymentService
from .yookassa import YooKassaServiceABC
from .prodamus import ProdamusServiceABC

PaymentMethod = Literal['yookassa']


class PaymentFactory:
    payment_methods_objs: dict[PaymentMethod, YooKassaServiceABC]

    def __init__(
            self,
            yookassa: YooKassaServiceABC | None
    ):
        self.yookassa = yookassa
        # self.prodamus = prodamus

        self.payment_methods_objs = {
            'yookassa': yookassa,
            # 'prodamus': prodamus
        }

    async def create_payment(self, payment_method: PaymentMethod,
                             amount: int, description: str,
                             save_payment_method_id: bool = True,
                             payment_method_id: str | None = None,
                             test: bool = False) -> PaymentData:
        # if payment_method == 'prodamus':
        #     return await self.payment_methods_objs[payment_method].create_payment(
        #         str(amount), description, test
        #     )
        return await self.payment_methods_objs[payment_method].create_payment(
            amount=amount, description=description, test=test,
            save_payment_method_id=save_payment_method_id,
            payment_method_id=payment_method_id
        )