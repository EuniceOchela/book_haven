# routes/downloads.py
from flask import Blueprint, send_file, abort, redirect, url_for
from flask_login import login_required, current_user
from app.models import DownloadLink, Book
from datetime import datetime

downloads_bp = Blueprint('downloads', __name__)

@downloads_bp.route('/pdf/<token>')
@login_required
def download_pdf(token):
    download_link = DownloadLink.query.filter_by(token=token).first()

    if not download_link:
        abort(404)

    if download_link.is_used:
        flash("This download link has already been used.", "danger")
        return redirect(url_for('main.home'))

    if download_link.expires_at and download_link.expires_at < datetime.utcnow():
        flash("This download link has expired.", "danger")
        return redirect(url_for('main.home'))

    # Mark as used
    download_link.is_used = True
    download_link.used_at = datetime.utcnow()
    db.session.commit()

    book = Book.query.get(download_link.book_id)
    if not book or not book.pdf_file_path:
        abort(404)

    try:
        return send_file(
            book.pdf_file_path,
            as_attachment=True,
            download_name=f"{book.title}.pdf"
        )
    except Exception as e:
        abort(500)