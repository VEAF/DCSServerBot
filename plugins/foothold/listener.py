from typing import TYPE_CHECKING

from core import EventListener

if TYPE_CHECKING:
    pass


class FootholdEventListener(EventListener["Foothold"]):
    """Event listener for Foothold plugin.

    Currently minimal as Foothold uses file-based polling rather than DCS events.
    Can be extended in the future to handle real-time DCS events.
    """

    pass
