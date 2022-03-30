local base      = _G
local Terrain   = base.require('terrain')
local UC        = base.require("utils_common")

local dcsbot    = base.dcsbot
local utils 	= base.require("DCSServerBotUtils")
local config	= base.require("DCSServerBotConfig")

local mission = mission or {}
mission.last_to_landing = {}
mission.last_change_slot = {}

function mission.onMissionLoadBegin()
    log.write('DCSServerBot', log.DEBUG, 'Mission: onMissionLoadBegin()')
	local msg = {}
	msg.command = 'onMissionLoadBegin'
	msg.current_mission = DCS.getMissionName()
	msg.current_map = DCS.getCurrentMission().mission.theatre
	msg.mission_time = 0
	if (lotatc_inst ~= nil) then
		msg.lotAtcSettings = lotatc_inst.options
	end
	utils.sendBotTable(msg)
end

function mission.onMissionLoadEnd()
    log.write('DCSServerBot', log.DEBUG, 'Mission: onMissionLoadEnd()')
    local msg = {}
    msg.command = 'onMissionLoadEnd'
    msg.current_mission = DCS.getMissionName()
    msg.current_map = DCS.getCurrentMission().mission.theatre
    msg.mission_time = 0
    msg.start_time = DCS.getCurrentMission().mission.start_time
    msg.date = DCS.getCurrentMission().mission.date
    msg.weather = DCS.getCurrentMission().mission.weather
    local clouds = msg.weather.clouds
    if clouds.preset ~= nil then
        local presets = nil
        local func, err = loadfile(lfs.currentdir() .. '/Config/Effects/clouds.lua')

        local env = {
            type = _G.type,
            next = _G.next,
            setmetatable = _G.setmetatable,
            getmetatable = _G.getmetatable,
            _ = _,
        }
        setfenv(func, env)
        func()
        local preset = env.clouds and env.clouds.presets and env.clouds.presets[clouds.preset]
        if preset ~= nil then
            msg.clouds = {}
            msg.clouds.base = clouds.base
            msg.clouds.preset = preset
        end
    else
        msg.clouds = clouds
    end
    msg.airbases = {}
    for airdromeID, airdrome in pairs(Terrain.GetTerrainConfig("Airdromes")) do
        if (airdrome.reference_point) and (airdrome.abandoned ~= true)  then
            local airbase = {}
            airbase.code = airdrome.code
            if airdrome.display_name then
                airbase.name = airdrome.display_name
            else
                airbase.name = airdrome.names['en']
            end
            airbase.id = airdrome.id
            airbase.lat, airbase.lng = Terrain.convertMetersToLatLon(airdrome.reference_point.x, airdrome.reference_point.y)
            airbase.alt = Terrain.GetHeight(airdrome.reference_point.x, airdrome.reference_point.y)
            local frequencyList = {}
            if airdrome.frequency then
                frequencyList	= airdrome.frequency
            else
                if airdrome.radio then
                    for k, radioId in pairs(airdrome.radio) do
                        local frequencies = DCS.getATCradiosData(radioId)
                        if frequencies then
                            for kk,vv in pairs(frequencies) do
                                table.insert(frequencyList, vv)
                            end
                        end
                    end
                end
            end
            airbase.frequencyList = frequencyList
            airbase.runwayList = {}
            if (airdrome.runwayName ~= nil) then
                for r, runwayName in pairs(airdrome.runwayName) do
                    table.insert(airbase.runwayList, runwayName)
                end
            end
            heading = UC.toDegrees(Terrain.getRunwayHeading(airdrome.roadnet))
            if (heading < 0) then
                heading = 360 + heading
            end
            airbase.rwy_heading = heading
            table.insert(msg.airbases, airbase)
        end
    end
    --[[
    if (dcsbot.updateSlots()['slots']['blue'] ~= nil) then
        msg.num_slots_blue = table.getn(dcsbot.updateSlots()['slots']['blue'])
    end
    if (dcsbot.updateSlots()['slots']['red'] ~= nil) then
        msg.num_slots_red = table.getn(dcsbot.updateSlots()['slots']['red'])
    end
    ]]--
    utils.sendBotTable(msg)
end

function mission.onPlayerConnect(id)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onPlayerConnect()')
	local msg = {}
	msg.command = 'onPlayerConnect'
	msg.id = id
	msg.name = net.get_player_info(id, 'name')
	msg.ucid = net.get_player_info(id, 'ucid')
	msg.ipaddr = net.get_player_info(id, 'ipaddr')
    msg.side = 0
    -- server user is never active
    if (msg.id == 1) then
        msg.active = false
    else
        msg.active = true
    end
	utils.sendBotTable(msg)
end

function mission.onPlayerStart(id)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onPlayerStart()')
	local msg = {}
	msg.command = 'onPlayerStart'
	msg.id = id
	msg.ucid = net.get_player_info(id, 'ucid')
	msg.name = net.get_player_info(id, 'name')
	msg.ipaddr = net.get_player_info(id, 'ipaddr')
    msg.side = 0
    -- server user is never active
    if (msg.id == 1) then
        msg.active = false
    else
        msg.active = true
    end
	utils.sendBotTable(msg)
end

function mission.onPlayerStop(id)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onPlayerStop()')
    local msg = {}
    msg.command = 'onPlayerStop'
    msg.id = id
    msg.ucid = net.get_player_info(id, 'ucid')
    msg.name = net.get_player_info(id, 'name')
    msg.active = false
    utils.sendBotTable(msg)
end

function mission.onPlayerChangeSlot(id)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onPlayerChangeSlot()')
    local msg = {}
    msg.command = 'onPlayerChangeSlot'
    msg.id = id
    msg.ucid = net.get_player_info(id, 'ucid')
    msg.name = net.get_player_info(id, 'name')
    msg.side = net.get_player_info(id, 'side')
    msg.unit_type, msg.slot, msg.sub_slot = utils.getMulticrewAllParameters(id)
    msg.unit_name = DCS.getUnitProperty(msg.slot, DCS.UNIT_NAME)
    msg.group_name = DCS.getUnitProperty(msg.slot, DCS.UNIT_GROUPNAME)
    msg.group_id = DCS.getUnitProperty(msg.slot, DCS.UNIT_GROUP_MISSION_ID)
    msg.unit_callsign = DCS.getUnitProperty(msg.slot, DCS.UNIT_CALLSIGN)
    msg.active = true
    utils.sendBotTable(msg)
end

function mission.onSimulationStart()
    log.write('DCSServerBot', log.DEBUG, 'Mission: onSimulationStart()')
    local msg = {}
    msg.command = 'onSimulationStart'
    utils.sendBotTable(msg)
end

function mission.onSimulationStop()
    log.write('DCSServerBot', log.DEBUG, 'Mission: onSimulationStop()')
    local msg = {}
    msg.command = 'onSimulationStop'
    utils.sendBotTable(msg)
end

function mission.onSimulationPause()
    log.write('DCSServerBot', log.DEBUG, 'Mission: onSimulationPause()')
	local msg = {}
	msg.command = 'onSimulationPause'
	utils.sendBotTable(msg)
end

function mission.onSimulationResume()
    log.write('DCSServerBot', log.DEBUG, 'Mission: onSimulationResume()')
	local msg = {}
	msg.command = 'onSimulationResume'
	utils.sendBotTable(msg)
end

function mission.onGameEvent(eventName,arg1,arg2,arg3,arg4,arg5,arg6,arg7)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onGameEvent(' .. eventName .. ')')
    -- ignore false events
    if eventName == 'change_slot' then
        mission.last_change_slot[arg1] = os.clock()
    elseif eventName == 'takeoff' or eventName == 'landing' then
        if mission.last_change_slot[arg1] and mission.last_change_slot[arg1] > (os.clock() - 60) then
            log.write('DCSServerBot', log.DEBUG, 'Mission: ignoring ' .. eventName .. ' event.')
            return
        end
        if mission.last_to_landing[arg1] and mission.last_to_landing[arg1] > (os.clock() - 10) then
            log.write('DCSServerBot', log.DEBUG, 'Mission: ignoring ' .. eventName .. ' event.')
            return
        else
            mission.last_to_landing[arg1] = os.clock()
        end
    end
	local msg = {}
	msg.command = 'onGameEvent'
	msg.eventName = eventName
	msg.arg1 = arg1
	msg.arg2 = arg2
	msg.arg3 = arg3
	msg.arg4 = arg4
	msg.arg5 = arg5
	msg.arg6 = arg6
	msg.arg7 = arg7
	if (msg.eventName == 'kill') then
		msg.victimCategory = utils.getCategory(arg5)
		msg.killerCategory = utils.getCategory(arg2)
	end
	utils.sendBotTable(msg)
end

function mission.onPlayerTrySendChat(from, message, to)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onPlayerTrySendChat()')
    if string.sub(message, 1, 1) == '-' then
        local msg = {}
        msg.command = 'onChatCommand'
        msg.message = message
        msg.from_id = net.get_player_info(from, 'id')
        msg.from_name = net.get_player_info(from, 'name')
        msg.to = to
        utils.sendBotTable(msg)
        return ''
    end
    return message
end

function mission.onChatMessage(message, from, to)
    log.write('DCSServerBot', log.DEBUG, 'Mission: onChatMessage()')
	local msg = {}
	msg.command = 'onChatMessage'
	msg.message = message
	msg.from_id = net.get_player_info(from, 'id')
	msg.from_name = net.get_player_info(from, 'name')
    msg.to = to
	utils.sendBotTable(msg, config.CHAT_CHANNEL)
end

DCS.setUserCallbacks(mission)
