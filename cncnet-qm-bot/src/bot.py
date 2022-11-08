# bot.py
import os

import discord
from apiclient import APIClient, JsonResponseHandler
from apiclient.exceptions import ServerError
from discord.ext import tasks
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents(messages=True, guilds=True, message_content=True, guild_messages=True)
bot = commands.Bot(command_prefix='!', intents=intents)
global api_client
global ladders


@bot.event
async def on_ready():
    print("bot online")

    global api_client
    api_client = MyClient(
        response_handler=JsonResponseHandler
    )

    global ladders
    ladders = []
    ladders_json = api_client.fetch_ladders()
    for item in ladders_json:
        if item["private"] == 0:
            ladders.append(item['abbreviation'])
    print("Ladders found: (" + ', '.join(ladders) + ")")

    get_stats.start()
    qms.start()


@bot.command()
async def maps(ctx, arg):
    print("Fetching maps for ladder: " + arg)

    channel = discord.utils.get(ctx.guild.channels, name="qm-bot")

    if not is_in_bot_channel(ctx.channel, arg):
        await ctx.send("Please use for " + channel.mention
                       + " bot commands")
        return

    if not ladders:
        await ctx.send('Error: No ladders available')
        return

    if arg not in ladders:
        await ctx.send(arg + " is not a valid ladder from (" + ', '.join(ladders) + ")")
        return

    maps_json = api_client.fetch_maps(arg)

    maps_arr = []
    for item in maps_json:
        maps_arr.append(item['description'])

    if not maps_arr:
        await ctx.send('Error: No maps found in ladder ' + arg)
        return

    await ctx.send("```\n" + '\n'.join(maps_arr) + "\n```")


@tasks.loop(minutes=1)
async def qms():
    print("Fetching active matches")

    if not ladders:
        print('Error: No ladders available')
        return

    guilds = bot.guilds
    for server in guilds:
        channel = discord.utils.get(server.channels, name="qm-bot")

        if not channel:
            continue

        ladder_abbrev = "all"
        if server.id == 188156159620939776:  # CnCNet discord
            ladder_abbrev = "ra"

        qms_json = api_client.fetch_qms(ladder_abbrev)

        # Display active games in all ladders
        whole_message = ""
        for ladder_abbrev in qms_json:
            qms_arr = []
            for item in qms_json[ladder_abbrev]:
                qms_arr.append(item.strip())

            if qms_arr:
                message = "Active **" + ladder_abbrev.upper() + "** QMs:\n```\n" + '\n'.join(qms_arr) + "\n```\n"
                whole_message += message

        if whole_message:
            await channel.send(whole_message, delete_after=59)


def is_in_bot_channel(channel, message):
    return channel.name == "qm-bot" or message.author.guild_permissions.administrator


@tasks.loop(minutes=5)
async def get_stats():
    print("getting stats and updating discord channel names")

    channel_name_ra2 = "ra2-active-players"
    channel_name_yr = "yr-active-players"
    channel_name_ra = "ra-active-players"

    try:
        active_players_yr = api_client.fetch_stats("yr")
        active_players_ra2 = api_client.fetch_stats("ra2")
        active_players_ra = api_client.fetch_stats("ra")
    except ServerError:
        print("An error occurred when fetching qm stats: " + ServerError.message)
        return

    new_name_ra2 = channel_name_ra2 + "-" + str(active_players_ra2)
    new_name_yr = channel_name_yr + "-" + str(active_players_yr)
    new_name_ra = channel_name_ra + "-" + str(active_players_ra)

    guilds = bot.guilds
    for server in guilds:
        channels = server.channels
        for channel in channels:
            if channel.name.__contains__(channel_name_ra2) and channel.name != new_name_ra2:
                await channel.edit(name=new_name_ra2)
            elif channel.name.__contains__(channel_name_yr) and channel.name != new_name_yr:
                await channel.edit(name=new_name_yr)
            elif channel.name.__contains__(channel_name_ra) and channel.name != new_name_ra:
                await channel.edit(name=new_name_ra)


class MyClient(APIClient):

    def fetch_stats(self, ladder):
        url = "https://ladder.cncnet.org/api/v1/qm/ladder/" + ladder + "/stats"
        json = self.get(url)
        queued_players = json['queuedPlayers']
        active_matches = json['activeMatches']
        return queued_players + active_matches

    def fetch_ladders(self):
        url = "https://ladder.cncnet.org/api/v1/ladder"
        return self.get(url)

    def fetch_maps(self, ladder):
        url = "https://ladder.cncnet.org/api/v1/qm/ladder/" + ladder + "/maps/public"
        return self.get(url)

    def fetch_qms(self, ladder):
        url = "https://ladder.cncnet.org/api/v1/qm/ladder/" + ladder + "/current_matches"
        return self.get(url)


bot.run(TOKEN)
