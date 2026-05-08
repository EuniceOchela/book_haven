# routes/checkout.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from app.models import db, Cart, CartItem, Order, OrderItem, DeliveryAddress, DownloadLink
from app.services.payment import initialize_flutterwave_payment, verify_flutterwave_payment
from datetime import datetime
import secrets

checkout_bp = Blueprint('checkout', __name__)


@checkout_bp.route('/process', methods=['POST', 'GET'])
@login_required
def process():
    cart_id = session.get('cart_id')
    if not cart_id:
        flash("Cart not found", "danger")
        return redirect(url_for('cart.view'))

    cart = Cart.query.get(cart_id)
    if not cart:
        flash("Cart not found", "danger")
        return redirect(url_for('cart.view'))

    # attach guest cart to current user
    cart.user_id = current_user.id
    db.session.commit()

    items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not items:
        flash("Your cart is empty", "warning")
        return redirect(url_for('cart.view'))

    total = sum(item.quantity * item.unit_price for item in items)

    order = Order(
        user_id=current_user.id,
        total_amount=total,
        payment_status='pending',
        order_status='pending'
    )
    db.session.add(order)
    db.session.flush()

    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            book_id=item.book_id,
            format_type=item.format_type,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.quantity * item.unit_price
        )
        db.session.add(order_item)

        if item.format_type == 'pdf':
            download_link = DownloadLink(
                user_id=current_user.id,
                book_id=item.book_id,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow()
            )
            db.session.add(download_link)

    if any(item.format_type == 'hardcopy' for item in items):
        delivery = DeliveryAddress(
            order_id=order.id,
            full_name=request.form.get('full_name'),
            phone_number=request.form.get('phone'),
            email=request.form.get('email'),
            country=request.form.get('country'),
            state=request.form.get('state'),
            city=request.form.get('city'),
            street_address=request.form.get('street_address'),
            postal_code=request.form.get('postal_code')
        )
        db.session.add(delivery)

    db.session.commit()

    payment_data = {
        'tx_ref': f"BOOKHAVEN-{order.id}-{secrets.token_hex(8)}",
        'amount': str(total),
        'currency': "NGN",
        'customer': {
            'email': current_user.email,
            'name': current_user.full_name or "Customer"
        },
        'customizations': {
            'title': "Book Haven Purchase",
            'description': "Payment for books"
        }
    }

    payment_url = initialize_flutterwave_payment(payment_data, order.id)

    if payment_url:
        return redirect(payment_url)

    flash("Payment initialization failed. Please try again.", "danger")
    return redirect(url_for('checkout.index'))
    

@checkout_bp.route('/callback')
def callback():
    tx_ref = request.args.get('tx_ref')
    status = request.args.get('status')
    transaction_id = request.args.get('transaction_id')

    if status == 'successful' and transaction_id:
        transaction = verify_flutterwave_payment(transaction_id)

        if transaction and transaction.get('status') == 'success':
            data = transaction.get('data', {})

            if data.get('status') == 'successful' and data.get('tx_ref') == tx_ref:
                order = Order.query.filter_by(flutterwave_ref=tx_ref).first()

                if order:
                    order.payment_status = 'paid'
                    order.order_status = 'processing'

                    # empty cart
                    cart_id = session.get('cart_id')
                    if cart_id:
                        cart = Cart.query.get(cart_id)
                        if cart:
                            CartItem.query.filter_by(cart_id=cart.id).delete()
                            db.session.delete(cart)
                        session.pop('cart_id', None)

                    db.session.commit()

                    flash("Payment successful! Thank you for your purchase.", "success")
                    return redirect(url_for('main.home'))

    flash("Payment verification failed or was cancelled.", "danger")
    return redirect(url_for('cart.view'))

@checkout_bp.route('/')
@login_required
def index():
    cart_id = session.get('cart_id')
    if not cart_id:
        flash("Cart not found", "danger")
        return redirect(url_for('cart.view'))

    cart = Cart.query.get(cart_id)
    if not cart:
        flash("Cart not found", "danger")
        return redirect(url_for('cart.view'))

    items = CartItem.query.filter_by(cart_id=cart.id).all()
    if not items:
        flash("Your cart is empty", "warning")
        return redirect(url_for('cart.view'))

    has_hardcopy = any(item.format_type == 'hardcopy' for item in items)
    total = sum(item.quantity * item.unit_price for item in items)

    return render_template(
        'checkout/index.html',
        items=items,
        total=total,
        has_hardcopy=has_hardcopy
    )