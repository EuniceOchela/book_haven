# routes/main.py
from flask import Blueprint, render_template
from app.models import Book, Advertisement

main_bp = Blueprint('main', __name__)

from flask import request, render_template

from flask import request
from sqlalchemy import or_

@main_bp.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    per_page = 9

    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)

    # Featured books (unchanged)
    featured_books = (
        Book.query
        .filter_by(is_featured=True, is_active=True)
        .order_by(Book.id.desc())
        .limit(5)
        .all()
    )

    # Base query
    query = Book.query.filter_by(is_featured=False, is_active=True)

    # 🔍 Search by title or author
    if search_query:
        query = query.filter(
            or_(
                Book.title.ilike(f"%{search_query}%"),
                Book.author.ilike(f"%{search_query}%")
            )
        )

    # 📚 Filter by category
    if category_id:
        query = query.filter(Book.category_id == category_id)

    # Pagination
    pagination = query.order_by(Book.id.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    books = pagination.items

    # Adverts
    left_adverts = Advertisement.query.filter_by(position='left').order_by(Advertisement.id.desc()).all()
    right_adverts = Advertisement.query.filter_by(position='right').order_by(Advertisement.id.desc()).all()

    # Categories (needed for dropdown)
    # categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'home.html',
        featured_books=featured_books,
        books=books,
        pagination=pagination,
        # categories=categories,
        left_adverts=left_adverts,
        right_adverts=right_adverts,
    )