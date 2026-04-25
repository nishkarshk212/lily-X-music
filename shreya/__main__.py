# Copyright (c) 2025 ShreyamousX1025
# Licensed under the MIT License.
# This file is part of ShreyaMusic


import asyncio
import signal
import importlib
from contextlib import suppress

# Fix for asyncio event loop error in Python 3.10+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from shreya import (anon, app, config, db, logger,
                   stop, thumb, userbot, yt)
from shreya.plugins import all_modules


async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()

from shreya.core.cleanup import auto_clean

async def main():
    auto_clean()
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"shreya.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    sudoers = await db.get_sudoers()
    app.sudoers.update(sudoers)
    app.bl_users.update(await db.get_blacklisted())
    logger.info(f"Loaded {len(app.sudoers)} sudo users.")

    await idle()
    await stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
