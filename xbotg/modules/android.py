# UserindoBot
# Copyright (C) 2020  UserindoBot Team, <https://github.com/MoveAngel/UserIndoBot.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time

from bs4 import BeautifulSoup
from requests import get
from telegram import ParseMode, Update, Bot, MessageEntity
from telegram.error import BadRequest
from telegram.ext import run_async

from xbotg import dispatcher
from xbotg.modules.disable import DisableAbleCommandHandler
from xbotg.modules.helper_funcs.alternate import typing_action

GITHUB = "https://github.com"
DEVICES_DATA = "https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json"


@run_async
def magisk(_bot: Bot, update: Update):
    url = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"
    releases = ""
    for type, branch in {
        "Stable": ["master/stable", "master"],
        "Beta": ["master/beta", "master"],
        "Canary": ["canary/canary", "canary"],
    }.items():
        data = get(url + branch[0] + ".json").json()
        if str(type) == "Canary":
            data["magisk"]["link"] = "https://github.com/topjohnwu/magisk_files/raw/canary/" + data["magisk"]["link"]
            data["app"]["link"] = "https://github.com/topjohnwu/magisk_files/raw/canary/" + data["app"]["link"]
            data["uninstaller"]["link"] = "https://github.com/topjohnwu/magisk_files/raw/canary/" + data["uninstaller"]["link"]
        releases += (
            f"*{type}*: \n"
            f"• [Changelog](https://github.com/topjohnwu/magisk_files/blob/{branch[1]}/notes.md)\n"
            f'• Zip - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["magisk"]["link"]}) \n'
            f'• App - [{data["app"]["version"]}-{data["app"]["versionCode"]}]({data["app"]["link"]}) \n'
            f'• Uninstaller - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["uninstaller"]["link"]})\n\n'
        )
        
    del_msg = update.message.reply_text(
        "*Latest Magisk Releases:*\n{}".format(releases),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
    time.sleep(300)
    try:
        del_msg.delete()
        update.effective_message.delete()
    except BadRequest as err:
        if (err.message == "Message to delete not found") or (
            err.message == "Message can't be deleted"
        ):
            return


@run_async
def device(_bot: Bot, update: Update, args):
    if len(args) == 0:
        reply = "No codename provided, write a codename for fetching informations."
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    device = " ".join(args)
    db = get(DEVICES_DATA).json()
    newdevice = device.strip("lte") if device.startswith("beyond") else device
    try:
        reply = f"Search results for {device}:\n\n"
        brand = db[newdevice][0]["brand"]
        name = db[newdevice][0]["name"]
        model = db[newdevice][0]["model"]
        codename = newdevice
        reply += (
            f"<b>{brand} {name}</b>\n"
            f"Model: <code>{model}</code>\n"
            f"Codename: <code>{codename}</code>\n\n"
        )
    except KeyError:
        reply = f"Couldn't find info about {device}!\n"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    update.message.reply_text(
        "{}".format(reply), parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


@run_async
def twrp(_bot: Bot, update: Update, args):
    if len(args) == 0:
        reply = "No codename provided, write a codename for fetching informations."
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return

    device = " ".join(args)
    url = get(f"https://eu.dl.twrp.me/{device}/")
    if url.status_code == 404:
        reply = f"Couldn't find twrp downloads for {device}!\n"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    else:
        reply = f"*Latest Official TWRP for {device}*\n"
        db = get(DEVICES_DATA).json()
        newdevice = device.strip("lte") if device.startswith("beyond") else device
        try:
            brand = db[newdevice][0]["brand"]
            name = db[newdevice][0]["name"]
            reply += f"*{brand} - {name}*\n"
        except KeyError:
            pass
        page = BeautifulSoup(url.content, "lxml")
        date = page.find("em").text.strip()
        reply += f"*Updated:* {date}\n"
        trs = page.find("table").find_all("tr")
        row = 2 if trs[0].find("a").text.endswith("tar") else 1
        for i in range(row):
            download = trs[i].find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = trs[i].find("span", {"class": "filesize"}).text
            reply += f"[{dl_file}]({dl_link}) - {size}\n"

        update.message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


@run_async
def los(_bot: Bot, update: Update, args) -> str:
    message = update.effective_message
    update.effective_chat
    try:
        device = args[0]
    except Exception:
        device = ""

    if device == "":
        reply_text = f"*Please Type Your Device Codename*\nExample : `/los lavender`"
        message.reply_text(
            reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
        return

    fetch = get(f"https://download.lineageos.org/api/v1/{device}/nightly/*")
    if fetch.status_code == 200 and len(fetch.json()["response"]) != 0:
        usr = fetch.json()
        data = len(usr["response"]) - 1  # the latest rom are below
        response = usr["response"][data]
        filename = response["filename"]
        url = response["url"]
        buildsize_a = response["size"]
        buildsize_b = xsize(int(buildsize_a))
        version = response["version"]

        reply_text = f"*Download :* [{filename}]({url})\n"
        reply_text += f"*Build Size :* `{buildsize_b}`\n"
        reply_text += f"*Version :* `{version}`\n"

        keyboard = [
            [InlineKeyboardButton(text="Click Here To Downloads", url=f"{url}")]
        ]
        message.reply_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    else:
        message.reply_text(
            "`Couldn't find any results matching your query.`",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        
        
__help__ = """
Get Latest magisk relese, Twrp for your device or info about some device using its codename, Directly from Bot!

*Android related commands:*

 × /magisk - Gets the latest magisk release for Stable/Beta/Canary.
 × /device <codename> - Gets android device basic info from its codename.
 × /twrp <codename> -  Gets latest twrp for the android device using the codename.
"""

__mod_name__ = "Android"

MAGISK_HANDLER = DisableAbleCommandHandler("magisk", magisk)
DEVICE_HANDLER = DisableAbleCommandHandler("device", device, pass_args=True)
TWRP_HANDLER = DisableAbleCommandHandler("twrp", twrp, pass_args=True)
LOS_HANDLER = DisableAbleCommandHandler("los", los, pass_args=True)

dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(DEVICE_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
dispatcher.add_handler(LOS_HANDLER)
