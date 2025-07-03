import random, string
from app.extensions import db
from app.forms import LoginForm, RegisterForm, PasswordRecovery
from flask import Blueprint, render_template, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user
from app.models import Users, Project
from app.utils import send_internal_mail

auth_bp = Blueprint('auth', __name__)

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    recovery_form = PasswordRecovery()

    if current_user.is_authenticated:
        flash('Вы уже авторизованы, логиниться вам не нужно ;)', 'info')
        return redirect(url_for('project_new.index'))
    
    if form.submit.data and form.validate_on_submit():

        staff_number = form.staff_number.data
        password = form.password.data

        user = Users.query.filter_by(staff_number=staff_number, verification_code=password).first()

        if user:
            # if user.is_verified:
            #     flash('Вы уже в системе', 'warning')
            #     return redirect(url_for('project_new.index'))
            # else:
                login_user(user)
                user.is_verified = True
                db.session.commit()
                flash('Вы успешно вошли', 'success')
                return redirect(url_for('project_new.index'))
        else:
            flash('Ошибка авторизации, проверьте введенные данные.', 'danger')
            return redirect(url_for('auth.login'))

    if recovery_form.submit.data and recovery_form.validate_on_submit():

        user = Users.query.filter_by(staff_number=recovery_form.staff_number.data).first()

        if not user:
            flash('Ваш аккаунт не найден, проверьте введеный табельный номер или зарегистрируетесь', "warning")
            return redirect(url_for('auth.login'))
        else:
            # send_internal_mail(user.email, f'Ваш логин: {user.staff_number} \n Ваш код подтверждения: {user.verification_code}')
            print(user.verification_code)
            flash('На вашу почту был выслан пароль', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html', form=form, recovery=recovery_form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        flash('Вы уже авторизованы, регистрация вам не нужна ^_^', 'info')
        return redirect(url_for('project_new.index'))
    
    form = RegisterForm()

    if form.validate_on_submit():

        full_name = form.full_name.data
        staff_number = form.staff_number.data
        department = form.department.data
        position = form.position.data
        email = form.email.data

        code = generate_code()

        if not Users.query.filter_by(email=email, staff_number=staff_number).first():

            # send_internal_mail(email, f'Ваш логин: {staff_number} \n Ваш код подтверждения: {code}')
            print(code)
        
            user = Users(
                full_name = full_name,
                staff_number = staff_number,
                department = department,
                position = position,
                email = email,
                verification_code = code,
                is_verified = False
            )

            db.session.add(user)
            db.session.commit()

            return redirect(url_for('auth.login'))
        
        else:
            flash('У вас уже есть аккаунт! Если забыли пароль, можете его восстановить', 'danger')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile', methods=['GET'])
def profile():

    if current_user.is_authenticated:
        
        user_email = current_user.email
        user_staff_number = current_user.staff_number
        user_department = current_user.department
        user_position = current_user.position
        user_full_name = current_user.full_name

        user_status = 'Пользователь' if current_user.status == 0 else 'Администратор'
        users_projects = Project.query.filter_by(creator=current_user.id).all()

    else:
        flash('Пожалуйста, авторизуйтесь', 'danger')
        return redirect(url_for('auth.login'))

    return render_template(
        'auth/profile.html', 
        user_staff_number=user_staff_number, 
        user_email=user_email,
        user_full_name=user_full_name,
        user_department=user_department,
        user_position=user_position,
        user_status=user_status,
        users_projects=users_projects
        )

@auth_bp.route('/logout')
def logout():
    current_user.is_verified = False
    db.session.commit()
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/check_users')
def check_users():
    users = Users.query.all()  # Получаем всех пользователей
    return render_template('auth/profile.html', users=users)

@auth_bp.before_request
def check_user_verified():
    if current_user.is_authenticated and not current_user.is_verified:
        logout_user()
        session.clear()
        flash('Ваша сессия была сброшена администратором', 'warning')
        return redirect(url_for('auth.login'))