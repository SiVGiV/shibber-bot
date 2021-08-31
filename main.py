# System imports
import asyncio
import re
import time
import os
import json
from dotenv import load_dotenv
from datetime import datetime as dt
# Project imports
from utils import *
import conversion
from loggable import Loggable
# Framework imports
import discord
import discord_slash
from discord.http import Route
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands, manage_components
from discord_slash.model import ButtonStyle, ContextMenuType
from discord_slash.context import MenuContext
# Helper package imports
from tinydb import TinyDB, where
from tpblite import TPB
from imdb import IMDb, IMDbError, helpers
from mal import Anime, AnimeSearch
from random import randint
from colorama import init, Fore

# Package initializations
load_dotenv()
init()
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
imdb_client = IMDb()
poll_db = TinyDB("./databases/poll.db")
token = os.getenv("SHIBBER_TOKEN")
currency_convert = conversion.CurrencyConverter(os.getenv("COINLAYER_TOKEN"))
tpb = TPB("https://tpb.party/")
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
        await ctx.reply(content="Please use the command inside of a server (the bot must also be on that server).",
                        hidden=True)
        return

    member = await ctx.guild.fetch_member(ctx.author_id)
    if not member.voice:  # if the author isn't connected to voice
        log.warning(f"/youtube: User not connected to VC, handling canceled.")
        await ctx.send(content="You don't appear to be in any voice channel.", hidden=True)
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
        await ctx.send("Sorry, but there was a problem with handling your command. Try again later.", hidden=True)
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
        await ctx.send(content="Please use the command inside of a server (the bot must also be on that server).",
                       hidden=True)
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
            name=f"{get_number_emoji(i)} - {choice}",
            value=f"0 votes (0%)\n{'░' * 20}",
            inline=False
        )
    components = []
    for i in range(len(choices)):
        components.append(
            manage_components.create_button(  # create a button for each option
                style=ButtonStyle.grey,
                label=ellipsis_truncate(choices[i], 30, mid_ellipsis=True),
                emoji=get_number_emoji_dict(i + 1),
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
        await ctx.send("Error occurred with voting. Try later?", hidden=True)
        return
    embed = ctx.origin_message.embeds[0]  # make the poll embed into a dict
    vote_count = []
    for field in embed.fields:  # scrub current embed for data
        vote_count.append(int(field.value.split()[0])),  # split by whitespace, take first choice = vote count

    if poll_db.contains(
            (where('poll_id') == ctx.origin_message_id) &
            (where('user_id') == ctx.author.id)):  # if voted on msg

        res = poll_db.search(
            (where('poll_id') == ctx.origin_message_id) &
            (where('user_id') == ctx.author.id))  # look it up

        last_vote = res[0]["option_id"]  # get the last voted item
        vote_count[int(last_vote.split("_")[1])] -= 1  # reduce vote from previous vote
    vote_count[int(ctx.custom_id.split("_")[1])] += 1  # increase vote for current vote
    poll_db.upsert({  # update database if exist, insert if doesn't
        "poll_id": ctx.origin_message_id,  # poll_id = poll message id
        "option_id": ctx.custom_id,  # option_id = poll button custom id ("poll_{N}")
        "user_id": ctx.author.id  # user_id = user who pressed a button
    }, (where('poll_id') == ctx.origin_message_id) &
       (where('user_id') == ctx.author.id))  # the query for checking if exists

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
            await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.", hidden=True)
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
                    await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.",
                                    hidden=True)
                    return
                # skip iteration if 'tv movie' or 'movie'
                if not movie["kind"] == "movie" and not movie["kind"] == "tv movie":
                    continue
                movie_info.append({
                    "title": none2str(movie["title"]),
                    "year": none2str(movie["year"]),
                    "genres": list2str(movie["genres"], 3),
                    "runtime": list2str(movie.get("runtimes")),
                    "plot": list2str(movie.get("plot")),
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
                    "directors": list2str(directors, 3),
                    "writers": list2str(writers, 3),
                    "cast": list2str(cast, 5),
                })
                i -= 1
            for movie in movie_info:
                embed = discord.Embed(title=f"{movie['title']} ({movie['year']})",
                                      url=f"https://www.imdb.com/title/tt{movie['id']}",
                                      description=f"`{movie['genres']} | {movie['runtime']} min`\n"
                                                  f"{ellipsis_truncate(movie['plot'], 200)}",
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
            await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.", hidden=True)
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
                    await ctx.reply("Sorry, there seems to have been a disagreement between the bot and IMDb.",
                                    hidden=True)
                    return
                if not show["kind"] == "tv series" and not show["kind"] == "tv mini series":
                    continue
                show_info.append({
                    "title": none2str(show["title"]),
                    "year": none2str(show["series years"]),
                    "genres": list2str(show["genres"], 3),
                    "plot": list2str(show.get("plot")),
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
                    "writers": list2str(writers, 3),
                    "creators": list2str(creators, 3),
                    "cast": list2str(cast, 5),
                })
                i -= 1
            for show in show_info:
                embed = discord.Embed(title=f"{show['title']} ({show['year']})",
                                      url=f"https://www.imdb.com/title/tt{show['id']}",
                                      description=f"`{show['genres']}"
                                                  f""" | {show['seasons']} season{'' if show['seasons'] == 1 else 's'}`
{ellipsis_truncate(show['plot'], 200)}""",
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


# <<<=======================/ANIME===================================
@slash.slash(
    name="anime",
    description="Searches MyAnimeList for weeb shit.",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="search_query",
            description="Query to search for on MyAnimeList",
            option_type=3,
            required=True
        )
    ]
)
async def anime(ctx, **options):
    await ctx.defer()
    await asyncio.sleep(3)
    log.event("/Anime command received.")
    search = AnimeSearch(options["search_query"])
    if not search:
        log.warning("/Anime: Couldn't find a result.")
        log.event("/Anime: Handling finished.")
        await ctx.send(f"Couldn't find a result for \"{options['search_query']}\"", hidden=True)
        return
    try:
        result = Anime(search.results[0].mal_id)
    except Exception as e:
        log.error(str(e))
        log.error("Stopping /Anime execution")
        await ctx.send("Error encountered while executing the /Anime command.", hidden=True)
        return

    # title_english, title_japanese, url, image_url, genres, synopsis
    embed = discord.Embed(
        title=f"{result.title_english}"
              f"{'(' + result.title_japanese + ')' if result.title_japanese is not None else ''}",
        url=result.url,
        description=f"`{list2str(result.genres, 3)}`\n{list2str(result.synopsis.split('.'), 3, '.')}."
    )
    embed.set_thumbnail(url=result.image_url)
    embed.set_footer(text="ʸᵒᵘ ᶠᵘᶜᵏᶦⁿᵍ ʷᵉᵉᵇ")
    await ctx.send(embed=embed)
    log.success("/Anime: Handling finished")


# ==========================/ANIME================================>>>


# <<<=======================/PIRATEBAY===============================
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
    log.event("/piratebay command received")
    await ctx.defer()
    tor_limit = 5
    res_embeds = []
    print(options["query"])
    piratebay_torrents = tpb.search(options["query"])
    # create piratebay embed
    temp_embed = discord.Embed(title="PirateBay Results", description=f"Query: {options['query']}")
    i = 1
    for tor in piratebay_torrents:
        if i > tor_limit:
            break
        try:
            magnet = magnet_shorten(tor.magnetlink)
        except NameError as e:
            log.error(str(e))
            await ctx.send("There was an error in processing your request. Please try again later.", hidden=True)
            return
        temp_embed.add_field(
            value=f"{i}) **Name: [{tor.title}]({magnet})**\n*{tor.category}*",
            name=f"Size: {tor.filesize} | Seeders: {tor.seeds} | Leechers: {tor.leeches}",
            inline=False
        )
        i += 1
    res_embeds.append(temp_embed)
    await ctx.send(embeds=res_embeds)
    log.success("/piratebay: handling finished")


# ==========================/PIRATEBAY============================>>>


# <<<=======================/RANDOM=================================
@slash.subcommand(base="random",
                  base_description="A random choices command",
                  name="choices",
                  description="Chooses an item from multiple items.",
                  guild_ids=_bot_values["slash_cmd_guilds"],
                  options=[
                      manage_commands.create_option(
                          name="choice1",
                          option_type=3,
                          required=True,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice2",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice3",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice4",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice5",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice6",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice7",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice8",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice9",
                          option_type=3,
                          required=False,
                          description="A choice."
                      ),
                      manage_commands.create_option(
                          name="choice10",
                          option_type=3,
                          required=False,
                          description="A choice."
                      )
                  ])
async def _random_choices(ctx, **choices):
    log.event("/random choices command received")
    selection = randint(1, len(choices))
    total_string = "**All choices (selection is marked):**\n"
    i = 1
    for choice in choices:
        if i == selection:
            total_string += "`"
        total_string += choice
        if i == selection:
            total_string += "`"
        total_string += "\n"
        i += 1
    await ctx.send(total_string)
    log.success("/random choices: handling finished")


@slash.subcommand(base="random",
                  base_description="A random choices command",
                  name="numbers",
                  description="Sends a number/numbers from a range.",
                  guild_ids=_bot_values["slash_cmd_guilds"],
                  options=[
                      manage_commands.create_option(
                          name="max",
                          option_type=4,
                          description="The maximum number in the range (included in choice)",
                          required=True
                      ),
                      manage_commands.create_option(
                          name="min",
                          option_type=4,
                          description="The minimum number in the range (included), 1 if omitted.",
                          required=False
                      ),
                      manage_commands.create_option(
                          name="amount",
                          option_type=4,
                          description="Number of random numbers to generate (default 1).",
                          required=False
                      )
                  ])
async def _random_numbers(ctx, **options):
    log.event("/random numbers command received")
    numbers = []
    if "amount" not in options:
        options["amount"] = 1
    elif options["amount"] <= 0:
        options["amount"] = 1
    for i in range(options["amount"]):
        numbers.append(randint(1 if "min" not in options else options["min"], options["max"]))
    if options["amount"] == 1:
        await ctx.send(f"The random number in range "
                       f"{1 if 'min' not in options else options['min']} -> {options['max']} is **{numbers[0]}**")
    else:
        await ctx.send(f"The random numbers in range "
                       f"{1 if 'min' not in options else options['min']}"
                       f" -> {options['max']} is **{', '.join(map(str, numbers))}**")
    log.success("/random numbers: handling finished")


# ==========================/RANDOM==============================>>>


# <<<=======================/KESSIFY================================
@slash.slash(name="kessify",
             description="Kessifies text",
             guild_ids=_bot_values["slash_cmd_guilds"],
             options=[
                 manage_commands.create_option(
                     name="message",
                     description="text to kessify",
                     option_type=3,
                     required=True
                 )
             ])
async def kessify(ctx, message):
    log.event("/kessify command received")
    new_msg = ""
    choice = randint(1, 3)
    if choice > 1:
        for ind in range(len(message)):
            if bool(randint(0, 1)):
                new_msg += message[ind].lower()
            else:
                new_msg += message[ind].upper()
    else:
        start_ind = randint(0, len(message) - 1)
        if bool(randint(0, 1)):
            new_msg += message[:start_ind].upper()
            new_msg += message[start_ind:].lower()
        else:
            new_msg += message[:start_ind].lower()
            new_msg += message[start_ind:].upper()
    await ctx.send(new_msg)
    log.success("/kessify: command handled")


# ==========================/KESSIFY=============================>>>


# <<<=======================/CONVERT================================

@slash.subcommand(
    base="convert",
    name="length",
    description="Converts length units",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="The conversion quantity"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="Convert from",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.length.items()
            ))
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="Convert to",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.length.items()
            ))
        )
    ]
)
async def _convert_length(ctx, **options):
    log.event("/convert length command received")
    await ctx.send(
        f"{options['quantity']} {conversion.length[options['from']]['name']} "
        f"is {conversion.convert_length(options['quantity'], options['from'], options['to']):.2f}"
        f" {conversion.length[options['to']]['name']}")


@slash.subcommand(
    base="convert",
    name="weight",
    description="Converts weight units",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="The conversion quantity"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="Convert from",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.weight.items()
            ))
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="Convert to",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.weight.items()
            ))
        )
    ]
)
async def _convert_weight(ctx, **options):
    log.event("/convert weight command received")
    await ctx.send(
        f"{options['quantity']} {conversion.weight[options['from']]['name']} "
        f"is {conversion.convert_weight(options['quantity'], options['from'], options['to']):.2f}"
        f" {conversion.weight[options['to']]['name']}")


@slash.subcommand(
    base="convert",
    name="area",
    description="Converts area units",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="The conversion quantity"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="Convert from",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.area.items()
            ))
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="Convert to",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.area.items()
            ))
        )
    ]
)
async def _convert_area(ctx, **options):
    log.event("/convert area command received")
    await ctx.send(
        f"{options['quantity']} {conversion.area[options['from']]['name']} "
        f"is {conversion.convert_area(options['quantity'], options['from'], options['to']):.2f}"
        f" {conversion.area[options['to']]['name']}")


@slash.subcommand(
    base="convert",
    name="speed",
    description="Converts speed units",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="The conversion quantity"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="Convert from",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.speed.items()
            ))
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="Convert to",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.speed.items()
            ))
        )
    ]
)
async def _convert_speed(ctx, **options):
    log.event("/convert speed command received")
    await ctx.send(
        f"{options['quantity']} {conversion.speed[options['from']]['name']} "
        f"is {conversion.convert_speed(options['quantity'], options['from'], options['to']):.2f}"
        f" {conversion.speed[options['to']]['name']}")


@slash.subcommand(
    base="convert",
    name="volume",
    description="Converts volume units",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="The conversion quantity"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="Convert from",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.volume.items()
            ))
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="Convert to",
            choices=list(map(
                lambda x: manage_commands.create_choice(name=x[1]['name'], value=x[0]),
                conversion.volume.items()
            ))
        )
    ]
)
async def _convert_volume(ctx, **options):
    log.event("/convert volume command received")
    await ctx.send(
        f"{options['quantity']} {conversion.volume[options['from']]['name']} "
        f"is {conversion.convert_volume(options['quantity'], options['from'], options['to']):.2f}"
        f" {conversion.volume[options['to']]['name']}")


@slash.subcommand(
    base="convert",
    name="temperature",
    description="Converts temperature units",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="The conversion quantity"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="Convert from",
            choices=[
                manage_commands.create_choice(name="celsius", value="c"),
                manage_commands.create_choice(name="fahrenheit", value="f"),
                manage_commands.create_choice(name="kelvin", value="k")
            ]
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="Convert to",
            choices=[
                manage_commands.create_choice(name="celsius", value="c"),
                manage_commands.create_choice(name="fahrenheit", value="f"),
                manage_commands.create_choice(name="kelvin", value="k")
            ]
        )
    ]
)
async def _convert_temperature(ctx, **options):
    log.event("/convert temperature command received")
    await ctx.send(
        f"{options['quantity']} {conversion.temperature[options['from']]['name']} "
        f"is {conversion.convert_temperature(options['quantity'], options['from'], options['to']):.2f}"
        f" {conversion.temperature[options['to']]['name']}")


@slash.subcommand(
    base="convert",
    name="currency",
    description="Converts from a currency to another",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="quantity",
            option_type=10,
            required=True,
            description="Amount to convert"
        ),
        manage_commands.create_option(
            name="from",
            option_type=3,
            required=True,
            description="3 Letter code of currency to convert from"
        ),
        manage_commands.create_option(
            name="to",
            option_type=3,
            required=True,
            description="3 Letter code of currency to convert to"
        )
    ]
)
async def _convert_currency(ctx, **options):
    log.event("/convert currency command received")
    check_pattern = r"\A[a-zA-Z]{3}\Z"
    if not re.search(check_pattern, options["from"]) or not re.search(check_pattern, options["to"]):
        log.warning("Handling canceled due to false currency string.")
        await ctx.send("One of the currency codes specified was incorrect (not 3 letters)", hidden=True)
        return
    try:
        result = currency_convert.convert(options["from"], options["to"], options["quantity"])
    except ValueError:
        log.error("Error occurred with currency conversion, handling canceled")
        await ctx.send("An error occurred converting, likely due to wrong currency codes.", hidden=True)
        return
    await ctx.send(f"{options['quantity']} {options['from'].upper()} = {result:.2f} {options['to'].upper()}")
    log.success("/convert currency handling finished")
# ==========================/CONVERT=============================>>>


# <<<=======================SEND LOVE===============================
@slash.context_menu(target=ContextMenuType.USER,
                    name="heart",
                    guild_ids=_bot_values["slash_cmd_guilds"])
async def heart(ctx: MenuContext):
    await ctx.target_author.send("Someone sent you a  ❤️")
    await ctx.send("Heart sent to <@"+str(ctx.target_author.id)+">", hidden=True)
# ==========================SEND LOVE============================>>>


client.run(token)  # run the bot
