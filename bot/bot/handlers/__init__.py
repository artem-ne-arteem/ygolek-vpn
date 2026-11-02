from aiogram import Router

from bot.handlers import admin, legal, mykey, payment, plans, start, trial


def build_root_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(trial.router)
    router.include_router(plans.router)
    router.include_router(payment.router)
    router.include_router(mykey.router)
    router.include_router(legal.router)
    router.include_router(admin.router)
    return router
