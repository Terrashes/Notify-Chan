import requests
import discord
import asyncio
import json
import logging
import logging.handlers
from discord.ext import commands, tasks
from datetime import *
import os
import sys


logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
logging.getLogger("discord.http").setLevel(logging.INFO)


handler = logging.handlers.RotatingFileHandler(
    filename="debug.log", encoding="utf-8", maxBytes=32 * 1024 * 1024, backupCount=5
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def writeConfig():
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4, separators=(",", ": "))


with open("config.json", "r") as f:
    config = json.load(f)

embedColor = 0x8000FF


def get_prefix(client, message):
    return config["servers"][str(message.guild.id)]["prefix"], "n!"


intents = discord.Intents.all()
startupDate = datetime.now(timezone.utc)
bot = commands.Bot(command_prefix=get_prefix, help_command=None, intents=intents)


def beautifyDateDelta(date):
    timeDelta = datetime.now(timezone.utc) - date
    timeDeltaDays = timeDelta.days
    timeDeltaSecs = int((timeDelta.total_seconds() - timeDelta.days * 86400) // 1)
    timeParams = [
        timeDeltaDays // 365,
        timeDeltaDays % 365 // 30,
        timeDeltaDays % 365 % 30,
        timeDeltaSecs // 3600,
        timeDeltaSecs % 3600 // 60,
        timeDeltaSecs % 3600 % 60,
    ]
    return timeParams


@bot.event
async def on_ready():
    activity = discord.Game(name="n!help")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"[{startupDate.isoformat(sep=' ')}] Notify Chan is online now!")


@bot.event
async def on_guild_join(guild):
    config["servers"].update(
        {
            str(guild.id): {
                "prefix": "n!",
                "joinMessageChannel": "",
                "leaveMessageChannel": "",
                "joinMessage": "{} joined the server!",
                "leaveMessage": "{} left the server!",
            }
        }
    )
    writeConfig()


@bot.event
async def on_guild_remove(guild):
    del config["servers"][str(guild.id)]
    writeConfig()


@bot.command()
async def onjoin(ctx):
    config["servers"][str(ctx.guild.id)]["joinMessageChannel"] = str(ctx.channel.id)
    if message == None:
        message = "{} just joined the server! Welcome!☺✋"

    config["servers"][str(ctx.guild.id)]["joinMessage"] = message
    writeConfig()
    await ctx.channel.send(
        "Now notification about new members will be shown in this channel"
    )


@bot.command()
async def onjoindel(ctx):
    del config["servers"][str(ctx.guild.id)]["joinMessageChannel"]
    del config["servers"][str(ctx.guild.id)]["joinMessage"]
    writeConfig()
    await ctx.channel.send(
        "Now notification about new members will be shown in this channel"
    )


@bot.event
async def on_member_join(Member):
    channel = bot.get_channel(
        int(config["servers"][str(Member.guild.id)]["joinMessageChannel"])
    )
    await channel.send(
        config["servers"][str(Member.guild.id)]["joinMessage"].format(Member.mention)
    )


@bot.command()
async def onleave(ctx, message=None):
    config["servers"][str(ctx.guild.id)]["leaveMessageChannel"] = str(ctx.channel.id)
    if message == None:
        message = "{} just left the server! Bye!😔"
    config["servers"][str(ctx.guild.id)]["leaveMessage"] = message
    writeConfig()
    await ctx.channel.send(
        "Now notification about left members will be shown in this channel"
    )


@bot.command()
async def onleavedel(ctx):
    del config["servers"][str(ctx.guild.id)]["leaveMessageChannel"]
    del config["servers"][str(ctx.guild.id)]["leaveMessage"]
    writeConfig()
    await ctx.channel.send(
        "Now notification about new members will be shown in this channel"
    )


@bot.event
async def on_member_remove(Member):
    channel = bot.get_channel(
        int(config["servers"][str(Member.guild.id)]["leaveMessageChannel"])
    )
    await channel.send(
        config["servers"][str(Member.guild.id)]["leaveMessage"].format(
            str(Member.name) + "#" + str(Member.discriminator)
        )
    )


@bot.group(invoke_without_command=True)
async def help(ctx):
    prefix = get_prefix(bot, ctx)[1]
    embed = discord.Embed(
        title="Hi👋 My name is `Notify Chan`! \nHere's my commands:", color=embedColor
    )
    embed.add_field(
        name="`twadd` to add twitch channel",
        value=(f"Sample: `n!twadd zxcursed`"),
        inline=False,
    )
    embed.add_field(
        name="",
        value=(
            f"To mention streamer while creating message use `$user`\nSample: $user is live!."
        ),
        inline=False,
    )
    embed.add_field(
        name="`twdel` to remove twitch channel",
        value=(f"Sample: `n!twdel zxcursed`"),
        inline=False,
    )
    embed.add_field(name="`twlist` to show all tracking channels", value="", inline=False)
    embed.add_field(name="Other commands:", value="", inline=False)
    embed.add_field(
        name="`prefix` to change server prefix",
        value=(f"Current server prefix is `{prefix}`."),
        inline=False,
    )
    embed.add_field(
        name="`status` to check bot's statistics",
        value=("This command doesn't have any arguments."),
        inline=False,
    )
    embed.add_field(
        name="`onjoin` and `onleave` to add messages for users who just joined and left server",
        value=('Sample: `n!onjoin "Welcome, {}!"` ({} - for mention user)'),
        inline=False,
    )
    embed.add_field(
        name="`roll` to roll a random number",
        value=("Sample: `n!roll 1 1000` (By default it's rolling in 1-100 interval.)"),
        inline=False,
    )
    embed.add_field(
        name="`flip` to flip a coin",
        value=(
            "Sample: `n!flip head` (Guess side of the coin using `head/tail` after command)"
        ),
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(pass_context=True)
async def status(ctx):
    botOnlineDuration = beautifyDateDelta(startupDate)
    serverCount = len(config["servers"])
    embed = discord.Embed(
        color=embedColor,
        title="Bot's uptime",
        description="Uptime: {} days, {} hours, {} min, {} sec".format(
            botOnlineDuration[2],
            botOnlineDuration[3],
            botOnlineDuration[4],
            botOnlineDuration[5],
        ),
    )
    embed.add_field(
        name="Last started",
        value=(startupDate.strftime("`%H:%M:%S` `%d.%m.%Y`")),
        inline=False,
    )
    embed.add_field(
        name="Servers",
        value=("Working on `{}` servers".format(serverCount)),
        inline=False,
    )
    embed.add_field(
        name="Latency",
        value=("Current latency is `{}` ms".format(int(bot.latency * 1000 // 1))),
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def prefix(ctx, prefixValue=""):
    if prefixValue == config["servers"][str(ctx.guild.id)]["prefix"]:
        await ctx.channel.send(
            "Current prefix is `{}`. Server prefix didn't change because you specified the same prefix as current.".format(
                config["servers"][str(ctx.guild.id)]["prefix"]
            )
        )
    elif prefixValue == "":
        await ctx.channel.send(
            "Current prefix is `{}`.".format(
                config["servers"][str(ctx.guild.id)]["prefix"]
            )
        )
    else:
        config["servers"][str(ctx.guild.id)]["prefix"] = prefixValue
        writeConfig()
        await ctx.channel.send(
            "Server prefix changed. Current prefix is `{}`.".format(
                config["servers"][str(ctx.guild.id)]["prefix"]
            )
        )


TWITCH_CLIENT_ID = config["twitch_client_id"]
TWITCH_CLIENT_SECRET = config["twitch_secret"]


auth_url = "https://id.twitch.tv/oauth2/token"
auth_params = {
    "client_id": TWITCH_CLIENT_ID,
    "client_secret": TWITCH_CLIENT_SECRET,
    "grant_type": "client_credentials",
    "scope": "user:read:email",
}


response = requests.post(auth_url, params=auth_params).json()


twitch_access_token = response["access_token"]


def is_stream_live(streamerUsername):
    try:
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {twitch_access_token}",
        }
        TWITCH_API_URL = (
            f"https://api.twitch.tv/helix/streams?user_login={streamerUsername}"
        )
        response = requests.get(TWITCH_API_URL, headers=headers).json()
        status = bool(response.get("data", []))
        title = ""
        thumbnail = ""
        if status:
            title = response["data"][0]["title"]
            thumbnail = response["data"][0]["thumbnail_url"].format(
                width=640, height=360
            )
        return status, title, thumbnail
    except Exception as e:
        print(f"{e}")
        pass


@bot.command()
async def twadd(ctx, streamerUsername=None):
    if streamerUsername:
        messageLive = f"Hey everyone! {streamerUsername} is now live!"
        messageOff = f"{streamerUsername} is offline now"
        await ctx.channel.send(
            "Please enter a message for when the streamer goes live:"
        )

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            TWITCH_API_URL = (
                f"https://api.twitch.tv/helix/streams?user_login={streamerUsername}"
            )
            headers = {
                "Client-ID": TWITCH_CLIENT_ID,
                "Authorization": f"Bearer {twitch_access_token}",
            }
            response = requests.get(TWITCH_API_URL, headers=headers)

            if response.status_code == 400:
                await ctx.channel.send(
                    f"Error: channel not found for {streamerUsername}"
                )
            elif response.status_code == 200:
                try:
                    messageLive = (
                        await bot.wait_for("message", check=check, timeout=60)
                    ).content
                    if "$user" not in messageLive:
                        messageLive += f" {streamerUsername}"
                    else:
                        messageLive = messageLive.replace("$user", streamerUsername)
                except asyncio.TimeoutError:
                    await ctx.channel.send("You took too long to respond.")
                await ctx.channel.send(
                    "Please enter a message for when the streamer goes offline:"
                )
                try:
                    messageOff = (
                        await bot.wait_for("message", check=check, timeout=60)
                    ).content
                    if "$user" not in messageOff:
                        messageOff += f" {streamerUsername}"
                    else:
                        messageOff = messageOff.replace("$user", streamerUsername)
                except asyncio.TimeoutError:
                    await ctx.channel.send("You took too long to respond.")
                if streamerUsername not in config["twitch"]:
                    config["twitch"].update(
                        {
                            str(streamerUsername): {
                                "status": False,
                                "channels": {
                                    str(ctx.channel.id): {
                                        "messageLive": messageLive,
                                        "messageOff": messageOff,
                                    }
                                },
                            }
                        }
                    )
                    writeConfig()
                    await ctx.channel.send(f"Streamer `{streamerUsername}` added")
                elif (
                    ctx.channel.id not in config["twitch"][streamerUsername]["channels"]
                ):
                    config["twitch"][streamerUsername]["channels"].update(
                        {
                            str(ctx.channel.id): {
                                "messageLive": messageLive,
                                "messageOff": messageOff,
                            }
                        }
                    )
                    writeConfig()
                    await ctx.channel.send(f"Streamer `{streamerUsername}` added")
                else:
                    print("heres error")
                    await ctx.channel.send(
                        f"Streamer `{streamerUsername}` was already added"
                    )
                await send_notification(streamerUsername)
        except Exception as e:
            print(f"{e}")
            await ctx.channel.send(f"Sorry, an error occured. Please, try again.")
            pass
    else:
        await ctx.channel.send("Please, specify streamer's nickname to add")


@bot.command()
async def twdel(ctx, streamerUsername=None):
    if streamerUsername:
        try:
            del config["twitch"][streamerUsername]["channels"][str(ctx.channel.id)]
            if len(config["twitch"][streamerUsername]["channels"]) == 0:
                del config["twitch"][streamerUsername]
            writeConfig()
            await ctx.channel.send(f"Streamer `{streamerUsername}` deleted")
        except Exception as e:
            print(f"remove {e}")
            await ctx.channel.send(f"Error: channel not found for {streamerUsername}")
    else:
        await ctx.channel.send("Please, specify streamer's nickname to remove")


@bot.command()
async def twlist(ctx):
    message = "**Streamers:**"
    for streamerUsername in config["twitch"]:
        try:
            if str(ctx.channel.id) in config["twitch"][streamerUsername]["channels"]:
                if config["twitch"][streamerUsername]["status"]:
                    status = ":green_circle:`live`"
                else:
                    status = ":o:`offline`"
                message = "".join([message, f"\n {streamerUsername} {status}"])
        except Exception:
            pass
    if message == "**Streamers:**":
        await ctx.channel.send("There is no tracking streamers in this channel")
    else:
        await ctx.channel.send(message)


async def send_notification(streamerUsername):
    streamer_info = config["twitch"][streamerUsername]
    streamer_info["status"] = config["twitch"][streamerUsername]["status"]
    # print(f'[{datetime.now(timezone.utc)}]working on {streamerUsername}')
    params = is_stream_live(streamerUsername)
    status = params[0]
    if status != streamer_info["status"]:
        try:
            for channel in streamer_info["channels"].keys():
                if channel is not None:
                    channelId = bot.get_channel(int(channel))
                    if status:
                        title = params[1]
                        thumbnail = params[2]
                        embed = discord.Embed(
                            color=embedColor,
                            title=config["twitch"][streamerUsername]["channels"][
                                channel
                            ]["messageLive"],
                            description="",
                        )
                        embed.add_field(
                            name=title,
                            value=f"https://www.twitch.tv/{streamerUsername}",
                            inline=False,
                        )
                        embed.set_image(url=thumbnail)
                        await channelId.send(embed=embed)
                    else:
                        await channelId.send(
                            config["twitch"][streamerUsername]["channels"][channel][
                                "messageOff"
                            ]
                        )
                else:
                    print(f"Error: channel not found for {streamerUsername}")
            config["twitch"][streamerUsername]["status"] = status
            writeConfig()
        except Exception as e:
            print(f"send notif {e}")
            pass


async def send_notifications():
    while not bot.is_closed():
        try:
            timeout = 60
            if config["twitch"]:
                for streamerUsername in config["twitch"]:
                    if config["twitch"][streamerUsername]["channels"]:
                        await send_notification(streamerUsername)
                timeout = 60 / len(config["twitch"])
                if timeout < 10:
                    timeout = 10
            await asyncio.sleep(timeout)
        except Exception as e:
            print(f"{e}")
            pass


async def main():
    notification_task = asyncio.create_task(send_notifications())
    await bot.start(config["token"])
    await notification_task


if __name__ == "__main__":
    asyncio.run(main())
