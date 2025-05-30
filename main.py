import discord
from discord.ext import commands, tasks
import aiohttp
import xml.etree.ElementTree as ET
import os
import random  # Added for the roll command

intents = discord.Intents.default()
intents.members = True  # Needed for member join events and role assignments
intents.message_content = True  # Needed for reading message content for commands

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # disables default help command

WELCOME_CHANNEL_NAME = "welcome"
WELCOME_ROLE_NAME = "Monke"
VIDEO_UPDATES_CHANNEL = "video-updates"
YOUTUBE_CHANNEL_ID = "UC9SlnWoViZi8EWc-UUy9sPg"  # your YouTube channel ID

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    if channel:
        await channel.send(
            f"Welcome to the server, {member.mention}! Enjoy your stay and remember to follow the rules. "
            "Toxicity may result in a ban."
        )
    role = discord.utils.get(member.guild.roles, name=WELCOME_ROLE_NAME)
    if role:
        await member.add_roles(role)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Deleted {amount} messages.", delete_after=5)

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.command()
async def monkey(ctx):
    await ctx.send("🦍 Ooh ooh ah ah! 🐒")

@bot.command()
async def roll(ctx, sides: int = 6):
    """Roll a dice with the given number of sides (default 6)."""
    if sides < 1:
        await ctx.send("The dice must have at least 1 side!")
        return
    result = random.randint(1, sides)
    await ctx.send(f"🎲 You rolled a {result} on a {sides}-sided dice!")

@bot.command()
async def help(ctx):
    help_text = (
        "**Commands:**\n"
        "`!kick @user [reason]` - Kick a user (moderators only)\n"
        "`!ban @user [reason]` - Ban a user (moderators only)\n"
        "`!purge [amount]` - Delete messages (moderators only)\n"
        "`!ping` - Check bot latency\n"
        "`!monkey` - Fun monkey message\n"
        "`!roll [sides]` - Roll a dice (default 6 sides)\n"
        "`!help` - Show this message\n"
    )
    await ctx.send(help_text)

@tasks.loop(minutes=10)
async def check_youtube():
    channel = discord.utils.get(bot.get_all_channels(), name=VIDEO_UPDATES_CHANNEL)
    if not channel:
        return

    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.text()

    root = ET.fromstring(data)
    latest_video = root.find('{http://www.w3.org/2005/Atom}entry')
    if not latest_video:
        return

    video_id_element = latest_video.find('{http://www.w3.org/2005/Atom}videoId')
    if video_id_element is None or video_id_element.text is None:
        return

    video_id = video_id_element.text

    video_title_element = latest_video.find('{http://www.w3.org/2005/Atom}title')
    video_title = video_title_element.text if video_title_element is not None else "No title"

    video_link_element = latest_video.find('{http://www.w3.org/2005/Atom}link')
    video_link = video_link_element.attrib['href'] if video_link_element is not None else "No link"

    if not hasattr(bot, 'last_video_id'):
        bot.last_video_id = None

    if video_id != bot.last_video_id:
        await channel.send(f"New video uploaded: **{video_title}**\n{video_link}")
        bot.last_video_id = video_id

@bot.event
async def on_ready():
    print(f"Bot is ready as {bot.user}")
    check_youtube.start()

bot.run(os.getenv('TOKEN'))
