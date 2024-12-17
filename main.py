from flask import Flask, render_template, request
import pymysql 
from dynaconf import Dynaconf

app = Flask(__name__)
conf = Dynaconf(
    settings_file = ["settings.toml"]
    
)

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
    return render_template("product.html.jinja", product = result)
    
@app.route("/signup")
def signuppage():
    return render_template("signup.html.jinja")