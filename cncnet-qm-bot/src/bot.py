# bot.py
import os
from http.client import HTTPException

import discord
from apiclient import JsonResponseHandler
from discord import Forbidden, DiscordServerError
from discord.ext import tasks
from discord.utils import get
from dotenv import load_dotenv
from discord.ext import commands
from CnCNetApiSvc import CnCNetApiSvc
from io import StringIO

load_dotenv()
TOKEN = os.getenv('DISCORD_CLIENT_SECRET')
intents = discord.Intents(messages=True, guilds=True, message_content=True, guild_messages=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intents)
global cnc_api_client
global ladders
global burg

BURG_ID = 123726717067067393  # Burg#8410
YR_DISCORD_ID = 252268956033875970  # YR Discord Server ID
YR_BOT_CHANNEL_LOGS_ID = 852300478691672146  # cncnet-bot-logs
QM_BOT_CHANNEL_NAME = "qm-bot"


@bot.event
async def on_ready():
    print("bot online")

    global cnc_api_client
    cnc_api_client = CnCNetApiSvc(
        response_handler=JsonResponseHandler
    )

    global ladders
    ladders = []
    ladders_json = cnc_api_client.fetch_ladders()
    for item in ladders_json:
        if item["private"] == 0:
            ladders.append(item["abbreviation"])

    ladders_string = ", ".join(ladders)
    print(f"Ladders found: ({ladders_string})")

    await purge_bot_channel()  # Delete messages in bot-channel
    fetch_active_qms.start()
    update_qm_roles.start()

    global burg
    burg = bot.get_user(123726717067067393)


@bot.command()
async def maps(ctx, arg=""):
    print("Fetching maps for ladder '{arg}'")

    if not ladders:
        await ctx.send("Error: No ladders available")
        return

    if not arg:
        ladders_string = ', '.join(ladders)
        await ctx.send(f"No ladder provided, select a valid ladder from `[{ladders_string}]`, like `!maps ra2`")
        return

    if arg not in ladders:
        ladders_string = ', '.join(ladders)
        await ctx.send(f"{arg} is not a valid ladder from `{ladders_string}`")
        return

    maps_json = cnc_api_client.fetch_maps(arg)

    maps_arr = []
    for item in maps_json:
        maps_arr.append(item["description"])

    if not maps_arr:
        await ctx.send(f"Error: No maps found in ladder': {arg}'")
        return

    maps_string = '\n'.join(maps_arr)
    message = f"** {arg} ** maps:\n```\n{maps_string}\n```"
    await ctx.send(message)


@tasks.loop(minutes=1)
async def fetch_active_qms():
    if not ladders:
        print("Error: No ladders available")
        return

    guilds = bot.guilds
    for server in guilds:
        channel = discord.utils.get(server.channels, name=QM_BOT_CHANNEL_NAME)

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

            qms_json = cnc_api_client.fetch_qms(ladder_abbrev)
            if not qms_json:
                return

            # Display active games in all ladders
            for ladder_abbrev_i in qms_json:
                qms_arr = []
                for item in qms_json[ladder_abbrev_i]:
                    qms_arr.append(item.strip())

                # Get players in queue
                in_queue_json = cnc_api_client.fetch_stats(ladder_abbrev_i)
                if not in_queue_json:
                    return

                in_queue = in_queue_json['queuedPlayers']
                total_in_qm = in_queue + (len(qms_arr) * 2)
                message = str(total_in_qm) + " player(s) in **" + ladder_abbrev_i.upper() + "** QM:\n- " \
                          + str(in_queue) + " player(s) in queue"

                if qms_arr:
                    message += "\n- " + str(len(qms_arr)) + " active matches:\n```\n- " \
                               + '\n- '.join(qms_arr) + "\n```\n"
                else:
                    message += "\n- 0 active matches.\n\n"

                whole_message += message

        if whole_message:
            try:
                await channel.send(whole_message, delete_after=56)
            except HTTPException as he:
                msg = f"Failed to send message: '{whole_message}', exception '{he}'"
                print(msg)
                await burg.send(msg)
                return
            except Forbidden as f:
                msg = f"Failed to send message due to forbidden error: '{whole_message}', exception '{f}'"
                print(msg)
                await burg.send(msg)
                return
            except DiscordServerError as de:
                msg = f"Failed to send message due to DiscordServerError:  '{whole_message}', exception '{de}'"
                print(msg)
                await burg.send(msg)
                return


@bot.command()
async def purge_bot_channel_command(ctx):
    if not ctx.message.author.guild_permissions.administrator:
        print(f"{ctx.message.author} is not admin, exiting command.")
        return
    await purge_bot_channel()


async def purge_bot_channel():
    guilds = bot.guilds

    for server in guilds:

        channel = discord.utils.get(server.channels, name=QM_BOT_CHANNEL_NAME)

        if not channel:
            continue

        deleted = await channel.purge()
        print(f"Deleted {len(deleted)} message(s) from: server '{server.name}', channel: '{channel.name}'")


def is_in_bot_channel(ctx):
    return ctx.channel.name == QM_BOT_CHANNEL_NAME or ctx.message.author.guild_permissions.administrator


@tasks.loop(hours=8)
async def update_qm_roles():
    await remove_qm_roles()  # remove discord members QM roles

    await assign_qm_role()  # assign discord members QM roles


async def remove_qm_roles():
    print("Removing QM roles")
    guilds = bot.guilds

    for server in guilds:

        if server.id != YR_DISCORD_ID:  # YR discord
            continue

        for member in server.members:
            for role in member.roles:

                if role.name.lower() == 'RA2 QM Rank 1'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM Rank 1'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'RA2 QM Top 3'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM Top 3'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'RA2 QM TOP 5'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM TOP 5'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'RA2 QM TOP 10'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM TOP 10'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'RA2 QM TOP 10'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM TOP 10'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'RA2 QM TOP 25'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM TOP 25'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'RA2 QM TOP 50'.lower():
                    await member.remove_roles(role)
                elif role.name.lower() == 'YR QM TOP 50'.lower():
                    await member.remove_roles(role)

    print("Finished removing QM roles")


async def assign_qm_role():
    print("Assigning QM Roles")
    guilds = bot.guilds

    for server in guilds:

        if server.id != YR_DISCORD_ID:  # YR discord
            continue

        # Fetch QM player ranks
        rankings_json = cnc_api_client.fetch_rankings()
        if not rankings_json:
            return

        ladder_abbrev_arr = ["RA2", "YR"]
        for ladder in ladder_abbrev_arr:
            rank = 0
            text = ""
            for item in rankings_json[ladder]:
                rank = rank + 1

                discord_name = item["discord_name"]
                player_name = item["player_name"]

                if not discord_name:
                    message = f"No discord name found for player '{player_name}', rank {rank}"
                    text += message + "\n"
                    continue

                member = server.get_member_named(discord_name)  # find the discord user by the name provided

                if not member:
                    message = f"No user found with name '{discord_name}' for player '{player_name}', rank {rank}, in " \
                              f"server {server} "

                    text += message + "\n"
                    continue

                role_name = ""
                if ladder == "YR" and rank == 1:
                    role_name = "YR QM Rank 1"
                elif ladder == "RA2" and rank == 1:
                    role_name = "RA2 QM Rank 1"
                elif ladder == "YR" and rank <= 3:
                    role_name = "YR QM Top 3"
                elif ladder == "RA2" and rank <= 3:
                    role_name = "RA2 QM Top 3"
                elif ladder == "YR" and rank <= 5:
                    role_name = "YR QM Top 5"
                elif ladder == "RA2" and rank <= 5:
                    role_name = "RA2 QM Top 5"
                elif ladder == "YR" and rank <= 10:
                    role_name = "YR QM Top 10"
                elif ladder == "RA2" and rank <= 10:
                    role_name = "RA2 QM Top 10"
                elif ladder == "YR" and rank <= 25:
                    role_name = "YR QM Top 25"
                elif ladder == "RA2" and rank <= 25:
                    role_name = "RA2 QM Top 25"
                elif ladder == "YR" and rank <= 50:
                    role_name = "YR QM Top 50"
                elif ladder == "RA2" and rank <= 50:
                    role_name = "RA2 QM Top 50"

                if not role_name:
                    message = f"No valid role found for ladder '{ladder}' rank {rank}"

                    text += message + "\n"
                    continue

                role = get(server.roles, name=role_name)
                if not role:
                    message = f"No valid role found for role_name '{role_name}'"

                    text += message + "\n"
                    continue

                message = f"Assigning role '{role}' to user '{member}', (player '{player_name}', rank: {rank})"
                text += message + "\n"

                await member.add_roles(role)  # Add the Discord QM role

            channel = bot.get_channel(YR_BOT_CHANNEL_LOGS_ID)
            buffer = StringIO(text)
            f = discord.File(buffer, filename=f"{ladder}_update_qm_roles_log.txt")
            await channel.send(file=f)
    print("Completed assigning QM Roles")

bot.run(TOKEN)
