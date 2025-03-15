from datetime import datetime, timedelta
import pytz
from resources.config_loader import get_config

TIMEZONE = get_config("timezone", "name")

def time_now():
    return datetime.now(pytz.timezone(TIMEZONE)) - timedelta(hours=3)
