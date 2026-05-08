# routes/cart.py
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from app.models import Book, Cart, CartItem, db

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/add/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    format_type = request.form.get('format_type') or request.args.get('format', 'pdf')

    book = Book.query.get_or_404(book_id)

    if 'cart_id' not in session:
        cart = Cart(user_id=None)
        db.session.add(cart)
        db.session.commit()
        session['cart_id'] = cart.id

    cart = Cart.query.get(session['cart_id'])

    item = CartItem.query.filter_by(
        cart_id=cart.id,
        book_id=book.id,
        format_type=format_type
    ).first()

    if item:
        if format_type == 'hardcopy':
            item.quantity += 1
            flash(f"{book.title} quantity updated in your cart", "info")
        else:
            flash(f"{book.title} is already in your cart", "info")
    else:
        price = book.pdf_price if format_type == 'pdf' else book.hardcopy_price

        item = CartItem(
            cart_id=cart.id,
            book_id=book.id,
            format_type=format_type,
            quantity=1,
            unit_price=price
        )

        db.session.add(item)
        flash(f"{book.title} has been added to your cart", "success")

    db.session.commit()

    cart_count = db.session.query(db.func.sum(CartItem.quantity)).filter_by(
        cart_id=cart.id
    ).scalar() or 0

    session['cart_count'] = cart_count

    return redirect(url_for('main.home'))

@cart_bp.route('/')
def view():
    if 'cart_id' not in session:
        return render_template('cart.html', items=[], total=0)

    cart = Cart.query.get(session['cart_id'])
    items = CartItem.query.filter_by(cart_id=cart.id).all()

    total = sum(item.quantity * item.unit_price for item in items)

    return render_template('cart.html', items=items, total=total)

@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'cart_id' not in session:
        flash("No active cart", "warning")
        return redirect(url_for('cart.view'))

    cart = Cart.query.get(session['cart_id'])

    item = CartItem.query.filter_by(
        id=item_id,
        cart_id=cart.id
    ).first()

    if not item:
        flash("Item not found", "danger")
        return redirect(url_for('cart.view'))

    db.session.delete(item)
    db.session.commit()

    flash("Item removed from cart", "success")
    return redirect(url_for('cart.view'))