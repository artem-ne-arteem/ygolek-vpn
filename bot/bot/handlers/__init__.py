from aiogram import Router

from bot.handlers import admin, applogin, devices, gift, legal, mykey, payment, plans, start, trial


def build_root_router() -> Router:
    router = Router()
    # gift и applogin — раньше start: /start gift_<code> и /start app_<code>
    # должны попасть в свои обработчики, а не в общее меню
    router.include_router(gift.router)
    router.include_router(applogin.router)
    router.include_router(start.router)
    router.include_router(trial.router)
    router.include_router(plans.router)
    router.include_router(payment.router)
    router.include_router(devices.router)
    router.include_router(mykey.router)
    router.include_router(legal.router)
    router.include_router(admin.router)
    return router
