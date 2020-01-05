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
import time

conn = sqlite3.connect('pricer.db')
c = conn.cursor()
login = False

def create_user_table():
    c.execute('''CREATE TABLE if not exists users
                 (id integer primary key,
                 login text, 
                 password text, 
                 email varchar)''')

def create_products_table():
    c.execute('''CREATE TABLE if not exists products 
                (id integer primary key,
                user_login text,
                link text,
                product text,
                price float,
                time_date text)''')

create_user_table()
create_products_table()

def register_account():
    ID = input("Choose id for your account")
    password = input("Choose password for your account")
    email = input("Choose email for your account")

    c.execute("SELECT * FROM users WHERE login=:login OR email=:email", {'login': ID, 'email': email})
    if c.fetchone():
        print("User already exists")
    else:
        c.execute("INSERT INTO users VALUES (:id, :login, :password, :email)", {'id': None, 'login': ID, 'password': password, 'email': email})
        conn.commit()
        print("Successfully registered")

def login_account():
    global login, userid, userpw
    userid = input("ID:")
    userpw = input("PW:")

    # check if name and password exists from user
    c.execute("SELECT * FROM users WHERE login=:login AND password=:password", {'login': userid, 'password': userpw})
    user_authentication = c.fetchone()
    if user_authentication is not None:
        print("Welcome {} successfully logged in!".format(user_authentication[1]))
        login = True

    else:
        print("Login failed")

def forgot_password():
    stringLength = 10
    lettersAndDigits = string.ascii_letters + string.digits
    generate_code = ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

    email = input("Put in your email to get reset link")

    c.execute("SELECT * from users WHERE email=:email", {'email': email})
    data_records = c.fetchall()

    if c.fetchall() is not None:
        print("Email is available Sending you a code that you need to submit to change your password")
        reset_code = generate_code
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "pricercheckyourproducts@gmail.com"
        receiver_email = email
        password = "pricer!3%7)"
        message = "Subject: <Reset code for password>" + "\n" + "Hello " + str(data_records[0][1]) + "\n " + " here is your reset code: " + reset_code

        context = ssl.create_default_context()

        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

        code_submit = input("Type in the code we send you through email: ")
        if code_submit == reset_code:
            print("Successfully entered the code right")
            userpw = input("New PW: ")

            try:
                c.execute("UPDATE users SET password=:password WHERE email=:email", {'password': userpw, 'email': email})
                print("Successfully changed your password")

            except:
                print("Couldnt find this user")
        else:
            print("The code you submitted was not right")
    else:
        print("Couldnt find email ")

def about():
    print("This app is about collecting your favourite products and manually or letting it automatically \n"
          "check in a certain time frame if your products went up or down and getting an automated email.\n"
          "Future version is planned as a webapp based on the Django framework")


def add_product():

    URL = str(input("Add the amazon link to your product that you want to add"))
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
    c.execute("SELECT * from products WHERE user_login=:user_login AND link=:link", {'user_login': userid, 'link': link})
    product_check = c.fetchone()
    if product_check:
        print("Product already exists in your product list")
        print(product_check)

    else:
        c.execute("INSERT INTO products VALUES (:id, :user_login, :link, :product, :price, :time_date)", {'id': None, 'user_login': userid, 'link': link, 'product': product, 'price': price, 'time_date': time})
        c.execute("SELECT * from products WHERE user_login=:user_login", {'user_login': userid})
        conn.commit()
        print("Successfully added product")

def show_product():
    c.execute("SELECT * from products WHERE user_login=:user_login", {'user_login': userid})
    product_results = c.fetchall()
    for products in product_results:
        print(products)

def check_product():
    id_key = int(input("Put in the key of your product you wish to check for a price increase or decrease"))
    try:
        c.execute("SELECT * from products WHERE user_login=:user_login AND id=:id", {'user_login': userid, 'id':id_key})
        product_results = c.fetchall()
        for products in product_results:
            old_price = products[4]
            current_price_check = re.sub('[€$]', '', old_price)
            current_price_check_add_float = re.sub('[,]', '.', current_price_check)
            current_price_check_final_format = current_price_check_add_float

        URL = str(product_results[0][2])
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
            c.execute("UPDATE products SET price=:price, time_date=:time_date WHERE id=:id", {'price': new_price_check_final_reformat, 'time_date': time, 'id': id_key})
            conn.commit()
            print("Successfully updated product")

        else:
            print("You choose to not update your product price and date-time")
    except:
        print("Couldnt match id for your product")

def remove_product():
    id_key = int(input("Put in the key of your product you wish to remove"))
    c.execute("DELETE from products WHERE user_login=:user_login AND id=:id", {'user_login': userid, 'id': id_key})
    conn.commit()
    c.execute("SELECT * from products WHERE user_login=:user_login", {'user_login': userid})
    product_results = c.fetchall()
    for products in product_results:
        print(products)

def change_password():
    old_password = input("Type in your old password")
    if old_password == userpw:
        new_password = input("Type in your new password")
        try:
            c.execute("UPDATE users SET password=:password WHERE login=:login", {'password': new_password, 'login': userid})
            conn.commit()
            print("Successfully updated your password!")
        except:
            print("Couldnt update password")
    else:
        print("Your old password was wrong")

def automated_check_product():
    id_key = int(input("Put in the key of your product you wish to check for a price increase or decrease"))
    time_frame = int(input("Type in how many seconds everytime the programm should wait for the next check"))
    while True:

        try:
            c.execute("SELECT * from products WHERE user_login=:user_login AND id=:id", {'user_login': userid, 'id': id_key})
            product_results = c.fetchall()
        except:
            print("Couldnt match id for your product")
            break
        for products in product_results:
            old_price = products[4]
            current_price_check = re.sub('[€$]', '', old_price)
            current_price_check_add_float = re.sub('[,]', '.', current_price_check)
            current_price_check_final_format = current_price_check_add_float

        URL = str(product_results[0][2])
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

        # link = URL
        # product = formatted_title
        price = formatted_price2
        times = date_time

        if current_price_check_final_format > new_price_check_final_format:

            c.execute("SELECT * from users WHERE login=:login", {'login': userid})
            data_records = c.fetchall()
            port = 587  # For starttls
            smtp_server = "smtp.gmail.com"
            sender_email = "pricercheckyourproducts@gmail.com"
            receiver_email = data_records[0][3]
            password = "pricer!3%7)"
            message = "Subject: <One of your added products got a reduced price>" + "\n" + "Hello " + str(
            data_records[0][1]) + "\n " + " your product: " + str(product_results[0][3]) + " went down from: " + str(current_price_check_final_format) + " to " + str(new_price_check_final_format) + "\n" + "here is the link if you want to buy it: " + str(product_results[0][2])

            context = ssl.create_default_context()

            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message)

            over_write_data = input("Do you want to update your data? (Yes/No)")
            new_price_check_delete_float = re.sub('[.]', ',', new_price_check)
            new_price_check_add_euro = new_price_check_delete_float + "€"
            new_price_check_final_reformat = re.sub('[\xa0]', '', new_price_check_add_euro)

            if over_write_data == "Yes":
                c.execute("UPDATE products SET price=:price, time_date=:time_date WHERE id=:id",
                          {'price': new_price_check_final_reformat, 'time_date': times, 'id': id_key})
                conn.commit()
                print("Successfully updated product")
                break

            else:
                print("You choose to not update your product price and date-time")
                break
        else:
            time.sleep(time_frame)
            print("Checking again...")
            continue

def check_all_product():
    try:
        c.execute("SELECT * from products WHERE user_login=:user_login", {'user_login': userid})
        product_results = c.fetchall()
        for i in range(len(product_results)):

            old_price = product_results[i][4]
            current_price_check = re.sub('[€$]', '', old_price)
            current_price_check_add_float = re.sub('[,]', '.', current_price_check)
            current_price_check_final_format = current_price_check_add_float

            URL = str(product_results[i][2])
            headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

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

            # link = URL
            # product = formatted_title
            price = formatted_price2
            time = date_time

            if current_price_check_final_format > new_price_check_final_format:
                print("Price went down " + product_results[i][3])
            elif current_price_check_final_format < new_price_check_final_format:
                print("Price went up " + product_results[i][3])
            else:
                print("Price remains the same " + product_results[i][3])
    except:
        print("Couldnt find any products")


def logout():
    global login
    login = False
    print("Successfully logged out")



def menu1():

    print("Type in the following numbers for your next action:")
    print("1. Register Account \n"
          "2. Login \n"
          "3. Forgot Password \n"
          "4. About \n"
          "5. Quit")
    choices = {"1": register_account,
               "2": login_account,
               "3": forgot_password,
               "4": about,
               "5": sys.exit
               }
    choice = input("Enter and option: ")
    action = choices.get(choice)
    if action:
        action()
    else:
        print("{0} is not a valid choice".format(choice))
        
def menu2():
    print("Type in the following numbers for your next action:")
    print("1. Add product \n"
          "2. Show products \n"
          "3. Check product \n"
          "4. Remove product \n"
          "5. Change Password \n"
          "6. Automated Check product \n"
          "7. Check all products \n"
          "8. Logout")
    choices = {"1": add_product,
               "2": show_product,
               "3": check_product,
               "4": remove_product,
               "5": change_password,
               "6": automated_check_product,
               "7": check_all_product,
               "8": logout
               }
    choice = input("Enter and option: ")
    action = choices.get(choice)
    if action:
        action()
    else:
        print("{0} is not a valid choice".format(choice))

while True:
    if login == False:
        menu1()
    elif login == True:
        menu2()














