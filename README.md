# Playstation 5 AutoBuyer | The Netherlands only

*Please note; usage of tools like this to gain an advantage over other customers is not ethically right.*

**Auto-buy works for Coolblue, BOL.COM, Mediamarkt and Nedgame.**

This script's aim is to auto-buy Playstation 5 consoles. At first, this little fun project was meant to be designed only for notifying users when a Playstation 5 might be in stock. However, the more time I put in this, the more I wanted to expand it.
The script is designed only to work for pre-determined web-stores within the Netherlands.

Furthermore, feel free to contact me on [twitter](https://twitter.com/dejongolle) if you have any questions.

## Get started

### Installation

1) Install python, and make sure you check the box which says: "Add Python VERSION to PATH".  
  

2) Install python packages via pip:
```
pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```

3) Download the Chrome WebDriver

Make sure you have Chrome installed. Then; check what version of Chrome you have got installed on your system. Like so:  

<img src="resources/chrome-version.png" width='80%' alt="Get Chrome Version"/>  

Memorize the version number, and download the Chrome WebDriver with the same version number [here](https://chromedriver.chromium.org/downloads).   
Go ahead and store the driver executable anywhere you like and copy its full/absolute path. Like so:  

<img src="resources/copy_as_path.jpg" width='80%' alt="Copy As Path"/>  

Now, in StockNotifierPS5.py, in the initialize_webdriver() function,
paste your path inside the quotation marks (") where it tells you to do so. **Be aware**. Windows paths should have double backslashes 
and MacOS paths should have single forward slashes.

## Usage
Once the steps stated above have been completed, you can proceed to change the application its settings. Once you've done that, you'll be able to run it.

### Settings
All these settings can be changed in the config file (config.ini) file.

#### NATIVELY NOTIFY
Windows as well as MacOS both have a way of natively notifying the user when there is important information the be known.
To be notified using this mechanism when one is in stock somewhere, set the *natively_notify* value to **true**.

#### SMS NOTIFY
This might come in handy when you're not at home, you have auto-buy enabled, but the purchase somehow fails.   
If you would like to be notified via SMS, set the *sms_notify* value to true. Also, make sure you have correctly filled out your
mobile phone number (including country code). This is the *phone* variable.  
Furthermore, if you want to use the SMS notify feature, make sure you have a [callr](https://www.callr.com/) account with credit on it. 
Fill out your credentials in the config file. Variables *username* and *password* under the *callr credentials* section.

#### AUTO-BUY
Webshop       | Method of payment
------------- | -------------
Coolblue      | Bank Transfer
BOL.COM       | Afterpay (availability depends on account)
Mediamarkt    | Paypal  
Nedgame       | Afterpay (phone number needed)
Gamemania     | *To be implemented* 
Intertoys     | *To be implemented*  


For the usage of the auto-buy feature, set the *auto_buy* value to true. To be able to make the automatic purchase of items successful, 
you will need to have an account at each of the webshops. For the purchase at some webshops, you might need to have a paypal account. 
To make use of this feature, please fill out the *email* field and all the password fields under the *auto-buy passwords* section.

#### Maximum amount of ordered items
Clearly, for most of you reading this, you do not want to spend your entire bank account on only Playstation 5 consoles. 
Because of that, within the config.ini file, there is a setting through which you can tell the script how many consoles can be bought at a maximum.
To change this setting, change the value of *max_ordered_items*.

### Running the script

In a CommandPrompt window, navigate to the Playstation5AutoBuyer folder like so:  
```
cd C:\Users\YourPcName\Location\Of\Playstation5AutoBuyer
```

Once in the StockNotifier folder, run the script like so:
```
python PS5AutoBuyer.py
```
or  
```
python3 PS5AutoBuyer.py
```

<a href="https://www.buymeacoffee.com/olledejong"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=olledejong&button_colour=008a73&font_colour=ffffff&font_family=Poppins&outline_colour=ffffff&coffee_colour=FFDD00" style="float: right; margin-top: 20px !important;"></a>
