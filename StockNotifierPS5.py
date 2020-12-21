#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import callr
import configparser
import time
from time import sleep
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from notifypy import Notify

__author__ = "Olle de Jong"
__copyright__ = "Copyright 2020, Olle de Jong"
__license__ = "MIT"
__maintainer__ = "Olle de Jong"
__email__ = "olledejong@gmail.com"

# = parse config =#
parser = configparser.ConfigParser()
parser.read("config.ini")
edge_driver_path = parser.get("settings", "edge_driver_path")
# ================= #
# SETTING VARIABLES #
# ================= #
in_production = parser.getboolean("developer", "production")
max_ordered_items = parser.getint("settings", "max_ordered_items")
sms_enabled = parser.getboolean("settings", "sms_notify")
do_notify = parser.getboolean("settings", "default_notify")
buy_item_if_in_stock = parser.getboolean("settings", "buy_items")
# =================== #
# GENERAL CREDENTIALS #
# =================== #
phone = parser.get("info", "phone")
personal_email = parser.get("info", "email")
callr_username = parser.get("callr credentials", "username")
callr_password = parser.get("callr credentials", "password")
# ================= #
# WEBSHOP VARIABLES #
# ================= #
bol_pw = parser.get("webshop account info", "bol_pw")
coolblue_pw = parser.get("webshop account info", "coolblue_pw")

# = instantiate api =#
if sms_enabled:
    api = callr.Api(callr_username, callr_password)

# = instantiate driver = #
options = EdgeOptions()
options.use_chromium = True
options.headless = False
# insert your own path to the webdriver here
driver = Edge("path_to_edge_driver", options=options)

# = instantiate toast notifier = #
notification = Notify()

# = locations of probable sales =#
locations = {
    # 'COOLBLUE Airpods Pro': {
    #     'webshop': 'coolblue',
    #     'url': 'https://www.coolblue.nl/product/852042/apple-airpods-pro-met-draadloze-oplaadcase.html',
    #     'inStock': False,
    #     'outOfStockLabel': "Binnenkort leverbaar"},
    'BOL.COM Corsair HS50': {
        'webshop': 'bol',
        'url': 'https://www.bol.com/nl/p/corsair-hs50-pro-stereo-gaming-headset-carbon-zwart-ps5-pc-switch/9200000120229196/?bltgh=qD8SP3Gdn94yx1EYGbVGvA.1_28.29.ProductTitle',
        'inStock': False,
        'outOfStockLabel': "outofstock-buy-block"}

    # 'COOLBLUE Digital': {
    #     'webshop': 'coolblue',
    #     'url': 'https://www.coolblue.nl/product/865867/playstation-5-digital-edition.html',
    #     'inStock': False,
    #     'outOfStockLabel': "Binnenkort leverbaar"},
    # 'BOL.COM Disk': {
    #     'webshop': 'bol',
    #     'url': 'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282/?bltg=itm_event%3Dclick%26itm_id%3D2100003024%26itm_lp%3D1%26itm_type%3Dinstrument%26sc_type%3DPAST%26itm_ttd%3DFLEX_BANNER%26mmt_id%3DX9CvykOtXXDLPxSbVx07kgAABU0%26rpgActionId%3D68577%26rpgInstrumentId%3D2100003024%26pg_nm%3Dmain%26slt_id%3D819%26slt_pos%3DA1%26slt_owner%3DRPG%26sc_algo%3DFSL2%26slt_nm%3DFLEX_BANNER%26slt_ttd%3DFLEX_BANNER%26sc_id%3D18201&promo=main_819_PFSL268577_A1_MHP_1_2100003024&bltgh=g3lM1QRpG0EQTBvN6TdM6w.4.5.Banner',
    #     'inStock': False,
    #     'outOfStockLabel': "outofstock-buy-block"},
    # 'MEDIAMARKT Disk': {
    #     'webshop': 'mediamarkt',
    #     'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-disk-edition-1664768.html',
    #     'inStock': False,
    #     'outOfStockLabel': "Online uitverkocht"},
    # 'COOLBLUE Disk': {
    #     'webshop': 'coolblue',
    #     'url': 'https://www.coolblue.nl/product/865866/playstation-5.html',
    #     'inStock': False,
    #     'outOfStockLabel': "Binnenkort leverbaar"},
    # 'NEDGAME Disk': {
    #     'webshop': 'nedgame',
    #     'url': 'https://www.nedgame.nl/playstation-5/playstation-5--levering-begin-2021-/6036644854/?utm_campaign=CPS&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
    #     'inStock': False,
    #     'outOfStockLabel': "Uitverkocht"},
    # 'MEDIAMARKT Digital': {
    #     'webshop': 'mediamarkt',
    #     'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-digital-edition-1665134.html',
    #     'inStock': False,
    #     'outOfStockLabel': "Online uitverkocht"},
    # 'GAMEMANIA Disk': {
    #     'webshop': 'gamemania',
    #     'url': 'https://www.gamemania.nl/Consoles/playstation-5/144093_playstation-5-disc-edition',
    #     'inStock': False,
    #     'outOfStockLabel': "Niet beschikbaar"},
    # 'INTERTOYS Disk': {
    #     'webshop': 'intertoys',
    #     'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-825gb',
    #     'inStock': False,
    #     'outOfStockLabel': "uitverkocht!"},
    # 'NEDGAME Digital': {
    #     'webshop': 'nedgame',
    #     'url': 'https://www.nedgame.nl/playstation-5/playstation-5-digital-edition--levering-begin-2021-/9647865079/?utm_campaign=CPS&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
    #     'inStock': False,
    #     'outOfStockLabel': "Uitverkocht"},
    # 'INTERTOYS Digital': {
    #     'webshop': 'intertoys',
    #     'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-digital-edition-825gb',
    #     'inStock': False,
    #     'outOfStockLabel': "uitverkocht!"}
}


def main():
    # ====================== #
    # count of ordered items #
    # ====================== #
    ordered_items = 0
    # loop infinitely, so that it can just be run in background
    while True:
        # ==================================================== #
        # loop through all web-shops where potentially in stock #
        # ==================================================== #
        for place, info in locations.items():
            # ========================================== #
            # item not known to be in stock, check again #
            # ========================================== #
            if not info.get('inStock'):
                try:
                    content = requests.get(info.get('url'), timeout=5).content.decode('utf-8')
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                    print("[=== ERROR ===] [=== {} ===]".format(place))
                    continue
                # ======================================== #
                # item in stock, proceed to try and buy it #
                # ======================================== #
                if info.get('outOfStockLabel') not in content:
                    print("[=== OMG, MIGHT BE IN STOCK! ===] [=== {} ===]".format(place))
                    # if enabled, send sms
                    if sms_enabled:
                        try:
                            api.call('sms.send', 'SMS', phone,
                                     "ITEM MIGHT BE IN STOCK AT {}. URL: {}".format(place, info.get('url')), None)
                        except (callr.CallrException, callr.CallrLocalException) as e:
                            print("[=== ERROR ===] [=== SENDING SMS FAILED: ACCOUNT BALANCE MIGHT BE TOO LOW ===] ["
                                  "=== {} ===]".format(e))
                    # === NATIVE OS NOTIFICATION === #
                    if do_notify:
                        notification.title = "Item might be in stock at:".format(place)
                        notification.message = info.get('url')
                        notification.send()
                    # === IF ENABLED, BUY ITEM === #
                    if buy_item_if_in_stock:
                        # TODO add exception handling and only count +=1 if successful
                        delegate_buy_item(info.get('webshop'), info.get('url'))
                        ordered_items += 1

                    # === SET IN-STOCK TO TRUE === #
                    info['inStock'] = True
                # not in stock
                else:
                    print("[=== OUT OF STOCK ===] [=== {} ===]".format(place))
            # ================================== #
            # item is in stock, do the following #
            # ================================== #
            else:
                if ordered_items < max_ordered_items:
                    try:
                        content = requests.get(info.get('url'), timeout=5).content.decode('utf-8')
                    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                        print("[=== ERROR ===] [=== {} ===]".format(place))
                        continue
                    if info.get('outOfStockLabel') in content:
                        print("[=== NEW STOCK SOLD OUT ===] [=== {} ===]".format(place))
                        info['inStock'] = False
                    else:
                        print("[=== STILL IN STOCK! MOVE! ===] [=== {} ===]".format(place))
                # if item already ordered
                else:
                    print("[=== ITEM ALREADY ORDERED ===] [=== {} ===]".format(place))

        # =============================== #
        # wait half a minute and go again #
        # =============================== #
        print("\n Check over. Trying again in 30 seconds..\n")
        time.sleep(30)


def delegate_buy_item(webshop, url):
    driver.get(url)
    # buy item
    if webshop == 'coolblue':
        buy_item_at_coolblue(driver)
    elif webshop == 'bol':
        buy_item_at_bol(driver)
    else:
        print("Auto-buy is not yet implemented for: {}".format(webshop))


def buy_item_at_coolblue(driver):
    driver.find_element_by_name("accept_cookie").click()
    driver.find_element_by_class_name("js-coolbar-navigation-login-link").click()
    driver.implicitly_wait(1)
    driver.find_element_by_id("header_menu_emailaddress").send_keys(str(personal_email))
    driver.find_element_by_id("header_menu_password").send_keys(coolblue_pw)
    driver.find_element_by_xpath(
        "/html/body/header/div/div[4]/ul/li[2]/div/div/div[2]/div/form/div[2]/div[2]/div[2]/button").click()
    driver.find_element_by_class_name("js-add-to-cart-button").click()
    driver.get("https://coolblue.nl/winkelmandje")
    driver.find_elements_by_xpath("//*[contains(text(), 'Ik ga bestellen')]")[1].click()
    driver.find_element_by_xpath("//*[@id='main-content']/div/div/div[11]/div[2]/div/div/div[2]/button").click()
    driver.implicitly_wait(1)
    driver.find_element_by_xpath("//*[@id='main-content']/div[3]/div[3]/button").click()
    driver.find_element_by_xpath("//*[@id='main-content']/div[7]/div[3]/div/div").click()
    driver.find_element_by_xpath(
        "//*[@id='main-content']/div[7]/div[3]/div/div/div/div[2]/div/div[2]/div[2]/button").click()
    if in_production:
        driver.find_element_by_xpath("//*[@id='main-content']/div/div[4]/div/div/div[1]/div[2]/button").click()
    else:
        print("Confirmation of order prevented. Application is not in production, see config.ini")
    driver.implicitly_wait(5)
    driver.close()


def buy_item_at_bol(driver):
    # TODO Change to "Reserveer nu"?
    driver.find_element_by_xpath("//*[@id='modalWindow']/div[2]/div[2]/wsp-consent-modal/div[2]/div/div[1]/button").click()
    driver.find_element(By.LINK_TEXT, 'In winkelwagen').click()
    driver.get('https://www.bol.com/nl/order/basket.html')
    driver.find_element(By.ID, 'continue_ordering_top').click()
    # Action Chain to login
    actions = ActionChains(driver)
    actions.pause(1).send_keys_to_element(driver.find_element(By.ID, 'login_email'), str(personal_email))\
        .send_keys_to_element(driver.find_element(By.ID, 'login_password'), bol_pw)\
        .click(driver.find_element(By.XPATH, '//*[@id="existinguser"]/fieldset/div[3]/input')).perform()
    actions.reset_actions()

    if in_production:
        sleep(2)
        driver.find_element(By.XPATH, '//*[@id="executepayment"]/form/div/button').click()
    else:
        print("Confirmation of order prevented. Application is not in production, see config.ini")


# start of program
if __name__ == "__main__":
    main()
