#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import callr
import configparser
import time
import sys
import re
import platform
from os import system, name
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
in_production = parser.getboolean("developer", "production")

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
    # get settings
    settings, api = configure_settings()
    print("\nDone, program is starting now!\n")

    ordered_items = 0
    # loop until desired amount of ordered items is reached
    while ordered_items < settings.get("max_ordered_items"):
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
                    if settings.get("sms_notify") and not settings.get("auto_buy"):
                        try:
                            api.call('sms.send', 'SMS', settings.get("phone"),
                                     "ITEM MIGHT BE IN STOCK AT {}. URL: {}".format(place, info.get('url')), None)
                        except (callr.CallrException, callr.CallrLocalException) as e:
                            print("[=== ERROR ===] [=== SENDING SMS FAILED ===] [ CHECK ACCOUNT BALANCE AND VALIDITY OF CALLR CREDENTIALS ===]")
                    # === NATIVE OS NOTIFICATION === #
                    if settings.get("natively_notify"):
                        notification.title = "Item might be in stock at:".format(place)
                        notification.message = info.get('url')
                        notification.send()
                    # === IF ENABLED, BUY ITEM === #
                    if settings.get("auto_buy"):
                        ordered_items = prepare_auto_buy(api, info, ordered_items, place, settings)

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
                    if settings.get("auto_buy"):
                        ordered_items = prepare_auto_buy(api, info, ordered_items, place, settings)

        # =============================== #
        # wait half a minute and go again #
        # =============================== #
        print("\n Check over. Trying again in 30 seconds..\n")
        time.sleep(30)


def prepare_auto_buy(api, info, ordered_items, place, settings):
    if delegate_purchase(info.get('webshop'), info.get('url'), settings):
        print("[=== ITEM ORDERED, HOORAY! ===] [=== {} ===]".format(place))
        if settings.get("natively_notify"):
            notification.title = "Hooray, item ordered at {}".format(place)
            notification.message = "Check your email for a confirmation of your order"
            notification.send()
        if settings.get("sms_notify"):
            api.call('sms.send', 'SMS', settings.get("phone"),
                     "Hooray! Item ordered at {}!".format(place), None)
        ordered_items += 1
        # if reached max amount of ordered items
        if not ordered_items < settings.get("max_ordered_items"):
            print("[=== Desired amount of ordered items reached! ===] [=== Bye! ===]")
            sys.exit(0)
    return ordered_items


def configure_settings():
    clear_cmdline()
    settings = {}

    # GENERAL QUESTIONS #
    print("To get started, please answer the following questions.\n"
          "All information is vital. If not, I wouldn't be asking :).\n")
    email = get_email()
    settings["email"] = email
    phone = get_phone_number()
    settings["phone"] = phone

    # SETTING QUESTIONS #
    print("Please answer the following close-ended questions with either 'yes' or 'no'.\n")
    settings["natively_notify"] = get_notify_setting()
    sms_notify, api = get_sms_setting()
    settings["sms_notify"] = sms_notify
    auto_buy, max_amount, passwords = get_autobuy_setting()
    settings["auto_buy"] = auto_buy
    settings["max_ordered_items"] = max_amount
    settings["passwords"] = passwords

    return settings, api


def get_email():
    email = input("Please enter your email address:\n")
    while not re.match("(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|'(?:[\x01-\x08\x0b\x0c\x0e-"
                       "\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*')@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0"
                       "-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])"
                       ")\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:"
                       "[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])", email):
        clear_cmdline()
        email = input("That is not a valid email address. Please try again:\n")
    clear_cmdline()
    return email


def get_phone_number():
    phone_numbr = input("Please enter your phone number (example: +31674528539):\n")
    while not re.match("^[+][3][1][6][0-9]{8}$", phone_numbr):
        clear_cmdline()
        phone_numbr = input("That is not a valid dutch phone number. Please try again:\n")
    clear_cmdline()
    return phone_numbr


def get_notify_setting():
    do_natively_notify = input("Would you like to be natively notified via this machine?:\n")
    if do_natively_notify.lower() == "yes":
        do_natively_notify = True
    elif do_natively_notify.lower() == "no":
        do_natively_notify = False
    else:
        clear_cmdline()
        print("Please answer with either 'yes' or 'no'.")
        get_notify_setting()
    return do_natively_notify


def get_sms_setting():
    api = 'disabled'
    sms_notify = input("\nWould you like to be notified via text / SMS?:\n")
    if sms_notify.lower() == "yes":
        sms_notify = True
        # initialize callr api
        callr_username = input("\nWhat is your CALLR username?:\n")
        callr_password = input("\nWhat is your CALLR password?:\n")
        api = callr.Api(callr_username, callr_password)
    elif sms_notify.lower() == "no":
        sms_notify = False
    else:
        clear_cmdline()
        print("Please answer with either 'yes' or 'no'.")
        get_sms_setting()
    return sms_notify, api


def get_autobuy_setting():
    do_auto_buy = input("\nWould you like the program to auto-buy consoles when in stock?:\n")
    while not do_auto_buy.lower() == 'yes' or do_auto_buy.lower() == 'no':
        do_auto_buy = input("\nTry again, do you want to use the auto-buy feature?:\n")
    else:
        if do_auto_buy.lower() == "yes":
            do_auto_buy = True
            max_buy_amount = get_max_buy_amount()
            passwords = get_passwords()
        elif do_auto_buy.lower() == "no":
            do_auto_buy = False
            max_buy_amount = 0
            passwords = 'auto-buy disabled'
    return do_auto_buy, max_buy_amount, passwords


def get_max_buy_amount():
    max_buy_amount = input("\nWhat is the maximum amount of consoles you wish to order?:\n")
    while not max_buy_amount.isnumeric():
        max_buy_amount = input("\nWhat is the maximum amount of consoles you wish to order?:\n")
    return int(max_buy_amount)


def get_passwords():
    clear_cmdline()
    print("Now, onto the account passwords. These are needed for automatically buying the consoles at the "
          "different locations. \nFilling in a wrong password will result in failure of the auto-buy attempt.\n")
    return {"coolblue": input("What is your Coolblue account password?:\n"),
            "bol": input("What is your Bol.com account password?:\n"),
            "mediamarkt": input("What is your Mediamarkt account password?:\n"),
            "nedgame": input("What is your Nedgame account password?:\n"),
            "paypal": input("What is your Paypal account password? (needed for auto-buy at Mediamarkt):\n")}


def clear_cmdline():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


def initialize_webdriver(url):
    if platform.system() == "Windows" or platform.system() == "Darwin":
        from selenium.webdriver import Chrome, ChromeOptions
        options = ChromeOptions()
        options.use_chromium = True
        options.headless = True
        driver = Chrome(parser.get("driver", "path_to_driver"), options=options)
    else:
        print("Only Windows and MacOS are supported. Terminating.")
        sys.exit(0)
    driver.get(url)
    return driver


def delegate_purchase(webshop, url, settings):
    """
    Function that delegates the automatically ordering of items

    First, the driver is instantiated. After that, based on the webshop its name
    a function is called that executes the ordering sequence for that specific
    webshop. That is, if it is implemented / possible for that webshop.
    """
    if webshop == 'coolblue':
        return buy_item_at_coolblue(initialize_webdriver(url), settings)
    elif webshop == 'bol':
        return buy_item_at_bol(initialize_webdriver(url), url, settings)
    elif webshop == 'mediamarkt':
        return buy_item_at_mediamarkt(initialize_webdriver(url), settings)
    elif webshop == 'nedgame':
        return buy_item_at_nedgame(initialize_webdriver(url), settings)
    else:
        print("Auto-buy is not implemented for {} yet.".format(webshop))
        return False


def buy_item_at_coolblue(driver, settings):
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
        WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/header/div/div[4]/ul/li[2]/a/span[2]"))).click()
        # LOGIN
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_emailaddress'), settings.get("email")) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_password'), settings.get("passwords").get("coolblue")) \
            .click(driver.find_element(By.XPATH, '/html/body/header/div/div[4]/ul/li[2]/div/div/div[2]/div/form/div['
                                                 '2]/div[2]/div[2]/button')) \
            .perform()
        # ADD TO CART
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-add-to-cart-button'))).click()
        # GO TO BASKET
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'modal-box__container')))
        driver.get("https://www.coolblue.nl/winkelmandje")
        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-shopping-cart-item')))
        if len(driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')) != 1:
            one_item = False
            while not one_item:
                basket = driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'shopping-cart-item__remove-button').get_attribute(
                            'title')
                        remove_href = item.find_element(By.CLASS_NAME,
                                                        'shopping-cart-item__remove-button').get_attribute('href')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    print(title)
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        driver.get(remove_href)
                        if len(driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')) == 1:
                            one_item = True

        WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-shopping-cart-item')))
        driver.find_element(By.CLASS_NAME, "js-shopping-cart-item-quantity-input").clear()
        driver.find_element(By.CLASS_NAME, "js-shopping-cart-item-quantity-input").send_keys('1')
        # ORDER
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='shoppingcart_form']/div/div[4]/div[1]/div[2]/div[1]/div[2]/button"))).click()
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='main-content']/div/div/div[11]/div[2]/div/div/div[2]/button"))).click()
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[3]/div[3]/button"))).click()
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[7]/div[3]/div/div"))).click()
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='main-content']/div[7]/div[3]/div/div/div/div[2]/div/div[2]/div[2]/button"))).click()
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id='main-content']/div/div[4]/div/div/div[1]/div[2]/button"))).click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[=== Something went wrong while trying to order at Coolblue ===]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_bol(driver, url, settings):
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
        actions.pause(1).send_keys_to_element(driver.find_element(By.ID, 'login_email'), settings.get("email")) \
            .send_keys_to_element(driver.find_element(By.ID, 'login_password'),  settings.get("passwords").get("bol")) \
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
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'continue_ordering_bottom'))).click()
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            try:
                WDW(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="paymentsuggestions"]/div/div[2]/div/div/ul/div[1]/div'))).click()
            except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                print("Afterpay not available. Aborting.")
            # confirm
            driver.find_element(By.XPATH, '//*[@id="executepayment"]/form/div/button').click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[=== Something went wrong while trying to order at BOL.COM ===]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_mediamarkt(driver, settings):
    """
    Function that will buy the item from the Mediamarkt webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    """
    try:
        # ACCEPT COOKIES
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'gdpr-cookie-layer__btn--submit--all'))).click()
        # LOGIN
        driver.execute_script("document.getElementById('pdp-add-to-cart').click()")
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'basket-flyout-cart'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'cobutton-next'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'login-email'))).send_keys(settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'loginForm-password'))).send_keys(settings.get("passwords").get("mediamarkt"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'loginForm'))).find_element(By.CLASS_NAME,
                                                                                                   'cobutton-next').click()

        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        basket = WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cart-product-table')))
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
        delivery_form = WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'deliveryForm')))
        delivery_form.find_element(By.CLASS_NAME, 'cobutton-next').click()
        # PAYPAL
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'paypal__xpay'))).click()
        driver.execute_script("document.getElementsByClassName('cobutton-next')[1].click()")
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[4]/form/checkout-footer/div/div[1]/div/div[2]/button'))).click()
        email_input = WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'email')))
        email_input.clear()
        email_input.send_keys(settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys( settings.get("passwords").get("paypal"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'btnLogin'))).click()
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'confirmButtonTop'))).click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[=== Something went wrong while trying to order at Mediamarkt ===]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_nedgame(driver, settings):
    """
    Function that will buy the item from the Nedgame webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    :param phone:
    """
    try:
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'koopbutton'))).click()
        driver.get('https://www.nedgame.nl/winkelmand')
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login_emailadres'))).send_keys(settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login_wachtwoord'))).send_keys(settings.get("passwords").get("nedgame"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'bigbutton'))).click()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.ID, 'BetaalWijze_9'))).click()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.ID, 'mobiel'))).send_keys(settings.get("phone"))
        WDW(driver, 10).until(EC.visibility_of_element_located((By.NAME, 'dob_day'))).clear()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.NAME, 'dob_day'))).send_keys(10)
        WDW(driver, 10).until(EC.visibility_of_element_located((By.NAME, 'dob_month'))).clear()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.NAME, 'dob_month'))).send_keys(10)
        WDW(driver, 10).until(EC.visibility_of_element_located((By.NAME, 'dob_year'))).clear()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.NAME, 'dob_year'))).send_keys(1990)
        WDW(driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH, '/html/body/div[4]/div/div[2]/div[2]/div/div[1]/form/div/div[6]/button'))).click()
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[=== Something went wrong while trying to order at Nedgame ===]")
        driver.close()
        driver.quit()
        return False


# start of program
if __name__ == "__main__":
    main()
