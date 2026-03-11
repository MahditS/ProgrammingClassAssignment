# Scenario: Mini Shop Ordering System
# Program summary: Lets a user add items to a shopping cart, view the cart, and checkout. Also allows a user to login as admin (password 1234) and add new items to the menu
# Datatypes used: int, float, str, bool, list
# Validation: menu choice validation, quantity validation, empty name validation

from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def create_app():
    app = Flask(__name__)
    return app

#This code creates a map for the menu, containing a list of names and prices
menu = {
    "Burger": 5.99,
    "Pizza": 8.49,
    "Fries": 3.49,
    "Soda": 1.99
}

#creates an empty cart that the user can fill
cart = []

#renders the home page html file, and passes in our pre set menu
@app.route("/")
def home():
    return render_template("index.html", menu=menu)

#allows a user to login with the password "1234"
@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("passcode")
    if password == "1234":
        return render_template("admin.html")
    else:
        return redirect("/")

#allows a admin user to add an item to the menu
@app.route("/addMenu", methods=["POST"])
def addMenu():
    itemName = request.form.get("itemName")
    price = request.form.get("price")

    menu[itemName] = round(float(price),2)

    return redirect("/")

#allows a regular user to add items to the cart
@app.route("/add", methods=["POST"])
def add_item():
    item = request.form.get("item")
    quantity = request.form.get("quantity")

    # Validation
    if not quantity.isdigit():
        return redirect("/")

    quantity = int(quantity)

    if quantity <= 0:
        return redirect("/")

    price = menu[item]
    total = price * quantity

    cart.append({
        "name": item,
        "quantity": quantity,
        "price": price,
        "total": total
    })

    return redirect("/cart")


#renders the cart page and what is inside it
@app.route("/cart")
def view_cart():
    total_cost = sum(item["total"] for item in cart)
    tax = round(0.12 * total_cost,2)
    final_cost = round(total_cost + tax,2)
    return render_template("cart.html", cart=cart, total=total_cost, tax=tax, final_cost=final_cost)

#the checkout action, redirecting to the checkout page and calculating sums
@app.route("/checkout", methods=["POST"])
def checkout():
    name = request.form.get("name")

    if name.strip() == "":
        return redirect("/cart")

    total_cost = round(sum(item["total"] for item in cart), 2)
    tax = round(0.12 * total_cost, 2)
    final_cost = round(total_cost + tax, 2)

    cart.clear()

    return render_template("checkout.html", name=name, total=total_cost, tax=tax, final_cost=final_cost)

if __name__ == "__main__":
    app.run(debug=True)