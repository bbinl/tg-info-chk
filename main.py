import asyncio
import logging
from pathlib import Path
from telethon import TelegramClient, events, errors
from telethon.tl import types
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from config import load_config, save_config, CONFIG_FILE, PROFILE_PHOTOS_DIR, RESULTS_DIR
from telegram_user import TelegramUser, validate_phone_number, validate_username

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TelegramCheckerBot:
    def __init__(self):
        self.config = load_config()
        self.client = None
        PROFILE_PHOTOS_DIR.mkdir(exist_ok=True)
        RESULTS_DIR.mkdir(exist_ok=True)

    async def initialize(self):
        if not self.config.get('api_id'):
            print("First time setup - please enter your Telegram API credentials")
            print("You can get these from https://my.telegram.org/apps")
            self.config['api_id'] = int(input("Enter your API ID: "))
            self.config['api_hash'] = input("Enter your API hash: ")
            self.config['phone'] = validate_phone_number(input("Enter your phone number (with country code): "))
            save_config(self.config)

        # Use either bot token OR user session (not both)
        if 'bot_token' in self.config:
            self.client = TelegramClient('bot_session', self.config['api_id'], self.config['api_hash']).start(bot_token=self.config['bot_token'])
        else:
            self.client = TelegramClient('user_session', self.config['api_id'], self.config['api_hash'])
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(self.config['phone'])
                code = input("Enter the verification code sent to your Telegram: ")
                try:
                    await self.client.sign_in(self.config['phone'], code)
                except errors.SessionPasswordNeededError:
                    password = input("Enter your 2FA password: ")
                    await self.client.sign_in(password=password)

    # ... (rest of your methods remain the same until start_bot)

    async def start_bot(self):
        await self.initialize()
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await event.respond("""
            Welcome to Telegram Checker Bot!
            Commands:
            /check_phone [number] - Check a phone number
            /check_username [username] - Check a username
            """)

        @self.client.on(events.NewMessage(pattern='/check_phone'))
        async def phone_handler(event):
            try:
                phone = event.text.split(' ')[1]
                result = await self.check_phone(phone)
                if result:
                    response = f"""
                    Phone: {result.phone}
                    Name: {result.first_name} {result.last_name}
                    Username: @{result.username}
                    Last Seen: {result.last_seen}
                    Premium: {'Yes' if result.premium else 'No'}
                    Verified: {'Yes' if result.verified else 'No'}
                    """
                    await event.respond(response)
                else:
                    await event.respond("No account found for this phone number")
            except IndexError:
                await event.respond("Please provide a phone number after /check_phone")
            except Exception as e:
                await event.respond(f"Error: {str(e)}")

        @self.client.on(events.NewMessage(pattern='/check_username'))
        async def username_handler(event):
            try:
                username = event.text.split(' ')[1]
                result = await self.check_username(username)
                if result:
                    response = f"""
                    Username: @{result.username}
                    Name: {result.first_name} {result.last_name}
                    Last Seen: {result.last_seen}
                    Premium: {'Yes' if result.premium else 'No'}
                    Verified: {'Yes' if result.verified else 'No'}
                    """
                    await event.respond(response)
                else:
                    await event.respond("No account found for this username")
            except IndexError:
                await event.respond("Please provide a username after /check_username")
            except Exception as e:
                await event.respond(f"Error: {str(e)}")

        await self.client.run_until_disconnected()

if __name__ == "__main__":
    bot = TelegramCheckerBot()
    asyncio.run(bot.start_bot())
