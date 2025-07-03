from flask import redirect, render_template, session, abort, request, url_for, flash, Blueprint
from flask_login import current_user
from app.extensions import db
from app.utils import check_admin
from app.forms import DummyForm
from app.models import Users, Project
from app.logging import logger

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/add_admin_ip')
def add_admin_new_ip():
    """
    Назначает текущего пользователя администратором (если ещё не админ).
    """
    if not current_user.is_authenticated:
        flash('Необходимо авторизоваться, чтобы получить права админа.', 'warning')
        return redirect(url_for('auth.login'))  

    if current_user.status == 1:
        flash('Пользователь уже админ!', 'info')
        return redirect(url_for('project_new.index'))

    current_user.status = 1
    db.session.commit()
    flash(f'Пользователь {current_user.staff_number} назначен администратором.', 'success')
    logger.info(f"Пользователь {current_user.staff_number} стал админом")
    return redirect(url_for('project_new.index'))

@admin_bp.route('/admin_panel')
def admin_panel():
    """
    Отображает админ-панель со списком пользователей и проектов.
    """
    if not current_user.is_authenticated or not check_admin(current_user):
        abort(403)

    form = DummyForm()
    users = Users.query.all()
    projects = Project.query.all()

    return render_template(
        'admin/admin_panel.html',
        is_admin=True,
        user=current_user,
        form=form,
        users=users,
        projects=projects
    )

@admin_bp.route('/add_admin/<int:user_id>', methods=['POST'])
def add_admin(user_id):
    """
    Назначает выбранного пользователя администратором.
    """
    if current_user.status != 1:
        abort(403)

    user = Users.query.filter_by(id=user_id).first()
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))

    user.status = 1
    db.session.commit()
    flash(f'Пользователь {user.full_name} получил права админа!', 'success')
    logger.info(f"Назначен админ: {user.full_name} ({user.staff_number})")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin_unset/<int:user_id>', methods=['POST'])
def admin_unset(user_id):
    """
    Снимает с пользователя права администратора.
    """
    if current_user.status != 1:
        abort(403)

    user = Users.query.filter_by(id=user_id).first()
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))

    if user.id == current_user.id:
        flash('Вы не можете удалить или снять права с самого себя.', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    user.status = 0
    db.session.commit()
    flash(f'Пользователь {user.full_name} больше не админ!', 'warning')
    logger.info(f"Снят админ: {user.full_name} ({user.staff_number})")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/user_delete/<int:user_id>', methods=['POST'])
def user_delete(user_id):
    """
    Удаляет пользователя из базы данных.
    """
    if current_user.status != 1:
        abort(403)
    
    user = Users.query.filter_by(id=user_id).first()
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))

    if user.id == current_user.id:
        flash('Вы не можете удалить или снять права с самого себя.', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.full_name} удалён!', 'info')
    logger.info(f"Удалён пользователь: {user.full_name} ({user.staff_number})")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/project_delete/<int:project_id>', methods=['POST'])
def project_delete(project_id):
    """
    Удаляет проект из базы данных.
    """
    if current_user.status != 1:
        abort(403)

    project = Project.query.filter_by(id=project_id).first()
    if not project:
        flash('Проект не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))

    db.session.delete(project)
    db.session.commit()
    flash(f'Проект {project.title} удалён!', 'info')
    logger.info(f"Удалён проект: {project.title} (ID: {project.id})")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/project_back/<int:project_id>', methods=['POST'])
def project_back(project_id):
    """
    Возвращает проект в статус 'В работе'.
    """
    if current_user.status != 1:
        abort(403)

    project = Project.query.filter_by(id=project_id).first()
    if not project:
        flash('Проект не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))

    project.status = 'В работе'
    db.session.commit()
    flash(f'Проект {project.title} возвращён в работу!', 'info')
    logger.info(f"Проект восстановлен в работе: {project.title} (ID: {project.id})")
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/project_close/<int:project_id>', methods=['POST'])
def project_close(project_id):
    """
    Переводит проект в статус 'Завершен'.
    """
    if current_user.status != 1:
        abort(403)

    project = Project.query.filter_by(id=project_id).first()
    if not project:
        flash('Проект не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))

    project.status = 'Завершен'
    db.session.commit()
    flash(f'Проект {project.title} закрыт!', 'info')
    logger.info(f"Проект завершён: {project.title} (ID: {project.id})")
    return redirect(url_for('admin.admin_panel'))