#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import callr
import configparser
import time
from win10toast import ToastNotifier
from selenium import webdriver
import webbrowser

__author__ = "Olle de Jong"
__copyright__ = "Copyright 2020, Olle de Jong"

__license__ = "MIT"
__maintainer__ = "Olle de Jong"
__email__ = "olledejong@gmail.com"

# = parse config =#
parser = configparser.ConfigParser()
parser.read("config.ini")
phone = parser["info"]["phone"]
username = parser["callr credentials"]["username"]
password = parser["callr credentials"]["password"]
smsEnabled = parser["info"]["sms notify enabled"]

# = instantiate api =#
if smsEnabled == "TRUE":
    api = callr.Api(username, password)

# = instantiate toast notifier =#
toaster = ToastNotifier()

# = locations of probable sales =#
locations = {
    'COOLBLUE Digital': {
        'url': 'https://www.coolblue.nl/product/865867/playstation-5-digital-edition.html',
        'inStock': False,
        'outOfStockLabel': "Binnenkort leverbaar"},
    'BOL.COM Disk': {
        'url': 'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282/?bltg=itm_event%3Dclick%26itm_id%3D2100003024%26itm_lp%3D1%26itm_type%3Dinstrument%26sc_type%3DPAST%26itm_ttd%3DFLEX_BANNER%26mmt_id%3DX9CvykOtXXDLPxSbVx07kgAABU0%26rpgActionId%3D68577%26rpgInstrumentId%3D2100003024%26pg_nm%3Dmain%26slt_id%3D819%26slt_pos%3DA1%26slt_owner%3DRPG%26sc_algo%3DFSL2%26slt_nm%3DFLEX_BANNER%26slt_ttd%3DFLEX_BANNER%26sc_id%3D18201&promo=main_819_PFSL268577_A1_MHP_1_2100003024&bltgh=g3lM1QRpG0EQTBvN6TdM6w.4.5.Banner',
        'inStock': False,
        'outOfStockLabel': "outofstock-buy-block"},
    'MEDIAMARKT Disk': {
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-disk-edition-1664768.html',
        'inStock': False,
        'outOfStockLabel': "Online uitverkocht"},
    'COOLBLUE Disk': {
        'url': 'https://www.coolblue.nl/product/865866/playstation-5.html',
        'inStock': False,
        'outOfStockLabel': "Binnenkort leverbaar"},
    'NEDGAME Disk': {
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5--levering-begin-2021-/6036644854/?utm_campaign=CPS&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
        'inStock': False,
        'outOfStockLabel': "Uitverkocht"},
    'MEDIAMARKT Digital': {
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-digital-edition-1665134.html',
        'inStock': False,
        'outOfStockLabel': "Online uitverkocht"},
    'GAMEMANIA Disk': {
        'url': 'https://www.gamemania.nl/Consoles/playstation-5/144093_playstation-5-disc-edition',
        'inStock': False,
        'outOfStockLabel': "Niet beschikbaar"},
    'INTERTOYS Disk': {
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-825gb',
        'inStock': False,
        'outOfStockLabel': "uitverkocht!"},
    'NEDGAME Digital': {
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5-digital-edition--levering-begin-2021-/9647865079/?utm_campaign=CPS&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
        'inStock': False,
        'outOfStockLabel': "Uitverkocht"},
    'INTERTOYS Digital': {
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-digital-edition-825gb',
        'inStock': False,
        'outOfStockLabel': "uitverkocht!"}
}


def main():
    # loop infinitely, so that it can just be run in background
    while True:
        # loop through all sale locations
        for place, info in locations.items():
            # not known to be in stock, check if it is
            if not info.get('inStock'):
                try:
                    content = requests.get(info.get('url'), timeout=5).content.decode('utf-8')
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                    print("[=== ERROR ===] [=== {} ===]".format(place))
                    continue
                # in stock, notify via SMS
                if info.get('outOfStockLabel') not in content:
                    print("[=== OMG, MIGHT BE IN STOCK! ===] [=== {} ===]".format(place))
                    # if enabled, send sms
                    if smsEnabled == "TRUE":
                        try:
                            api.call('sms.send', 'SMS', phone,
                                     "ITEM MIGHT BE IN STOCK AT {}. URL: {}".format(place, info.get('url')), None)
                        except (callr.CallrException, callr.CallrLocalException) as e:
                            print("[=== ERROR ===] [=== SENDING SMS FAILED: ACCOUNT BALANCE MIGHT BE TOO LOW ===] ["
                                  "=== {} ===]".format(e))
                    toaster.show_toast("IN STOCK AT [{}]".format(place))
                    # open webbrowser with in stock link
                    webbrowser.open(info.get('url'))  # Go to example.com
                    info['inStock'] = True
                # not in stock
                else:
                    print("[=== OUT OF STOCK ===] [=== {} ===]".format(place))
            # in stock, check if it still is
            else:
                # not in stock anymore
                if info.get('outOfStockLabel') in requests.get(info.get('url')).content.decode('utf-8'):
                    print("[=== NEW STOCK SOLD OUT ===] [=== {} ===]".format(place))
                    if smsEnabled == "TRUE":
                        try:
                            api.call('sms.send', 'SMS', phone,
                                     "NEW STOCK AT {} SOLD OUT. URL: {}".format(place, info.get('url')),
                                     None)
                        except (callr.CallrException, callr.CallrLocalException) as e:
                            print("[=== ERROR ===] [=== SENDING SMS FAILED: ACCOUNT BALANCE MIGHT BE TOO LOW ===] ["
                                  "=== {} ===]".format(e))
                    info['inStock'] = False
                else:
                    print("[=== STILL IN STOCK! MOVE! ===] [=== {} ===]".format(place))

        # wait 15 seconds, and check again by re-running function
        print("\n Check over. Trying again in 30 seconds..\n")
        time.sleep(30)


# start of program
if __name__ == "__main__":
    main()
