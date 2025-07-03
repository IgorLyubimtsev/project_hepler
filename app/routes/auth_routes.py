import random
import string
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db
from app.forms import LoginForm, RegisterForm, PasswordRecovery
from app.models import Users, Project
from app.utils import send_internal_mail
from app.logging import logger

auth_bp = Blueprint('auth', __name__)


def generate_code(length=6) -> str:
    """
    Генерирует случайный числовой код длиной length.
    """
    return ''.join(random.choices(string.digits, k=length))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Обработка страницы входа.
    Поддерживает два действия:
    - Авторизация по табельному номеру и коду подтверждения (verification_code).
    - Восстановление пароля (высылает код на почту).
    """
    form = LoginForm()
    recovery_form = PasswordRecovery()

    if current_user.is_authenticated:
        flash('Вы уже авторизованы, логиниться вам не нужно ;)', 'info')
        return redirect(url_for('project_new.index'))

    # Обработка логина
    if form.submit.data and form.validate_on_submit():
        staff_number = form.staff_number.data
        password = form.password.data

        user = Users.query.filter_by(staff_number=staff_number, verification_code=password).first()

        if user:
            login_user(user)
            user.is_verified = True
            db.session.commit()
            logger.info(f'Пользователь {user.staff_number} вошёл в систему')
            flash('Вы успешно вошли', 'success')
            return redirect(url_for('project_new.index'))
        else:
            flash('Ошибка авторизации, проверьте введенные данные.', 'danger')
            return redirect(url_for('auth.login'))

    # Обработка восстановления пароля
    if recovery_form.submit.data and recovery_form.validate_on_submit():
        user = Users.query.filter_by(staff_number=recovery_form.staff_number.data).first()

        if not user:
            flash('Ваш аккаунт не найден, проверьте введённый табельный номер или зарегистрируйтесь', 'warning')
            return redirect(url_for('auth.login'))
        else:
            send_internal_mail(user.email, f'Ваш логин: {user.staff_number} \nВаш код подтверждения: {user.verification_code}')
            logger.info(f'Отправлен код восстановления пользователю {user.staff_number} на почту {user.email}')
            flash('На вашу почту был выслан пароль', 'info')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html', form=form, recovery=recovery_form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации нового пользователя.
    Проверяет, что email и табельный номер не заняты.
    Генерирует и сохраняет код подтверждения.
    """
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

        # Проверка существования по email или табельному номеру
        existing_user = Users.query.filter(
            (Users.email == email) | (Users.staff_number == staff_number)
        ).first()

        if existing_user:
            flash('У вас уже есть аккаунт! Если забыли пароль, можете его восстановить', 'danger')
            return redirect(url_for('auth.login'))

        # Создаем нового пользователя
        user = Users(
            full_name=full_name,
            staff_number=staff_number,
            department=department,
            position=position,
            email=email,
            verification_code=code,
            is_verified=False
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f'Зарегистрирован новый пользователь: {staff_number} ({email})')

        send_internal_mail(email, f'Ваш логин: {staff_number} \nВаш код подтверждения: {code}')
        logger.debug(f'Код подтверждения для {staff_number}: {code}')

        flash('Регистрация успешна! Проверьте почту для получения кода подтверждения.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """
    Отображает профиль текущего пользователя и проекты, созданные им.
    """
    user_status = 'Пользователь' if current_user.status == 0 else 'Администратор'
    users_projects = Project.query.filter_by(creator=current_user.id).all()

    return render_template(
        'auth/profile.html',
        user_staff_number=current_user.staff_number,
        user_email=current_user.email,
        user_full_name=current_user.full_name,
        user_department=current_user.department,
        user_position=current_user.position,
        user_status=user_status,
        users_projects=users_projects
    )

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Выход пользователя из системы.
    Обнуляет флаг is_verified и очищает сессию.
    """
    current_user.is_verified = False
    db.session.commit()
    logger.info(f'Пользователь {current_user.staff_number} вышел из системы')

    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.before_request
def check_user_verified():
    """
    Проверяет, что текущий пользователь подтверждён (is_verified).
    Если нет — выкидывает из сессии и перенаправляет на логин.
    Игнорирует статику и метод POST.
    """
    if request.endpoint == 'static':
        return
    if request.method == 'POST':
        return
    if current_user.is_authenticated and not current_user.is_verified:
        logout_user()
        session.clear()
        flash('Ваша сессия была сброшена администратором', 'warning')
        return redirect(url_for('auth.login'))