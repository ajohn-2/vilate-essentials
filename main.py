from itertools import product
from flask import Flask, render_template, request, flash, redirect
import flask_login

import pymysql 

from dynaconf import Dynaconf

app = Flask(__name__)
conf = Dynaconf(
    settings_file = ["settings.toml"]
)


app = Flask(__name__)
app.secret_key = conf.secret_key

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, user_id, username, email, name):
        self.id = user_id
        self.username = username
        self.email = email
        self.name = name

    def get_id(self):
        return str(self.id)
    
@login_manager.user_loader
def load_user(user_id):
    conn = connect_db
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id};")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result is not None:
        return User(result["id"], result["username"], result["email"], result["name"])
    

    

def connect_db():
    conn = pymysql.connect(
        host="10.100.34.80",
        database="ajohn_vilateé_essence",
        user="ajohn",
        password = conf.password,
        autocommit = True,
        cursorclass= pymysql.cursors.DictCursor
    )

    return conn

@app.route("/")
def index():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def browsepage():
    query = request.args.get('query')

    conn = connect_db()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product` ;")
    else:
        cursor.execute("SELECT * FROM `Product` WHERE `name` LIKE '%(query)%' ;")
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("browse.html.jinja", products = results)

@app.route("/product/<product_id>")
def productpage(product_id):
    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    total = 0
    try:
        for ratings in result:
            sum = ratings["ratings"]

            total = total + sum

            count = len(result)

        average = total / count
    except:
        average = 0

    return render_template("product.html.jinja", product = result, average = average)



@app.route("/product/<product_id>/cart", methods = ["POST"])
@flask_login.login_required
def add_to_cart(product_id):
    quantity = request.form["quantity"]
    customer_id = flask_login.current_user.id

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"""INSERT INTO 
                    `Cart` (`customer_id`, `product_id`, `quantity`) 
                   VALUES ('{customer_id}','{product_id}','{quantity}')
                   ON DUPLICATE KEY UPDATE 
                        'quantity' = 'quantity' + {quantity}
                   """)
                 
    cursor.close()
    conn.close()
    return redirect('/cart')
    
@app.route("/signup", methods=["POST", "GET"])
def signuppage():
    if flask_login.current_user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":

            name = request.form["name"]
            username = request.form["username"]
            password = request.form["pass"]
            confirmpassword = request.form["confirmpass"]
            email = request.form["email"]
            address = request.form["address"]
            conn = connect_db()
            cursor = conn.cursor()
            if len(password) < 8:
                flash("Password contains less than 8 characters")
            if confirmpassword != password:
                flash("The passwords don't match")
            else:
                try:
                    cursor.execute(f"""
                    INSERT INTO `Customer` 
                        (`name`, `username`, `password`, `email`, `address`)
                    VALUE
                        ('{name}', '{username}', '{password}', '{email}', '{address}');
                    """)
                except pymysql.err.IntegrityError:
                    flash("Username/Email is already in use")
                else:    
                    return redirect("/signin") 
                finally:
                    cursor.close()
                    conn.close()
        return render_template("signup.html.jinja")
    

@app.route("/signin", methods=["POST", "GET"])
def signinpage():
    if flask_login.current_user.is_authenticated:
        return redirect("/browse")
    else:
        if request.method == "POST":
            username = request.form['username'].strip()
            password = request.form['password']

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}';")
            
            result = cursor.fetchone()

            if result is None: 
                flash("Your username/password is incorrect")
            elif password != result["password"]:
                flash("Your username/password is incorrect")
            else: 
                user = User(result["id"], result["username"], result["email"], result["name"])

                flask_login.login_user(user)

                return redirect('/')

       
    return render_template("signin.html.jinja")


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')

@app.route("/cart")
@flask_login.login_required
def add_cart():
    conn = connect_db()
    cursor = conn.cursor()

    customer_id = flask_login.current_user.id

    cursor.execute(f"""SELECT `name`, `price`, `quantity`, `image`, `product_id`, `Cart`.`id`
    FROM 'Cart' JOIN `Product` ON `product_id` = `Product`.`id`
    WHERE `customer_id` = {customer_id};""")

    results = cursor.fetchall()

    total = 0 
    for products in results:

        quantity = products["quantity"]
        price = products["price"]
        item_total = quantity * price
        total = item_total + total

    cursor.close()      
    conn.close()

    return render_template("cart.html.jinja", products=results)

@app.route("/cart/<cart_id>/del", methods = ["POST"])
@flask_login.login_required
def delete(cart_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM 'Cart' WHERE 'id' ={cart_id};")
    cursor.close()
    conn.close()
    return redirect("/cart")

@app.route("/cart/<cart_id>/update", methods = ["POST"])
@flask_login.login_required
def update(cart_id):
    quantity = request.form["UPDATE"]
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE 'Cart' SET 'quantity' = {'quantity'} WHERE 'id'={cart_id};")
    cursor.close()
    conn.close()
    return redirect("/cart")

@app.route("/checkout")
@flask_login.login_required
def add_checkout():
    conn = connect_db()
    cursor = conn.cursor()
    
    customer_id = flask_login.current_user.id

    cursor.execute(f""" SELECT 
            `product`, 
            `price`, 
            `quantity`, 
            `image`, 
            `product_id`, 
            `Cart`.`id` 
        FROM `Cart` JOIN `Product` ON `product_id` = `Product`.`id` 
        WHERE `customer_id` = {customer_id};""")

    results = cursor.fetchall()

    if len(results) > 0:

        total=0
        for products in results:
            quantity = products["quantity"]
            price = products["price"]
            item_total = quantity * price
            total = item_total + total

        cursor.close()      
        conn.close()

        return render_template("checkout.html.jinja", total=total, products=results)
    else:
        return redirect("/cart")
    
@app.route("/sales", methods = ["POST"])
def sales():
    conn = connect_db()
    cursor = conn.cursor()

    customer_id = flask_login.current_user.id

    address = request.form["address"]
    payment = request.form["payment"]

    cursor.execute(f"""
                   INSERT INTO `Sale`
                      (`address`, `payment`, `customer_id`)
                   VALUES
                      ('{address}', '{payment}', '{customer_id}');
                   """)
    
    sale_id = cursor.lastrowid

    cursor.execute(f""" SELECT * FROM `Cart` WHERE `customer_id` = {customer_id};""")
    
    results = cursor.fetchall()

    for products in results:
        product_id = products["product_id"]
        quantity = products["quantity"]
        cursor.execute(f""" 
                        INSERT INTO `SaleProduct`
                            (`product_id`, `quantity`, `sale_id`)
                        VALUES
                            ('{product_id}','{quantity}', '{sale_id}');
                       """)
    cursor.execute(f"DELETE FROM `Cart` WHERE `customer_id` = '{customer_id}';")
    cursor.close()
    conn.close()
    return redirect("/thank_you")


@app.route("/thank_you")
@flask_login.login_required
def thank_you(): 
    return render_template("thank_you.html.jinja")


@app.route("/product/<product_id>/reviews", methods = ["POST"])
@flask_login.login_required
def update_reviews(product_id):
    comments = request.form("comments")
    ratings = request.form("ratings")

    conn = connect_db()
    cursor = conn.cursor()

    customer_id = flask_login.current_user.id


    cursor.execute(f"""INSERT INTO 
                    `Reviews`(`customer_id`, `product_id`, `comments`, `ratings`) 
                   VALUES ("{customer_id}","{product_id}","{comments}", "{ratings}")
                   ON DUPLICATE KEY UPDATE 
                   `comments` = "{comments}"
                   `ratings` = "{ratings}"
                   """)
                    
    
    results = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("product.html.jinja", product=results)                 


@app.route("/salehistory")
 
def sale_history(sale_id):
    conn = connect_db()
    cursor = conn.cursor()
    
    customer_id = flask_login.login_required

    cursor.execute(f"""
            SELECT * FROM `Sale` WHERE `customer_id` = "{customer_id}" """)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("salehistory.html.jinja", sales=results)

@app.route("/sale_history/<sale_id>")
@flask_login.login_required
def pastorders(sale_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT 
            `product`, 
            `price`, 
            `quantity`, 
            `image`, 
            `product_id`, 
            `SaleProduct`.`id` 
        FROM `SaleProduct` 
        JOIN `Product` ON `product_id` = `Product`.`id` 
        WHERE `sale_id` = {sale_id};""")

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("past_user_order.html.jinja", products = results)





