UPDATE missionstats SET init_id = sub.new_ucid FROM (SELECT p1.ucid as old_ucid, p2.ucid AS new_ucid FROM players p1, (SELECT DISTINCT ON(discord_id) discord_id, name, ucid, last_seen FROM players WHERE discord_id != -1 AND manual is true ORDER BY discord_id, last_seen DESC) p2 WHERE p1.discord_id = p2.discord_id AND p1.last_seen <> p2.last_seen) AS sub WHERE init_id = sub.old_ucid;
UPDATE missionstats SET target_id = sub.new_ucid FROM (SELECT p1.ucid as old_ucid, p2.ucid AS new_ucid FROM players p1, (SELECT DISTINCT ON(discord_id) discord_id, name, ucid, last_seen FROM players WHERE discord_id != -1 AND manual is true ORDER BY discord_id, last_seen DESC) p2 WHERE p1.discord_id = p2.discord_id AND p1.last_seen <> p2.last_seen) AS sub WHERE target_id = sub.old_ucid;
UPDATE players p SET discord_id = -1, manual = False FROM (SELECT DISTINCT ON(discord_id) discord_id, name, ucid, last_seen FROM players WHERE discord_id != -1 AND manual is true ORDER BY discord_id, last_seen DESC) sub WHERE p.discord_id = sub.discord_id AND p.ucid != sub.ucid;
