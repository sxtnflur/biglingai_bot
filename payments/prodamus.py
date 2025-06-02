import abc
from hashlib import sha256
from hmac import new
from aiohttp import ClientSession
import uuid
from .base import AbstractPaymentService, PaymentData


class ProdamusOrder:
    def __init__(
            self,
            pay_url: str,
            secret_key: str,
            products=None,
            data=None
    ) -> None:
        self.__pay_url: str = pay_url
        self.__secret_key: str = secret_key

        true_data = self.__successful_data(data)
        true_products = self.__successful_products(products)
        if true_data[0] and true_products[0]:
            self.URL = self.__create_order_url(products, data)

        elif not (true_data[0]):
            raise true_data[1]

        else:
            raise true_products[1]

    async def create_pay_link(self) -> str:
        async with ClientSession() as session:
            resp = await session.get(self.URL)
            if resp.status == 200:
                return await resp.text()
            else:
                raise ConnectionError(f"Server error {resp.status}")

    def get_sign(self) -> str:
        try:
            return self.sign
        except:
            raise KeyError("Sign еще не сформирован")

    def __create_order_url(self, products, data) -> str:
        products_url = "?" + "&".join(
            [f"products[0][{i}]={products[i]}" for i in products]
        )
        data_url = "&" + "&".join([f"{i}={data[i]}" for i in data])
        self.__create_signature(data, products)
        return (
            f"https://{self.__pay_url}/"
            + products_url
            + data_url
            + "&do=link"
            + f"&singature={self.sign}"
        )

    def __successful_products(self, products) -> tuple[bool, Exception | None]:

        true_products = {
            "price": [str, float],
            "quantity": [str, int],
            "name": [str],
        }
        for i in true_products:
            if i not in products:
                return False, TypeError(f"Not found {i} for order")

            if type(products[i]) not in true_products[i]:
                return False, TypeError(f"Not correct type for {i}")

            return True, None

    def __successful_data(self, data) -> tuple[bool, Exception | None]:
        return True, None

    def __create_signature(self, data, products):

        data.update(products)

        self.sign = new(
            self.__secret_key.encode(), str(data).encode(), sha256
        ).hexdigest()


class ProdamusServiceABC(AbstractPaymentService):
    @abc.abstractmethod
    def __init__(self, pay_url: str, secret_key: str):
        ...


class ProdamusService(ProdamusServiceABC):
    def __init__(self, pay_url: str, secret_key: str):
        self.__pay_url = pay_url
        self.__secret_key = secret_key

    @staticmethod
    def generate_order_id() -> str:
        return uuid.uuid4().hex[:16]

    async def create_payment(self, amount: int, description: str, test: bool = False) -> PaymentData:
        order_id = self.generate_order_id()
        products = {
            "name": description,
            "price": amount,
            "quantity": "1",
        }
        data = {
            "do": "pay",
            "order_id": str(order_id)
        }

        order = ProdamusOrder(
            pay_url=self.__pay_url,
            secret_key=self.__secret_key,
            products=products,
            data=data
        )
        url = await order.create_pay_link()
        return PaymentData(
            id=order_id,
            url=url
        )
