#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import callr
import configparser
import time
import sys
import platform
import datetime
from selenium.common import exceptions as SE
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW
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
auto_buy = parser.getboolean("settings", "auto_buy")
# = INFO =#
phone = parser.get("info", "phone")
personal_email = parser.get("info", "email")
# = AUTO-BUY PASSWORDS =#
paypal_pw = parser.get("auto-buy passwords", "paypal")
bol_pw = parser.get("auto-buy passwords", "bol")
coolblue_pw = parser.get("auto-buy passwords", "coolblue")
mediamarkt_pw = parser.get("auto-buy passwords", "mediamarkt")

# ==================== #
# INITIALIZE CALLR API #
# ==================== #
if sms_enabled:
    callr_username = parser.get("callr credentials", "username")
    callr_password = parser.get("callr credentials", "password")
    api = callr.Api(callr_username, callr_password)

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
    """
    Function that loops until the 'desired amount of items bought' is reached.

    While that amount is not reached, the function checks whether the item is
    in stock for every webshop in the locations dictionary. Once an item is in
    stock, it will proceed to buy this item by calling the `delegate_purchase`
    function. This function takes the name of the webshop and the url of the
    item as its arguments.

    Between every check, there is a wait of 30 seconds.
    """
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
                            print("[=== ERROR ===] [=== SENDING SMS FAILED ===] [ CHECK ACCOUNT BALANCE AND VALIDITY OF CALLR CREDENTIALS ===]")
                    # === NATIVE OS NOTIFICATION === #
                    if do_notify:
                        notification.title = "Item might be in stock at:".format(place)
                        notification.message = info.get('url')
                        notification.send()
                    # === IF ENABLED, BUY ITEM === #
                    if auto_buy:
                        if delegate_purchase(info.get('webshop'), info.get('url')):
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
                    if auto_buy:
                        if delegate_purchase(info.get('webshop'), info.get('url')):
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


def initialize_webdriver(url):
    if platform.system() == "Windows" or platform.system() == "Darwin":
        from selenium.webdriver import Chrome, ChromeOptions
        options = ChromeOptions()
        options.use_chromium = True
        options.headless = False
        driver = Chrome("paste_driver_path_here", options=options)
    else:
        print("Only Windows and MacOS are supported (for now). Terminating.")
        sys.exit(0)
    driver.get(url)
    return driver


def delegate_purchase(webshop, url):
    """
    Function that delegates the automatically ordering of items

    First, the driver is instantiated. After that, based on the webshop its name
    a function is called that executes the ordering sequence for that specific
    webshop. That is, if it is implemented / possible for that webshop.
    """
    if webshop == 'coolblue':
        return buy_item_at_coolblue(initialize_webdriver(url))
    elif webshop == 'bol':
        return buy_item_at_bol(initialize_webdriver(url), url)
    elif webshop == 'mediamarkt':
        return buy_item_at_mediamarkt(initialize_webdriver(url))
    else:
        print("Auto-buy is not yet implemented for: {}".format(webshop))
        return False


def buy_item_at_coolblue(driver):
    """
    Function that will buy the item from the COOLBLUE webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_name("accept_cookie").click()
        driver.find_element_by_class_name("js-coolbar-navigation-login-link").click()
        # LOGIN
        ActionChains(driver).pause(1)\
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_emailaddress'), str(personal_email)) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_password'), coolblue_pw) \
            .click(driver.find_element(By.XPATH, '/html/body/header/div/div[4]/ul/li[2]/div/div/div[2]/div/form/div['
                                                 '2]/div[2]/div[2]/button'))\
            .perform()
        # ADD TO CART
        WDW(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-add-to-cart-button'))).click()
        # GO TO BASKET
        WDW(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'modal-box__container')))
        driver.get("https://www.coolblue.nl/winkelmandje")
        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        WDW(driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-shopping-cart-item')))
        if len(driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')) != 1:
            one_item = False
            while not one_item:
                basket = driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'shopping-cart-item__remove-button').get_attribute('title')
                        remove_href = item.find_element(By.CLASS_NAME, 'shopping-cart-item__remove-button').get_attribute('href')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    print(title)
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        driver.get(remove_href)
                        if len(driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')) == 1:
                            one_item = True

        WDW(driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-shopping-cart-item')))
        driver.find_element(By.CLASS_NAME, "js-shopping-cart-item-quantity-input").clear()
        driver.find_element(By.CLASS_NAME, "js-shopping-cart-item-quantity-input").send_keys('1')
        # ORDER
        WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[@id='shoppingcart_form']/div/div[4]/div[1]/div[2]/div[1]/div[2]/button"))).click()
        WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div/div/div[11]/div[2]/div/div/div[2]/button"))).click()
        WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[3]/div[3]/button"))).click()
        WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[7]/div[3]/div/div"))).click()
        WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[7]/div[3]/div/div/div/div[2]/div/div[2]/div[2]/button"))).click()
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div/div[4]/div/div/div[1]/div[2]/button"))).click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
        print("Something went wrong while trying to order at COOLBLUE. Stack:\n{}".format(e))
        driver.close()
        driver.quit()
        return False


def buy_item_at_bol(driver, url):
    """
    Function that will buy the item from the BOL.COM webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    :param url:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_xpath(
            "//*[@id='modalWindow']/div[2]/div[2]/wsp-consent-modal/div[2]/div/div[1]/button").click()
        # LOGIN
        driver.get('https://www.bol.com/nl/rnwy/account/overzicht')
        actions = ActionChains(driver)
        actions.pause(1).send_keys_to_element(driver.find_element(By.ID, 'login_email'), str(personal_email))\
            .send_keys_to_element(driver.find_element(By.ID, 'login_password'), bol_pw)\
            .click(driver.find_element(By.XPATH, '//*[@id="existinguser"]/fieldset/div[3]/input')).perform()
        actions.reset_actions()
        driver.get(url)
        # LOGIC FOR REGULAR ORDER / PREORDER
        try:
            driver.find_element(By.LINK_TEXT, 'Reserveer nu').click()
        except SE.NoSuchElementException as e:
            driver.find_element(By.LINK_TEXT, 'In winkelwagen').click()
        driver.get('https://www.bol.com/nl/order/basket.html')
        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        if len(driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')) != 2:
            # there is more than the auto-buy item in cart
            only_one_item = False
            while not only_one_item:
                basket = driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'product-details__title').get_attribute('title')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        remove_url = item.find_element(By.ID, 'tst_remove_from_basket').get_attribute('href')
                        driver.get(remove_url)
                        if len(driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')) == 2:
                            only_one_item = True
        # PROCEED
        WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'continue_ordering_bottom'))).click()
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            try:
                WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="paymentsuggestions"]/div/div[2]/div/div/ul/div[1]/div'))).click()
            except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                print("Afterpay not available. Aborting.")
            # confirm
            driver.find_element(By.XPATH, '//*[@id="executepayment"]/form/div/button').click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
        print("Something went wrong while trying to order at BOL.COM. Stack:\n{}".format(e))
        driver.close()
        driver.quit()
        return False


def buy_item_at_mediamarkt(driver):
    try:
        # ACCEPT COOKIES
        WDW(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'gdpr-cookie-layer__btn--submit--all'))).click()
        # LOGIN
        driver.execute_script("document.getElementById('pdp-add-to-cart').click()")
        WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'basket-flyout-cart'))).click()
        WDW(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'cobutton-next'))).click()
        WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'login-email'))).send_keys(personal_email)
        WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'loginForm-password'))).send_keys(mediamarkt_pw)
        WDW(driver, 15).until(EC.presence_of_element_located((By.NAME, 'loginForm'))).find_element(By.CLASS_NAME, 'cobutton-next').click()

        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        basket = WDW(driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cart-product-table')))
        length_basket = len(basket)
        if length_basket > 1:
            print(len(basket))
            while length_basket > 1:
                basket = driver.find_elements(By.CLASS_NAME, 'cart-product-table')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'cproduct-heading').get_attribute('innerHTML')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        try:
                            options = item.find_element_by_class_name('js-cartitem-qty')
                        except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                            continue
                        for option in options.find_elements_by_tag_name('option'):
                            if option.text == 'Verwijder':
                                option.click()
                            length_basket -= 1

        # PROCEED TO PAYMENT
        delivery_form = WDW(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'deliveryForm')))
        delivery_form.find_element(By.CLASS_NAME, 'cobutton-next').click()
        # PAYPAL
        WDW(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'paypal__xpay'))).click()
        driver.execute_script("document.getElementsByClassName('cobutton-next')[1].click()")
        WDW(driver, 15).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/form/checkout-footer/div/div[1]/div/div[2]/button'))).click()
        email_input = WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'email')))
        email_input.clear()
        email_input.send_keys(personal_email)
        WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(paypal_pw)
        WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'btnLogin'))).click()
        if in_production:
            WDW(driver, 15).until(EC.presence_of_element_located((By.ID, 'confirmButtonTop'))).click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
        print("Something went wrong while trying to order at Mediamarkt. Stack:\n{}".format(e))
        driver.close()
        driver.quit()
        return False


# start of program
if __name__ == "__main__":
    main()
