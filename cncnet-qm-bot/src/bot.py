# bot.py
import os
from http.client import HTTPException

import discord
from apiclient import APIClient, JsonResponseHandler
from apiclient.exceptions import UnexpectedError, ServerError
from discord import Forbidden
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

    qms.start()


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

    message = "**" + arg + "** maps:\n" + "```\n" + '\n'.join(maps_arr) + "\n```"
    await ctx.send(message)


@tasks.loop(minutes=1)
async def qms():

    if not ladders:
        print('Error: No ladders available')
        return

    guilds = bot.guilds
    for server in guilds:
        channel = discord.utils.get(server.channels, name="qm-bot")

        if not channel:
            continue

        ladder_abbrev_arr = []
        if server.id == 188156159620939776:  # CnCNet discord
            ladder_abbrev_arr = ["ra"]
        elif server.id == 252268956033875970:  # YR discord
            ladder_abbrev_arr = ["ra2", "yr"]
        elif server.id == 818265922615377971:  # RA2CashGames discord
            ladder_abbrev_arr = ["blitz"]

        whole_message = ""

        # Loop through each ladder and get the results
        for ladder_abbrev in ladder_abbrev_arr:

            qms_json = api_client.fetch_qms(ladder_abbrev)
            if not qms_json:
                return

            # Display active games in all ladders
            for ladder_abbrev_i in qms_json:
                qms_arr = []
                for item in qms_json[ladder_abbrev_i]:
                    qms_arr.append(item.strip())

                # Get players in queue
                in_queue_json = api_client.fetch_stats(ladder_abbrev_i)
                if not in_queue_json:
                    return

                in_queue = in_queue_json['queuedPlayers']
                message = "**" + ladder_abbrev_i.upper() + "** QMs: `" + str(in_queue) + " player(s) in queue`"

                if qms_arr:
                    message += ", `" + str(len(qms_arr)) + " Active Matches`:\n```\n- "\
                               + '\n- '.join(qms_arr) + "\n```\n"
                else:
                    message += ". `0 Active matches.`\n"

                whole_message += message

        if whole_message:
            try:
                await channel.send(whole_message, delete_after=58)
            except HTTPException as he:
                print("Failed to send message: " + whole_message)
                print(he)
                return
            except Forbidden as f:
                print("Failed to send message due to forbidden error: " + whole_message)
                print(f)
                return


def is_in_bot_channel(ctx):
    return ctx.channel.name == "qm-bot" or ctx.message.author.guild_permissions.administrator


class MyClient(APIClient):

    def fetch_stats(self, ladder):
        url = "https://ladder.cncnet.org/api/v1/qm/ladder/" + ladder + "/stats"
        return self.get_call(url)

    def fetch_ladders(self):
        url = "https://ladder.cncnet.org/api/v1/ladder"
        return self.get_call(url)

    def fetch_maps(self, ladder):
        url = "https://ladder.cncnet.org/api/v1/qm/ladder/" + ladder + "/maps/public"
        return self.get_call(url)

    def fetch_qms(self, ladder):
        url = "https://ladder.cncnet.org/api/v1/qm/ladder/" + ladder + "/current_matches"
        return self.get_call(url)

    def get_call(self, url):
        try:
            return self.get(url)
        except UnexpectedError as ue:
            print(ue.message)
            return None
        except HTTPException as he:
            print(he)
            return None
        except ServerError as se:
            print(se)
            return None


bot.run(TOKEN)
