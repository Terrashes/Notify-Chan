import requests
import discord
import asyncio
import json
import logging
import logging.handlers
from discord.ext import commands, tasks
from datetime import *


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)


handler = logging.handlers.RotatingFileHandler(
    filename='twitch.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)


with open("config.json", "r") as f:
    config = json.load(f)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix = 'mm', help_command=None, intents=intents)


def writeConfig():
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4,  
                        separators=(',',': '))


@bot.event
async def on_ready():
    print("started!")
    activity = discord.Game(name="m!help")
    await bot.change_presence(status=discord.Status.online, activity=activity)


TWITCH_CLIENT_ID = config["twitch_client_id"]
TWITCH_CLIENT_SECRET = config["twitch_secret"]


auth_url = "https://id.twitch.tv/oauth2/token"
auth_params = {
    "client_id": TWITCH_CLIENT_ID,
    "client_secret": TWITCH_CLIENT_SECRET,
    "grant_type": "client_credentials",
    "scope": "user:read:email"
}


response = requests.post(auth_url, params=auth_params).json()


twitch_access_token = response["access_token"]


def is_stream_live(streamerUsername):
    try:
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {twitch_access_token}"
        }
        TWITCH_API_URL = f"https://api.twitch.tv/helix/streams?user_login={streamerUsername}"
        response = requests.get(TWITCH_API_URL, headers=headers).json()
        status = bool(response.get("data", []))
        title = ""
        thumbnail = ""
        if status:
            title = response['data'][0]['title']
            thumbnail = response['data'][0]['thumbnail_url'].format(width=640, height=360)
        return status, title, thumbnail
    except Exception as e:
        print(f"{e}")
        pass





@bot.command()
async def twadd(ctx, streamerUsername=None, messageLive="Hey everyone! {streamerUsername} is now live!", messageOff="{streamerUsername} is offline now"):
    if streamerUsername:
        # try:
            TWITCH_API_URL = f"https://api.twitch.tv/helix/streams?user_login={streamerUsername}"
            headers = {
                "Client-ID": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {twitch_access_token}"
            }
            response = requests.get(TWITCH_API_URL, headers=headers)
            
            if response.status_code == 400:
                await ctx.channel.send(f"Error: channel not found for {streamerUsername}")
            elif response.status_code == 200:
                if streamerUsername not in config["streamers"]:
                    config["streamers"].update({
                        str(streamerUsername) :
                            {
                                "status": False,
                                "messageLive": messageLive,
                                "messageOff": messageOff,
                                "channels": [ctx.channel.id]
                            }
                        })
                    writeConfig()
                    await ctx.channel.send(f'Streamer `{streamerUsername}` added')
                if ctx.channel.id not in config["streamers"][streamerUsername]["channels"]:
                    config["streamers"][streamerUsername]["channels"].append(ctx.channel.id)
                    writeConfig()
                    await ctx.channel.send(f'Streamer `{streamerUsername}` added')
                else:
                    await ctx.channel.send(f'Streamer `{streamerUsername}` was already added')
                await send_notification(streamerUsername)
        # except Exception as e:
        #     print(f"An SSL error occurred: {e}")
        #     pass
    else:
        await ctx.channel.send('Please, specify streamer\'s nickname to add')


@bot.command()
async def twdel(ctx, streamerUsername=None):
    if streamerUsername:
        try:
            print(type(config), type(config["streamers"][streamerUsername]["channels"]), type(ctx.channel.id))
            config["streamers"][streamerUsername]["channels"].remove(int(ctx.channel.id))
            if len(["streamers"][streamerUsername]["channels"]) == 0:
                del config["streamers"][streamerUsername]
            writeConfig()
            await ctx.channel.send(f'Streamer `{streamerUsername}` deleted')
        except Exception as e:
            print(f"{e}")
            await ctx.channel.send(f"Error: channel not found for {streamerUsername}")
    else:
        await ctx.channel.send('Please, specify streamer\'s nickname to remove')


@bot.command()
async def twshow(ctx):
    message = "**Streamers**"
    for streamerUsername in config["streamers"]:
        try:
            if ctx.channel.id in config["streamers"][streamerUsername]["channels"]:
                if config['streamers'][streamerUsername]['status']:
                    status=":green_circle:`live`"
                else:
                    status=":o:`offline`"
                message="".join([message, f"\n {streamerUsername} {status}"])
        except Exception:
            pass
    if message == "Streamer's list:":
        await ctx.channel.send('There is no tracking streamers in this channel')
    else:
        await ctx.channel.send(message)


async def send_notification(streamerUsername):
    streamer_info = config["streamers"][streamerUsername]
    streamer_info["status"] = config["streamers"][streamerUsername]["status"]
    print(f'[{datetime.now(timezone.utc)}]working on {streamerUsername}')
    params = is_stream_live(streamerUsername)
    status = params[0]
    if status != streamer_info["status"]:
        try:
            for channel in list(streamer_info["channels"]):
                if channel is not None:
                    channel = bot.get_channel(int(channel))
                    messageLive = f"Подруба {streamerUsername}"
                    if status:
                        title = params[1]
                        thumbnail = params[2]
                        embed = discord.Embed(
                            color=0xff6961, 
                            title=messageLive, 
                            description="")
                        embed.add_field(
                            name=title,
                            value = "", inline=False)
                        embed.set_image(url=thumbnail)
                        await channel.send(embed=embed)
                        # await .send(f"Hey everyone, {streamerUsername} is now live on Twitch! https://www.twitch.tv/{streamerUsername}")
                    else:
                        await channel.send(f"{streamerUsername} has gone offline.")
                else:
                    print(f"Error: channel not found for {streamerUsername}")
            config["streamers"][streamerUsername]["status"] = status
            writeConfig()
        except Exception as e:
            print(f"{e}")
            pass


async def send_notifications():
    while not bot.is_closed():
        try:
            for streamerUsername in config["streamers"]:
                if config["streamers"][streamerUsername]["channels"]:
                    timeout = 2/len(config["streamers"])
                    if timeout < 1:
                        timeout = 1
                    await asyncio.sleep(timeout)
                    await send_notification(streamerUsername)
        except Exception as e:
            print(f"{e}")
            pass


async def main():
    notification_task = asyncio.create_task(send_notifications())
    await bot.start(config["token"])
    await notification_task


if __name__ == "__main__":
    asyncio.run(main())