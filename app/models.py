# app/models.py
from . import db
from flask_login import UserMixin
from datetime import datetime
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String(20))
        # ✅ ADD THIS
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # ✅ ADD THIS
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    isbn = db.Column(db.String(50), nullable=True)
    year_of_publication = db.Column(db.Integer, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)
    pdf_file_path = db.Column(db.String(255), nullable=True)
    pdf_price = db.Column(db.Float, default=0)
    hardcopy_price = db.Column(db.Float, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    format_type = db.Column(db.String(10), nullable=False)  # 'pdf' or 'hardcopy'
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)

    book = db.relationship('Book', backref='cart_items')

class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime, nullable=True)
    order_status = db.Column(db.String(50), default='pending')
    total_amount = db.Column(db.Float, default=0)
    customer_name = db.Column(db.String(150), nullable=True)
    customer_email = db.Column(db.String(150), nullable=True)
    customer_phone = db.Column(db.String(30), nullable=True)
    delivery_address = db.Column(db.Text, nullable=True)
    delivery_city = db.Column(db.String(100), nullable=True)
    delivery_state = db.Column(db.String(100), nullable=True)
    delivery_country = db.Column(db.String(100), nullable=True)
    payment_reference = db.Column(db.String(120), unique=True, nullable=True)
    payment_processor = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(50), nullable=True)
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    format_type = db.Column(db.String(10), nullable=False)   # 'pdf' or 'hardcopy'
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    book = db.relationship('Book', backref='order_items')

class DeliveryAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150))
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    street_address = db.Column(db.String(255), nullable=False)
    postal_code = db.Column(db.String(20))

class DownloadLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    is_used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='download_links')
    book = db.relationship('Book', backref='download_links')


class Advertisement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=True)
    media_type = db.Column(db.String(20), nullable=False)   # image or video
    media_url = db.Column(db.String(255), nullable=False)   # saved file path
    target_url = db.Column(db.String(255), nullable=False)  # link when clicked
    position = db.Column(db.String(20), nullable=False, default='left')  # left or right
    created_at = db.Column(db.DateTime, default=db.func.now())