from datetime import datetime, timedelta
from schemas.subs import CreditsPack, Sub
from .base import td_to_text


class SubsTexts:
    CREDITS_AND_SUBS = '''
Ты можешь купить кредиты или подписку с безлимитом на все:

<b>Кредиты:</b>
<i>- Тратятся за каждый запрос (сообщение или задание, созданное нейросетью)</i>

<b>Подписки:</b>
<i>- Имеют ограничение лишь по времени</i>
'''

    CREDITS = 'Выбери набор кредитов:'
    SUBS = '<b>Выбери подходящую подписку:</b>'
    EVERY_CREDITS_PACK = '<b>{}</b> кредитов / <b>{}</b> рублей'
    EVERY_SUB = '<b>{sub.name}:</b> <b>{sub.days}</b> дней / <b>{sub.price}</b> рублей'

    BUY_CREDITS_PACK = '''
<b>Кредитов:</b> {credits}
<b>Цена:</b> {price} рублей

Если возникнут проблемы, обращайтесь сюда: @teledeff_support
'''
    BUY_SUB = '''
<b>Подписка на:</b> {days} дн
<b>Цена:</b> {price} руб

Если возникнут проблемы, обращайтесь сюда: @teledeff_support
'''
    I_WANT_MORE_BUTTON = 'Посмотреть подписки'

    @staticmethod
    def buy_credits_pack(credits_pack: CreditsPack):
        return SubsTexts.BUY_CREDITS_PACK.format(
            credits=credits_pack.credits,
            price=credits_pack.price
        )

    @staticmethod
    def buy_sub(sub: Sub):
        return SubsTexts.BUY_SUB.format(
            days=sub.days,
            price=sub.price
        )

    @staticmethod
    def credits_packs(credits_packs: list[CreditsPack]):
        return SubsTexts.CREDITS + '\n\n' + '\n'.join(list(map(
            lambda x: SubsTexts.EVERY_CREDITS_PACK.format(x.credits, x.price) + (
                ' <i>(на {}% выгоднее)</i>'.format(x.sale) if x.sale else ''
            ),
            credits_packs)
        ))

    @staticmethod
    def subs(
        subs: list[Sub],
        td_before_sub_end: timedelta | None = None,
        has_autopayment: bool = False,
        autopayment_duration: timedelta | None = None
    ):
        text = ''
        if td_before_sub_end and td_before_sub_end > timedelta(seconds=0):
            if has_autopayment:
                text += f'🕝 <b>Следующее автосписание произойдет через:</b> ' \
                        f'<code>{td_to_text(td_before_sub_end)}</code>\n' \
                        f'<blockquote>Чтобы отменить автосписание, нажмите кнопку ' \
                        f'"❌ Отменить автопродление"</blockquote>\n'
            else:
                text += f'🕝 <b>Текущая подписка закончится через:</b> ' \
                            f'<code>{td_to_text(td_before_sub_end)}</code>\n\n'

            text += '<blockquote>Если вы купите подписку, ' \
                    'ваша текущая подписка продлится на выбранное время</blockquote>\n\n'

        text += SubsTexts.SUBS + '\n\n' + '\n'.join(list(map(
            lambda x: SubsTexts.EVERY_SUB.format(sub=x) + (
                ' <i>(на {}% выгоднее)</i>'.format(x.sale) if x.sale else ''
            ), subs
        )))
        return text