#!/usr/bin/env python

import logging
from PIL import Image
import numpy as np
import scipy.linalg as la
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

help_str = 'Send me your location and I will show it on the map. Also you can type your ' \
           'coordinates in decimal degrees copied from Google Maps. Example: 60.21662, 29.75197\n\nTo see the map ' \
           'without your location use /map. '


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi!')
    update.message.reply_text(help_str)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(help_str)


def map_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_photo(open('map.jpg', 'rb'))


def reply_to_text(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    message = message.replace(',', ' ').split()
    x, y = 0.0, 0.0
    try:
        assert len(message) == 2
        y = float(message[0])
        x = float(message[1])
    except (ValueError, AssertionError):
        update.message.reply_text(help_str)
        return
    reply(update, y, x)


def reply_to_loc(update: Update, context: CallbackContext) -> None:
    loc = update.message.location
    reply(update, loc['latitude'], loc['longitude'])


def reply(update, y, x) -> None:
    point = where_on_map(y, x)
    if 0 < point[0] < 1 and 0 < point[1] < 1:
        add_marker(point)
        update.message.reply_photo(open('out.png', 'rb'))
    else:
        update.message.reply_text('Coordinates you sent are outside of the map.')


def where_on_map(y, x):
    map_corner_up_left = np.array([60.227471, 29.726933]).reshape(-1, 1)
    map_corner_up_right = np.array([60.222312, 29.784189]).reshape(-1, 1)
    map_corner_down_left = np.array([60.208120, 29.719854]).reshape(-1, 1)
    map_corner_down_right = np.array([60.203202, 29.776830]).reshape(-1, 1)

    matrix = la.inv(np.block([map_corner_down_left - map_corner_up_left, map_corner_up_right - map_corner_up_left]))

    coord = np.array([y, x]).reshape(-1, 1)
    point = matrix @ (coord - map_corner_up_left)
    return list(point.reshape(-1))


def add_marker(point):
    marker_size = 100
    map_img = Image.open('map.jpg', 'r')
    marker = Image.open('marker.png', 'r')
    marker.thumbnail((marker_size, marker_size), Image.ANTIALIAS)
    y = int(point[0] * map_img.size[1]) - marker_size + marker_size // 5
    x = int(point[1] * map_img.size[0]) - marker_size // 2
    map_img.paste(marker, (x, y), marker)
    map_img.save('out.png')


def main():
    updater = Updater("")  # paste token

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("map", map_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_to_text))
    dispatcher.add_handler(MessageHandler(Filters.location, reply_to_loc))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
