# Copyright (c) 2025 Lilyx1025
# Licensed under the MIT License.
# This file is part of LilyMusic

import asyncio
import random
from pyrogram import enums, filters, types

from lily import app, config, db, lang, logger
from lily.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    await m.reply_text(
        text=m.lang["help_menu"],
        reply_markup=buttons.help_markup(m.lang),
        quote=True,
    )


@app.on_message(filters.command(["groups"]) & filters.user(config.OWNER_ID))
async def list_groups(_, message: types.Message):
    groups = ""
    async for dialog in app.get_dialogs():
        if dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            groups += f"{dialog.chat.title} ({dialog.chat.id})\n"
    if not groups:
        groups = "No groups found."
    await message.reply_text(groups)

@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    logger.info(f"Start command received in chat {message.chat.id} from user {message.from_user.id if message.from_user else 'None'}")
    try:
        if message.from_user and message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
            return await message.reply_text(message.lang["bl_user_notify"])

        if len(message.command) > 1 and message.command[1] == "help":
            return await _help(_, message)

        private = message.chat.type == enums.ChatType.PRIVATE
        logger.info(f"Start command - private chat: {private}")
        
        _text = (
            message.lang["start_pm"].format(message.from_user.mention if message.from_user else "User", app.mention)
            if private
            else message.lang["start_gp"].format(message.from_user.mention if message.from_user else "User", app.mention)
        )
        logger.info(f"Start text generated: {_text[:50]}...")
        
        logger.info(f"START_IMG config: {config.START_IMG}")
        if not config.START_IMG:
            logger.info("No START_IMG, sending text only")
            return await message.reply_text(_text)

        _img = random.choice(config.START_IMG) if isinstance(config.START_IMG, list) else config.START_IMG
        logger.info(f"Selected image: {_img}")

        key = buttons.start_key(message.lang, private)
        logger.info("Sending start photo...")
        await message.reply_photo(
            photo=_img,
            caption=_text,
            reply_markup=key,
            quote=not private,
        )
        logger.info("Start photo sent successfully")

        if private and message.from_user:
            if not await db.is_user(message.from_user.id):
                await utils.send_log(message)
                await db.add_user(message.from_user.id)
        elif not private:
            if not await db.is_chat(message.chat.id):
                await utils.send_log(message, True)
                await db.add_chat(message.chat.id)
    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        try:
            await message.reply_text("An error occurred. Please try again later.")
        except:
            pass


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    skip_mode = await db.get_skip_mode(message.chat.id)
    _language = await db.get_lang(message.chat.id)
    await message.reply_text(
        text=message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, cmd_delete, skip_mode, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)
