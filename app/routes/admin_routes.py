from flask import redirect, render_template, session, abort, request, url_for, flash, Blueprint
from flask_login import current_user
from app.extensions import db
from app.utils import check_admin
from app.forms import DummyForm
from app.models import Users, Project

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/add_admin_ip')
def add_admin_new_ip():
    from app import db

    if not current_user.is_authenticated:
        flash('Необходимо авторизоваться, чтобы получить права админа.', 'warning')
        return redirect(url_for('auth.login'))  

    if current_user.status == 1:
        flash('Пользователь уже админ!', 'info')
        return redirect(url_for('project_new.index'))
    else:
        current_user.status = 1
        db.session.commit()
        flash(f'Пользователь {current_user.staff_number} назначен администратором.', 'success')
        return redirect(url_for('project_new.index'))

@admin_bp.route('/admin_panel')
def admin_panel():

    if current_user.is_authenticated:
        user = current_user
        is_admin = check_admin(user)
    else:
        abort(403)

    if not is_admin:
        abort(403)

    form = DummyForm()
    
    users = Users.query.all()
    projects = Project.query.all()

    return render_template('admin/admin_panel.html', 
                           is_admin=is_admin, 
                           user=user, 
                           form=form,
                           users=users,
                           projects=projects
                           )

@admin_bp.route('/add_admin/<int:user_id>', methods=['GET', 'POST'])
def add_admin(user_id):

    if current_user.status != 1:
        abort(403)
    
    user = Users.query.filter_by(id=user_id).first()

    if user:
        user.status = 1
        db.session.commit()
        flash(f'Пользователь {user.full_name} получил права админа!', 'success')
    else:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin_unset/<int:user_id>', methods=['GET', 'POST'])
def admin_unset(user_id):
    
    if current_user.status != 1:
        abort(403)

    user = Users.query.filter_by(id=user_id).first()

    if user:
        user.status = 0
        db.session.commit()
        flash(f'Пользователь {user.full_name} больше не админ!', 'warning')
    else:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/user_delete/<int:user_id>', methods=['GET', 'POST'])
def user_delete(user_id):
    
    if current_user.status != 1:
        abort(403)

    user = Users.query.filter_by(id=user_id).first()

    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.full_name} удален из БД!', 'info')
    else:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/project_delete/<int:project_id>', methods=['GET', 'POST'])
def project_delete(project_id):
    
    if current_user.status != 1:
        abort(403)

    project = Project.query.filter_by(id=project_id).first()

    if project:
        db.session.delete(project)
        db.session.commit()
        flash(f'Проект {project.title} удален из БД!', 'info')
    else:
        flash('Проект не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/project_back/<int:project_id>', methods=['GET', 'POST'])
def project_back(project_id):
    
    if current_user.status != 1:
        abort(403)

    project = Project.query.filter_by(id=project_id).first()

    if project:
        project.status = 'В работе'
        db.session.commit()
        flash(f'Проект {project.title} вернут в работу!', 'info')
    else:
        flash('Проект не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/project_close/<int:project_id>', methods=['GET', 'POST'])
def project_close(project_id):
    
    if current_user.status != 1:
        abort(403)

    project = Project.query.filter_by(id=project_id).first()

    if project:
        project.status = 'Завершен'
        db.session.commit()
        flash(f'Проект {project.title} закрыт!', 'info')
    else:
        flash('Проект не найден', 'danger')
        return redirect(url_for('admin.admin_panel'))
    
    return redirect(url_for('admin.admin_panel'))