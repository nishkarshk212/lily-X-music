from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")

        self.BOT_TOKEN = getenv("BOT_TOKEN")
        self.MONGO_URL = getenv("MONGO_URL")

        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 180)) * 60
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))

        self.SESSION1 = getenv("SESSION", None)
        self.SESSION2 = getenv("SESSION2", None)
        self.SESSION3 = getenv("SESSION3", None)

        self.SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/Tele_212_bots")
        self.SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/bot_support_23")

        self.AUTO_LEAVE: bool = getenv("AUTO_LEAVE", "False").lower() == "true"
        self.AUTO_END: bool = getenv("AUTO_END", "False").lower() == "true"
    
        self.THUMB_GEN: bool = getenv("THUMB_GEN", "True").lower() == "true"
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", "True").lower() == "true"

        self.LANG_CODE = getenv("LANG_CODE", "en")

        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "").split(" ")
            if url and ("batbin.me" in url or "pastebin.com" in url)
        ]
        self.COOKIES_FILE = getenv("COOKIES_FILE", None)
        self.API_URL = getenv("API_URL", "https://pvtz.nexgenbots.xyz")
        self.API_KEY = getenv("API_KEY", "30DxNexGenBots5d0469")
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://te.legra.ph/file/3e40a408286d4eda24191.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://files.catbox.moe/haagg2.png")
        self.START_IMG = getenv("START_IMG", "https://i.ibb.co/LzSPPvK1/72d928954979411e1a77fd8c6611dbcd.jpg https://i.ibb.co/kg353Fqq/489d19473e5e268acfc611f5c343294f.jpg https://i.ibb.co/1fq59f2t/5085c37f435e4cbdc9deb7c9dbb16b44.jpg https://i.ibb.co/jk425GN9/7237ec0566e37f344c9767c042050a03.jpg https://i.ibb.co/LhYpwdHV/cebef20a181283bfc7edcb3cccafdb99.jpg https://i.ibb.co/G46PLZRK/Face-Photo-Pose.jpg").split()

    def check(self):
        missing = [
            var
            for var in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID", "SESSION1"]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
