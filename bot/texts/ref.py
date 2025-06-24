from datetime import datetime


class RefTexts:
    MAIN = '''
<b>Приглашай друзей и получай подписки бесплатно!</b>

<i>С каждой покупки подписки твоего приглашенного друга ты получишь 50% от его подписки бесплатно</i>
<blockquote>Например: Твой друг купил подписку на 30 дней -> Ты получаешь подписку на 15 дней</blockquote>

<b>Приведено:</b> <code>{}</code>
<b>Оплативших:</b> <code>{}</code>
'''

    SPECIAL_MAIN = '''
<b>Вы учавствуете в специальной реферальной программе!</b>
<i>Приглайшайте рефералов и получайте процент от их первой оплаты</i> 💰

<b>Ваш баланс:</b> <code>{}</code>
<b>Ваш процент от оплаты реферала:</b> <code>{}</code>
<b>Оплативших:</b> <code>{}</code>
'''

    REF_NOTIFICATION = '''
От вас пришел реферал: <b><a href="https://t.me/{username}">{full_name}</a></b>

<b>Вы получили:</b> <code>{add_credits}</code> кредитов
<b>Всего кредитов:</b> <code>{all_credits}</code>    
'''
    REF_PAID_NOTIFICATION = '''
Ваш реферал <b><a href="https://t.me/{username}">{full_name}</a></b> произвел оплату

<b>Ваша подписка увеличена на:</b> <code>{days}</code> дней
<b>Подписка закончится:</b> <code>{sub_end}</code>
'''

    REF_SPECIAL_PAID_NOTIFICATION = '''
Ваш реферал <b><a href="https://t.me/{username}">{full_name}</a></b> произвел оплату

<b>Вы получили:</b> <code>{add_balance}</code> руб на баланс
<b>Теперь ваш баланс составляет:</b> <code>{all_balance}</code>
'''

    ABOUT_SPECIAL_REF = '''
<b>Вы можете поучавствовать в нашей специальной реферальной программе!</b>

Если вы блогер или имеете какую-либо возможность привести в бота большую аудиторию,
вам подойдет это предложение!

<i>- В чем ваша выгода от специальной программы?</i>
Вы будете получать *процент за первую оплату каждого приглашенного вами реферала

<b>Чтобы подать заявку, нажмите кнопку внизу "Подать заявку", и мы свяжемся с Вами</b>

* - процент рассчитывается индивидуально
'''

    ABOUT_SPECIAL_REF_IF_ON_MODERATION = '''
<b>Спасибо, что подали заявку на участие в нашей специальной реферальной программе!</b>

<i>- В чем ваша выгода от специальной программы?</i>
Вы будете получать *процент за первую оплату каждого приглашенного вами реферала

<b>Ваша заявка сейчас находится на рассмотрении...</b>

* - процент рассчитывается индивидуально  
'''

    ON_SUBMIT_REQUEST_SPECIAL_REF = '''
Пользователь {} подал заявку на участие в специальной реферальной программе    
'''

    SPECIAL_REF_BUTTON = '✴ Специальная программа'
    ALL_STATISTIC_BUTTON = '📊 Смотреть всю статистику'
    DELETE_THIS_MESSAGE = '🗑 Удалить это сообщение'
    SEND_ORDER_SPECIAL_REF_BUTTON = 'Подать заявку'

    @staticmethod
    def main(
        count_refs: int,
        count_paid_refs: int
    ) -> str:
        return RefTexts.MAIN.format(
            count_refs, count_paid_refs
        )

    @staticmethod
    def special_main(
        balance: int, percent: int, paid_refs: int
    ):
        return RefTexts.SPECIAL_MAIN.format(
            balance, percent, paid_refs
        )

    @staticmethod
    def about_special_ref(on_moderation: bool):
        if on_moderation:
            return RefTexts.ABOUT_SPECIAL_REF_IF_ON_MODERATION
        else:
            return RefTexts.ABOUT_SPECIAL_REF

    @staticmethod
    def ref_notif(full_name: str, username: str | None, add_credits: int, all_credits: int):
        return RefTexts.REF_NOTIFICATION.format(
            username=username, full_name=full_name, add_credits=add_credits, all_credits=all_credits
        )

    @staticmethod
    def ref_paid_notification(full_name: str, username: str | None, days: int, sub_end: datetime):
        return RefTexts.REF_PAID_NOTIFICATION.format(
            username=username, full_name=full_name, days=days, sub_end=sub_end.strftime('%H:%M %d.%m.%Y')
        )

    @staticmethod
    def ref_special_ref_paid_notification(
            full_name: str, username: str | None, add_balance: int, all_balance: int
    ):
        return RefTexts.REF_SPECIAL_PAID_NOTIFICATION.format(
            full_name=full_name, username=username, add_balance=add_balance,
            all_balance=all_balance
        )

    @staticmethod
    def on_submit_request_special_ref(user_id: int, full_name: str, username: str | None = None):
        return RefTexts.ON_SUBMIT_REQUEST_SPECIAL_REF.format(
            'ID: {}, full_name: {}, username: @{}'.format(user_id, full_name, username)
        )