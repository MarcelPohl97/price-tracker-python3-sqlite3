import sqlite3
import sys
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re
import random
import string
import smtplib
import ssl

conn = sqlite3.connect('pricer.db')
c = conn.cursor()
login = False
last_login = ""

def create_register_table():
    c.execute('''CREATE TABLE if not exists register
                 (id integer primary key,
                 login text, 
                 password text, 
                 email text)''')

def create_user_table():
    c.execute('''CREATE TABLE if not exists user 
                (id integer primary key, 
                register_id integer, 
                register_login text, 
                register_password text, 
                register_email text)''')

def create_products_table():
    c.execute('''CREATE TABLE if not exists products 
                (id integer primary key,
                user_id integer,
                link text,
                product text,
                price float,
                time_date text)''')

create_register_table()
create_user_table()
create_products_table()

try:
    c.execute('''CREATE TABLE register
             (username text, password text, email text)''')
except:
    print("Already created data entry point")

c = conn.cursor()

def register_account():
    ID = input("Choose id for your account")
    password = input("Choose password for your account")
    email = input("Choose email for your account")
    c.execute('SELECT * from register WHERE username="%s" OR email="%s"' % (ID, email))
    if c.fetchone():
        print("User already exists")
    else:
        c.execute("INSERT INTO register VALUES ('%s', '%s', '%s')" % (ID, password, email))
        # Save (commit) the changes
        conn.commit()
        print("Successfully registered")

def login_account():
    global login, userid, userpw
    userid = input("ID:")
    userpw = input("PW:")

    # check if name and password exists from user
    c.execute('SELECT * from register WHERE username="%s" AND password="%s"' % (userid, userpw))
    #wenn fetch nicht None ist dann user und password erkannt vom user
    if c.fetchone() is not None:
        print("Welcome successfully logged in!")
        login = True
    else:
        print("Login failed")

def forgot_password():
    global login
    stringLength = 10
    lettersAndDigits = string.ascii_letters + string.digits
    generate_code = ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

    email = input("Put in your email to get reset link")
    c.execute('SELECT * from register WHERE email="%s"' % (email))
    data_records = c.fetchall()

    # check if name and password exists from user
    c.execute('SELECT * from register WHERE email="%s"' % (email))
    # wenn fetch nicht None ist dann user und password erkannt vom user
    if c.fetchone() is not None:
        print("Email is available Sending you a code that you need to submit to change your password")
        reset_code = generate_code
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "pricercheckyourproducts@gmail.com"
        receiver_email = email
        password = "pricer!3%7)"
        message = "Subject: <Reset code for password>" + "\n" + "Hello " + str(data_records[0][0]) + "\n " + " here is your reset code: " + reset_code

        context = ssl.create_default_context()

        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

        code_submit = input("Type in the code we send you through email: ")
        if code_submit == reset_code:
            print("Successfully entered the code right")
            userpw = input("New PW: ")
            # check if name and password exists from user
            try:
                c.execute('UPDATE register SET password="%s" WHERE email="%s"' % (userpw, email))
                print("Successfully changed your password")
            # wenn fetch nicht None ist dann user und password erkannt vom user
            except:
                print("Couldnt find this user")
        else:
            print("The code you submitted was not right")
    else:
        print("Couldnt find email ")


def add_product():
    user_id = input("Put in your id as data entry point for your products")
    if user_id == userid:

        try:
            c.execute('''CREATE TABLE %s
                     (id integer primary key, link text, product text, price blob, time_date blob)''' % (user_id))
            print("Created product table for user")
        except:
            print("Already created data entry point")

        URL = "https://www.amazon.de/dp/B07G9RM9GN/ref=AGS_NW_DE_GW_D_P0_MSO_C?pf_rd_p=9b90496b-f129-4d8a-b6e6-e4287712d446&pf_rd_r=MJ8D247GQ6JPNA6CD82M"
        headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

        page = requests.get(URL, headers=headers)

        soup = BeautifulSoup(page.text, "html.parser")

        title = soup.find(id="productTitle")
        price = soup.find(id="priceblock_ourprice")
        current_price = "70$"
        current_price_check = re.sub('[€$]', '', current_price)

        dt_now = datetime.now()

        date_time = dt_now.strftime("%d/%m/%Y %H:%M:%S")

        formatted_title = title.text.replace("\n", "").strip()

        formatted_price = price.text.replace("\n", "").strip()
        formatted_price2 = re.sub('[\xa0]', '', formatted_price)
        new_price_check = re.sub('[€$]', '', formatted_price)

        link = URL
        product = formatted_title
        price = formatted_price2
        time = date_time
        c.execute('SELECT * from ' + user_id + ' WHERE link="%s"' % (URL))
        product_check = c.fetchone()
        if product_check:
            print("Product already exists in your product list")
            for check in product_check:
                print(check)

        else:
            c.execute("INSERT INTO " + user_id + " (link, product, price, time_date) VALUES (?,?,?,?) ", (link, product, price, time))
            c.execute('SELECT * from ' + user_id)
            print(c.fetchall())
            # Save (commit) the changes
            conn.commit()
            print("Successfully added product")
    else:
        print("Wrong userid or userpw")

def show_product():
    user_id = input("Put in your id as data entry point for your products")
    c.execute('SELECT * from ' + user_id)
    product_results = c.fetchall()
    for products in product_results:
        print(products)

def check_product():
    user_id = input("Put in your id as data entry point for your products")
    id_key = int(input("Put in the key of your product you wish to check for a price increase or decrease"))
    c.execute('SELECT * from ' + user_id + ' WHERE id="%s"' % (id_key))
    product_results = c.fetchall()
    for products in product_results:
        old_price = products[3]
        current_price_check = re.sub('[€$]', '', old_price)
        current_price_check_add_float = re.sub('[,]', '.', current_price_check)
        current_price_check_final_format = current_price_check_add_float

    URL = "https://www.amazon.de/dp/B07G9RM9GN/ref=AGS_NW_DE_GW_D_P0_MSO_C?pf_rd_p=9b90496b-f129-4d8a-b6e6-e4287712d446&pf_rd_r=MJ8D247GQ6JPNA6CD82M"
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    page = requests.get(URL, headers=headers)

    soup = BeautifulSoup(page.text, "html.parser")

    title = soup.find(id="productTitle")
    price = soup.find(id="priceblock_ourprice")

    dt_now = datetime.now()

    date_time = dt_now.strftime("%d/%m/%Y %H:%M:%S")

    formatted_title = title.text.replace("\n", "").strip()

    formatted_price = price.text.replace("\n", "").strip()
    formatted_price2 = re.sub('[\xa0]', '', formatted_price)
    new_price_check = re.sub('[€$]', '', formatted_price)
    new_price_check_add_float = re.sub('[,]', '.', new_price_check)
    new_price_check_remove_white_space = new_price_check_add_float.strip()
    new_price_check_final_format = new_price_check_remove_white_space

    #link = URL
    #product = formatted_title
    price = formatted_price2
    time = date_time

    if current_price_check_final_format > new_price_check_final_format:
        print("Price went down!")
    elif current_price_check_final_format < new_price_check_final_format:
        print("Price went up")
    else:
        print("Price remains the same")

    over_write_data = input("Do you want to update your data? (Yes/No)")
    new_price_check_delete_float = re.sub('[.]', ',', new_price_check)
    new_price_check_add_euro = new_price_check_delete_float + "€"
    new_price_check_final_reformat = re.sub('[\xa0]', '', new_price_check_add_euro)

    if over_write_data == "Yes":
        c.execute('UPDATE ' + user_id + ' SET price="%s", time_date="%s" WHERE id="%s"' % (new_price_check_final_reformat, time, id_key))
        conn.commit()
        print("Successfully updated product")

    else:
        print("You choose to not update your product price and time")




def remove_product():
    user_id = input("Put in your id as data entry point for your products")
    id_key = int(input("Put in the key of your product you wish to remove"))
    c.execute('DELETE from ' + user_id + ' WHERE id="%s"' % (id_key))
    conn.commit()
    c.execute('SELECT * from ' + user_id)
    product_results = c.fetchall()
    for products in product_results:
        print(products)


def menu1():
    print("Type in the following numbers for your next action:")
    print("1. Register Account \n"
          "2. Login \n"
          "3. Forgot Password \n"
          "4. Close ")
    action = input()
    if action == str(1):
        register_account()
    elif action == str(2):
        login_account()
    elif action == str(3):
        forgot_password()
    elif action == str(4):
        sys.exit()
        
def menu2():
    print("Type in the following numbers for your next action:")
    print("1. Add product \n"
          "2. Show products \n"
          "3. Check product \n"
          "4. Remove product \n"
          "5. Change Password \n"
          "6. Log out")
    action = input()
    if action == str(1):
        add_product()
    elif action == str(2):
        show_product()
    elif action == str(3):
        check_product()
    elif action == str(4):
        remove_product()
    elif action == str(5):
        print("Log out")
    

while True:
    if login == False:
        menu1()
    elif login == True:
        menu2()














