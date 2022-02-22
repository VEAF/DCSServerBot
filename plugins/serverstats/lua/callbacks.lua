local base      = _G
local dcsbot    = base.dcsbot
local utils 	= base.require("DCSServerBotUtils")

local serverstats = serverstats or {}
local counter     = 0
local starttime   = -1

function serverstats.onSimulationFrame()
    if starttime == -1 then
        starttime = os.clock()
    end
    if counter == 3600 then
        local endtime = os.clock()
        msg = {}
        msg.command = 'perfmon'
        msg.fps = counter / (endtime-starttime)
    	utils.sendBotTable(msg)
        counter = 0
        starttime = endtime
    else
        counter = counter + 1
    end
end

DCS.setUserCallbacks(serverstats)
