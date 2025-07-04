import pickle
from pathlib import Path

CONFIG_FILE = Path("config.pkl")
PROFILE_PHOTOS_DIR = Path("profile_photos")
RESULTS_DIR = Path("results")

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'rb') as f:
                config = pickle.load(f)
                # বট টোকেন যুক্ত আছে কিনা চেক করুন
                if 'bot_token' not in config:
                    config['bot_token'] = '7066548759:AAFvZ-tEuz0tOeZS_hHPU-rRBcnQzgi8pjQ'  # এখানে আপনার বট টোকেন
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {'bot_token': '7066548759:AAFvZ-tEuz0tOeZS_hHPU-rRBcnQzgi8pjQ'}  # ডিফল্ট হিসেবে টোকেন
    return {'bot_token': '7066548759:AAFvZ-tEuz0tOeZS_hHPU-rRBcnQzgi8pjQ'}  # নতুন কনফিগ তৈরি হলে

def save_config(config):
    # নিশ্চিত করুন যে বট টোকেন কনফিগে আছে
    if 'bot_token' not in config:
        config['bot_token'] = '7066548759:AAFvZ-tEuz0tOeZS_hHPU-rRBcnQzgi8pjQ'
    
    with open(CONFIG_FILE, 'wb') as f:
        pickle.dump(config, f)
