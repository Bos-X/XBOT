import html
import re
from typing import List
import time

import requests
from telegram import Bot, Update, MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import mention_html

from xbotg import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, DEV_USERS, SARDEGNA_USERS, WHITELIST_USERS
from xbotg.__main__ import STATS, USER_INFO, TOKEN
from xbotg.modules.disable import DisableAbleCommandHandler
from xbotg.modules.helper_funcs.chat_status import user_admin, sudo_plus
from xbotg.modules.helper_funcs.extraction import extract_user
import xbotg.modules.sql.users_sql as sql

MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {dispatcher.bot.first_name} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""

@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:
        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"The original sender, {html.escape(user2.first_name)},"
                f" has an ID of <code>{user2.id}</code>.\n"
                f"The forwarder, {html.escape(user1.first_name)},"
                f" has an ID of <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(f"Your id is <code>{chat.id}</code>.",
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(f"This group's id is <code>{chat.id}</code>.",
                           parse_mode=ParseMode.HTML)


@run_async
def gifid(_bot: Bot, update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not message.parse_entities(
                [MessageEntity.TEXT_MENTION]))):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = (f"<b>Characteristics:</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"First Name: {html.escape(user.first_name)}")

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"

    num_chats = sql.get_user_num_chats(user.id)
    text += f"\nChat count: <code>{num_chats}</code>"

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == 'administrator':
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}")
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result['custom_title']
                text += f"\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass


    if user.id == OWNER_ID:
            text += f'\nThe Nation level of this person is <a href="https://t.me/XBOTGBOT?start=nations">God</a>'
    elif user.id in DEV_USERS:
            text += f'\nThe Nation level of this person is <a href="https://t.me/XBOTGBOT?start=nations">Hero Union</a>'
    elif user.id in SUDO_USERS:
            text += f'\nThe Nation level of this person is <a href="https://t.me/XBOTGBOT?start=nations">Royal</a>'
    elif user.id in SUPPORT_USERS:
            text += f'\nThe Nation level of this person is <a href="https://t.me/XBOTGBOT?start=nations">Sakura</a>'
    elif user.id in SARDEGNA_USERS:
            text += f'\nThe Nation level of this person is <a href="https://t.me/XBOTGBOT?start=nations">Sardegna</a>'
    elif user.id in WHITELIST_USERS:
            text += f'\nThe Nation level of this person is <a href="https://t.me/XBOTGBOT?start=nations">Neptunia</a>'


    text += "\n"
    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue

        try:
            mod_info = mod.__user_info__(user.id)
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id)
        if mod_info:
            text += "\n" + mod_info

    update.effective_message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True)


@run_async
def ping(bot: Bot, update: Update):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    message.edit_text("*Pong!!!*🏓\n`{}ms`".format(ping_time),
                      parse_mode=ParseMode.MARKDOWN)


@run_async
@user_admin
def echo(_bot: Bot, update: Update):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)

    message.delete()


@run_async
def markdown_help(_bot: Bot, update: Update):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!")
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")


@run_async
@sudo_plus
def stats(bot: Bot, update: Update):
    stats = "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r'(\d+)', r'<code>\1</code>', stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


__help__ = """
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /gifid: reply to a gif to me to tell you its file ID.
 - /info: get information about a user.
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats.
 - /karma - Coming soon
"""

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
PING_HANDLER = DisableAbleCommandHandler("ping", ping)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)
ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.group)
MD_HELP_HANDLER = CommandHandler(
    "markdownhelp",
    markdown_help,
    filters=Filters.private)
STATS_HANDLER = CommandHandler("stats", stats)

dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(PING_HANDLER)

__mod_name__ = "Misc"
__command_list__ = ["id", "info", "echo"]
__handlers__ = [
    ID_HANDLER,
    GIFID_HANDLER,
    INFO_HANDLER,
    ECHO_HANDLER,
    MD_HELP_HANDLER,
    STATS_HANDLER
]
