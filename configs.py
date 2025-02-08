from os import getenv as genv

API_ID = genv("API_ID", "")
API_HASH = genv("API_HASH", "")
BOT_TOKEN = genv("BOT_TOKEN", "")
BASE_URL = genv("BASE_URL", "")
DATABASE_URL = genv("DATABASE_URL", "")

START_TXT = '''<b>{},

๏ I ᴄᴀɴ Cᴏɴᴠᴇʀᴛ ʏᴏᴜʀ ʟɪɴᴋs ᴛᴏ Sʜᴏʀᴛ ʟɪɴᴋs ᴜsɪɴɢ ʏᴏᴜʀ ᴀᴩɪ.

๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ Hᴇʟᴩ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴄᴏᴍᴍᴀɴᴅs.

๏ By - @TechifyBots</b>'''

HELP_TXT = '''Send Shortener URL & API along with the command.

Ex: <code>/shortlink example.com api</code>

Now send me any link I will convet that link into your connected Shortener'''

ABOUT_TXT = '''<b>╔════❰ ShortLink Bot ❱═══❍
║ ┏━━━━━━━━━❥
║ ┣ Mʏ ɴᴀᴍᴇ -> {}
║ ┣ Mʏ Oᴡɴᴇʀ -> @CallOwnerBot
║ ┣ Uᴘᴅᴀᴛᴇꜱ -> @TechifyBots
║ ┣ 𝖲ᴜᴘᴘᴏʀᴛ -> @TechifySupport
║ ┣ ๏ Cʜᴇᴄᴋ ʜᴇʟᴘ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ.
║ ┗━━━━━━━━━❥
╚═════❰ @ ❱═════❍</b>'''
