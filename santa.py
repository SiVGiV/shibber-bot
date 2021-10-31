import os
import random
import discord
from dotenv import load_dotenv
from datetime import datetime as dt
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands
from discord_slash.model import SlashCommandPermissionType
from tinydb import TinyDB, where
from loggable import Loggable
from colorama import init, Fore

init()
load_dotenv()
wankbunker = 140496498939920384
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
main_db = TinyDB("./databases/main.db")
santa_db = main_db.table("santa")
modifiers_db = main_db.table("modifiers")
token = os.getenv("BOTTINGSON_TOKEN")
log = Loggable(
    "./santa_logs/" + dt.now().strftime("%H%M%S_%d%m%Y.log"),
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


@client.event
async def on_ready():
    log.success("Bot Connected")


@slash.slash(name="joinlist",
             description="Join this year's secret Santa event!",
             guild_ids=[wankbunker],
             default_permission=False,
             options=[
                 manage_commands.create_option(
                     name="firstname",
                     description="Your first name.",
                     option_type=3,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="lastname",
                     description="Your last name.",
                     option_type=3,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="address1",
                     description="The 1st line of your address [Street name, house number]",
                     option_type=3,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="address2",
                     description="The 2nd line of your address [Town/City, County/Region, Postal Code]",
                     option_type=3,
                     required=True
                 ),
                 manage_commands.create_option(
                     name="country",
                     description="Your country of residence",
                     option_type=3,
                     required=True
                 )
             ])
async def joinlist(ctx, **address):
    log.success(str(ctx.author) + " has joined this year's secret Santa!")
    santa_db.upsert({
        "userID": ctx.author_id,
        "firstName": address["firstname"],
        "lastName": address["lastname"],
        "address1": address["address1"],
        "address2": address["address2"],
        "country": address["country"]
    }, where("userID") == ctx.author_id)
    reply_embed = discord.Embed(
        title="You've successfully joined this year's secret Santa!",
        description="The following is the address you entered, you may use the command again to update it:\n```" +
                    address["firstname"] + " " + address["lastname"] + "\n" +
                    address["address1"] + "\n" + address["address2"] + "\n" + address["country"]+"```",
        color=0xF40000
    )
    await ctx.send(embed=reply_embed, hidden=True)


@slash.slash(
    name="leavelist",
    description="Leave the secret Santa event.",
    guild_ids=[wankbunker],
    default_permission=False,
    options=[
        manage_commands.create_option(
            name="ireallywannaleave",
            option_type=5,
            description="I really want to leave.",
            required=True
        )
    ]
)
async def leavelist(ctx, **options):
    if options["ireallywannaleave"]:
        removed = santa_db.remove(where("userID") == ctx.author_id)
        if len(removed) == 0:
            await ctx.send("Seems you weren't in the list in the first place.", hidden=True)
        else:
            await ctx.send("Sad to see you leave! Enjoy your holiday, hope you join us next year!", hidden=True)
    else:
        if santa_db.contains(where("userID") == ctx.author_id):
            await ctx.send("Glad to have you with us!", hidden=True)
        else:
            await ctx.send("It seems you're not yet in the list, use /joinlist to join!", hidden=True)


@slash.slash(
    name="assign_chimneys",
    description="Assign a Santa to everyone who opted in.",
    guild_ids=[wankbunker],
    default_permission=False,
    permissions={
        wankbunker: [manage_commands.create_permission(140495238476070912, SlashCommandPermissionType.USER, True)]
    }
)
async def assign_chimneys(ctx):
    ban_seed = modifiers_db.all()
    joined_santas = []
    santas = santa_db.all()
    for i in range(len(santas)):
        for j in range(len(ban_seed)):
            if ban_seed[j]["id"] == santas[i]["userID"]:
                joined_santas.append(ban_seed[j])
    else:
        random.shuffle(joined_santas)
        santa_list = find_list(joined_santas, [])
    if not santa_list:
        await ctx.send("Can't find a no-repeat list.", hidden=True)
    if len(santa_list) <= 1:
        await ctx.send("Not enough people have joined!", hidden=True)
        return
    for i in range(len(santa_list)):
        # print(f"{santa_list[i] = }")
        receiver = santa_db.get(where("userID") == santa_list[i]["id"])
        giver = santa_db.get(where("userID") == santa_list[i-1]["id"])
        user = await client.fetch_user(giver["userID"])
        embed = discord.Embed(title=f"Merry Christmas {giver['firstName']}!",
                              description=f"This year, you will be {receiver['firstName']}'s Santa!\n"
                                          f"**Their address is:**\n```{receiver['firstName']} {receiver['lastName']}\n"
                                          f"{receiver['address1']}\n{receiver['address2']}\n{receiver['country']}```\n"
                                          f"***The Rules are as follows:***",
                              color=0xf50000)
        embed.add_field(name="Rule #1", value="All gifts must be under the total of £25. Shipping not included.",
                        inline=False)
        embed.add_field(name="Rule #2", value="Try to prevent people knowing who their Santa is.", inline=False)
        embed.add_field(name="Rule #3", value="*No* NSFW gifts!",
                        inline=False)
        embed.add_field(name="Rule #4", value="Try to give people a gift they'd like, even if it's some weeb shit.",
                        inline=False)
        embed.add_field(name="Rule #5", value="All gifts should arrive at least a week before Dec 25th."
                                              f" We'll try to open them together on Christmas week"
                                              f" (probably won't happen)",
                        inline=False)
        santa_db.update({"santaID": giver["userID"]}, where("userID") == receiver["userID"])
        santa_db.update({"received": False}, where("userID") == receiver["userID"])
        await user.send(embed=embed)
    await ctx.send("Santa list sent!", hidden=True)


@slash.slash(
    name="dearsanta",
    description="Send your Santa a message!",
    guild_ids=[wankbunker],
    options=[
        manage_commands.create_option(
            name="message",
            option_type=3,
            description="The message to send",
            required=True
        )
    ]
)
async def dearsanta(ctx, message):
    receiver = santa_db.get(where("userID") == ctx.author_id)
    santa = await client.fetch_user(int(receiver["santaID"]))
    if not santa:
        await ctx.send("Couldn't find santa - Report the problem to Siv.", hidden=True)
        log.error(f"Couldn't find {receiver['firstName']}'s santa.")
        return
    embed = discord.Embed(title=f"You have a message from {receiver['firstName']}:", description=message,
                          color=0xf50000)
    await santa.send(embed=embed)
    await ctx.send("Message sent to Santa. Rudolph will see that it gets to him.", hidden=True)


@slash.slash(
    name="hohoho",
    description="Send your target a message!",
    guild_ids=[wankbunker],
    options=[
        manage_commands.create_option(
            name="message",
            option_type=3,
            description="The message to send",
            required=True
        )
    ]
)
async def hohoho(ctx, message):
    santa = santa_db.get(where("santaID") == ctx.author_id)
    receiver = await client.fetch_user(int(santa["userID"]))
    if not receiver:
        await ctx.send("Couldn't find target - Report the problem to Siv.", hidden=True)
        log.error(f"Couldn't find {santa['firstName']}'s receiver.")
        return
    embed = discord.Embed(title=f"You have a message from Santa:", description=message,
                          color=0xf50000)
    await receiver.send(embed=embed)
    await ctx.send(f"Message sent to {santa['firstName']}.", hidden=True)


def find_list(remaining, solution):
    if not remaining:
        if not solution:
            raise ValueError("Both parameter lists empty.")
        if len(solution) == 1:
            return solution
        if solution[0]["id"] not in solution[-1]["ban"] and solution[1]["id"] not in solution[0]["ban"]:
            return solution
        return None
    for i in range(len(remaining)):
        # print(f"{i = }, {remaining = }")
        if not solution:
            temp = find_list(remove_from_list(remaining.copy(), i), [remaining[i]])
            if temp is not None:
                return temp
        elif remaining[i]["id"] not in solution[-1]["ban"]:
            temp = find_list(remove_from_list(remaining.copy(), i), [*solution, remaining.copy().pop(i)])
            if temp is not None:
                return temp
    return None


def remove_from_list(lst: list, index: int):
    temp = lst.copy()
    temp.remove(temp[index])
    return temp


client.run(token)  # run the bot
