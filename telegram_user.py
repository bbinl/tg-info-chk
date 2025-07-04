from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
from telethon.tl import types
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.functions.users import GetFullUserRequest

@dataclass
class TelegramUser:
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: str
    premium: bool
    verified: bool
    fake: bool
    bot: bool
    last_seen: str
    last_seen_exact: Optional[str] = None
    status_type: Optional[str] = None
    bio: Optional[str] = None
    common_chats_count: Optional[int] = None
    blocked: Optional[bool] = None
    profile_photos: List[str] = None
    privacy_restricted: bool = False

    @classmethod
    async def from_user(cls, client, user: types.User, phone: str = "") -> 'TelegramUser':
        try:
            bio = ''
            common_chats_count = 0
            blocked = False
            
            try:
                full_user = await client(GetFullUserRequest(user.id))
                user_full_info = full_user.full_user
                bio = getattr(user_full_info, 'about', '') or ''
                common_chats_count = getattr(user_full_info, 'common_chats_count', 0)
                blocked = getattr(user_full_info, 'blocked', False)
            except:
                pass

            status_info = get_enhanced_user_status(user.status)
            
            return cls(
                id=user.id,
                username=user.username,
                first_name=getattr(user, 'first_name', None) or "",
                last_name=getattr(user, 'last_name', None) or "",
                phone=phone,
                premium=getattr(user, 'premium', False),
                verified=getattr(user, 'verified', False),
                fake=getattr(user, 'fake', False),
                bot=getattr(user, 'bot', False),
                last_seen=status_info['display_text'],
                last_seen_exact=status_info['exact_time'],
                status_type=status_info['status_type'],
                bio=bio,
                common_chats_count=common_chats_count,
                blocked=blocked,
                privacy_restricted=status_info['privacy_restricted'],
                profile_photos=[]
            )
        except Exception as e:
            print(f"Error creating TelegramUser: {str(e)}")
            status_info = get_enhanced_user_status(getattr(user, 'status', None))
            return cls(
                id=user.id,
                username=getattr(user, 'username', None),
                first_name=getattr(user, 'first_name', None) or "",
                last_name=getattr(user, 'last_name', None) or "",
                phone=phone,
                premium=getattr(user, 'premium', False),
                verified=getattr(user, 'verified', False),
                fake=getattr(user, 'fake', False),
                bot=getattr(user, 'bot', False),
                last_seen=status_info['display_text'],
                last_seen_exact=status_info['exact_time'],
                status_type=status_info['status_type'],
                privacy_restricted=status_info['privacy_restricted'],
                profile_photos=[]
            )

def get_enhanced_user_status(status):
    result = {
        'display_text': 'Unknown',
        'exact_time': None,
        'status_type': 'unknown',
        'privacy_restricted': False
    }
    
    if isinstance(status, types.UserStatusOnline):
        result.update({
            'display_text': "Currently online",
            'status_type': 'online',
            'privacy_restricted': False
        })
    elif isinstance(status, types.UserStatusOffline):
        exact_time = status.was_online.strftime('%Y-%m-%d %H:%M:%S UTC')
        result.update({
            'display_text': f"Last seen: {exact_time}",
            'exact_time': exact_time,
            'status_type': 'offline',
            'privacy_restricted': False
        })
    elif isinstance(status, types.UserStatusRecently):
        result.update({
            'display_text': "Last seen recently (1 second - 3 days ago)",
            'status_type': 'recently',
            'privacy_restricted': True
        })
    elif isinstance(status, types.UserStatusLastWeek):
        result.update({
            'display_text': "Last seen within a week (3-7 days ago)",
            'status_type': 'last_week',
            'privacy_restricted': True
        })
    elif isinstance(status, types.UserStatusLastMonth):
        result.update({
            'display_text': "Last seen within a month (7-30 days ago)",
            'status_type': 'last_month',
            'privacy_restricted': True
        })
    elif status is None:
        result.update({
            'display_text': "Status unavailable",
            'status_type': 'unavailable'
        })
    
    return result

def validate_phone_number(phone: str) -> str:
    phone = re.sub(r'[^\d+]', '', phone.strip())
    if not phone.startswith('+'): phone = '+' + phone
    if not re.match(r'^\+\d{10,15}$', phone): raise ValueError(f"Invalid phone number format: {phone}")
    return phone

def validate_username(username: str) -> str:
    username = username.strip().lstrip('@')
    if not re.match(r'^[A-Za-z]\w{3,30}[A-Za-z0-9]$', username): raise ValueError(f"Invalid username format: {username}")
    return username
