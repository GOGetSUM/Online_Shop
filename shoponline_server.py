from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, SubmitField,TextAreaField, IntegerField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
from django.contrib import messages
import collections
import os

#--------------SetUp App----------------------------------------------------------------

app = Flask(__name__)
#Secret Key for DB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap(app)

#-------------Connect DB-----------------------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL","sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#--------------Login Manager------------------------------------------------------------
# create a login manager
login_manager = LoginManager()
login_manager.init_app(app)
# create a user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#-------------Configure Databases-----------------------------------------------------------------
class Inventory(db.Model):
    __tablename__ = "Inventory"
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(250),unique=True, nullable=False)
    size= db.Column(db.String(250),nullable=False)
    price = db.Column(db.Float, nullable=False)
    product_desc = db.Column(db.Text,nullable=False)
    location= db.Column(db.String(250),nullable=False)
    inventory=db.Column(db.Integer,nullable=False)
    image=db.Column(db.String(250),nullable=True)

##CREATE TABLE IN DB for Users
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

# CreateTable for cart
class Cart(db.Model):
    __tablename__= 'cart'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer,nullable=False)
    product_id= db.Column(db.Integer,nullable=False)
    product_name= db.Column(db.String(100),nullable=False)
    prod_price = db.Column(db.Float, nullable=False)
    Tot_price = db.Column(db.Float, nullable=False)

db.create_all()

#-------------Create Record-----------------------------------------------------------------
new_product = Inventory(
    id=1,
    product_name='Dodgers Jacket',
    size='Large',
    price=74.99,
    product_desc="Don't miss out on this super swaggy find. Its in great conditions!",
    location='Long Beach',
    inventory=1,
)

# db.session.add(new_product)
# db.session.commit()

#-------------Admin Only function-----------------------------------------------------------------

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


#-------------Index Home-----------------------------------------------------------------
@app.route('/')
def home():
    #Retrieve all Product from Database to Build
    all_product = Inventory.query.order_by(Inventory.inventory.desc()).all()

    return render_template('index.html', all=all_product, logged_in=current_user.is_authenticated)

#-------------Index Login-----------------------------------------------------------------

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user =  User.query.filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


#-------------Index Register-----------------------------------------------------------------
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", logged_in=current_user.is_authenticated)

#-------------Index Add Products-----------------------------------------------------------------
#Add -  Product Form
class AddProductForm(FlaskForm):
    product_name= StringField('Product Name',validators=[DataRequired()])
    size= StringField('Size',validators=[DataRequired()])
    price = StringField('Price',validators=[DataRequired()])
    product_desc = TextAreaField('Description',validators=[DataRequired()])
    location= StringField('Location',validators=[DataRequired()])
    inventory=StringField('Inventory',validators=[DataRequired()])
    submit = SubmitField("Add Product")

#Add site
@app.route('/add', methods=["GET", "POST"])
@login_required
@admin_only
def add_product():
    #Call Add Product Form--------------
    form1= AddProductForm()
    #Retrieve Latest ID-----------------
    id_prev = Inventory.query.order_by(Inventory.id).all()
    id_new = len(id_prev)+1

    #on Form Acitvation(Submital)
    if form1.validate_on_submit():
        #new product-------------------
        new_product= Inventory(
            id=id_new,
            product_name=request.form['product_name'],
            size=request.form['size'],
            price=float(request.form['price']),
            product_desc=request.form['product_desc'],
            location=request.form['location'],
            inventory=int(request.form['inventory']))

        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template('add.html', form=form1)


#-------------Index Delete Products-----------------------------------------------------------------
@app.route('/delete', methods=["GET"])
@login_required
@admin_only
def delete():
    # Get Prod ID and DB Query
    prod_id = request.args.get('id')
    prod = Inventory.query.get(prod_id)

    db.session.delete(prod)
    db.session.commit()
    return redirect(url_for('home'))

#-------------Index Update Image-----------------------------------------------------------------

@app.route('/image')
@login_required
@admin_only
def image():
    # Get Prod ID and DB Query
    prod_id = request.args.get('id')
    prod = Inventory.query.get(prod_id)
    return render_template('image.html',id=prod_id)


@admin_only
@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    prod_id = request.args.get('id')
    prod = Inventory.query.get(prod_id)
    #uploader on post command
    fp = request.form['filepath']
    prod.image = fp
    db.session.commit()
    return redirect(url_for('home'))


#---------Index Log Out---------------------------------------------------------------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


#---------Index Cart---------------------------------------------------------------------
@app.route('/Cart')
@login_required
def cart():
    id = current_user.id
    cart__ = Cart.query.filter_by(profile_id=f'{id}').all()
    product_id =[]
    name =[]
    price = []
    tot_ =0
    product_info = Inventory.query.order_by('id').all()

    #Convert query into list
    for item in cart__:
        if item.profile_id == id:
            product_id.append(item.product_id)

    print(product_id)
    # remove duplicates from list
    seen = set()
    uniq_item = [x for x in product_id if x not in seen and not seen.add(x)]

    for item in uniq_item:
        catalog = Inventory.query.get(item)
        tot_ = float(tot_) + catalog.price
        price.append(catalog.price)
        name.append(catalog.product_name)

    total = round(tot_,2)
    cart_dictionary = {i: [j, k] for i, j, k in zip(uniq_item,name,price)}



    return render_template('Cart.html', cart=cart_dictionary, tot=total )


#---------Add to Cart---------------------------------------------------------------------

@app.route('/additem')
@login_required
def additem():
    prod_id = request.args.get('id')
    prod = Inventory.query.get(prod_id)

    id_prev = Cart.query.order_by(Cart.id).all()
    id_new = len(id_prev)+1

    prod_n_= prod.product_name
    price_ = prod.price
    prod_id_ = prod.id
    prof_id = current_user.id
    tot_ = price_*2

    new_item = Cart(
        id=id_new,
        profile_id= prof_id,
        product_id = prod_id_,
        prod_price = price_,
        Tot_price = tot_,
        product_name= prod_n_,
    )
    db.session.add(new_item)
    db.session.commit()

    return redirect('/')


#---------Remove from Cart---------------------------------------------------------------------

@app.route('/remove', methods=['GET'])
@login_required
def remove():
    item_id = request.args.get('cart_id')
    print(item_id)
    query_ =  Cart.query.filter_by(product_id=f'{item_id}').delete()
    db.session.commit()

    return redirect('/Cart')

#---------Payment Transaction---------------------------------------------------------------------

# Section for stripe functionability.

#---------Payment Transaction Completed-Remove Sold Items---------------------------------------------------------------------

def removeitems():
    id=current_user.id
    order_db = Cart.query.profile_id(id)

    for item_ in order_db:
        prod_id = item_.product_id
        prod = Inventory.query.get(prod_id)

        prod.inventory = 0

    item_.delete().where(item_.c.profile_id == f'{id}')
    return

#---------Run App---------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)