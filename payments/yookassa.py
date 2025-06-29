import json
import abc
import uuid
from yookassa import Configuration, Payment
from .base import AbstractPaymentService, PaymentData
from config import settings


class YooKassaServiceABC(AbstractPaymentService):
    @abc.abstractmethod
    def __init__(
            self,
            shop_id: str = settings.YOOKASSA_SHOP_ID,
            api_token: str = settings.YOOKASSA_API_KEY
    ): pass


class YooKassaService(YooKassaServiceABC):
    def __init__(
            self,
            shop_id: str = settings.YOOKASSA_SHOP_ID,
            api_token: str = settings.YOOKASSA_API_KEY
    ):
        Configuration.account_id = shop_id
        Configuration.secret_key = api_token

    async def create_payment(
            self,
            amount: int,
            description: str,
            save_payment_method_id: bool = True,
            payment_method_id: str | None = None,
            test: bool = False
    ) -> PaymentData:
        data = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "description": description,
            "receipt": {
                "customer": {
                    "full_name": "Иванов Иван Иванович",
                    "phone": "79000000000"
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": amount,
                            "currency": "RUB"
                        },
                        "vat_code": "2",
                        "payment_mode": "full_prepayment",
                        "payment_subject": "commodity"
                    }
                ]
            },
            "test": test
        }
        if payment_method_id:
            data.update(payment_method_id=payment_method_id)
        elif save_payment_method_id:
            data.update(save_payment_method_id=save_payment_method_id)

        payment = await Payment.create(data)

        payment_data = json.loads(payment.json())
        payment_id = payment_data['id']
        payment_url = (payment_data['confirmation'])['confirmation_url']
        return PaymentData(
            id=payment_id, url=payment_url
        )

    async def create_auto_payment(
            self,
            amount: int,
            description: str,
            payment_method_id: str,
            test: bool = False
    ) -> str:
        data = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "description": description,
            "receipt": {
                "customer": {
                    "full_name": "Иванов Иван Иванович",
                    "phone": "79000000000"
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": amount,
                            "currency": "RUB"
                        },
                        "vat_code": "2",
                        "payment_mode": "full_prepayment",
                        "payment_subject": "commodity"
                    }
                ]
            },
            "payment_method_id": payment_method_id,
            "test": test
        }

        payment = await Payment.create(data)

        payment_data = json.loads(payment.json())
        return payment_data['id']

    async def cancel_payment(self, payment_id: str):
        return await Payment.cancel(payment_id)
