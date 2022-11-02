# bot.py
import os

import discord
from apiclient import APIClient, JsonResponseHandler
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
    get_stats.start()

    global api_client
    api_client = MyClient(
        response_handler=JsonResponseHandler
    )

    global ladders
    ladders = []
    ladders_json = api_client.fetch_ladders()
    for item in ladders_json:
        ladders.append(item['abbreviation'])
    print("Ladders found: (" + ', '.join(ladders) + ")")


@bot.command()
async def maps(ctx, arg):
    print("Fetching maps for ladder: " + arg)

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

    await ctx.send("```" + '\n'.join(maps_arr) + "```")


@tasks.loop(seconds=60)
async def get_stats():
    print("getting stats")

    active_players_yr = api_client.fetch_stats("yr")
    active_players_ra2 = api_client.fetch_stats("ra2")

    channel_name_ra2 = "ra2-active-players"
    channel_name_yr = "yr-active-players"

    new_name_ra2 = channel_name_ra2 + "-" + str(active_players_ra2)
    new_name_yr = channel_name_yr + "-" + str(active_players_yr)

    guilds = bot.guilds
    for server in guilds:
        channels = server.channels
        for channel in channels:
            if channel.name.__contains__(channel_name_ra2) and channel.name != new_name_ra2:
                await channel.edit(name=new_name_ra2)
            elif channel.name.__contains__(channel_name_yr) and channel.name != new_name_yr:
                await channel.edit(name=new_name_yr)


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


bot.run(TOKEN)
