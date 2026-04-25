from pyrogram import Client, filters, types
from pyrogram.raw.types import UpdateGroupCallParticipants, UpdateGroupCall
from shreya import app
import time

# Mapping to store call_id -> chat_id
CALL_CHATS = {}

@app.on_raw_update()
async def vc_join_watcher(client, update, users, chats):
    # 1. Capture mapping of call_id to chat_id
    if isinstance(update, UpdateGroupCall):
        CALL_CHATS[update.call.id] = update.chat_id
    
    # 2. Capture participant updates
    elif isinstance(update, UpdateGroupCallParticipants):
        chat_id = CALL_CHATS.get(update.call.id)
        if not chat_id:
            return
            
        for participant in update.participants:
            # Check if participant just joined (within last 10 seconds)
            # and it's not the bot itself
            if hasattr(participant.peer, "user_id"):
                user_id = participant.peer.user_id
                if user_id == client.me.id:
                    continue
                
                # Check join date
                if time.time() - participant.date < 10:
                    try:
                        user = await client.get_users(user_id)
                        await client.send_message(
                            chat_id,
                            f"{user.mention}\n{user.id}"
                        )
                    except Exception:
                        pass

# Fallback: Handle service messages for invitations
@app.on_message(filters.video_chat_members_invited)
async def vc_invited_handler(_, m: types.Message):
    for user in m.video_chat_members_invited.users:
        await m.reply_text(
            f"{user.mention}\n{user.id}"
        )
