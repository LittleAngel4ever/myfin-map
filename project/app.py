import webbrowser
import os
import credits as cr
from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta, datetime
from models_front import db
from models_back import Link
from logs import init_log_db
from cart import ExchangeMap
from update_data import update_data, set_update_date
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = cr.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = cr.accountDB
app.config['SQLALCHEMY_BINDS'] = {
    'portfolio': cr.portfolioDB,
    'logs': cr.logDB
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('show_main'))

@app.before_request
def check_session_inactivity():
    if 'username' in session:
        last_active = session.get('last_seen', 0)
        current_time = datetime.now().timestamp()
        if current_time - last_active > 1800:
            session.clear()
            return redirect(url_for('home'))
        session['last_seen'] = current_time

@app.route('/dashboard')
@app.route('/dashboard')
def show_main():

    return render_template('main.html')

@app.route('/api/parse', methods=['POST'])
def start_parsing():
    data = request.get_json()
    currency_code = data.get('currency', 'USD').upper()

    try:
        currency_link = getattr(Link, currency_code, Link.USD)
        def run_parser():
            try:
                update_data(currency_link)
                set_update_date()
            except Exception as e:
                print(f"[ERROR] Ошибка парсинга для {currency_code}: {e}")

        thread = threading.Thread(target=run_parser)
        thread.daemon = True
        thread.start()
        return jsonify({'success': True, 'message': 'Парсинг запущен'})
    except Exception as e:
        print(f"[ERROR] Ошибка при запуске парсинга: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/map', methods=['POST'])
def get_map():
    data = request.get_json()
    currency_code = data.get('currency', 'USD').upper()

    try:
        currency_link = getattr(Link, currency_code, Link.USD)
        exchange_map = ExchangeMap(currency=currency_link)
        exchange_map.build()
        map_html = exchange_map.get_html()
        return jsonify({'success': True, 'map_html': map_html})
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке карты для {currency_code}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/403')
def test_forbidden():
    abort(403)

@app.errorhandler(403)
def handle_forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def handle_not_found(error):
    return render_template('404.html'), 404


with app.app_context():
    db.create_all()
    init_log_db()

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)