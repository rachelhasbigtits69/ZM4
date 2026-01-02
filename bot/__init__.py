#!/usr/bin/env python3

# ========= PYTHON 3.12 ASYNCIO FIX (MUST BE FIRST) =========
import asyncio

try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ==========================================================

from asyncio import Lock
from collections import OrderedDict
from faulthandler import enable as faulthandler_enable
from logging import (ERROR, INFO, FileHandler, StreamHandler, basicConfig,
                     error, getLogger, info, warning)
from os import environ, path as ospath, remove, getcwd
from socket import setdefaulttimeout
from subprocess import Popen, run as zrun
from time import sleep, time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aria2p import API as ariaAPI
from aria2p import Client as ariaClient
from dotenv import load_dotenv
from pymongo import MongoClient
from pyrogram import Client as tgClient
from pyrogram import enums
from qbittorrentapi import Client as qbClient
from tzlocal import get_localzone
from uvloop import install

faulthandler_enable()
install()
setdefaulttimeout(600)

botStartTime = time()

basicConfig(
    format='%(levelname)s | From %(name)s -> %(module)s line no: %(lineno)d | %(message)s',
    handlers=[FileHandler('Z_Logs.txt'), StreamHandler()],
    level=INFO
)

LOGGER = getLogger(name)

getLogger("apscheduler").setLevel(ERROR)
getLogger("httpx").setLevel(ERROR)
getLogger("pyrogram").setLevel(ERROR)
getLogger("aria2c").setLevel(INFO)
getLogger("aria2p").setLevel(INFO)
getLogger("qbittorrentapi").setLevel(INFO)
getLogger("requests").setLevel(INFO)
getLogger("urllib3").setLevel(INFO)

load_dotenv('config.env', override=True)

aria2 = ariaAPI(ariaClient(host="http://localhost", port=6800, secret=""))

Interval = []
QbInterval = []
QbTorrents = {}
list_drives_dict = {}
shorteneres_list = []
extra_buttons = {}
GLOBAL_EXTENSION_FILTER = ['.aria2', '!qB']
user_data = {}
aria2_options = {}
qbit_options = {}
queued_dl = {}
queued_up = {}
categories_dict = {}
non_queued_dl = set()
non_queued_up = set()

try:
    if bool(environ.get('_____REMOVE_THIS_LINE_____')):
        error('README is there to be read! Read and try again! Exiting now!')
        exit()
except:
    pass

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
queue_dict_lock = Lock()
qb_listener_lock = Lock()
subprocess_lock = Lock()
status_reply_dict = {}
download_dict = {}
rss_dict = {}
cached_dict = {}

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(':', 1)[0]

DATABASE_URL = environ.get('DATABASE_URL', '')
if DATABASE_URL:
    conn = MongoClient(DATABASE_URL)
    db = conn.z
    if config_dict := db.settings.config.find_one({'_id': bot_id}):
        del config_dict['_id']
        for key, value in config_dict.items():
            environ[key] = str(value)
    conn.close()

OWNER_ID = int(environ.get('OWNER_ID', '0'))
TELEGRAM_API = int(environ.get('TELEGRAM_API', '0'))
TELEGRAM_HASH = environ.get('TELEGRAM_HASH', '')

DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '/usr/src/app/downloads/')
if not DOWNLOAD_DIR.endswith("/"):
    DOWNLOAD_DIR += "/"

if BASE_URL := environ.get('BASE_URL', '').rstrip("/"):
    BASE_URL_PORT = int(environ.get('BASE_URL_PORT', 80))
    Popen(
        f"gunicorn web.wserver:app --bind 0.0.0.0:{BASE_URL_PORT} --worker-class gevent",
        shell=True
    )

zrun(["qbittorrent-nox", "-d", f"--profile={getcwd()}"])

bot = tgClient(
    'bot',
    TELEGRAM_API,
    TELEGRAM_HASH,
    bot_token=BOT_TOKEN,
    workers=1000,
    parse_mode=enums.ParseMode.HTML
).start()

bot_loop = bot.loop
bot_name = bot.me.username
info(f"Starting Bot @{bot_name}...")

scheduler = AsyncIOScheduler(
    timezone=str(get_localzone()),
    event_loop=bot_loop
)
