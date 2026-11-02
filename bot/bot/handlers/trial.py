import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import texts
from bot.db.repo import get_or_create_user, marzban_username_for, record_subscription
from bot.db.session import get_session
from bot.keyboards import back_to_menu, plans_menu
from bot.h1panel.client import H1PanelClient, H1PanelError
from bot.plans import TRIAL_DAYS, TRIAL_ENABLED, TRIAL_TRAFFIC_GB
from bot.telegram_utils import safe_answer

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "trial:activate")
async def activate_trial(callback: CallbackQuery, panel_client: H1PanelClient) -> None:
    # в старых сообщениях кнопку «Пробный период» всё ещё можно нажать
    if not TRIAL_ENABLED:
        await safe_answer(callback)
        await callback.message.answer(texts.TRIAL_DISABLED, reply_markup=plans_menu())
        return

    async with get_session() as session:
        user = await get_or_create_user(session, callback.from_user)

        if user.trial_used:
            await safe_answer(callback)
            await callback.message.answer(texts.TRIAL_ALREADY_USED, reply_markup=plans_menu())
            return

        marzban_username = user.marzban_username or marzban_username_for(user.tg_id)

        try:
            key = await panel_client.upsert_user(
                username=marzban_username,
                days=TRIAL_DAYS,
                traffic_gb=TRIAL_TRAFFIC_GB,
            )
        except H1PanelError:
            logger.exception("Failed to issue trial key for tg_id=%s", user.tg_id)
            await safe_answer(callback)
            await callback.message.answer(texts.MARZBAN_ERROR)
            return

        user.marzban_username = marzban_username
        user.trial_used = True
        await record_subscription(session, user.id, plan_id="trial", days=TRIAL_DAYS)
        await session.commit()

    await safe_answer(callback)
    await callback.message.answer(
        texts.TRIAL_ISSUED.format(
            days=TRIAL_DAYS,
            traffic=texts.traffic_label(TRIAL_TRAFFIC_GB),
            key=key,
        ),
        reply_markup=back_to_menu(keep_message=True),
    )
