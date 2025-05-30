from schemas.subs import CreditsPack, Sub


class SubsTexts:
    CREDITS_AND_SUBS = '''
Ты можешь купить кредиты или подписку с безлимитом на все:

<b>Кредиты:</b>
<i>- Тратятся за каждый запрос (сообщение или задание, созданное нейросетью)</i>

<b>Подписки:</b>
<i>- Имеют ограничение лишь по времени</i>
'''

    CREDITS = 'Выбери набор кредитов:'
    SUBS = 'Выбери подходящую подписку:'
    EVERY_CREDITS_PACK = '<b>{}</b> кредитов / <b>{}</b> рублей'
    EVERY_SUB = '<b>{sub.name}:</b> <b>{sub.days}</b> дней / <b>{sub.price}</b> рублей'

    BUY_CREDITS_PACK = '''
<b>Кредитов:</b> {credits}
<b>Цена:</b> {price} рублей

Если возникнут проблемы, обращайтесь сюда: @sheggy_love
'''
    BUY_SUB = '''
<b>Подписка закончится через {days} дней</b>    
<b>Цена:</b> {price}

Если возникнут проблемы, обращайтесь сюда: @sheggy_love
'''

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
    def subs(subs: list[Sub]):
        return SubsTexts.SUBS + '\n\n' + '\n'.join(list(map(
            lambda x: SubsTexts.EVERY_SUB.format(sub=x) + (
                ' <i>(на {}% выгоднее)</i>'.format(x.sale) if x.sale else ''
            ), subs
        )))