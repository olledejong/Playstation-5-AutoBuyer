#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import callr
import configparser
import time
import sys
from time import sleep
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.common import exceptions as SE
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from notifypy import Notify

__author__ = "Olle de Jong"
__copyright__ = "Copyright 2020, Olle de Jong"
__license__ = "MIT"
__maintainer__ = "Olle de Jong"
__email__ = "olledejong@gmail.com"

# ================= #
# PARSE CONFIG FILE #
# ================= #
parser = configparser.ConfigParser()
parser.read("config.ini")
# = SETTING VARIABLES =#
in_production = parser.getboolean("developer", "production")
max_ordered_items = parser.getint("settings", "max_ordered_items")
sms_enabled = parser.getboolean("settings", "sms_notify")
do_notify = parser.getboolean("settings", "natively_notify")
buy_item_if_in_stock = parser.getboolean("settings", "buy_item_if_in_stock")
# = GENERAL CREDENTIALS =#
phone = parser.get("info", "phone")
personal_email = parser.get("info", "email")
callr_username = parser.get("callr credentials", "username")
callr_password = parser.get("callr credentials", "password")
# = WEBSHOP VARIABLES =#
bol_pw = parser.get("webshop account info", "bol_pw")
coolblue_pw = parser.get("webshop account info", "coolblue_pw")

# ==================== #
# INITIALIZE CALLR API #
# ==================== #
if sms_enabled:
    api = callr.Api(callr_username, callr_password)

# ================= #
# INITIALIZE DRIVER #
# ================= #
options = EdgeOptions()
options.use_chromium = True
options.headless = False
# CHANGE PATH IN delegate_buy_item

# =================== #
# INITIALIZE NOTIFIER #
# =================== #
notification = Notify()

# =============================== #
# DICTIONARY WITH WEBSHOP DETAILS #
# =============================== #
locations = {
    'COOLBLUE Digital': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/865867/playstation-5-digital-edition.html',
        'inStock': False,
        'outOfStockLabel': "Binnenkort leverbaar"},
    'BOL.COM Disk': {
        'webshop': 'bol',
        'url': 'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282/?bltg=itm_event%3Dclick%26itm_id%3D2100003024%26itm_lp%3D1%26itm_type%3Dinstrument%26sc_type%3DPAST%26itm_ttd%3DFLEX_BANNER%26mmt_id%3DX9CvykOtXXDLPxSbVx07kgAABU0%26rpgActionId%3D68577%26rpgInstrumentId%3D2100003024%26pg_nm%3Dmain%26slt_id%3D819%26slt_pos%3DA1%26slt_owner%3DRPG%26sc_algo%3DFSL2%26slt_nm%3DFLEX_BANNER%26slt_ttd%3DFLEX_BANNER%26sc_id%3D18201&promo=main_819_PFSL268577_A1_MHP_1_2100003024&bltgh=g3lM1QRpG0EQTBvN6TdM6w.4.5.Banner',
        'inStock': False,
        'outOfStockLabel': "outofstock-buy-block"},
    'MEDIAMARKT Disk': {
        'webshop': 'mediamarkt',
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-disk-edition-1664768.html',
        'inStock': False,
        'outOfStockLabel': "Online uitverkocht"},
    'COOLBLUE Disk': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/865866/playstation-5.html',
        'inStock': False,
        'outOfStockLabel': "Binnenkort leverbaar"},
    'NEDGAME Disk': {
        'webshop': 'nedgame',
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5--levering-begin-2021-/6036644854/?utm_campaign=CPS&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
        'inStock': False,
        'outOfStockLabel': "Uitverkocht"},
    'MEDIAMARKT Digital': {
        'webshop': 'mediamarkt',
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-digital-edition-1665134.html',
        'inStock': False,
        'outOfStockLabel': "Online uitverkocht"},
    'GAMEMANIA Disk': {
        'webshop': 'gamemania',
        'url': 'https://www.gamemania.nl/Consoles/playstation-5/144093_playstation-5-disc-edition',
        'inStock': False,
        'outOfStockLabel': "Niet beschikbaar"},
    'INTERTOYS Disk': {
        'webshop': 'intertoys',
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-825gb',
        'inStock': False,
        'outOfStockLabel': "uitverkocht!"},
    'NEDGAME Digital': {
        'webshop': 'nedgame',
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5-digital-edition--levering-begin-2021-/9647865079/?utm_campaign=CPS&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
        'inStock': False,
        'outOfStockLabel': "Uitverkocht"},
    'INTERTOYS Digital': {
        'webshop': 'intertoys',
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-digital-edition-825gb',
        'inStock': False,
        'outOfStockLabel': "uitverkocht!"}
}


def main():
    # ====================== #
    # count of ordered items #
    # ====================== #
    ordered_items = 0
    # loop until desired amount of ordered items is reached
    while ordered_items < max_ordered_items:
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
                        delegate_buy_item(info.get('webshop'), info.get('url'))
                        print("[=== ITEM ORDERED, HOORAY! ===] [=== {} ===]".format(place))
                        ordered_items += 1
                        # if reached max amount of ordered items
                        if not ordered_items < max_ordered_items:
                            print("[=== Desired amount of ordered items reached! ===] [=== Bye! ===]")
                            sys.exit(0)

                    # === SET IN-STOCK TO TRUE === #
                    info['inStock'] = True
                # not in stock
                else:
                    print("[=== OUT OF STOCK ===] [=== {} ===]".format(place))
            # ================================== #
            # item is in stock, do the following #
            # ================================== #
            else:
                try:
                    content = requests.get(info.get('url'), timeout=5).content.decode('utf-8')
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                    print("[=== ERROR ===] [=== {} ===]".format(place))
                    continue
                if info.get('outOfStockLabel') in content:
                    print("[=== NEW STOCK SOLD OUT ===] [=== {} ===]".format(place))
                    info['inStock'] = False
                else:
                    print("[=== STILL IN STOCK! ===] [=== {} ===]".format(place))
                    if buy_item_if_in_stock:
                        delegate_buy_item(info.get('webshop'), info.get('url'))
                        print("[=== ITEM ORDERED, HOORAY! ===] [=== {} ===]".format(place))
                        ordered_items += 1
                        # if reached max amount of ordered items
                        if not ordered_items < max_ordered_items:
                            print("[=== Desired amount of ordered items reached! ===] [=== Bye! ===]")
                            sys.exit(0)

        # =============================== #
        # wait half a minute and go again #
        # =============================== #
        print("\n Check over. Trying again in 30 seconds..\n")
        time.sleep(30)


def delegate_buy_item(webshop, url):
    # FILL YOUR PATH IN HERE
    driver = Edge("your_path_to_msedgedriver.exe", options=options)
    driver.get(url)
    # buy item
    if webshop == 'coolblue':
        buy_item_at_coolblue(driver)
    elif webshop == 'bol':
        buy_item_at_bol(driver)
    else:
        print("Auto-buy is not yet implemented for: {}".format(webshop))


def buy_item_at_coolblue(edge_driver):
    # change to prettier code
    edge_driver.find_element_by_name("accept_cookie").click()
    edge_driver.find_element_by_class_name("js-coolbar-navigation-login-link").click()

    actions = ActionChains(edge_driver)
    actions.pause(1).send_keys_to_element(edge_driver.find_element(By.ID, 'header_menu_emailaddress'), str(personal_email)) \
        .send_keys_to_element(edge_driver.find_element(By.ID, 'header_menu_password'), coolblue_pw) \
        .click(edge_driver.find_element(By.XPATH, '/html/body/header/div/div[4]/ul/li[2]/div/div/div[2]/div/form/div['
                                             '2]/div[2]/div[2]/button')).perform()
    actions.reset_actions()

    edge_driver.find_element_by_class_name("js-add-to-cart-button").click()
    edge_driver.get("https://coolblue.nl/winkelmandje")
    edge_driver.find_elements_by_xpath("//*[contains(text(), 'Ik ga bestellen')]")[1].click()
    edge_driver.find_element_by_xpath("//*[@id='main-content']/div/div/div[11]/div[2]/div/div/div[2]/button").click()
    edge_driver.implicitly_wait(1)
    edge_driver.find_element_by_xpath("//*[@id='main-content']/div[3]/div[3]/button").click()
    edge_driver.find_element_by_xpath("//*[@id='main-content']/div[7]/div[3]/div/div").click()
    edge_driver.find_element_by_xpath(
        "//*[@id='main-content']/div[7]/div[3]/div/div/div/div[2]/div/div[2]/div[2]/button").click()
    if in_production:
        edge_driver.find_element_by_xpath("//*[@id='main-content']/div/div[4]/div/div/div[1]/div[2]/button").click()
    else:
        print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
    sleep(2)
    edge_driver.close()


def buy_item_at_bol(edge_driver):
    # ===================== #
    # add to cart and login #
    # ===================== #
    edge_driver.find_element_by_xpath(
        "//*[@id='modalWindow']/div[2]/div[2]/wsp-consent-modal/div[2]/div/div[1]/button").click()
    # check whether button is preorder or regular order button
    try:
        pre_order = edge_driver.find_element(By.LINK_TEXT, "//*[contains(text(),'Reserveer nu')]")
        pre_order.click()
    except SE.NoSuchElementException as e:
        edge_driver.find_element(By.LINK_TEXT, 'In winkelwagen').click()
    edge_driver.get('https://www.bol.com/nl/order/basket.html')
    sleep(1)
    edge_driver.find_element(By.ID, 'continue_ordering_bottom').click()
    # Action Chain to login
    actions = ActionChains(edge_driver)
    actions.pause(1).send_keys_to_element(edge_driver.find_element(By.ID, 'login_email'), str(personal_email))\
        .send_keys_to_element(edge_driver.find_element(By.ID, 'login_password'), bol_pw)\
        .click(edge_driver.find_element(By.XPATH, '//*[@id="existinguser"]/fieldset/div[3]/input')).perform()
    actions.reset_actions()

    # ===================================== #
    # if other items in basket, remove them #
    # ===================================== #
    current_url = edge_driver.current_url
    if "basket.html" in current_url:
        # there is more than the auto-buy item in cart
        only_one_item = False
        while not only_one_item:
            basket = edge_driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')
            for item in basket:
                try:
                    title = item.find_element(By.CLASS_NAME, 'product-details__title').get_attribute('title')
                except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                    continue
                if "HS70" not in title:
                    remove_url = item.find_element(By.ID, 'tst_remove_from_basket').get_attribute('href')
                    edge_driver.get(remove_url)
                    if len(edge_driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')) == 2:
                        only_one_item = True
        # done, continue to checkout
        else:
            sleep(5)
            edge_driver.find_element(By.ID, 'continue_ordering_bottom').click()

    # ================================================== #
    # if app in production; complete order with afterpay #
    # ================================================== #
    if in_production:
        sleep(2)
        try:
            edge_driver.find_element(By.XPATH, '//*[@id="paymentsuggestions"]/div/div[2]/div/div/ul/div[1]/div').click()
        except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
            print("Afterpay not available. Aborting..")
        # confirm
        edge_driver.find_element(By.XPATH, '//*[@id="executepayment"]/form/div/button').click()
    else:
        print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")

    # wait for two seconds and close the driver
    sleep(2)
    edge_driver.close()


# start of program
if __name__ == "__main__":
    main()
