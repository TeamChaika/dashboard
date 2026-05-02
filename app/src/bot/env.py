from environs import Env

env = Env()
env.read_env(override=True)

bot_token = env.str('BOT_TOKEN')
app_host = env.str('APP_HOST')
public_url = env.str('PUBLIC_URL', app_host)
