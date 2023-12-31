from abc import ABC
from typing import Final


class Constants(ABC):
    # Embed Limits
    EMBED_TITLE_LIMIT: Final[int] = 256
    EMBED_DESCRIPTION_LIMIT: Final[int] = 4_096
    EMBED_FIELD_LIMIT: Final[int] = 25
    EMBED_FIELD_NAME_LIMIT: Final[int] = 256
    EMBED_FIELD_VALUE_LIMIT: Final[int] = 1_024
    EMBED_FOOTER_TEXT_LIMIT: Final[int] = 2_048
    EMBED_AUTHOR_NAME_LIMIT: Final[int] = 256
    # Select Menu Limits
    SELECT_MENU_OPTIONS_LIMIT: Final[int] = 25
    SELECT_MENU_OPTION_LABEL_LIMIT: Final[int] = 100
    SELECT_MENU_OPTION_VALUE_LIMIT: Final[int] = 100
    SELECT_MENU_CUSTOM_ID_LIMIT: Final[int] = 100
    SELECT_MENU_PLACEHOLDER_LIMIT: Final[int] = 100
    # Button Limits
    BUTTON_LABEL_LIMIT: Final[int] = 80
    BUTTON_CUSTOM_ID_LIMIT: Final[int] = 100
