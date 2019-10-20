import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from main_app.database import get_db


SECRET_KEY = generate_password_hash('12345')
auth_bp = Blueprint("auth", __name__, url_prefix="")


@auth_bp.route("/register", methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        print(request.form)
        register_type = request.form["register_type"]
        db = get_db()
        error = None
        if register_type != 'admin' and register_type != 'patient':
            error = 'please choose a correct type of user to register.'
            flash(error)
            return render_template('/auth/register.html')

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        password = request.form["password"]
        repeat_password = request.form["repeat_password"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]
        gender = request.form["gender"]
        if repeat_password != password:
            error = "two passwords are not the same."
            flash(error)
            return render_template('/auth/register.html')
        if register_type == "patient":
            height = request.form["height"]
            weight = request.form["weight"]
            data_of_birth = request.form["birthday"]
            emergency_contacts = request.form["emergency_contacts"]

            if not first_name:
                error = "first name is required."
            elif not last_name:
                error = "last name is required"
            elif not password:
                error = "password is required."
            elif not email:
                error = "email is required."
            elif not phone_number:
                error = "phone_number is required."
            elif not gender:
                error = "gender is required."
            elif not height:
                error = "height is required."
            elif not weight:
                error = "weight is required."
            elif not data_of_birth:
                error = "birthday is required."
            elif db.execute('SELECT id FROM patients WHERE email = ?', (email, )).fetchone() is not None:
                error = "Email {} has already registered.".format(email)

            if error is None:
                db.execute('INSERT INTO patients (last_name, first_name, password, email, phone_number, gender, height, weight, data_of_birth, emergency_contacts) VALUES '
                           '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (last_name, first_name, generate_password_hash(password), email, phone_number, gender, height, weight, data_of_birth, emergency_contacts)
                           )
                db.commit()
                return redirect(url_for("auth.login"))

            flash(error)

            # return render_template('auth/register.html')

        elif register_type == "admin":
            secret_key = request.form["secret_key"]

            if not check_password_hash(SECRET_KEY, secret_key):
                error = "Wrong key, validation failed."
            else:
                if not last_name:
                    error = "last_name is required."
                elif not first_name:
                    error = "first_name is required."
                elif not password:
                    error = "password is required."
                elif not email:
                    error = "email is required."
                elif not phone_number:
                    error = "phone_number is required."
                elif not gender:
                    error = "gender is required."
            if error is None:
                db.execute('INSERT INTO administrators (last_name, first_name, password, email, phone_number, gender) VALUES '
                           '(?, ?, ?, ?, ?, ?)',
                           (last_name, first_name, generate_password_hash(password), email, phone_number, gender)
                           )
                db.commit()

                return redirect(url_for('auth.login'))

            flash(error)

    return render_template('/auth/register.html')


@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        login_type = request.form['login_type']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        if login_type == 'patient':
            user = db.execute(
                'SELECT * FROM patients WHERE email = ?', (email,)
            ).fetchone()
        elif login_type == 'admin':
            user = db.execute(
                'SELECT * FROM administrators WHERE email = ?', (email,)
            ).fetchone()
        elif login_type == 'doctor':
            user = db.execute(
                'SELECT * FROM doctors WHERE email = ?', (email,)
            ).fetchone()
        else:
            error = 'Unknown type of user.'
            flash(error)
            return render_template('/auth/login.html')

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['login_type'] = login_type
            if login_type == 'admin':
                return redirect(url_for('admin.show_main'))
            elif login_type == 'patient':
                return redirect(url_for('patient.show_main', id=user['id']))
            else:
                return redirect(url_for('doctor.show_main'))

        flash(error)

    return render_template('/auth/login.html')


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    login_type = session.get('login_type')

    if user_id is None:
        g.user = None
    else:
        if login_type == 'admin':
            g.user = get_db().execute(
                'SELECT * FROM administrators WHERE id = ?', (user_id,)
            ).fetchone()
        elif login_type == 'patient':
            g.user = get_db().execute(
                'SELECT * FROM patients WHERE id = ?', (user_id,)
            ).fetchone()
        else:
            g.user = get_db().execute(
                'SELECT * FROM doctors WHERE id = ?', (user_id,)
            ).fetchone()


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('authentication.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('authentication.login'))

        return view(**kwargs)

    return wrapped_view
