#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import platform
import re
import sys
import time
from os import system, name

import callr
import requests
import six
from PyInquirer import (Token, ValidationError, Validator, prompt,
                        style_from_dict)
from notifypy import Notify
from pyconfigstore import ConfigStore
from pyfiglet import figlet_format
from selenium.common import exceptions as SE
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW

try:
    from termcolor import colored
except ImportError:
    colored = None

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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/87.0.4280.141 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT": "1",
    "Connection": "close", "Upgrade-Insecure-Requests": "1"
}

# =============================== #
# DICTIONARY WITH WEBSHOP DETAILS #
# =============================== #
locations = {
    'Amazon NL Disk': {
        'webshop': 'amazon-nl',
        'url': 'https://www.amazon.nl/Sony-PlayStation-PlayStation%C2%AE5-Console/dp/B08H93ZRK9',
        'inStock': False,
        'outOfStockLabel': "Momenteel niet verkrijgbaar"},
    'Amazon NL Digital': {
        'webshop': 'amazon-nl',
        'url': 'https://www.amazon.nl/Sony-PlayStation-playstation_4-PlayStation%C2%AE5-Digital/dp/B08H98GVK8',
        'inStock': False,
        'outOfStockLabel': "Momenteel niet verkrijgbaar"},
    'Alternate DE Disk': {
        'webshop': 'Alternate.de',
        'url': 'https://www.alternate.de/Sony-Interactive-Entertainment/PlayStation-5-Spielkonsole/html/product'
               '/1651220?',
        'inStock': False,
        'outOfStockLabel': "Artikel kann nicht gekauft werden"},
    'Alternate DE Digital': {
        'webshop': 'Alternate.de',
        'url': 'https://www.alternate.de/Sony-Interactive-Entertainment/PlayStation-5-Digital-Edition-Spielkonsole'
               '/html/product/1651221?',
        'inStock': False,
        'outOfStockLabel': "Artikel kann nicht gekauft werden"},
    'COOLBLUE Disk': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/865866/playstation-5.html',
        'inStock': False,
        'outOfStockLabel': "Tijdelijk uitverkocht"},
    'COOLBLUE Digital': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/865867/playstation-5-digital-edition.html',
        'inStock': False,
        'outOfStockLabel': "Tijdelijk uitverkocht"},
    'BOL.COM Disk': {
        'webshop': 'bol',
        'url': 'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282/',
        'inStock': False,
        'outOfStockLabel': "outofstock-buy-block"},
    'BOL.COM Digital': {
        'webshop': 'bol',
        'url': 'https://www.bol.com/nl/p/sony-playstation-5-all-digital-console/9300000004162392/',
        'inStock': False,
        'outOfStockLabel': "outofstock-buy-block"},
    'MEDIAMARKT Disk': {
        'webshop': 'mediamarkt',
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-disk-edition-1664768.html',
        'inStock': False,
        'outOfStockLabel': "Online uitverkocht"},
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
    'GAMEMANIA Digital': {
        'webshop': 'gamemania',
        'url': 'https://www.gamemania.nl/Consoles/playstation-5/145721_playstation-5-digital-edition',
        'inStock': False,
        'outOfStockLabel': "Niet beschikbaar"},
    'INTERTOYS Disk': {
        'webshop': 'intertoys',
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-825gb',
        'inStock': False,
        'outOfStockLabel': "uitverkocht!"},
    'INTERTOYS Digital': {
        'webshop': 'intertoys',
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-digital-edition-825gb',
        'inStock': False,
        'outOfStockLabel': "uitverkocht!"},
    'NEDGAME Disk': {
        'webshop': 'nedgame',
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5--levering-begin-2021-/6036644854/?utm_campaign=CPS'
               '&utm_medium=referral&utm_source=tradetracker&utm_content=linkgeneratorDeeplink&utm_term=273010',
        'inStock': False,
        'outOfStockLabel': "Uitverkocht"},
      'NEDGAME Digital': {
        'webshop': 'nedgame',
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5-digital-edition--levering-begin-2021-/9647865079/',
        'inStock': False,
        'outOfStockLabel': "Uitverkocht"}
}

style = style_from_dict({
    Token.QuestionMark: '#ff7f50 bold',
    Token.Answer: '#ff7f50 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})


class EmailValidator(Validator):
    """
    Checks if the input is a valid email address
    """
    pattern = r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?"

    def validate(self, email):
        if len(email.text):
            if re.match(self.pattern, email.text):
                return True
            else:
                raise ValidationError(
                    message="That is not a valid email address",
                    cursor_position=len(email.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(email.text))


class EmptyValidator(Validator):
    """
    Checks if the input to the question is not empty
    """

    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class PhoneValidator(Validator):
    """
    Checks if the input is a valid dutch number
    """
    pattern = r"^[+][3][1][6][0-9]{8}$"

    def validate(self, phone):
        if len(phone.text):
            if re.match(self.pattern, phone.text):
                return True
            else:
                raise ValidationError(
                    message="That is not a valid dutch phone number",
                    cursor_position=len(phone.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(phone.text))


class NumberValidator(Validator):
    """
    Checks if the input is a number
    """

    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))


def ask_to_configure_settings():
    """
    Asks the user to configure the settings of the script via the cli
    """
    clear_cmdline()
    log("The PS5 AutoBuyer", "white", "larry3d", True)
    log("Welcome. To get started, please answer the following questions. All information is vital. \nIf it wasn't, "
        "I wouldn't be asking :). Don't worry about leaking your passwords. This script \nwill run locally on your "
        "very own machine. I can not, in any way, reach your credentials.\n",
        "cyan")

    questions = [
        {
            'type': 'input',
            'name': 'email',
            'message': 'Enter your email address:',
            'validate': EmailValidator
        },
        {
            'type': 'input',
            'name': 'phone',
            'message': 'Enter your phone number (e.g. +31612345678):',
            'validate': PhoneValidator
        },
        # natively notify
        {
            'type': 'confirm',
            'name': 'natively_notify',
            'message': 'Do you want to be updated via this machine?'
        },
        # sms notify
        {
            'type': 'confirm',
            'name': 'sms_notify',
            'message': 'Do you want to be updated via SMS / text messages?'
        },
        # callr credentials
        {
            'type': 'input',
            'name': 'callr_username',
            'message': 'What is your CALLR username?:',
            'when': lambda answers: answers['sms_notify']
        },
        {
            'type': 'password',
            'name': 'callr_password',
            'message': 'What is your CALLR password?:',
            'when': lambda answers: answers['sms_notify']
        },
        # auto-buy
        {
            'type': 'confirm',
            'name': 'auto_buy',
            'message': 'Do you want to automatically buy consoles when in stock?'
        },
        {
            'type': 'input',
            'name': 'max_ordered_items',
            'message': 'How many consoles do you wish to buy at a maximum?',
            'validate': NumberValidator,
            'when': lambda answers: answers['auto_buy'],
            'filter': lambda val: int(val)
        },
        # web-shop passwords
        {
            'type': 'password',
            'name': 'amazon_password',
            'message': 'What is your Amazon account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'coolblue_password',
            'message': 'What is your Coolblue account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'bol_password',
            'message': 'What is your Bol.com account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'mediamarkt_password',
            'message': 'What is your Mediamarkt account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'nedgame_password',
            'message': 'What is your Nedgame account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'paypal_password',
            'message': 'What is your Paypal account password (needed for auto-buy at Mediamarkt)?:',
            'when': lambda answers: answers['auto_buy']
        }
    ]

    answers = prompt(questions, style=style)
    log("\nThank you. Program is starting now!\n", "cyan")

    return answers


def log(string, color, font="slant", figlet=False):
    """
    Prints a cli message with extra options
    """
    if colored:
        if not figlet:
            six.print_(colored(string, color, attrs=["bold"]))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color, attrs=["bold"]))
    else:
        six.print_(string)


def auto_buy_item(info, ordered_items, place, settings):
    """
    Proceeds to auto-buy the item that is in stock. Notifies the
    user if notifications are enabled.
    """
    if delegate_purchase(info.get('webshop'), info.get('url'), settings):
        print("[=== ITEM ORDERED, HOORAY! ===] [=== {} ===]".format(place))
        if settings.get("natively_notify"):
            notification.title = "Hooray, item ordered at {}".format(place)
            notification.message = "Check your email for a confirmation of your order"
            notification.send()
        if settings.get("sms_notify"):
            try:
                api = callr.Api(settings.get("callr_username"), settings.get("callr_password"))
                api.call('sms.send', 'SMS', settings.get("phone"),
                         "Hooray! Item ordered at {}!".format(place), None)
            except (callr.CallrException, callr.CallrLocalException) as e:
                print("[=== ERROR ===] [=== SENDING SMS FAILED ===] [ CHECK ACCOUNT BALANCE AND VALIDITY OF CALLR "
                      "CREDENTIALS ===]")
        ordered_items += 1
        # if reached max amount of ordered items
        if not ordered_items < settings.get("max_ordered_items"):
            print("[=== Desired amount of ordered items reached! ===] [=== Bye! ===]")
            sys.exit(0)
    return ordered_items


def clear_cmdline():
    """
    Clears the cmd window.
    """
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


def initialize_webdriver(url):
    """
    This function initializes the webdriver.

    :param: url
    """
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
    if webshop == 'amazon-nl':
        return buy_item_at_amazon(initialize_webdriver(url), settings)
    elif webshop == 'coolblue':
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


def buy_item_at_amazon(driver, settings):
    """
    Function that will buy the item from the Amazon webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_id("sp-cc-accept").click()
        # ADD TO CART
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'add-to-cart-button'))).click()
        # GO TO BASKET
        driver.get("https://www.amazon.nl/gp/cart/view.html")
        # ACCEPT BASKET
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'a-button-primary'))).click()
        # LOGIN USERNAME
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'ap_email'), settings.get("email")) \
            .click(driver.find_element(By.ID, 'continue')) \
            .perform()
        # LOGIN PASSWORD
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'ap_password'), settings.get("amazon_password")) \
            .click(driver.find_element(By.ID, 'signInSubmit')) \
            .perform()
        # ACCEPT SHIPPING ADDRESS
        WDW(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, 'Bezorgen op dit adres'))).click()
        # ACCEPT SHIPPING METHOD
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'a-button-text'))).click()
        # SELECT PAYMENT METHOD
        WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div/div[2]/div/form/div/div/div/div[3]/div[2]/div/div/div/div/div/div/span/div/label/input'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div[2]/div[2]/div/div[2]/div/form/div/div/div/div[3]/div[2]/div/div/div/div/div/div/span/div/label/input'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'a-button-text'))).click()
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'place-your-order-button'))).click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[=== Something went wrong while trying to order at Coolblue ===]")
        driver.close()
        driver.quit()
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
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/header/div/div[4]/ul/li[2]/a/span[2]"))).click()
        # LOGIN
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_emailaddress'), settings.get("email")) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_password'), settings.get("coolblue_password")) \
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
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
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
    :param settings:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_xpath(
            "//*[@id='modalWindow']/div[2]/div[2]/wsp-consent-modal/div[2]/div/div[1]/button").click()
        # LOGIN
        driver.get('https://www.bol.com/nl/rnwy/account/overzicht')
        actions = ActionChains(driver)
        actions.pause(1).send_keys_to_element(driver.find_element(By.ID, 'login_email'), settings.get("email")) \
            .send_keys_to_element(driver.find_element(By.ID, 'login_password'), settings.get("bol_password")) \
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
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
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
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'loginForm-password'))).send_keys(
            settings.get("mediamarkt_password"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'loginForm'))).find_element(By.CLASS_NAME,
                                                                                                   'cobutton-next').click()

        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        basket = WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cart-product-table')))
        length_basket = len(basket)
        if length_basket > 1:
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
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(
            settings.get("paypal_password"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'btnLogin'))).click()
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'confirmButtonTop'))).click()
        else:
            print("[=== Confirmation of order prevented. Application not in production ===] [=== See config.ini ===]")
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
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
    :param settings:
    """
    try:
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'koopbutton'))).click()
        driver.get('https://www.nedgame.nl/winkelmand')
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login_emailadres'))).send_keys(
            settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login_wachtwoord'))).send_keys(
            settings.get("nedgame_password"))
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
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[=== Something went wrong while trying to order at Nedgame ===]")
        driver.close()
        driver.quit()
        return False


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
    settings = ask_to_configure_settings()

    ordered_items = 0
    # loop until desired amount of ordered items is reached
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
                    content = requests.get(info.get('url'), timeout=5, headers=headers).content.decode('utf-8')
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout,
                        requests.exceptions.ChunkedEncodingError) as e:
                    print("[=== ERROR ===] [=== {} ===]".format(place))
                    continue
                # ======================================== #
                # item in stock, proceed to try and buy it #
                # ======================================== #
                if info.get('outOfStockLabel') not in content:
                    print("[=== OMG, MIGHT BE IN STOCK! ===] [=== {} ===]".format(place))
                    # if enabled, send sms
                    if settings.get("sms_notify"):
                        try:
                            api = callr.Api(settings.get("callr_username"), settings.get("callr_password"))
                            api.call('sms.send', 'SMS', settings.get("phone"),
                                     "Item might be in stock at {}. URL: {}".format(place, info.get('url')), None)
                        except (callr.CallrException, callr.CallrLocalException) as e:
                            print("[=== ERROR ===] [=== SENDING SMS FAILED ===] [ CHECK ACCOUNT BALANCE AND VALIDITY "
                                  "OF CALLR CREDENTIALS ===]")
                    # === NATIVE OS NOTIFICATION === #
                    if settings.get("natively_notify"):
                        notification.title = "Item might be in stock at:".format(place)
                        notification.message = info.get('url')
                        notification.send()
                    # === IF ENABLED, BUY ITEM === #
                    if settings.get("auto_buy"):
                        ordered_items = auto_buy_item(info, ordered_items, place, settings)

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
                    content = requests.get(info.get('url'), timeout=5, headers=headers).content.decode('utf-8')
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout,
                        requests.exceptions.ChunkedEncodingError) as e:
                    print("[=== ERROR ===] [=== {} ===]".format(place))
                    continue
                if info.get('outOfStockLabel') in content:
                    print("[=== NEW STOCK SOLD OUT ===] [=== {} ===]".format(place))
                    info['inStock'] = False
                else:
                    print("[=== STILL IN STOCK! ===] [=== {} ===]".format(place))
                    if settings.get("auto_buy"):
                        ordered_items = auto_buy_item(info, ordered_items, place, settings)

        # =============================== #
        # wait half a minute and go again #
        # =============================== #
        print("\n Check over. Trying again in 30 seconds..\n")
        time.sleep(30)


# start of program
if __name__ == "__main__":
    main()
