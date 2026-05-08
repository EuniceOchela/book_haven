# services/payment.py
import requests
import os
from flask import current_app, url_for
from app.models import Order, Cart, OrderItem
from app import db

def initialize_flutterwave_payment(payment_data, order_id):
    """Initialize payment with Flutterwave"""
    url = "https://api.flutterwave.com/v3/payments"

    headers = {
        "Authorization": f"Bearer {current_app.config['FLW_SECRET_KEY']}",
        "Content-Type": "application/json"
    }

    payload = {
        "tx_ref": payment_data['tx_ref'],
        "amount": payment_data['amount'],
        "currency": payment_data.get('currency', "NGN"),
        "redirect_url": url_for('checkout.callback', _external=True),
        "customer": {
            "email": payment_data['customer']['email'],
            "name": payment_data['customer'].get('name', 'Customer')
        },
        "customizations": {
            "title": payment_data['customizations'].get('title', 'Book Haven'),
            "description": payment_data['customizations'].get('description', 'Book Purchase'),
            "logo": "https://yourdomain.com/static/images/logo.png"
        },
        "meta": {
            "order_id": order_id
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('status') == 'success':
            return response_data['data']['link']  # Flutterwave checkout URL
        else:
            print("Flutterwave Error:", response_data)
            return None

    except Exception as e:
        print("Flutterwave Payment Error:", str(e))
        return None


from flask import request, redirect, url_for, flash
from flask_login import current_user
from datetime import datetime

# @payment_bp.route("/verify")
def verify_payment():
    transaction_id = request.args.get("transaction_id")
    status = request.args.get("status")
    tx_ref = request.args.get("tx_ref")

    if not transaction_id or status != "successful":
        flash("Payment was not successful.", "danger")
        return redirect(url_for("books.cart"))

    verified_data = verify_flutterwave_payment(transaction_id)

    if not verified_data:
        flash("Unable to verify payment.", "danger")
        return redirect(url_for("books.cart"))

    # Flutterwave core data
    flw_tx_id = str(verified_data.get("id", ""))
    tx_ref = verified_data.get("tx_ref")
    amount = verified_data.get("amount", 0)
    currency = verified_data.get("currency")
    payment_status = verified_data.get("status")
    payment_type = verified_data.get("payment_type")

    # Customer details
    customer = verified_data.get("customer", {}) or {}
    customer_name = customer.get("name")
    customer_email = customer.get("email")
    customer_phone = customer.get("phone_number")

    # Metadata (best place for delivery details)
    meta = verified_data.get("meta", {}) or {}
    delivery_address = meta.get("delivery_address")
    delivery_city = meta.get("delivery_city")
    delivery_state = meta.get("delivery_state")
    delivery_country = meta.get("delivery_country")

    # Avoid duplicate order creation
    existing_order = Order.query.filter(
        (Order.flutterwave_transaction_id == flw_tx_id) |
        (Order.payment_reference == tx_ref)
    ).first()

    if existing_order:
        flash("Payment already verified for this order.", "info")
        return redirect(url_for("books.payment_success"))

    # Create order
    order = Order(
        user_id=current_user.id if current_user.is_authenticated else None,
        created_at=datetime.utcnow(),
        order_status="pending",

        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,

        delivery_address=delivery_address,
        delivery_city=delivery_city,
        delivery_state=delivery_state,
        delivery_country=delivery_country,

        total_amount=amount,
        amount_paid=amount,
        payment_reference=tx_ref,
        flutterwave_transaction_id=flw_tx_id,
        payment_processor="flutterwave",
        payment_status=payment_status,
        payment_currency=currency,
        payment_method=payment_type
    )

    db.session.add(order)
    db.session.flush()  # get order.id before adding items

    # Save purchased books from cart
    cart_items = Cart.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []

    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            book_title=cart_item.book.title,
            quantity=cart_item.quantity
        )
        db.session.add(order_item)

    # Clear cart after successful payment
    for cart_item in cart_items:
        db.session.delete(cart_item)

    db.session.commit()

    flash("Payment verified successfully.", "success")
    return redirect(url_for("books.payment_success"))


import os
import requests

def verify_flutterwave_payment(transaction_id):
    secret_key = os.getenv("FLW_SECRET_KEY")

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }

    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"

    response = requests.get(url, headers=headers)
    data = response.json()

    print("Flutterwave verify response:", data)
    return data