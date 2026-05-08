# routes/books.py
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from app.models import Book
from app import db

books_bp = Blueprint('books', __name__)
admin_bp = Blueprint('admin', __name__)

@books_bp.route('/books')
def books_page():
    featured_books = Book.query.filter_by(is_featured=True).order_by(Book.id.desc()).all()
    books = Book.query.filter_by(is_featured=False).order_by(Book.id.desc()).all()

    return render_template('books/home.html', featured_books=featured_books, books=books)

@books_bp.route('/')
def list_books():
    books = Book.query.filter_by(is_active=True).all()
    return render_template('books.html', books=books)

@books_bp.route('/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('books_detail.html', book=book)

@books_bp.route('/manage-books')
def manage_books():
    books = Book.query.order_by(Book.id.desc()).all()
    return render_template('admin/manage_books.html', books=books)

@books_bp.route('/delete-book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.', 'success')
    return redirect(url_for('books.manage_books'))

@books_bp.route('/edit-book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.description = request.form.get('description')
        book.isbn = request.form.get('isbn')
        book.year_of_publication = request.form.get('year_of_publication') or None
        book.pdf_price = request.form.get('pdf_price') or 0
        book.hardcopy_price = request.form.get('hardcopy_price') or 0
        book.is_featured = True if request.form.get('is_featured') == 'on' else False

        db.session.commit()
        flash('Book updated successfully.', 'success')
        return redirect(url_for('admin.manage_books'))

    return render_template('admin/edit_book.html', book=book)