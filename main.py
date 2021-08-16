import discord
import discord_slash
import json
import time
import os

import utils

from dotenv import load_dotenv
from imdb import IMDb, IMDbError, helpers
from discord.http import Route
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands, manage_components
from discord_slash.model import ButtonStyle
from random import randint
from tinydb import TinyDB, Query

load_dotenv()
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
imdb_client = IMDb()
poll_db = TinyDB("./databases/poll.db")
token = os.getenv("BOTTINGSON_TOKEN")

with open("bot-values.json"):
    f = open("bot-values.json", )
    _bot_values = json.load(f)
if not _bot_values:
    _bot_values = {"slash_cmd_guilds": []}


@client.event
async def on_ready():
    pass  # Log login event


@client.event
async def on_component(ctx: discord_slash.ComponentContext):
    if ctx.custom_id.startswith("poll_"):
        print("component of type 'poll' triggered")
        await handle_poll_component(ctx)


# <<<====================/YOUTUBE================================
# Command: /youtube
# Sends invite link to Youtube Together in user's voice channel
@slash.slash(name="youtube",
             description="Sends an invite link to a Youtube Together activity in your voice channel.",
             guild_ids=_bot_values["slash_cmd_guilds"])
async def youtube(ctx):
    if not ctx.guild:  # if the message was sent in a DMChannel
        await ctx.reply(content="Please use the command inside of a server (the bot must also be on that server).")
        return

    member = await ctx.guild.fetch_member(ctx.author_id)
    if not member.voice:  # if the author isn't connected to voice
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
    inv = await client.http.request(r, reason=None, json=payload)  # send an http to get the channel invite

    embed = discord.Embed(color=0xff0000)  # create new embed
    embed.set_thumbnail(url="https://i.imgur.com/6XnPq2s.png")
    embed.add_field(name="Your Youtube Together invite is here!",
                    value=(
                        f"[Click here to launch Youtube Together](http://discord.gg/{inv['code']})\n"
                        f"Invite expiration: <t:{int(time.time()) + 86400}:R>"
                    ), inline=False)
    await ctx.send(embed=embed)


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
    if not ctx.guild:  # if the message was sent in a DMChannel
        await ctx.send(content="Please use the command inside of a server (the bot must also be on that server).")
        return
    choices = []
    for option in options:  # import all options into an indexed list
        if not option == "question":  # except for the question itself
            choices.append(options[option])
    embed = discord.Embed(
        title=f"Poll by {ctx.author.name}#{ctx.author.discriminator}",
        description="**" + options["question"] + "**",
        color=randint(0x000000, 0xffffff))  # select a random color
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


async def handle_poll_component(ctx: discord_slash.ComponentContext):
    if not ctx.origin_message:  # if there is no origin message, cancel
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
    for field in vote_count:
        total_votes += field
    new_embed = discord.Embed(title=embed.title, color=embed.color, description=embed.description)
    for i in range(len(embed.fields)):
        percent = int(vote_count[i] / total_votes * 100)
        new_value = f"{vote_count[i]} votes ({percent}%)\n"
        new_value += "▓" * int(percent // 5)
        new_value += "░" * int(20 - (percent // 5))
        new_embed.add_field(name=embed.fields[i].name, value=new_value, inline=False)

    await ctx.edit_origin(embed=new_embed)


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
                             name="Person",
                             value="person"
                         ),
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
    await ctx.defer()
    embeds = []
    if options["search_type"] == "movie":  # if search for person
        try:
            movies = imdb_client.search_movie(options["query"])[:5]
        except IMDbError:
            await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.")
            return
        movie_info = []
        if movies:
            i = 1
            for movie in movies:
                if i <= 0:
                    break
                try:
                    imdb_client.update(movie, info=[
                        "main", "plot"
                    ])
                except IMDbError:
                    await ctx.reply("Sorry, but there seems to have been a disagreement between the bot and IMDb.")
                    return
                print(movie)
                if movie["kind"] != "movie":
                    continue
                movie_info.append({
                    "title": none2str(movie["title"]),
                    "year": none2str(movie["year"]),
                    "genres": utils.list2str(movie["genres"], 3),
                    "runtime": utils.list2str(movie.get("runtimes")),
                    "plot": utils.list2str(movie.get("plot")),
                    "rating": none2str(movie.get("rating")),
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
                print(movie_info[-1])
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
                await ctx.send(embeds=embeds)
    elif options["search_type"] == "person":  # if search for person
        persons = imdb_client.search_person(options["query"])
    elif options["search_type"] == "tv":  # if search for tv series
        shows = imdb_client.search_movie(options["query"])


# ==========================/IMDB===============================>>>

def none2str(x):
    if x is None:
        return ""
    else:
        return x


client.run(token)
