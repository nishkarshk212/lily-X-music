# Copyright (c) 2025 Lilyx1025
# Licensed under the MIT License.
# This file is part of LilyMusic


import asyncio
from pathlib import Path

from pyrogram import filters, types

from lily import anon, app, config, db, lang, logger, queue, tg, yt
from lily.helpers import buttons, utils
from lily.helpers._play import checkUB, background_download


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        asyncio.create_task(background_download(track))
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text

@app.on_message(filters.all, group=-1)
async def log_all_messages(_, m: types.Message):
    logger.info(f"Message received: {m.text or m.caption or 'Media'} in chat {m.chat.id} from {m.from_user.id if m.from_user else 'System'}")

# Debug: Log all messages to see if filters are working
# DISABLED FOR DEBUGGING
# @app.on_message(filters.command(["play", "playforce", "vplay", "vplayforce"]), group=-10)
# async def debug_play_filter(_, m: types.Message):
#     logger.info(f"DEBUG: Play command detected in filter")


# TEST: Simple play handler without decorators
@app.on_message(filters.command(["testplay"]) & filters.group)
async def test_play_handler(_, m: types.Message):
    logger.info(f">>> TEST PLAY HANDLER TRIGGERED <<< by {m.from_user.id}")
    await m.reply_text("Test play handler is working!")



@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
)
@lang.language()
# @checkUB  # TEMPORARILY DISABLED FOR TESTING
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    try:
        logger.info(f">>> PLAY HANDLER TRIGGERED <<< in chat {m.chat.id} from user {m.from_user.id}")
        logger.info(f"Play command received in chat {m.chat.id} from user {m.from_user.id}")
        sent = await m.reply_text(m.lang["play_searching"])
        file = None
        mention = m.from_user.mention
        media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
        tracks = []

        if media:
            setattr(sent, "lang", m.lang)
            file = await tg.download(m.reply_to_message, sent)

        elif m3u8:
            file = await tg.process_m3u8(url, sent.id, video)

        elif url:
            if "playlist" in url:
                await sent.edit_text(m.lang["playlist_fetch"])
                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT, mention, url, video
                )

                if not tracks:
                    return await sent.edit_text(m.lang["playlist_error"])

                file = tracks[0]
                tracks.remove(file)
                file.message_id = sent.id
            else:
                file = await yt.search(url, sent.id, video=video)

            if not file:
                return await sent.edit_text(
                    m.lang["play_not_found"].format(config.SUPPORT_CHAT)
                )

        elif len(m.command) >= 2:
            query = " ".join(m.command[1:])
            file = await yt.search(query, sent.id, video=video)
            if not file:
                return await sent.edit_text(
                    m.lang["play_not_found"].format(config.SUPPORT_CHAT)
                )

        if not file:
            return await sent.edit_text(m.lang["play_usage"])

        if file.duration_sec > config.DURATION_LIMIT:
            return await sent.edit_text(
                m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
            )

        if await db.is_logger():
            await utils.play_log(m, sent.link, file.title, file.duration)

        file.user = mention
        if force:
            queue.force_add(m.chat.id, file)
        else:
            position = queue.add(m.chat.id, file)

            if position != 0 or await db.get_call(m.chat.id):
                asyncio.create_task(background_download(file))
                await sent.edit_text(
                    m.lang["play_queued"].format(
                        position,
                        file.url,
                        file.title,
                        file.duration,
                        m.from_user.mention,
                    ),
                    reply_markup=buttons.play_queued(
                        m.chat.id, file.id, m.lang["play_now"]
                    ),
                )
                if tracks:
                    added = playlist_to_queue(m.chat.id, tracks)
                    await app.send_message(
                        chat_id=m.chat.id,
                        text=m.lang["playlist_queued"].format(len(tracks)) + added,
                    )
                return

        if not file.file_path:
            fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
            if Path(fname).exists():
                file.file_path = fname
            else:
                await sent.edit_text(m.lang["play_downloading"])
                file.file_path = await yt.download(file.id, video=video)

        logger.info(f"Calling anon.play_media for chat {m.chat.id} with file {file.file_path}")
        await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
        if not tracks:
            return
        added = playlist_to_queue(m.chat.id, tracks)
        await app.send_message(
            chat_id=m.chat.id,
            text=m.lang["playlist_queued"].format(len(tracks)) + added,
        )
    except Exception as e:
        logger.error(f"Error in play_hndlr for chat {m.chat.id}: {e}", exc_info=True)
        try:
            await m.reply_text(f"An error occurred: {e}")
        except Exception:
            pass
