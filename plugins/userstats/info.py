import discord
from contextlib import closing
from core import report, Side, Player, DataObjectFactory, Member, utils
from datetime import datetime
from typing import Union, Optional
from psycopg.rows import dict_row


class Header(report.EmbedElement):
    def render(self, member: Union[discord.Member, str]):
        sql = 'SELECT p.last_seen, CASE WHEN p.ucid = b.ucid THEN 1 ELSE 0 END AS banned ' \
              'FROM players p LEFT OUTER JOIN bans b ON (b.ucid = p.ucid) WHERE p.discord_id = '
        if isinstance(member, str):
            sql += f"(SELECT discord_id FROM players WHERE ucid = '{member}' AND discord_id != -1) OR " \
                   f"p.ucid = '{member}' OR LOWER(p.name) ILIKE '{member.casefold()}' "
        else:
            sql += f"'{member.id}'"
        sql += ' GROUP BY p.ucid, b.ucid'
        with self.pool.connection() as conn:
            with closing(conn.cursor(row_factory=dict_row)) as cursor:
                cursor.execute(sql)
                if cursor.rowcount == 0:
                    self.embed.description = 'User "{}" is not linked.'.format(utils.escape_string(member if isinstance(member, str) else member.display_name))
                    return
                rows = list(cursor.fetchall())
        self.embed.description = f'Information about '
        if isinstance(member, discord.Member):
            self.embed.description += 'member **{}**:'.format(utils.escape_string(member.display_name))
            self.add_field(name='Discord ID:', value=member.id)
        else:
            self.embed.description += 'a non-member user:'
        last_seen = datetime(1970, 1, 1)
        banned = False
        for row in rows:
            if row['last_seen'] and row['last_seen'] > last_seen:
                last_seen = row['last_seen']
            if row['banned'] == 1:
                banned = True
        if last_seen != datetime(1970, 1, 1):
            self.add_field(name='Last seen:', value=last_seen.strftime("%m/%d/%Y, %H:%M:%S"))
        if banned:
            self.add_field(name='Status', value='Banned')


class UCIDs(report.EmbedElement):
    def render(self, member: Union[discord.Member, str]):
        sql = 'SELECT p.ucid, p.manual, COALESCE(p.name, \'?\') AS name FROM players p WHERE p.discord_id = '
        if isinstance(member, str):
            sql += f"(SELECT discord_id FROM players WHERE ucid = '{member}' AND discord_id != -1) OR " \
                   f"p.ucid = '{member}' OR LOWER(p.name) ILIKE '{member.casefold()}' "
        else:
            sql += f"'{member.id}'"
        with self.pool.connection() as conn:
            with closing(conn.cursor(row_factory=dict_row)) as cursor:
                rows = cursor.execute(sql).fetchall()
                if not rows:
                    return
                self.add_field(name='▬' * 13 + ' Connected UCIDs ' + '▬' * 12, value='_ _', inline=False)
                self.add_field(name='UCID', value='\n'.join([row['ucid'] for row in rows]))
                self.add_field(name='DCS Name', value='\n'.join([utils.escape_string(row['name']) for row in rows]))
                if isinstance(member, discord.Member):
                    self.add_field(name='Validated', value='\n'.join(
                        ['Approved' if row['manual'] is True else 'Not Approved' for row in rows]))


class History(report.EmbedElement):
    def render(self, member: Union[discord.Member, str]):
        sql = 'SELECT name, max(time) AS time FROM players_hist p WHERE p.discord_id = '
        if isinstance(member, str):
            sql += f"(SELECT discord_id FROM players WHERE ucid = '{member}' AND discord_id != -1) OR " \
                   f"p.ucid = '{member}' OR LOWER(p.name) ILIKE '{member.casefold()}' "
        else:
            sql += f"'{member.id}'"
        sql += ' GROUP BY name ORDER BY time DESC LIMIT 10'
        with self.pool.connection() as conn:
            with closing(conn.cursor(row_factory=dict_row)) as cursor:
                rows = cursor.execute(sql).fetchall()
                if not rows:
                    return
                self.add_field(name='▬' * 13 + ' Change History ' + '▬' * 13, value='_ _', inline=False)
                self.add_field(name='DCS Name', value='\n'.join([utils.escape_string(row['name'] or 'n/a') for row in rows]))
                self.add_field(name='Time', value='\n'.join([f"{row['time']:%y-%m-%d %H:%M:%S}" for row in rows]))
                self.add_field(name='_ _', value='_ _')


class ServerInfo(report.EmbedElement):
    def render(self, member: Union[discord.Member, str], player: Optional[Player]):
        if player:
            self.add_field(name='▬' * 13 + ' Current Activity ' + '▬' * 13, value='_ _', inline=False)
            self.add_field(name='Active on Server', value=player.server.display_name)
            self.add_field(name='DCS Name', value=player.display_name)
            self.add_field(name='Slot', value=player.unit_type if player.side != Side.SPECTATOR else 'Spectator')


class Footer(report.EmbedElement):
    def render(self, member: Union[discord.Member, str], player: Optional[Player]):
        if isinstance(member, discord.Member):
            _member: Member = DataObjectFactory().new('Member', member=member)
            if len(_member.ucids):
                footer = '🔀 Unlink all DCS players from this user\n'
                if not _member.verified:
                    footer += '💯 Verify this DCS link\n'
                footer += '✅ Unban this user\n' if _member.banned else '⛔ Ban this user (DCS only)\n'
            else:
                footer = ''
        else:
            footer = '✅ Unban this user\n' if utils.is_banned(self, member) else '⛔ Ban this user (DCS only)\n'
        footer += '⏏️ Kick this user from the active server\n' if player else ''
        footer += '⏹️Cancel'
        self.embed.set_footer(text=footer)
