import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from collections import defaultdict
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 🔄 Message memory for spam detection
user_messages = defaultdict(list)

# 📁 File path to save servers
SERVER_FILE = "servers.txt"

# 🚀 Load server list from file
def load_servers():
    if not os.path.exists(SERVER_FILE):
        return []
    with open(SERVER_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# 💾 Save new server
def save_server(server_name):
    with open(SERVER_FILE, "a") as f:
        f.write(server_name + "\n")

# 📩 DM handler and spam detector
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # 🧠 Spam detection
    user_id = message.author.id
    user_messages[user_id].append(content)
    if len(user_messages[user_id]) > 5:
        user_messages[user_id].pop(0)

    recent = user_messages[user_id]
    if recent.count(content) == 2:
        await message.channel.send(f"⚠️ {message.author.mention}, please don’t spam...")
    elif recent.count(content) == 3:
        await message.channel.send(f"❗ {message.author.mention}, last warning! One more and I’ll delete it.")
    elif recent.count(content) >= 4:
        try:
            await message.delete()
            await message.channel.send(f"🛑 {message.author.mention}, your message was deleted due to repeated spamming.")
        except (discord.errors.NotFound, discord.errors.Forbidden):
            pass

    # 📩 Respond in DMs
    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("👋 Hello! I’m your Minecraft Slayer bot.\nUse commands like `!servers`, `!login`, or `!submitserver`.")

    await bot.process_commands(message)

# 📜 Show all submitted servers
@bot.command()
async def servers(ctx):
    servers = load_servers()
    if not servers:
        await ctx.send("📭 No servers listed yet.")
    else:
        msg = "\n".join(f"🌐 {s}" for s in servers)
        await ctx.send(f"📜 Available Servers:\n{msg}")

# ✍️ Submit a new server
@bot.command()
async def submitserver(ctx, *, server: str):
    save_server(server)
    await ctx.send(f"✅ Server '{server}' added to the list.")
    
    # Only try to post to submission channel if the command was used in a guild (not DM)
    if ctx.guild:
        submission_channel = discord.utils.get(ctx.guild.text_channels, name="server-submissions")
        if submission_channel:
            await submission_channel.send(f"🆕 {ctx.author} submitted: {server}")

# 🎮 Skyblock server
@bot.command()
async def serverskyblock(ctx):
    await ctx.send("🌲 Skyblock Server: `play.sky-mc.net`")

# ⚔️ PvP server
@bot.command()
async def serverpvp(ctx):
    await ctx.send("⚔️ PvP Server: `pvp.legendserver.net`")

# 🔐 Login (bind)
@bot.command()
async def login(ctx, username: str):
    await ctx.send(f"🔐 Bound Discord user `{ctx.author}` to Minecraft name `{username}`.")

# 👑 Creator info
@bot.command()
async def creator(ctx):
    await ctx.send("👑 My creator is **Ansh** — the true Minecraft Slayer.")

# 😎 Bow down
@bot.command()
async def bow(ctx):
    await ctx.send("🛐 Bow before the legend — **Ansh**.")

# 🛰️ Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency is `{round(bot.latency * 1000)}ms`")

# ❔ Custom help
@bot.command(name="myhelp")
async def myhelp(ctx):
    await ctx.send("""
📘 **Bot Commands**
- `!servers` – Show community Minecraft servers
- `!submitserver <name>` – Submit your server to the list
- `!serverskyblock` – Recommended skyblock server
- `!serverpvp` – Recommended PvP server
- `!login <username>` – Bind your Minecraft name
- `!creator` – Meet the creator
- `!bow` – Praise time
- `!ping` – Check bot latency

🔒 Anti-spam enabled. DM friendly. Minecraft forever!
""")

# 📡 Invite tracking
invites = {}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as: {bot.user}")
    for guild in bot.guilds:
        invites[guild.id] = await guild.invites()
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


@bot.event
async def on_member_join(member):
    guild = member.guild
    new_invites = await guild.invites()
    old_invites = invites.get(guild.id, [])
    for invite in new_invites:
        for old_inv in old_invites:
            if invite.code == old_inv.code and invite.uses > old_inv.uses:
                inviter = invite.inviter
                if guild.system_channel:
                    await guild.system_channel.send(f"🎉 {member.mention} joined using {inviter.mention}'s invite link!")
                break
    invites[guild.id] = new_invites
    # Welcome message
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"👋 Welcome {member.mention} to the server! Type `!myhelp` to begin.")

# 🌐 Slash Commands
@bot.tree.command(name="servers", description="Show all submitted Minecraft servers")
async def slash_servers(interaction: discord.Interaction):
    servers = load_servers()
    if not servers:
        await interaction.response.send_message("📭 No servers listed yet.")
    else:
        msg = "\n".join(f"🌐 {s}" for s in servers)
        await interaction.response.send_message(f"📜 Available Servers:\n{msg}")

@bot.tree.command(name="submitserver", description="Submit a new Minecraft server")
@app_commands.describe(server="The server IP or name to add")
async def slash_submitserver(interaction: discord.Interaction, server: str):
    save_server(server)
    await interaction.response.send_message(f"✅ Server '{server}' added to the list.")
    
    # Only try to post to submission channel if the command was used in a guild (not DM)
    if interaction.guild:
        submission_channel = discord.utils.get(interaction.guild.text_channels, name="server-submissions")
        if submission_channel:
            await submission_channel.send(f"🆕 {interaction.user} submitted: {server}")

@bot.tree.command(name="skyblock", description="Get the recommended Skyblock server")
async def slash_skyblock(interaction: discord.Interaction):
    await interaction.response.send_message("🌲 Skyblock Server: `play.sky-mc.net`")

@bot.tree.command(name="pvp", description="Get the recommended PvP server")
async def slash_pvp(interaction: discord.Interaction):
    await interaction.response.send_message("⚔️ PvP Server: `pvp.legendserver.net`")

@bot.tree.command(name="login", description="Bind your Discord to a Minecraft username")
@app_commands.describe(username="Your Minecraft username")
async def slash_login(interaction: discord.Interaction, username: str):
    await interaction.response.send_message(f"🔐 Bound Discord user `{interaction.user}` to Minecraft name `{username}`.")

@bot.tree.command(name="creator", description="Meet the bot creator")
async def slash_creator(interaction: discord.Interaction):
    await interaction.response.send_message("👑 My creator is **Ansh** — the true Minecraft Slayer.")

@bot.tree.command(name="bow", description="Bow before the legend")
async def slash_bow(interaction: discord.Interaction):
    await interaction.response.send_message("🛐 Bow before the legend — **Ansh**.")

@bot.tree.command(name="ping", description="Check bot latency")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency is `{round(bot.latency * 1000)}ms`")

@bot.tree.command(name="help", description="Show all available commands")
async def slash_help(interaction: discord.Interaction):
    await interaction.response.send_message("""
📘 **Bot Commands**
- `/servers` – Show community Minecraft servers
- `/submitserver <name>` – Submit your server to the list
- `/skyblock` – Recommended skyblock server
- `/pvp` – Recommended PvP server
- `/login <username>` – Bind your Minecraft name
- `/creator` – Meet the creator
- `/bow` – Praise time
- `/ping` – Check bot latency

🔒 Anti-spam enabled. DM friendly. Minecraft forever!
""")

# 🔁 Optional: rotating bot status (uncomment to enable)
statuses = ["Minecraft Slayer", "/help", "Skyblock Realms"]
 @tasks.loop(seconds=20)
 async def change_status():
     await bot.change_presence(activity=discord.Game(name=random.choice(statuses)))
 change_status.start()

# 🌐 Keep-alive for Replit or web hosting
keep_alive()

# 🔑 Bot token from environment
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN environment variable not set")
bot.run(token)
