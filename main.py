import asyncio
import json
import logging
from pathlib import Path
from telethon import TelegramClient, events, errors
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
            self.config['api_id'] = int(input("Enter your API ID: 29665515"))
            self.config['api_hash'] = input("Enter your API hash: 5aa4caa1f24428621d3feddb293469f4")
            self.config['phone'] = validate_phone_number(input("Enter your phone number (with country code): +8801775179605"))
            save_config(self.config)

        self.bot_client = TelegramClient('bot_session', self.config['api_id'], self.config['api_hash']).start(bot_token='7066548759:AAFvZ-tEuz0tOeZS_hHPU-rRBcnQzgi8pjQ')
        
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.config['phone'])
            code = input("Enter the verification code sent to your Telegram: ")
            try:
                await self.client.sign_in(self.config['phone'], code)
            except errors.SessionPasswordNeededError:
                password = input("Enter your 2FA password: ")
                await self.client.sign_in(password=password)

    async def download_profile_photos(self, user, user_data):
        try:
            photos = await self.client.get_profile_photos(user)
            if not photos: return
            user_data.profile_photos = []
            for i, photo in enumerate(photos):
                identifier = user_data.phone if user_data.phone else user_data.username
                photo_path = PROFILE_PHOTOS_DIR / f"{user.id}_{identifier}_photo_{i}.jpg"
                await self.client.download_media(photo, file=photo_path)
                user_data.profile_photos.append(str(photo_path))
        except Exception as e:
            logger.error(f"Error downloading profile photos: {str(e)}")

    async def check_phone(self, phone):
        try:
            phone = validate_phone_number(phone)
            try:
                user = await self.client.get_entity(phone)
                telegram_user = await TelegramUser.from_user(self.client, user, phone)
                await self.download_profile_photos(user, telegram_user)
                return telegram_user
            except:
                contact = types.InputPhoneContact(client_id=0, phone=phone, first_name="Test", last_name="User")
                result = await self.client(ImportContactsRequest([contact]))
                
                if not result.users: return None
                
                user = result.users[0]
                try:
                    full_user = await self.client.get_entity(user.id)
                    await self.client(DeleteContactsRequest(id=[user.id]))
                    telegram_user = await TelegramUser.from_user(self.client, full_user, phone)
                    await self.download_profile_photos(full_user, telegram_user)
                    return telegram_user
                finally:
                    try:
                        await self.client(DeleteContactsRequest(id=[user.id]))
                    except:
                        pass
        except Exception as e:
            logger.error(f"Error checking phone: {str(e)}")
            return None

    async def check_username(self, username):
        try:
            username = validate_username(username)
            user = await self.client.get_entity(username)
            if not isinstance(user, types.User): return None
            telegram_user = await TelegramUser.from_user(self.client, user, "")
            await self.download_profile_photos(user, telegram_user)
            return telegram_user
        except Exception as e:
            logger.error(f"Error checking username: {str(e)}")
            return None

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
