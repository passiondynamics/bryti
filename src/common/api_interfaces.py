from src.common.state_table_interface import StateTableInterface
from src.twitch.interface import TwitchInterface


class APIInterfaces:
    def __init__(
        self,
        state_table_interface: StateTableInterface,
        twitch_interface: TwitchInterface,
    ):
        self.state_table = state_table_interface
        self.twitch = twitch_interface
