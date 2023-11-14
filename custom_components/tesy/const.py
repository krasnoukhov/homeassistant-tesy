"""Constants for the Tesy integration."""
from homeassistant.const import CONF_IP_ADDRESS

DOMAIN = "tesy"
HTTP_TIMEOUT = 15
UPDATE_INTERVAL = 30

IP_ADDRESS = CONF_IP_ADDRESS

ATTR_API = "api"
ATTR_CURRENT_TEMP = "tmpC"
ATTR_IS_HEATING = "ht"
ATTR_MAC = "MAC"
ATTR_MODE = "mode"
ATTR_POWER = "pwr"
ATTR_SOFTWARE = "wsw"
ATTR_TARGET_TEMP = "tmpT"
