import logging
from pathlib import Path
from environs import Env

logger = logging.getLogger(__name__)

env = Env()
env.read_env(override=True)

secret_key = env.str('SECRET_KEY')
is_debug = env.bool('IS_DEBUG', False)
allowed_hosts = env.list('ALLOWED_HOSTS', ['*'])
log_level = env.str('LOG_LEVEL', 'DEBUG')

github_webhook_secret = env.str('GITHUB_WEBHOOK_SECRET', None)
gitea_webhook_secret = env.str('GITEA_WEBHOOK_SECRET', None)

db_name = env.str('DB_NAME')
db_username = env.str('DB_USERNAME')
db_password = env.str('DB_PASSWORD')
db_host = env.str('DB_HOST')
db_port = env.int('DB_PORT')
logger.debug(f"Database config loaded: host={db_host}, port={db_port}, db={db_name}, user={db_username}")
iiko_host = env.str('IIKO_API_SERVER')
iiko_username = env.str('IIKO_API_USERNAME')
iiko_password = env.str('IIKO_API_PASSWORD')

bot_token = env.str('BOT_TOKEN')
app_host = env.str('APP_HOST')
# Публичный URL для ссылок в уведомлениях (если не задан, используем APP_HOST)
public_url = env.str('PUBLIC_URL', app_host)

static_dir = env.str('STATIC_DIR', None)
data_dir = env.str(
    'DATA_DIR',
    default=Path(__file__).resolve().parent.parent / 'data'
)
