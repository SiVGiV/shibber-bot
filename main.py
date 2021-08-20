import discord
import discord_slash
import json
import time
import os
from datetime import datetime as dt

import utils
from loggable import Loggable

from dotenv import load_dotenv
from discord.http import Route
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands, manage_components
from discord_slash.model import ButtonStyle

from tinydb import TinyDB, Query
from tpblite import TPB
from imdb import IMDb, IMDbError, helpers
from random import randint
from colorama import init, Fore

load_dotenv()
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
imdb_client = IMDb()
poll_db = TinyDB("./databases/poll.db")
token = os.getenv("BOTTINGSON_TOKEN")
t = TPB("https://tpb.party/")

log = Loggable(
    "./logs/" + dt.now().strftime("%H%M%S_%d%m%Y.log"),
    colors=[
        "",
        Fore.LIGHTBLUE_EX,
        Fore.GREEN,
        Fore.YELLOW,
        Fore.RED
    ],
    log_to=[
        {"console": True, "file": False},
        {"console": True, "file": True},
        {"console": True, "file": True},
        {"console": True, "file": True},
        {"console": True, "file": True}
    ],
    file_wrapper=lambda msg, lt: f"[{dt.now().strftime('%H:%M:%S %d/%m/%y')}] {lt.name} | {msg}",
    print_wrapper=lambda msg, lt: f"[{dt.now().strftime('%H:%M:%S %d/%m/%y')}] {msg}"
)

with open("bot-values.json") as f:
    _bot_values = json.load(f)
if not _bot_values:
    _bot_values = {"slash_cmd_guilds": []}


@client.event
async def on_ready():
    log.success("Bot Connected")


@client.event
async def on_component(ctx: discord_slash.ComponentContext):
    log.event(
        f"Component event detected: [{ctx.custom_id},"
        f"msg:{ctx.origin_message_id},channel:{ctx.channel_id}]")
    if ctx.custom_id.startswith("poll_"):
        await handle_poll_component(ctx)


# <<<====================/YOUTUBE================================
# Command: /youtube
# Sends invite link to Youtube Together in user's voice channel
@slash.slash(name="youtube",
             description="Sends an invite link to a Youtube Together activity in your voice channel.",
             guild_ids=_bot_values["slash_cmd_guilds"])
async def youtube(ctx):
    log.event(f"/youtube command detected in [{ctx.channel_id}:{ctx.guild_id}]")
    if not ctx.guild:  # if the message was sent in a DMChannel
        log.warning(f"/youtube: Command sent in DM. handling canceled.")
        await ctx.reply(content="Please use the command inside of a server (the bot must also be on that server).")
        return

    member = await ctx.guild.fetch_member(ctx.author_id)
    if not member.voice:  # if the author isn't connected to voice
        log.warning(f"/youtube: User not connected to VC, handling canceled.")
        await ctx.send(content="You don't appear to be in any voice channel.")
        return

    r = Route("POST", "/channels/{channel_id}/invites",
              channel_id=ctx.author.voice.channel.id)
    payload = {
        "max_age": 86400,
        "max_uses": 0,
        "temporary": False,
        "target_application_id": "755600276941176913",
        "target_type": 2
    }
    try:
        inv = await client.http.request(r, reason=None, json=payload)  # send an http to get the channel invite
    except discord.DiscordException as e:
        log.error(f"Error with Discord.py: {e}")
        await ctx.send("Sorry, but there was a problem with handling your command. Try again later.")
    else:
        embed = discord.Embed(color=0xff0000)  # create new embed
        embed.set_thumbnail(url="https://i.imgur.com/6XnPq2s.png")
        embed.add_field(name="Your Youtube Together invite is here!",
                        value=(
                            f"[Click here to launch Youtube Together](http://discord.gg/{inv['code']})\n"
                            f"Invite expiration: <t:{int(time.time()) + 86400}:R>"
                        ), inline=False)
        await ctx.send(embed=embed)
    finally:
        log.success("/youtube: Handling finished")


# ===========================/YOUTUBE===========================>>>


# <<<========================/POLL=================================
@slash.slash(name="poll",
             description="Posts a poll in the channel",
             guild_ids=_bot_values["slash_cmd_guilds"],
             options=[  # Create all of the slash command options
                 manage_commands.create_option(
                     name="question", description="The poll question",
                     option_type=3, required=True),
                 manage_commands.create_option(
                     name="choice1", description="A poll choice",
                     option_type=3, required=True),
                 manage_commands.create_option(
                     name="choice2", description="A poll choice",
                     option_type=3, required=True),
                 manage_commands.create_option(
                     name="choice3", description="A poll choice",
                     option_type=3, required=False),
                 manage_commands.create_option(
                     name="choice4", description="A poll choice",
                     option_type=3, required=False),
                 manage_commands.create_option(
                     name="choice5", description="A poll choice",
                     option_type=3, required=False),
                 manage_commands.create_option(
                     name="choice6", description="A poll choice",
                     option_type=3, required=False),
                 manage_commands.create_option(
                     name="choice7", description="A poll choice",
                     option_type=3, required=False),
                 manage_commands.create_option(
                     name="choice8", description="A poll choice",
                     option_type=3, required=False)
             ])
async def poll(ctx, **options):
    log.event(f"/poll command detected in [{ctx.channel_id}:{ctx.guild_id}]")
    if not ctx.guild:  # if the message was sent in a DMChannel
        log.warning(f"/poll: Command sent in DM. handling canceled.")
        await ctx.send(content="Please use the command inside of a server (the bot must also be on that server).")
        return
    choices = []
    for option in options:  # import all options into an indexed list except for the question
        if not option == "question":
            choices.append(options[option])
    embed = discord.Embed(
        title=f"Poll by {ctx.author.name}#{ctx.author.discriminator}",
        description="**" + options["question"] + "**",
        color=randint(0x000000, 0xffffff))
    i = 0
    for choice in choices:  # add a field for each poll choice
        i += 1
        embed.add_field(
            name=f"{utils.get_number_emoji(i)} - {choice}",
            value=f"0 votes (0%)\n{'░' * 20}",
            inline=False
        )
    components = []
    for i in range(len(choices)):
        components.append(
            manage_components.create_button(  # create a button for each option
                style=ButtonStyle.grey,
                label=utils.ellipsis_truncate(choices[i], 30, mid_ellipsis=True),
                emoji=utils.get_number_emoji_dict(i + 1),
                custom_id=f"poll_{i}"
            )
        )
    if len(components) > 5:  # if more than 5 buttons
        max_row_width = len(components) // 2 + len(components) % 2  # spread buttons on 2 rows
    else:
        max_row_width = 5  # if less or equal 5, put them all in one row
    actionrows = manage_components.spread_to_rows(*components, max_in_row=max_row_width)
    await ctx.send(embed=embed, components=actionrows)
    log.success("/poll: Handling finished.")


async def handle_poll_component(ctx: discord_slash.ComponentContext):
    log.event("Poll choice detected.")
    if not ctx.origin_message:  # if there is no origin message, cancel
        log.warning("Failed to locate origin message for " + ctx.custom_id)
        return
    embed = ctx.origin_message.embeds[0]  # make the poll embed into a dict
    vote_count = []
    for field in embed.fields:  # scrub current embed for data
        vote_count.append(int(field.value.split()[0])),  # split by whitespace, take first choice = vote count

    q = Query()
    if poll_db.contains((q.poll_id == ctx.origin_message_id) & (q.user_id == ctx.author.id)):  # if user voted on msg
        res = poll_db.search((q.poll_id == ctx.origin_message_id) & (q.user_id == ctx.author.id))  # look it up
        last_vote = res[0]["option_id"]  # get the last voted item
        vote_count[int(last_vote.split("_")[1])] -= 1  # reduce vote from previous vote
    vote_count[int(ctx.custom_id.split("_")[1])] += 1  # increase vote for current vote
    poll_db.upsert({  # update database if exist, insert if doesn't
        "poll_id": ctx.origin_message_id,  # poll_id = poll message id
        "option_id": ctx.custom_id,  # option_id = poll button custom id ("poll_{N}")
        "user_id": ctx.author.id  # user_id = user who pressed a button
    }, (q.poll_id == ctx.origin_message_id) & (q.user_id == ctx.author.id))  # the query for checking if exists

    total_votes = 0  # total poll votes
    for field in vote_count:  # reconstruct embed with new values
        total_votes += field
    new_embed = discord.Embed(title=embed.title, color=embed.color, description=embed.description)
    for i in range(len(embed.fields)):
        percent = int(vote_count[i] / total_votes * 100)
        new_value = f"{vote_count[i]} votes ({percent}%)\n"
        new_value += "▓" * int(percent // 5)
        new_value += "░" * int(20 - (percent // 5))
        new_embed.add_field(name=embed.fields[i].name, value=new_value, inline=False)

    try:
        await ctx.edit_origin(embed=new_embed)
    except discord.DiscordException:
        log.error("Failed to edit origin message for " + ctx.custom_id)
    else:
        log.success("Poll choice handling finished.")


# ===========================/POLL==============================>>>


# <<<=======================/IMDB==================================
@slash.slash(name="imdb",
             description="Searches imdb",
             guild_ids=_bot_values["slash_cmd_guilds"],
             options=[
                 manage_commands.create_option(
                     name="search_type",
                     description="The type of imdb listing to search for.",
                     option_type=3,
                     required=True,
                     choices=[
                         manage_commands.create_choice(
                             name="Movie",
                             value="movie"
                         ),
                         manage_commands.create_choice(
                             name="TV Series",
                             value="tv"
                         )
                     ]
                 ),
                 manage_commands.create_option(
                     name="query",
                     description="The search query",
                     option_type=3,
                     required=True
                 )
             ])
async def imdb(ctx, **options):
    log.event(f"/imdb command detected in [{ctx.channel_id}:{ctx.guild_id}]")
    await ctx.defer()  # Display 'bot is thinking' message
    embeds = []
    if options["search_type"] == "movie":  # if search for movie
        try:
            movies = imdb_client.search_movie(options["query"])[:5]  # Take the top 5 results
        except IMDbError as e:
            log.error("IMDb API error: " + str(e) + "\nCanceled handling.")
            await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.")
            return
        movie_info = []  # container to hold the movie information we're gonna use for the embed
        if movies:
            i = 1
            for movie in movies:
                if i <= 0:
                    break
                try:
                    imdb_client.update(movie, info=[
                        "main", "plot"
                    ])
                except IMDbError as e:
                    log.error("IMDb API error: " + str(e) + "\nCanceled handling.")
                    await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.")
                    return
                # skip iteration if 'tv movie' or 'movie'
                if not movie["kind"] == "movie" and not movie["kind"] == "tv movie":
                    continue
                movie_info.append({
                    "title": none2str(movie["title"]),
                    "year": none2str(movie["year"]),
                    "genres": utils.list2str(movie["genres"], 3),
                    "runtime": utils.list2str(movie.get("runtimes")),
                    "plot": utils.list2str(movie.get("plot")),
                    "cover": none2str(movie.get("cover url")),
                    "id": none2str(movie["imdbID"])
                })
                person2str = helpers.makeObject2Txt(personTxt=u"[%(name)s](https://www.imdb.com/name/nm%(personID)s/)")
                temp_directors = movie.get("directors")
                temp_writers = movie.get("writers")
                temp_cast = movie.get("cast")
                directors = []
                writers = []
                cast = []

                if isinstance(temp_directors, list):
                    for person in temp_directors:
                        directors.append(person2str(person))
                else:
                    directors = person2str(temp_directors)

                if isinstance(temp_writers, list):
                    for person in temp_writers:
                        writers.append(person2str(person))
                else:
                    writers = person2str(temp_writers)

                if isinstance(temp_writers, list):
                    for person in temp_cast:
                        cast.append(person2str(person))
                else:
                    cast = person2str(temp_cast)

                movie_info[-1].update({
                    "directors": utils.list2str(directors, 3),
                    "writers": utils.list2str(writers, 3),
                    "cast": utils.list2str(cast, 5),
                })
                i -= 1
            for movie in movie_info:
                embed = discord.Embed(title=f"{movie['title']} ({movie['year']})",
                                      url=f"https://www.imdb.com/title/tt{movie['id']}",
                                      description=f"""`{movie['genres']} | {movie['runtime']} min`
{utils.ellipsis_truncate(movie['plot'], 200)}""",
                                      color=randint(0x000000, 0xffffff))
                embed.set_thumbnail(url=movie['cover'])
                embed.add_field(name="Directed by:", value=movie["directors"], inline=False)
                embed.add_field(name="Written by:", value=movie["writers"], inline=False)
                embed.add_field(name="Cast:", value=movie["cast"], inline=False)
                embeds.append(embed)
                try:
                    await ctx.send(embeds=embeds)
                except discord.DiscordException as e:
                    log.error("Couldn't reply to /imdb. Error:" + str(e))
                else:
                    log.success("/imdb: Handling finished.")
    elif options["search_type"] == "tv":  # if search for tv series
        try:
            shows = imdb_client.search_movie(options["query"])
        except IMDbError as e:
            log.error("IMDb API error: " + str(e) + "\nCanceled handling.")
            await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.")
            return
        show_info = []
        if shows:
            i = 1
            for show in shows:
                if i <= 0:
                    break
                try:
                    imdb_client.update(show, info=[
                        "main", "plot"
                    ])
                except IMDbError as e:
                    log.error("IMDb API error: " + str(e) + "\nCanceled handling.")
                    await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.")
                    return
                if not show["kind"] == "tv series" and not show["kind"] == "tv mini series":
                    continue
                show_info.append({
                    "title": none2str(show["title"]),
                    "year": none2str(show["series years"]),
                    "genres": utils.list2str(show["genres"], 3),
                    "plot": utils.list2str(show.get("plot")),
                    "cover": none2str(show.get("cover url")),
                    "seasons": none2str(show.get("number of seasons")),
                    "id": none2str(show["imdbID"])
                })
                person2str = helpers.makeObject2Txt(personTxt=u"[%(name)s](https://www.imdb.com/name/nm%(personID)s/)")
                temp_writers = show.get("writer")
                temp_creators = show.get("creator")
                temp_cast = show.get("cast")
                writers = []
                creators = []
                cast = []

                if isinstance(temp_writers, list):
                    for person in temp_writers:
                        writers.append(person2str(person))
                else:
                    writers = person2str(temp_writers)

                if isinstance(temp_creators, list):
                    for person in temp_creators:
                        creators.append(person2str(person))
                else:
                    creators = person2str(temp_creators)

                if isinstance(temp_cast, list):
                    for person in temp_cast:
                        cast.append(person2str(person))
                else:
                    cast = person2str(temp_cast)

                show_info[-1].update({
                    "writers": utils.list2str(writers, 3),
                    "creators": utils.list2str(creators, 3),
                    "cast": utils.list2str(cast, 5),
                })
                i -= 1
            for show in show_info:
                embed = discord.Embed(title=f"{show['title']} ({show['year']})",
                                      url=f"https://www.imdb.com/title/tt{show['id']}",
                                      description=f"`{show['genres']}"
                                                  f""" | {show['seasons']} season{'' if show['seasons'] == 1 else 's'}`
{utils.ellipsis_truncate(show['plot'], 200)}""",
                                      color=randint(0x000000, 0xffffff))
                embed.set_thumbnail(url=show['cover'])
                if not show["creators"] is None:
                    embed.add_field(name="Created by:", value=show["creators"], inline=False)
                else:
                    embed.add_field(name="Written by:", value=show["writers"], inline=False)
                embed.add_field(name="Cast:", value=show["cast"], inline=False)
                embeds.append(embed)
                try:
                    await ctx.send(embeds=embeds)
                except discord.DiscordException as e:
                    log.error("Couldn't reply to /imdb. Error:" + str(e))
                else:
                    log.success("/imdb: Handling finished.")


# ==========================/IMDB===============================>>>


# <<<=======================/TORRENT===============================
@slash.slash(name="piratebay",
             description="fetches from piratebay a list of magnet links for a search query.",
             guild_ids=_bot_values["slash_cmd_guilds"],
             options=[
                 manage_commands.create_option(
                     name="query",
                     description="The search query",
                     option_type=3,
                     required=True
                 )
             ])
async def piratebay(ctx, **options):
    log.event("/torrent command received")
    await ctx.defer()
    tor_limit = 5
    res_embeds = []
    print(options["query"])
    piratebay_torrents = t.search(options["query"])
    # create piratebay embed
    temp_embed = discord.Embed(title="PirateBay Results", description=f"Query: {options['query']}")
    i = 1
    for tor in piratebay_torrents:
        if i > tor_limit:
            break
        try:
            magnet = utils.magnet_shorten(tor.magnetlink)
        except NameError as e:
            log.error(str(e))
            await ctx.send("There was an error in processing your request. Please try again later.")
            return
        temp_embed.add_field(
            value=f"{i}) **Name: [{tor.title}]({magnet})**\n*{tor.category}*",
            name=f"Size: {tor.filesize} | Seeders: {tor.seeds} | Leechers: {tor.leeches}",
            inline=False
        )
        i += 1
    res_embeds.append(temp_embed)
    await ctx.send(embeds=res_embeds)

# ==========================/TORRENT============================>>>


def none2str(x):
    """
    returns a string if variable is None
    :param x: any type variable
    :return: empty string if None
    """
    if x is None:
        return ""
    else:
        return x


client.run(token)
