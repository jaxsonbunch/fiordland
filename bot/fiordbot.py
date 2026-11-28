import json
import os
from pathlib import Path

import aiohttp
import discord
from discord import app_commands
from discord.ext import tasks

import core

COLOR = 0x8EC5FF
STATE = Path(os.environ.get("STATE_DIRECTORY", "/var/lib/fiordland-bot")) / "state.json"
CRED = Path(os.environ.get("CREDENTIALS_DIRECTORY", "/run/credentials/fiordland-bot.service")) / "token"
NO_MENTIONS = discord.AllowedMentions.none()
HELP_TEMPLATE = (
    "Include these so we can help quickly:\n"
    "1. Fiordland version and kernel (`uname -r`)\n"
    "2. Desktop or window manager\n"
    "3. What you did and what you expected\n"
    "4. The exact error text, as text rather than a photo\n"
    "5. Hardware: CPU, GPU, and whether it is a VM"
)


def embed(title, description=None, url=None):
    return discord.Embed(title=title, description=description, url=url, color=COLOR)


def load_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(STATE)


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.http_session = None
        self.status_index = 0

    async def setup_hook(self):
        timeout = aiohttp.ClientTimeout(total=15)
        self.http_session = aiohttp.ClientSession(timeout=timeout, headers={"User-Agent": "fiordland-bot"})
        await self.tree.sync()
        self.releases.start()
        self.rotate.start()

    async def close(self):
        if self.http_session:
            await self.http_session.close()
        await super().close()

    async def fetch(self, url):
        async with self.http_session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    @tasks.loop(minutes=10)
    async def releases(self):
        try:
            data = await self.fetch(f"https://api.github.com/repos/{core.REPO}/releases/latest")
        except aiohttp.ClientResponseError as error:
            if error.status == 404:
                state = load_state()
                if "release" not in state:
                    state["release"] = 0
                    save_state(state)
            return
        except (aiohttp.ClientError, ValueError):
            return
        fields = core.release_embed_fields(data)
        state = load_state()
        if "release" not in state:
            state["release"] = fields["id"]
            save_state(state)
            return
        if state["release"] == fields["id"]:
            return
        state["release"] = fields["id"]
        save_state(state)
        e = embed(fields["title"], fields["description"], fields["url"])
        for guild in self.guilds:
            channel = discord.utils.get(guild.text_channels, name="announcements")
            if channel:
                try:
                    await channel.send(embed=e, allowed_mentions=NO_MENTIONS)
                except discord.HTTPException:
                    pass

    @releases.before_loop
    async def wait_ready(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=3)
    async def rotate(self):
        state = load_state()
        items = core.status_items(state)
        save_state({**load_state(), "dl": state["dl"]})
        kind, text = items[self.status_index % len(items)]
        self.status_index += 1
        activity = discord.Activity(type=discord.ActivityType.watching if kind == "watching" else discord.ActivityType.playing, name=text)
        try:
            await self.change_presence(activity=activity)
        except discord.HTTPException:
            pass

    @rotate.before_loop
    async def wait_ready_rotate(self):
        await self.wait_until_ready()


bot = Bot()


@bot.tree.command(description="Latest Fiordland ISO")
async def iso(interaction: discord.Interaction):
    try:
        info = core.iso_info()
    except (OSError, ValueError, KeyError):
        await interaction.response.send_message("Couldn't read the latest ISO info.", ephemeral=True)
        return
    e = embed(f"Fiordland {info['date']}", url=info["url"])
    e.add_field(name="Download", value=f"[{info['file']}]({info['url']})", inline=False)
    e.add_field(name="Size", value=info["size"])
    e.add_field(name="SHA256", value=f"`{info['sha256']}`", inline=False)
    await interaction.response.send_message(embed=e)


@bot.tree.command(description="Search the Fiordland and Arch repos")
@app_commands.describe(name="Package name")
async def pkg(interaction: discord.Interaction, name: str):
    q = core.clean_query(name)
    if not q:
        await interaction.response.send_message("Use a package name like `firefox`.", ephemeral=True)
        return
    await interaction.response.defer()
    lines = []
    try:
        for r in core.search_repo(q):
            lines.append(core.line("fiordland", r["name"], r["version"], r["desc"]))
    except (OSError, ValueError):
        pass
    try:
        for r in core.parse_arch(await bot.fetch(core.arch_url(q)), 5):
            url = f"https://archlinux.org/packages/{r['repo']}/x86_64/{r['name']}/"
            lines.append(core.line(r["repo"], r["name"], r["version"], r["desc"], url))
    except (aiohttp.ClientError, ValueError):
        pass
    if not lines:
        await interaction.followup.send(f"Nothing found for `{q}`. Try `/aur`.")
        return
    await interaction.followup.send(embed=embed(f"Packages matching {q}", "\n\n".join(lines)[:3900]))


@bot.tree.command(description="Search the AUR")
@app_commands.describe(name="Package name")
async def aur(interaction: discord.Interaction, name: str):
    q = core.clean_query(name)
    if not q:
        await interaction.response.send_message("Use a package name like `spotify`.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        rows = core.parse_aur(await bot.fetch(core.aur_url(q)), 5)
    except (aiohttp.ClientError, ValueError):
        await interaction.followup.send("The AUR didn't answer. Try again shortly.")
        return
    if not rows:
        await interaction.followup.send(f"Nothing found for `{q}` in the AUR.")
        return
    lines = [core.line("aur", r["name"], r["version"], r["desc"], f"https://aur.archlinux.org/packages/{r['name']}") for r in rows]
    await interaction.followup.send(embed=embed(f"AUR results for {q}", "\n\n".join(lines)[:3900]))


@bot.tree.command(description="How to install Fiordland")
async def install(interaction: discord.Interaction):
    text = (
        "1. Write the ISO to a USB stick\n2. Boot it and try the live session\n3. Run the installer and pick a desktop\n\n"
        "Needs 4 GB RAM and 20 GB disk. The installer uses the whole disk."
    )
    await interaction.response.send_message(embed=embed("Install Fiordland", text, f"{core.SITE}/#install"))


@bot.tree.command(description="Fiordland compared with CachyOS and Arch")
async def compare(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed("Fiordland, CachyOS and Arch", "What each one sets up after a default install.", f"{core.SITE}/why/#compare"))


@bot.tree.command(description="Links to the site, source and repo")
async def docs(interaction: discord.Interaction):
    text = f"[Website]({core.SITE})\n[Source](https://github.com/{core.REPO})\n[Package repo]({core.SITE}/repo/x86_64/)"
    await interaction.response.send_message(embed=embed("Fiordland links", text))


@bot.tree.command(name="helpme", description="What to include when asking for help")
async def helpme(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed("Asking for help", HELP_TEMPLATE))


@bot.tree.command(description="Mark this support thread as solved")
async def solved(interaction: discord.Interaction):
    thread = interaction.channel
    if not isinstance(thread, discord.Thread):
        await interaction.response.send_message("Use this inside a support thread.", ephemeral=True)
        return
    allowed = thread.owner_id == interaction.user.id or interaction.permissions.manage_threads
    if not allowed:
        await interaction.response.send_message("Only the thread author or a moderator can do that.", ephemeral=True)
        return
    await interaction.response.send_message("Marked as solved. Reply here to reopen it.")
    changes = {"archived": True}
    if isinstance(thread.parent, discord.ForumChannel):
        tag = discord.utils.find(lambda t: t.name.lower() == "solved", thread.parent.available_tags)
        tags = list(thread.applied_tags)
        if tag and tag not in tags:
            tags.append(tag)
        changes["applied_tags"] = tags[:5]
    elif not thread.name.startswith("[Solved]"):
        changes["name"] = f"[Solved] {thread.name}"[:100]
    try:
        await thread.edit(**changes)
    except discord.HTTPException:
        pass


def main():
    token = CRED.read_text().strip() if CRED.exists() else os.environ["DISCORD_BOT_TOKEN"]
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
