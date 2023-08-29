import aiohttp
import discord
import os
import platform
import shutil
import traceback
import yaml

from contextlib import closing
from core import utils, Plugin, Status, Server, command, NodeImpl, ServerTransformer, Node
from discord import app_commands
from discord.app_commands import Range, Group
from discord.ext import commands
from discord.ui import Select, View, Button, TextInput, Modal
from io import BytesIO
from services import DCSServerBot
from typing import Optional, Union
from zipfile import ZipFile, ZIP_DEFLATED


async def label_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        server: Server = await interaction.client.get_server(interaction)
        if not server:
            return []
        config = interaction.client.cogs['Admin'].get_config(server)
        choices: list[app_commands.Choice[str]] = [
            app_commands.Choice(name=x['label'], value=x['label']) for x in config['downloads']
            if not current or current.casefold() in x['label'].casefold()
        ]
        return choices[:25]
    except Exception:
        traceback.print_exc()


async def file_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        server: Server = await interaction.client.get_server(interaction)
        if not server:
            return []
        label = utils.get_interaction_param(interaction, "what")
        config = interaction.client.cogs['Admin'].get_config(server)
        config = next(x for x in config['downloads'] if x['label'] == label)
        choices: list[app_commands.Choice[str]] = [
            app_commands.Choice(name=os.path.basename(x), value=os.path.basename(x))
            for x in await server.node.list_directory(config['directory'].format(server=server), config['pattern'])
            if not current or current.casefold() in x
        ]
        return choices[:25]
    except Exception:
        traceback.print_exc()


class Admin(Plugin):

    def read_locals(self) -> dict:
        config = super().read_locals()
        if not config:
            self.log.info('  - No admin.yaml found, copying the sample.')
            shutil.copyfile('config/samples/admin.yaml', 'config/plugins/admin.yaml')
            config = super().read_locals()
        return config

    dcs = Group(name="dcs", description="Commands to manage your DCS installations")

    @dcs.command(description='Bans a user by name or ucid')
    @app_commands.guild_only()
    @utils.app_has_role('DCS Admin')
    async def ban(self, interaction: discord.Interaction,
                  user: Optional[app_commands.Transform[Union[discord.Member, str], utils.UserTransformer(linked=True)]]):

        class BanModal(Modal):
            reason = TextInput(label="Reason", default="n/a", max_length=80, required=False)
            period = TextInput(label="Days (empty = forever)", required=False)

            def __init__(self, user: Union[discord.Member, str]):
                super().__init__(title="Ban Details")
                self.user = user

            async def on_submit(derived, interaction: discord.Interaction):
                if derived.period.value:
                    days = int(derived.period.value)
                else:
                    days = None

                if isinstance(derived.user, discord.Member):
                    ucid = self.bot.get_ucid_by_member(derived.user)
                    name = derived.user.display_name
                elif utils.is_ucid(derived.user):
                    ucid = derived.user
                    # check if we should ban a member
                    name = self.bot.get_member_or_name_by_ucid(ucid)
                    if isinstance(name, discord.Member):
                        name = name.display_name
                    elif not name:
                        name = ucid
                else:
                    ucid, name = self.bot.get_ucid_by_name(derived.user)

                self.bus.ban(ucid, derived.reason.value, interaction.user.display_name, days)
                await interaction.response.send_message(f"Player {name} banned on all servers" +
                                                        (f" for {days} days." if days else ""))
                await self.bot.audit(f'banned player {name} (ucid={ucid} with reason "{derived.reason.value}"' +
                                     f' for {days} days.' if days else ' permanently.',
                                     user=interaction.user)

            async def on_error(derived, interaction: discord.Interaction, error: Exception) -> None:
                self.log.exception(error)

        await interaction.response.send_modal(BanModal(user))

    @dcs.command(description='Unbans a user by name or ucid')
    @app_commands.guild_only()
    @utils.app_has_role('DCS Admin')
    @app_commands.rename(ucid="user")
    @app_commands.autocomplete(ucid=utils.bans_autocomplete)
    async def unban(self, interaction: discord.Interaction, ucid: str):
        self.bus.unban(ucid)
        name = self.bot.get_member_or_name_by_ucid(ucid)
        if isinstance(name, discord.Member):
            name = name.display_name
        elif not name:
            name = ucid
        await interaction.response.send_message(f"Player {name} unbanned on all servers.")
        await self.bot.audit(f'unbanned player {name} (ucid={ucid})', user=interaction.user)

    @dcs.command(description='Shows active bans')
    @app_commands.guild_only()
    @utils.app_has_role('DCS Admin')
    @app_commands.autocomplete(user=utils.bans_autocomplete)
    async def bans(self, interaction: discord.Interaction, user: str):
        ban = next(x for x in self.bus.bans() if x['ucid'] == user)
        embed = discord.Embed(title='Bans Information', color=discord.Color.blue())
        if ban['discord_id'] != -1:
            user = self.bot.get_user(ban['discord_id'])
        else:
            user = None
        embed.add_field(name=utils.escape_string(user.name if user else ban['name'] if ban['name'] else '<unknown>'),
                        value=ban['ucid'])
        until = ban['banned_until'].strftime('%Y-%m-%d %H:%M')
        embed.add_field(name=f"Banned by: {ban['banned_by']}", value=f"Exp.: {until}" if not until.startswith('9999') else '_ _')
        embed.add_field(name='Reason', value=ban['reason'])
        await interaction.response.send_message(embed=embed)

    @dcs.command(description='Update your DCS installations')
    @app_commands.guild_only()
    @utils.app_has_role('DCS Admin')
    @app_commands.autocomplete(node=utils.nodes_autocomplete)
    @app_commands.describe(warn_time="Time in seconds to warn users before shutdown")
    async def update(self, interaction: discord.Interaction, node: Optional[str] = None, warn_time: Range[int, 0] = 60):
        _node: Node = next(x.node for x in self.bus.servers.values() if x.node.name == node)
        if not _node:
            await interaction.response.send_message(f"Can't reach node {node}, is it even active?")
            return
        await interaction.response.defer(thinking=True, ephemeral=True)
        branch, old_version = await _node.get_dcs_branch_and_version()
        new_version = await utils.getLatestVersion(branch, userid=_node.locals['DCS'].get('dcs_user'),
                                                   password=_node.locals['DCS'].get('dcs_password'))
        if old_version == new_version:
            await interaction.followup.send(
                f'Your installed version {old_version} is the latest on branch {branch}.', ephemeral=True)
        elif new_version:
            if await utils.yn_question(interaction,
                                       f'Would you like to update from version {old_version} to {new_version}?\n'
                                       f'All running DCS servers will be shut down!') is True:
                await self.bot.audit(f"started an update of all DCS servers on node {platform.node()}.",
                                     user=interaction.user)
                msg = await interaction.followup.send(f"Updating DCS to version {new_version}, please wait ...",
                                                      ephemeral=True)
                rc = await _node.update(warn_times=[warn_time] or [120, 60])
                if rc == 0:
                    await msg.edit(content=f"DCS updated to version {new_version} on node {node}.")
                    await self.bot.audit(f"updated DCS from {old_version} to {new_version} on node {node}.",
                                         user=interaction.user)
                else:
                    await msg.edit(content=f"Error while updating DCS, code={rc}")
        else:
            await interaction.followup.send(
                f"Can't update branch {branch}. You might need to provide proper DCS credentials to do so.",
                ephemeral=True)

    @dcs.command(name='install', description='Install available modules in your dedicated server')
    @app_commands.guild_only()
    @utils.app_has_role('Admin')
    @app_commands.autocomplete(node=utils.nodes_autocomplete)
    @app_commands.autocomplete(module=utils.available_modules_autocomplete)
    async def _install(self, interaction: discord.Interaction, node: str, module: str):
        if not await utils.yn_question(interaction,
                                       f"Shutdown all servers on node {node} for the installation?"):
            await interaction.followup.send("Aborted.", ephemeral=True)
            return
        _node: Optional[Node] = None
        for server in [x for x in self.bus.servers.values() if x.node.name == node]:
            _node = server.node
            if server.status != Status.SHUTDOWN:
                await server.shutdown(force=True)
        if not _node:
            await interaction.followup.send(f"Can't reach node {node}, is there any server active?")
            return
        await _node.handle_module('install', module)
        await interaction.followup.send(f"Module {module} installed on node {node}", ephemeral=True)

    @dcs.command(name='uninstall', description='Uninstall modules from your dedicated server')
    @app_commands.guild_only()
    @utils.app_has_role('Admin')
    @app_commands.autocomplete(node=utils.nodes_autocomplete)
    @app_commands.autocomplete(module=utils.installed_modules_autocomplete)
    async def _uninstall(self, interaction: discord.Interaction, node: str, module: str):
        if not await utils.yn_question(interaction,
                                       f"Shutdown all servers on node {node} for the uninstallation?"):
            await interaction.followup.send("Aborted.", ephemeral=True)
            return
        _node: Optional[Node] = None
        for server in [x for x in self.bus.servers.values() if x.node.name == node]:
            _node = server.node
            if server.status != Status.SHUTDOWN:
                await server.shutdown(force=True)
        if not _node:
            await interaction.followup.send(f"Can't reach node {node}, is there any server active?")
            return
        await _node.handle_module('uninstall', module)
        await interaction.followup.send(f"Module {module} uninstalled on node {node}", ephemeral=True)

    @command(description='Download files from your server')
    @app_commands.guild_only()
    @utils.app_has_role('DCS Admin')
    @app_commands.autocomplete(what=label_autocomplete)
    @app_commands.autocomplete(filename=file_autocomplete)
    async def download(self, interaction: discord.Interaction,
                       server: app_commands.Transform[Server, utils.ServerTransformer],
                       what: str, filename: str) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        config = next(x for x in self.get_config(server)['downloads'] if x['label'] == what)
        path = os.path.join(config['directory'].format(server=server), filename)
        file = await server.node.read_file(path)
        target = config.get('target')
        if target:
            target = target.format(server=server)
        if not filename.endswith('.zip') and not filename.endswith('.miz') and not filename.endswith('acmi') and \
                len(file) >= 25 * 1024 * 1024:
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "a", ZIP_DEFLATED, False) as zip_file:
                zip_file.writestr(filename, file)
            file = zip_buffer.getvalue()
        if not target:
            dm_channel = await interaction.user.create_dm()
            for channel in [dm_channel, interaction.channel]:
                try:
                    await channel.send(file=discord.File(filename=filename, fp=BytesIO(file)))
                    if channel == dm_channel:
                        await interaction.followup.send('File sent as a DM.', ephemeral=True)
                    else:
                        await interaction.followup.send('Here is your file:', ephemeral=True)
                    break
                except discord.HTTPException:
                    continue
            else:
                await interaction.followup.send('File too large. You need a higher boost level for your server.',
                                                ephemeral=True)
        elif target.startswith('<'):
            channel = self.bot.get_channel(int(target[4:-1]))
            try:
                await channel.send(file=discord.File(filename=filename, fp=BytesIO(file)))
            except discord.HTTPException:
                await interaction.followup.send('File too large. You need a higher boost level for your server.',
                                                ephemeral=True)
            if channel != interaction.channel:
                await interaction.followup.send('File sent to the configured channel.', ephemeral=True)
            else:
                await interaction.followup.send('Here is your file:', ephemeral=True)
        else:
            with open(os.path.expandvars(target), 'wb') as outfile:
                outfile.write(file)
            await interaction.followup.send('File copied to the specified location.', ephemeral=True)

    class CleanupView(View):
        def __init__(self):
            super().__init__()
            self.what = 'non-members'
            self.age = '180'
            self.command = None

        @discord.ui.select(placeholder="What to be pruned?", options=[
            discord.SelectOption(label='Non-member users (unlinked)', value='non-members', default=True),
            discord.SelectOption(label='Members and non-members', value='users'),
            discord.SelectOption(label='Data only (all users)', value='data')
        ])
        async def set_what(self, interaction: discord.Interaction, select: Select):
            self.what = select.values[0]
            await interaction.response.defer()

        @discord.ui.select(placeholder="Which age to be pruned?", options=[
            discord.SelectOption(label='Older than 90 days', value='90'),
            discord.SelectOption(label='Older than 180 days', value='180', default=True),
            discord.SelectOption(label='Older than 1 year', value='360 days')
        ])
        async def set_age(self, interaction: discord.Interaction, select: Select):
            self.age = select.values[0]
            await interaction.response.defer()

        @discord.ui.button(label='Prune', style=discord.ButtonStyle.danger, emoji='⚠')
        async def prune(self, interaction: discord.Interaction, button: Button):
            await interaction.response.defer()
            self.command = "prune"
            self.stop()

        @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: Button):
            await interaction.response.defer()
            self.command = "cancel"
            self.stop()

    @command(name='prune', description='Prune unused data in the database')
    @app_commands.guild_only()
    @utils.app_has_role('Admin')
    async def _prune(self, interaction: discord.Interaction):
        embed = discord.Embed(title=":warning: Database Prune :warning:")
        embed.description = "You are going to delete data from your database. Be advised.\n\n" \
                            "Please select the data to be pruned:"
        view = self.CleanupView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        try:
            await view.wait()
        finally:
            await interaction.delete_original_response()
        if view.command == "cancel":
            await interaction.followup.send('Aborted.', ephemeral=True)
            return

        with self.pool.connection() as conn:
            with conn.pipeline():
                with conn.transaction():
                    with closing(conn.cursor()) as cursor:
                        if view.what in ['users', 'non-members']:
                            sql = f"SELECT ucid FROM players WHERE last_seen < (DATE(NOW()) - interval '{view.age} days')"
                            if view.what == 'non-members':
                                sql += ' AND discord_id = -1'
                            ucids = [row[0] for row in cursor.execute(sql).fetchall()]
                            if not ucids:
                                await interaction.followup.send('No players to prune.', ephemeral=True)
                                return
                            if not await utils.yn_question(interaction, f"This will delete {len(ucids)} players incl. "
                                                                        f"their stats from the database.\n"
                                                                        f"Are you sure?"):
                                return
                            for plugin in self.bot.cogs.values():  # type: Plugin
                                await plugin.prune(conn, ucids=ucids)
                            for ucid in ucids:
                                cursor.execute('DELETE FROM players WHERE ucid = %s', (ucid, ))
                            await interaction.followup.send(f"{len(ucids)} players pruned.", ephemeral=True)
                        elif view.what == 'data':
                            days = int(view.age)
                            if not await utils.yn_question(interaction, f"This will delete all data older than {days} "
                                                                        f"days from the database.\nAre you sure?"):
                                return
                            for plugin in self.bot.cogs.values():  # type: Plugin
                                await plugin.prune(conn, days=days)
                            await interaction.followup.send(f"All data older than {days} days pruned.", ephemeral=True)
        await self.bot.audit(f'pruned the database', user=interaction.user)

    node = Group(name="node", description="Commands to manage your nodes")

    @node.command(name='list', description='Status of all nodes')
    @app_commands.guild_only()
    @utils.app_has_role('DCS Admin')
    async def _list(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"All Nodes", color=discord.Color.blue())
        master: NodeImpl = self.bot.node
        # master node
        names = []
        instances = []
        status = []
        embed.add_field(name="▬" * 32, value=f"**Master: {master.name}**", inline=False)
        for server in [server for server in self.bus.servers.values() if server.node == master]:
            instances.append(server.instance.name)
            names.append(server.name)
            status.append(server.status.name)
        embed.add_field(name="Instance", value='\n'.join(instances))
        embed.add_field(name="Server", value='\n'.join(names))
        embed.add_field(name="Status", value='\n'.join(status))
        embed.set_footer(text=f"Bot Version: v{self.bot.version}.{self.bot.sub_version}")
        # agent nodes
        names = []
        instances = []
        status = []
        for node in master.get_active_nodes():
            embed.add_field(name="▬" * 32, value=f"Agent: {node}", inline=False)
            for server in [server for server in self.bus.servers.values() if server.node.name == node]:
                instances.append(server.instance.name)
                names.append(server.name)
                status.append(server.status.name)
            embed.add_field(name="Instance", value='\n'.join(instances))
            embed.add_field(name="Server", value='\n'.join(names))
            embed.add_field(name="Status", value='\n'.join(status))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def run_on_nodes(self, interaction: discord.Interaction, method: str, node: Optional[str] = None):
        if not node:
            msg = f"Do you want to {method} all nodes?\n"
        else:
            msg = f"Do you want to {method} node {node}?\n"
        if not await utils.yn_question(interaction,
                                       msg + "It should autostart again, if being launched with run.cmd."):
            await interaction.followup.send('Aborted.', ephemeral=True)
            return
        for n in self.bot.node.get_active_nodes():
            if not node or node == n:
                self.bus.send_to_node({
                    "command": "rpc",
                    "object": "Node",
                    "method": method
                }, node=n)
            await interaction.followup.send(f'Node {node} - {method} sent.', ephemeral=True)
        if not node or node == platform.node():
            await interaction.followup.send(f'Master node is going to {method} **NOW**.', ephemeral=True)
            self.bot.node.shutdown()

    @node.command(description='Stop a specific node')
    @app_commands.guild_only()
    @utils.app_has_role('Admin')
    @app_commands.autocomplete(node=utils.nodes_autocomplete)
    async def exit(self, interaction: discord.Interaction, node: Optional[str] = None):
        await self.run_on_nodes(interaction, "shutdown", node)

    @node.command(description='Upgrade a node')
    @app_commands.guild_only()
    @utils.app_has_role('Admin')
    @app_commands.autocomplete(node=utils.nodes_autocomplete)
    async def upgrade(self, interaction: discord.Interaction, node: Optional[str] = None):
        await self.run_on_nodes(interaction, "upgrade", node)

    @command(description='Reloads a plugin')
    @app_commands.guild_only()
    @utils.app_has_role('Admin')
    @app_commands.autocomplete(plugin=utils.plugins_autocomplete)
    async def reload(self, interaction: discord.Interaction, plugin: Optional[str]):
        await interaction.response.defer(ephemeral=True)
        if plugin:
            if await self.bot.reload(plugin):
                await interaction.followup.send(f'Plugin {plugin.title()} reloaded.')
            else:
                await interaction.followup.send(
                    f'Plugin {plugin.title()} could not be reloaded, check the log for details.')
        else:
            if await self.bot.reload():
                await interaction.followup.send(f'All plugins reloaded.')
            else:
                await interaction.followup.send(
                    f'One or more plugins could not be reloaded, check the log for details.')

    # TODO: remote server implementation
    async def process_message(self, message: discord.Message) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.get(message.attachments[0].url) as response:
                if response.status == 200:
                    ctx = await self.bot.get_context(message)
                    if message.attachments[0].filename.endswith('.yaml'):
                        data = yaml.safe_load(await response.text(encoding='utf-8', errors='ignore'))
                        name = message.attachments[0].filename[:-5]
                        if name in ['main', 'nodes', 'presets', 'servers']:
                            targetpath = 'config'
                            plugin = False
                        elif name in ['backup', 'bot']:
                            targetpath = os.path.join('config', 'services')
                            plugin = False
                        elif name in self.bot.node.plugins:
                            targetpath = os.path.join('config', 'plugins')
                            plugin = True
                        else:
                            return False
                        targetfile = os.path.join(targetpath, name + '.yaml')
                        if os.path.exists(targetfile) and not \
                                await utils.yn_question(ctx, f'Do you want to overwrite {targetfile} on '
                                                             f'node {platform.node()}?'):
                            await message.channel.send('Aborted.')
                            return True
                        with open(targetfile, 'w', encoding="utf-8") as outfile:
                            yaml.safe_dump(data, outfile)
                        if plugin:
                            await self.bot.reload(name)
                            await message.channel.send(f"Plugin {name.title()} re-loaded.")
                        elif await utils.yn_question(ctx, 'Do you want to exit (restart) the bot?'):
                            await message.channel.send('Bot restart initiated.')
                            exit(-1)
                        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore bot messages or messages that does not contain json attachments
        if message.author.bot or not message.attachments or \
                not (
                    message.attachments[0].filename.endswith('.yaml') or
                    message.attachments[0].filename.endswith('.json')
                ):
            return
        # only Admin role is allowed to upload config files in channels
        if not utils.check_roles(self.bot.roles['Admin'], message.author):
            return
        if await self.bot.get_server(message) and await self.process_message(message):
            await message.delete()
            return
        if not message.attachments[0].filename.endswith('.json'):
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(message.attachments[0].url) as response:
                if response.status == 200:
                    data = await response.json(encoding="utf-8")
                    if 'configs' not in data:
                        embed = utils.format_embed(data)
                        msg = None
                        if 'message_id' in data:
                            try:
                                msg = await message.channel.fetch_message(int(data['message_id']))
                                await msg.edit(embed=embed)
                            except discord.errors.NotFound:
                                msg = None
                            except discord.errors.DiscordException as ex:
                                self.log.exception(ex)
                                await message.channel.send(f'Error while updating embed!')
                                return
                        if not msg:
                            await message.channel.send(embed=embed)
                        await message.delete()
                else:
                    await message.channel.send(f'Error {response.status} while reading JSON file!')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.bot.log.debug(f'Member {member.display_name} has joined guild {member.guild.name}')
        ucid = self.bot.get_ucid_by_member(member)
        if ucid and self.bot.locals.get('autoban', False):
            self.bus.unban(ucid)
        if self.bot.locals.get('greeting_dm'):
            channel = await member.create_dm()
            await channel.send(self.bot.locals['greeting_dm'].format(name=member.name, guild=member.guild.name))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.bot.log.debug(f'Member {member.display_name} has left the discord')
        ucid = self.bot.get_ucid_by_member(member)
        if ucid and self.bot.locals.get('autoban', False):
            self.bot.log.debug(f'- Banning them on our DCS servers due to AUTOBAN')
            self.bus.ban(ucid, self.bot.member.display_name, 'Player left discord.')


async def setup(bot: DCSServerBot):
    await bot.add_cog(Admin(bot))
