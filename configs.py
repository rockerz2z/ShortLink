from os import environ

API_ID = int(environ.get("API_ID", ""))
API_HASH = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
BASE_URL = environ.get("BASE_URL", "")
DATABASE_URL = environ.get("DATABASE_URL", "")
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", ""))
ADMINS = int(environ.get("ADMINS", ""))
IS_FSUB = bool(environ.get("IS_FSUB", True)) # Set "True" For Force Subscribe Enable and remove "True" if don't need 
AUTH_CHANNELS = environ.get("AUTH_CHANNEL", "") # Add Multiple Channels iD By Space
AUTH_CHANNELS = [int(channel_id) for channel_id in AUTH_CHANNELS.split(",")]


START_TXT = '''<b>{},

๏ I ᴄᴀɴ Cᴏɴᴠᴇʀᴛ ʏᴏᴜʀ ʟɪɴᴋs ᴛᴏ Sʜᴏʀᴛ ʟɪɴᴋs ᴜsɪɴɢ ʏᴏᴜʀ ᴀᴩɪ.

๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ Hᴇʟᴩ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴄᴏᴍᴍᴀɴᴅs.

๏ By - @TechifyBots</b>'''

LOG_TEXT = '''<b>#NewUser
    
ID - <code>{}</code>

Name - {}</b>'''

HELP_TXT = '''Send Shortener URL & API along with the command.

Ex: <code>/shortlink example.com api</code>

Now send me any link I will convet that link into your connected Shortener

If you want to remove your Shortener then use <code>/remove</code> command.'''

FORCE_SUBSCRIBE_TEXT = '''<b>{}, Tᴏ ᴜsᴇ ᴛʜᴇ ʙᴏᴛ ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ. Tʜᴇ ʙᴏᴛ ᴡɪʟʟ ɴᴏᴛ ᴘʀᴏᴄᴇss ᴀɴʏ ʀᴇǫᴜᴇsᴛs ᴡɪᴛʜᴏᴜᴛ ᴊᴏɪɴɪɴɢ.

बॉट का उपयोग करने के लिए आपको पहले हमारे चैनल में Join होना होगा। बॉट बिना शामिल हुए किसी भी Request को Process नहीं करेगा।</b>'''

ABOUT_TXT = '''<b>╔════❰ ShortLink Bot ❱═══❍
║ ┏━━━━━━━━━❥
║ ┣ Mʏ ɴᴀᴍᴇ -> {}
║ ┣ Mʏ Oᴡɴᴇʀ -> @CallOwnerBot
║ ┣ Uᴘᴅᴀᴛᴇꜱ -> @TechifyBots
║ ┣ 𝖲ᴜᴘᴘᴏʀᴛ -> @TechifySupport
║ ┣ ๏ Cʜᴇᴄᴋ ʜᴇʟᴘ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ.
║ ┗━━━━━━━━━❥
╚═════❰ @ ❱═════❍</b>'''
