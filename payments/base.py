import abc
import dataclasses


@dataclasses.dataclass
class PaymentData:
    id: str
    url: str


class AbstractPaymentService(abc.ABC):
    @abc.abstractmethod
    async def create_payment(self, amount: int, description: str, test: bool = False, **kwargs) -> PaymentData: ...
    @abc.abstractmethod
    async def create_auto_payment(
            self,
            amount: int,
            description: str,
            payment_method_id: str,
            test: bool = False
    ) -> str: ...