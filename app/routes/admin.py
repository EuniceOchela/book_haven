# routes/admin.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Book, Order, User, Advertisement, DeliveryAddress
from app import db
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload, selectinload
import os
from flask import abort



admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def restrict_to_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("Access denied. Admin only.", "danger")
        return redirect(url_for('main.home'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    total_books = Book.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(order_status='pending').count()
    if not current_user.is_admin:
        abort(403)

    return render_template('admin/dashboard.html',
                           total_books=total_books,
                           total_orders=total_orders,
                           pending_orders=pending_orders)

@admin_bp.route('/manage-books')
@login_required
def manage_books():
    books = Book.query.all()
    return render_template('admin/manage_books.html', books=books)


@admin_bp.route('/add-book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        year = request.form.get('year')
        description = request.form.get('description')
        pdf_price = float(request.form.get('pdf_price', 0) or 0)
        hardcopy_price = float(request.form.get('hardcopy_price', 0) or 0)

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            year_of_publication=year,
            description=description,
            pdf_price=pdf_price,
            hardcopy_price=hardcopy_price,
            is_featured=request.form.get('is_featured') == 'on'
        )

        covers_dir = os.path.join('app', 'static', 'uploads', 'covers')
        pdfs_dir = os.path.join('app', 'static', 'uploads', 'pdfs')

        os.makedirs(covers_dir, exist_ok=True)
        os.makedirs(pdfs_dir, exist_ok=True)

        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename:
            filename = secure_filename(cover_file.filename)
            cover_path = os.path.join(covers_dir, filename)
            cover_file.save(cover_path)
            book.cover_image = f'uploads/covers/{filename}'

        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename:
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(pdfs_dir, filename)
            pdf_file.save(pdf_path)
            book.pdf_file_path = f'uploads/pdfs/{filename}'

        db.session.add(book)
        db.session.commit()
        flash('Book added successfully', 'success')
        return redirect(url_for('admin.manage_books'))

    return render_template('admin/add_book.html')

@admin_bp.route('/orders')
@login_required
def manage_orders():
    orders = (
        Order.query
        .options(
            joinedload(Order.user),
            selectinload(Order.items)
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    return render_template('admin/manage_orders.html', orders=orders)

@admin_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
def mark_order_delivered(order_id):
    order = Order.query.get_or_404(order_id)
    order.order_status = 'delivered'
    db.session.commit()
    return redirect(url_for('admin.manage_orders'))


@admin_bp.route('/users')
@login_required
def manage_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/transactions')
@login_required
def manage_transactions():
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template('admin/manage_transactions.html', orders=orders)

@admin_bp.route('/adverts', methods=['GET', 'POST'])
@login_required
def advert():
    if request.method == 'POST':
        title = request.form.get('title')
        media_type = request.form.get('media_type')
        target_url = request.form.get('target_url')
        position = request.form.get('position')

        file = request.files.get('media_file')

        if not file or not file.filename:
            flash('Please upload an advert image or video.', 'danger')
            return redirect(url_for('admin.advert'))

        filename = secure_filename(file.filename)

        if media_type == 'image':
            upload_dir = os.path.join('app', 'static', 'uploads', 'adverts', 'images')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            media_url = f'uploads/adverts/images/{filename}'
        elif media_type == 'video':
            upload_dir = os.path.join('app', 'static', 'uploads', 'adverts', 'videos')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            media_url = f'uploads/adverts/videos/{filename}'
        else:
            flash('Invalid media type selected.', 'danger')
            return redirect(url_for('admin.advert'))

        advert = Advertisement(
            title=title,
            media_type=media_type,
            media_url=media_url,
            target_url=target_url,
            position=position
        )

        db.session.add(advert)
        db.session.commit()

        flash('Advert uploaded successfully.', 'success')
        return redirect(url_for('admin.advert'))

    adverts = Advertisement.query.order_by(Advertisement.id.desc()).all()
    return render_template('admin/advert.html', adverts=adverts)