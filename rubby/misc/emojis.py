from abc import ABC
from typing import Final


class Emojis(ABC):
    BOT: Final[object] = {
        "verified_bot": "<:verified_bot_left:1182697837805453426><:verified_bot_middle:1182698866865348649><:verified_bot_right:1182697840028430427>",
        "bot": "<:bot_left:1182697833288175616><:bot_right:1182697834743599174>",
    }

    BADGES: Final[object] = {
        "active_developer": "<:active_developer:1182688624324649020>",
        "bug_hunter": "<:bug_hunter:1182688625822015499>",
        "bug_hunter_level_2": "<:bug_hunter_level_2:1182688627961102437>",
        "discord_certified_moderator": "<:discord_certified_moderator:1182688629227790347>",
        "early_supporter": "<:early_supporter:1182688631681462362>",
        "early_verified_bot_developer": "<:early_verified_bot_developer:1182688633073971211>",
        "hypesquad": "<:hypesquad:1182688634516803724>",
        "hypesquad_balance": "<:hypesquad_balance:1182688636165165168>",
        "hypesquad_bravery": "<:hypesquad_bravery:1182688638040031252>",
        "hypesquad_brilliance": "<:hypesquad_brilliance:1182688640581763162>",
        "partner": "<:partner:1182688641898778765>",
        "system": "<:system:1182688647217152140>",
        "staff": "<:staff:1182688761033793627>",
        "verified_bot_developer": "<:verified_bot_developer:1182688731040317520>",
    }

    SYMBOLS: Final[object] = {
        "exclamation_mark_red": "<:exclamation_mark_red:1191025410071343234>",
        "check_mark_green": "<:check_mark_green:1191025408523632660>",
    }
