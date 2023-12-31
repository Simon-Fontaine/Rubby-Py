import disnake
from rubby.misc.constants import Constants


def truncate_embed(embed: disnake.Embed):
    embed.title = truncate_text(embed.title, Constants.EMBED_TITLE_LIMIT)

    embed.description = truncate_text(
        embed.description, Constants.EMBED_DESCRIPTION_LIMIT
    )

    if embed.footer and embed.footer.text:
        embed.set_footer(
            text=truncate_text(embed.footer.text, Constants.EMBED_FOOTER_TEXT_LIMIT)
        )

    truncated_fields = [
        (
            truncate_text(field.name, Constants.EMBED_FIELD_NAME_LIMIT),
            truncate_text(field.value, Constants.EMBED_FIELD_VALUE_LIMIT),
            field.inline,
        )
        for field in embed.fields[: Constants.EMBED_FIELD_LIMIT]
    ]
    embed.clear_fields()
    for fields in truncated_fields:
        embed.add_field(name=fields[0], value=fields[1], inline=fields[2])

    return embed


def truncate_buttons(buttons: list[disnake.ui.Button]) -> list[disnake.ui.Button]:
    for button in buttons:
        button.label = truncate_text(button.label, Constants.BUTTON_LABEL_LIMIT)
        button.custom_id = truncate_text(
            button.custom_id, Constants.BUTTON_CUSTOM_ID_LIMIT
        )

    return buttons


def truncate_select_menu(
    select_menu: disnake.ui.StringSelect,
) -> disnake.ui.StringSelect:
    select_menu.placeholder = truncate_text(
        select_menu.placeholder, Constants.SELECT_MENU_PLACEHOLDER_LIMIT
    )

    truncated_options = [
        (
            truncate_text(option.label, Constants.SELECT_MENU_OPTION_LABEL_LIMIT),
            truncate_text(option.value, Constants.SELECT_MENU_OPTION_VALUE_LIMIT),
            option.description,
            option.emoji,
            option.default,
        )
        for option in select_menu.options[: Constants.SELECT_MENU_OPTIONS_LIMIT]
    ]
    select_menu.clear_options()
    for option in truncated_options:
        select_menu.add_option(
            label=option[0],
            value=option[1],
            description=option[2],
            emoji=option[3],
            default=option[4],
        )

    return select_menu


def truncate_text(text: str, limit: int) -> str:
    return text[: limit - 3] + "..." if len(text) > limit else text
