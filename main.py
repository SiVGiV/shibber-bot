# System imports
import asyncio
import datetime
import re
import time
import os
import json
from dotenv import load_dotenv
from datetime import datetime as dt
from urllib.parse import quote_plus
# Project imports
from utils import *
import conversion
import tictactoe as ttt
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
from tinydb import TinyDB, where, operations
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
main_db = TinyDB("./databases/main.db")
poll_db = main_db.table("poll")
watchlist_db = main_db.table("watchlist")
tictactoe_db = main_db.table("tictactoe")
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
    elif ctx.custom_id.startswith("tictactoe_"):
        await handle_tictactoe_component(ctx)
    elif ctx.custom_id.startswith("watchlist_"):
        await handle_watchlist_component(ctx)


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
        print(movies)
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
                print(movie["kind"])
                if not movie["kind"] == "movie":
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
                        person_str = person2str(person)
                        if not person_str == "":
                            directors.append(person_str)
                else:
                    directors = person2str(temp_directors)

                if isinstance(temp_writers, list):
                    for person in temp_writers:
                        person_str = person2str(person)
                        if not person_str == "":
                            writers.append(person_str)
                else:
                    writers = person2str(temp_writers)

                if isinstance(temp_writers, list):
                    for person in temp_cast:
                        person_str = person2str(person)
                        if not person_str == "":
                            cast.append(person_str)
                else:
                    cast = person2str(temp_cast)
                print(f"{temp_writers=}")
                print(f"{writers=}")
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
                embed.add_field(name="Directed by:", value=movie["directors"], inline=True)
                embed.add_field(name="Written by:", value=movie["writers"], inline=True)
                embed.add_field(name="Cast:", value=movie["cast"], inline=False)
                embed.set_footer(text=f"tt{movie['id']}")
                embeds.append(embed)
                watchlist_buttons = [manage_components.create_button(
                    style=ButtonStyle.green,
                    label="Add to watchlist",
                    emoji="➕",
                    custom_id="watchlist_add"
                ),
                    manage_components.create_button(
                        style=ButtonStyle.red,
                        label="Remove from watchlist",
                        emoji="➖",
                        custom_id="watchlist_remove"
                    ),
                    manage_components.create_button(
                        style=ButtonStyle.blue,
                        label="List interested",
                        emoji="📝",
                        custom_id="watchlist_list"
                    )]
                tor_buttons = []
                try:
                    res = requests.get("https://yts.mx/api/v2/list_movies.json", params={
                        "query_term": f"tt{movie['id']}"
                    }).json()
                except Exception as e:
                    log.error(str(e))
                else:
                    trackers = "tr=udp://open.demonii.com:1337/announce\
                    &tr=udp://tracker.openbittorrent.com:80\
                    &tr=udp://tracker.coppersurfer.tk:6969\
                    &tr=udp://glotorrents.pw:6969/announce\
                    &tr=udp://tracker.opentrackr.org:1337/announce\
                    &tr=udp://torrent.gresille.org:80/announce\
                    &tr=udp://p4p.arenabg.com:1337\
                    &tr=udp://tracker.leechers-paradise.org:6969"
                    if res["status"] == "ok":
                        if res["data"]["movie_count"] == 1:
                            torrent_res = res["data"]["movies"][0]
                            for i in range(len(torrent_res["torrents"])):
                                tor = torrent_res["torrents"][i]
                                # print(torrent_res)
                                tor_buttons.append(manage_components.create_button(
                                    style=ButtonStyle.URL,
                                    label=f"{tor['quality']} {tor['type'].title()} "
                                          f"({tor['size']} | ▲{tor['seeds']} ▼{tor['peers']})",
                                    url=magnet_shorten(os.getenv("TINYURL_TOKEN"),
                                                       f"magnet:?xt=urn:btih:{tor['hash']}"
                                                       f"&dn={quote_plus(torrent_res['title_long'])}&{trackers}")
                                ))
                try:
                    await ctx.send(embeds=embeds, components=[manage_components.create_actionrow(*watchlist_buttons),
                                                              manage_components.create_actionrow(*tor_buttons)])
                except discord.DiscordException as e:
                    log.error("Couldn't reply to /imdb. Error:" + str(e))
                else:
                    log.success("/imdb: Handling finished.")
        else:
            log.error("/imdb failed: not Movie")
            ctx.send("Movie not found or other error occurred.", hidden=True)
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
                        person_str = person2str(person)
                        if not person_str == "":
                            writers.append(person_str)
                else:
                    writers = person2str(temp_writers)

                if isinstance(temp_creators, list):
                    for person in temp_creators:
                        person_str = person2str(person)
                        if not person_str == "":
                            creators.append(person_str)
                else:
                    creators = person2str(temp_creators)

                if isinstance(temp_cast, list):
                    for person in temp_cast:
                        person_str = person2str(person)
                        if not person_str == "":
                            cast.append(person_str)
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
                embed.set_footer(text=f"tt{show['id']}")
                embeds.append(embed)
                try:
                    await ctx.send(embeds=embeds)
                except discord.DiscordException as e:
                    log.error("Couldn't reply to /imdb. Error:" + str(e))
                else:
                    log.success("/imdb: Handling finished.")


# ==========================/IMDB=================================>>>


# <<<=======================/WATCHLIST===============================
@slash.slash(
    name="watchlist",
    description="Sends the watchlist of said person, or a list of common items between all people.",
    guild_ids=_bot_values["slash_cmd_guilds"],
    options=[
        manage_commands.create_option(
            name="users",
            description="User/users to send watchlist for",
            option_type=3,
            required=False
        )
    ]
)
async def watchlist(ctx, **options):
    await ctx.defer()
    log.event("/watchlist command received")
    msg_str = "Watchlist for "
    users = []
    if "users" not in options:
        msg_str += f"<@{ctx.author_id}>"
        users.append(ctx.author_id)
    else:
        str_users = re.findall(r"<@!(\d+)>", options["users"])
        for i in range(len(str_users)):
            users.append(int(str_users[i]))
            msg_str += f"{', ' if i > 0 else ''}<@{users[-1]}>"
        if len(users) == 0:
            await ctx.send("No user tags found in command option 'users'", hidden=True)
            log.warning("Command dispatched with no users")
            return
    msg_str += ":\n"
    film_doc_list = watchlist_db.search(where("user_id") == users[0])
    for i in range(1, len(users)):
        for j in range(len(film_doc_list)):
            if not watchlist_db.contains((where("user_id") == users[i]) &
                                         (where("film_id") == film_doc_list[j]["film_id"])):
                film_doc_list.remove(film_doc_list[j])
    for i in range(len(film_doc_list)):
        film_id = film_doc_list[i]["film_id"]
        temp = imdb_client.get_movie(film_id[2::])
        msg_str += f"**{temp.get('title')}** ({temp.get('year')})\n"
    if len(msg_str) > 0:
        await ctx.send(msg_str)
    else:
        await ctx.send("There are no movies in this list.")


async def handle_watchlist_component(ctx):
    if ctx.custom_id == "watchlist_add":
        mov_id = ctx.origin_message.embeds[0].footer.text
        if not watchlist_db.contains((where("user_id") == ctx.author_id) & (where("film_id") == mov_id)):
            watchlist_db.insert({"user_id": ctx.author_id, "film_id": mov_id})
            await ctx.send("Movie added to your watchlist.", hidden=True)
        else:
            await ctx.send("Movie already on your watchlist.", hidden=True)
    elif ctx.custom_id == "watchlist_remove":
        mov_id = ctx.origin_message.embeds[0].footer.text
        if watchlist_db.contains((where("user_id") == ctx.author_id) & (where("film_id") == mov_id)):
            watchlist_db.remove((where("user_id") == ctx.author_id) & (where("film_id") == mov_id))
            await ctx.send("Movie removed from your watchlist.", hidden=True)
        else:
            await ctx.send("Movie wasn't on your watchlist.", hidden=True)
    elif ctx.custom_id == "watchlist_list":
        mov_id = ctx.origin_message.embeds[0].footer.text
        interested = watchlist_db.search(where("film_id") == mov_id)
        msg = "People interested in **" + ctx.origin_message.embeds[0].title + "**:\n"
        for item in interested:
            if ctx.guild.fetch_member(item["user_id"]) is not None:
                msg += "<@" + str(item["user_id"]) + ">"
            else:
                interested.remove(item)
        msg = msg.replace("><", ">, <")
        if len(interested) > 0:
            await ctx.send(msg, hidden=True)
        else:
            await ctx.send("No one has added this movie to their watchlist (yet).", hidden=True)


# ==========================/WATCHLIST============================>>>


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
            magnet = magnet_shorten(os.getenv("TINYURL_TOKEN"), tor.magnetlink)
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
        total_string += choices[choice]
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
    await ctx.defer()
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


# <<<======================/TIMESTAMP=================================
@slash.slash(name="timestamp",
             description="Sends a timestamp (INPUT MUST BE UTC+0)",
             guild_ids=_bot_values["slash_cmd_guilds"],
             options=[
                 manage_commands.create_option(
                     name="year",
                     description="Enter year",
                     option_type=4,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="month",
                     description="Enter month",
                     option_type=4,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="day",
                     description="Enter day",
                     option_type=4,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="hour",
                     description="Enter hour (24h)",
                     option_type=4,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="minutes",
                     description="Enter minutes",
                     option_type=4,
                     required=True
                 )
             ])
async def timestamp(ctx, **options):
    if not 1970 < options["year"] < 2030:
        await ctx.send("Year not in valid range (1970 <= year < 2030).", hidden=True)
        return
    if not 1 <= options["month"] <= 12:
        await ctx.send("Month not in valid range (1 <= month <= 12)", hidden=True)
        return
    if not 1 <= options["day"] <= 31:
        await ctx.send("Day not in valid range (1 <= day <= 31)", hidden=True)
        return
    if not 0 <= options["hour"] <= 23:
        await ctx.send("Hour not in valid range (0 <= hour <= 23)", hidden=True)
        return
    if not 0 <= options["minutes"] <= 59:
        await ctx.send("Minutes not in valid range (0 <= minutes <= 59)", hidden=True)
        return
    try:
        stamp = datetime.datetime(options["year"],
                                  options["month"],
                                  options["day"],
                                  options["hour"] + 2,
                                  options["minutes"],
                                  0, 0)
    except ValueError:
        await ctx.send("Error in parsing date. Likely that the day chosen does not exist in that month.")
        return
    time_str = str(int(stamp.timestamp()))
    embed = discord.Embed(title="Timestamps")
    embed.add_field(name="Full - Short", value=f"<t:{time_str}:f> `<t:{time_str}:f>`", inline=False)
    embed.add_field(name="Full - Long", value=f"<t:{time_str}:F> `<t:{time_str}:F>`", inline=False)
    embed.add_field(name="Date - Short", value=f"<t:{time_str}:d> `<t:{time_str}:d>`", inline=False)
    embed.add_field(name="Date - Long", value=f"<t:{time_str}:D> `<t:{time_str}:D>`", inline=False)
    embed.add_field(name="Time - Short", value=f"<t:{time_str}:t> `<t:{time_str}:t>`", inline=False)
    embed.add_field(name="Time - Long", value=f"<t:{time_str}:T> `<t:{time_str}:T>`", inline=False)
    embed.add_field(name="Relative", value=f"<t:{time_str}:R> `<t:{time_str}:R>`", inline=False)
    await ctx.send(embed=embed, hidden=True)
# =========================/TIMESTAMP==============================>>>


# <<<======================TICTACTOE:USER===============================
@slash.context_menu(name="TicTacToe",
                    target=ContextMenuType.USER,
                    guild_ids=_bot_values["slash_cmd_guilds"])
async def tictactoe(ctx: MenuContext):
    log.event("TicTacToe context action detected.")
    player1 = ctx.target_author.id
    player2 = ctx.author_id
    if tictactoe_db.contains(where("player1") == ctx.author_id) \
            or tictactoe_db.contains(where("player2") == ctx.author_id):
        await ctx.send("You need to finish your existing games first.", hidden=True)
        log.warning("Player tried creating a new game despite having an unfinished one.")
        return
    msg_content = ""
    msg_content += f"🟦 <@{player1}> vs  🟥 <@{player2}>\n"
    board = ttt.TicTacToe()
    if player1 == client.user.id:
        msg_content += f"**<@{player2}>'s turn!**"
        board.update(1, ttt.compute_step(board, 1))
    else:
        msg_content += f"**<@{player1}>'s turn!**"
    components = board.get_buttons()
    message = await ctx.send(content=msg_content, components=components)
    tictactoe_db.insert({
        "game_id": message.id,
        "player1": player1,
        "player2": player2,
        "board": board.get_string(),
        "turn": 1 if board.blanks == 9 else 2
    })
    log.success("TicTacToe game posted.")


async def handle_tictactoe_component(ctx):
    db_item = tictactoe_db.get(where("game_id") == ctx.origin_message_id)
    if db_item is None:  # check for message
        if ctx.custom_id == "tictactoe_restart":
            board = ttt.TicTacToe()
            players = re.findall(r"<@(\d+)>.*<@(\d+)>.*", ctx.origin_message.content)[0]
            print(players)
            if int(players[0]) == client.user.id:
                board.update(1, ttt.compute_step(board, 1))
                tictactoe_db.insert({
                    "game_id": ctx.origin_message_id,
                    "player1": int(players[0]),
                    "player2": int(players[1]),
                    "board": board.get_string(),
                    "turn": 2
                })
            else:
                tictactoe_db.insert({
                    "game_id": ctx.origin_message_id,
                    "player1": int(players[0]),
                    "player2": int(players[1]),
                    "board": board.get_string(),
                    "turn": 1 if ctx.author_id == int(players[1]) else 2
                })
            db_item = tictactoe_db.get(where("game_id") == ctx.origin_message_id)
            msg_content = ""
            msg_content += f"🟦 <@{db_item['player1']}> vs  🟥 <@{db_item['player2']}>\n"
            msg_content += f"**<@{db_item['player' + str(db_item['turn'])]}>'s turn!**"

            await ctx.edit_origin(content=msg_content, components=board.get_buttons())
            log.success("Component action handled.")
            return
        else:
            log.error("Component call from message not in DB.")
            await ctx.send("There was an error handling your move.", hidden=True)
            return
    if ctx.custom_id == "tictactoe_restart":
        await ctx.send("Can only restart a stopped or finished game.", hidden=True)
        return
    if not ctx.author_id == db_item["player1"] and not ctx.author_id == db_item["player2"]:
        # check if player is in the game
        log.warning("Non player attempted move. Ignoring")
        await ctx.send(f"You're not a part of this game."
                       f" You can challenge someone by right clicking their name and choosing Apps->TicTacToe",
                       hidden=True)
        return
    if ctx.custom_id == "tictactoe_stop":
        board = ttt.TicTacToe()
        board.update(full_board=db_item["board"])
        msg_content = ""
        msg_content += f"🟦 <@{db_item['player1']}> vs  🟥 <@{db_item['player2']}>\n"
        msg_content += f"**Game stopped by <@{ctx.author_id}>**"
        await ctx.edit_origin(content=msg_content, components=board.get_buttons(force_stop=True))
        tictactoe_db.remove(where("game_id") == ctx.origin_message_id)
        log.success("Game stopped.")
        return
    if not ctx.author_id == db_item[f"player{db_item['turn']}"]:
        # check if player's turn
        log.warning("Player tried to play on opponent's turn. Ignoring")
        await ctx.send("You must wait your turn to play!", hidden=True)
        return
    board = ttt.TicTacToe()
    board.update(full_board=db_item["board"])
    board.update(player=db_item["turn"], i=int(ctx.custom_id[-1]))
    tictactoe_db.update(
        operations.set("turn", 2 if db_item["turn"] == 1 else 1),
        where("game_id") == ctx.origin_message_id
    )
    tictactoe_db.update(
        operations.set("board", board.get_string()),
        where("game_id") == ctx.origin_message_id
    )
    if board.game_over:
        msg_content = ""
        msg_content += f"🟦 <@{db_item['player1']}> vs 🟥 <@{db_item['player2']}>\n"
        if board.check_win() == -1:
            msg_content += "**Tie! No one won.**"
        else:
            msg_content += f"<@{db_item['player1']}>" if board.check_win() == 1 else f"<@{db_item['player2']}>"
            msg_content += " won the game!"
        await ctx.edit_origin(content=msg_content, components=board.get_buttons())
        tictactoe_db.remove(where("game_id") == ctx.origin_message_id)
        log.success("Game ended. Discarding.")
        return
    db_item = tictactoe_db.get(where("game_id") == ctx.origin_message_id)  # update item from db
    if db_item[f"player{db_item['turn']}"] == client.user.id:
        board.update(player=db_item['turn'], i=ttt.compute_step(board, 1))
        if board.game_over:
            msg_content = ""
            msg_content += f"🟦 <@{db_item['player1']}> vs 🟥 <@{db_item['player2']}>\n"
            if board.check_win() == -1:
                msg_content += "**Tie! No one won.**"
            else:
                msg_content += f"<@{db_item['player1']}>" if board.check_win() == 1 else f"<@{db_item['player2']}>"
                msg_content += " won the game!"
            await ctx.edit_origin(content=msg_content, components=board.get_buttons())
            tictactoe_db.remove(where("game_id") == ctx.origin_message_id)
            log.success("Game ended. Discarding.")
            return
        tictactoe_db.update(
            operations.set("turn", 2 if db_item["turn"] == 1 else 1),
            where("game_id") == ctx.origin_message_id
        )
        tictactoe_db.update(
            operations.set("board", board.get_string()),
            where("game_id") == ctx.origin_message_id
        )
        await ctx.edit_origin(content=ctx.origin_message.content, components=board.get_buttons())
        return
    msg_content = ""
    msg_content += f"🟦 <@{db_item['player1']}> vs  🟥 <@{db_item['player2']}>\n"
    msg_content += f"**<@{db_item['player' + str(db_item['turn'])]}>'s turn!**"
    await ctx.edit_origin(content=msg_content, components=board.get_buttons())
    log.success("Component action handled.")


# =========================TICTACTOE:USER============================>>>


# <<<=======================SUMMON:USER===============================
@slash.context_menu(target=ContextMenuType.USER,
                    name="Summon",
                    guild_ids=_bot_values["slash_cmd_guilds"])
async def summon(ctx: MenuContext):
    member = await ctx.guild.fetch_member(ctx.author_id)
    if not member.voice:
        log.warning("Couldn't send a summon - user not in a voice channel")
        await ctx.send("You must be in a voice channel to summon someone.", hidden=True)
        return
    embed = discord.Embed(title="You've been summoned by " + str(ctx.author) + "!",
                          description=f"They are connected to {member.voice.channel.name}")
    invite = await member.voice.channel.create_invite(max_uses=1, temporary=True, max_age=900)
    button = [
        manage_components.create_actionrow(
            manage_components.create_button(style=ButtonStyle.URL,
                                            url=invite.url,
                                            label="Join their channel here!"))]
    await ctx.target_author.send(embed=embed, components=button)
    await ctx.send("Summon sent to <@" + str(ctx.target_author.id) + ">", hidden=True)


# ==========================SUMMON:USER============================>>>


# <<<=======================SEND LOVE:USER===============================
@slash.context_menu(target=ContextMenuType.USER,
                    name="Send a heart",
                    guild_ids=_bot_values["slash_cmd_guilds"])
async def send_a_heart(ctx: MenuContext):
    await ctx.target_author.send("Someone sent you a  ❤️")
    await ctx.send("Heart sent to <@" + str(ctx.target_author.id) + ">", hidden=True)


# ==========================SEND LOVE:USER============================>>>


client.run(token)  # run the bot
