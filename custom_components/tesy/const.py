"""Constants for the Tesy integration."""
from homeassistant.const import CONF_IP_ADDRESS

DOMAIN = "tesy"
HTTP_TIMEOUT = 15
UPDATE_INTERVAL = 30

IP_ADDRESS = CONF_IP_ADDRESS


#Api to make calls to 
ATTR_API = "api"

#Current software version
ATTR_SOFTWARE = "wsw"

#Mac address of the device
ATTR_MAC = "MAC"

"""Id of the thermocontroller, 
2000 - ModEco With display
2002 - BelliSlimo, only support showers 0-4(maximum depends on size and position)
2003 - BiLight Smart
2004 - Modeco with bar graph and only two buttons
2005 - BeliSlimo Lite, only support showers 0-4(maximum depends on size and position)
"""
ATTR_DEVICE_ID = "id"

#If currently the heater is heating at che moment
ATTR_IS_HEATING = "ht"


#Current temperature measured. Current showers on Belislimo.
ATTR_CURRENT_TEMP = "tmpC"

#Target temperature in manual mode, target showers on Belislimo. Integer value in both cases.
ATTR_TARGET_TEMP = "tmpT"

#READ-ONLY Target temperature that the controller is using depending on mode. If not on manual it will differ from tmpT.
ATTR_CURRENT_TARGET_TEMP = "tmpR"

"""
Current Operating mode, depending on the device. P1 and P2 heat up in advance so you have the target at the specified time. P3 is like normal thermostat. 
0     	manual
1		P1
2		P2
3		P3 
4		ECO
5		ECO Confort
6		ECO Night
"""

TESY_MODE_P1 = "P1"
TESY_MODE_P2 = "P2"
TESY_MODE_P3 = "P3"
TESY_MODE_EC2 = "EC2"
TESY_MODE_EC3 = "EC3"

ATTR_MODE = "mode"

#Standby flag, 0 - Off(Antifreeze), 1 -On. If device is off and plugged in will prevent the water from freezing event if off.
ATTR_POWER = "pwr"

#Boost flag 1 - Active, 0 - Inactive. If set Heater will heat once to max, hold there for some time and clear the flag.
ATTR_BOOST = "bst"

#Long time counter, counting seconds the heater was operetional. On double tank devices there are  two counters separated by ";" for both heaters. 
#There is also pwc_u, it can be reset from UI and holds the last reset timestamp
ATTR_LONG_COUNTER = "pwc_t"

#RSSI
ATTR_RSSI = "wdBm"


"""
some devices have additional parameters:
"extr" - Base64 and url encoded Json, typically containing custom name if renaimed from UI in the CLoud
"lck" - chield lock. 1- Locked, 0-Unlocked
"cdt" - count down timer untill target is reached
"tmpMX" - maximum showers could be set on the device, depends on the leters of the heater, and horisontal/vertical position
"psn" - Position, vertical/horisontal
"wup" - Uptime in seconds since last bootup

"""