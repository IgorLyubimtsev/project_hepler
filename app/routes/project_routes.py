from app.extensions import db
from app.forms import CreateProjectForm, EditProjectForm, TechnicalExtensionForm
from app.models import Project, Users
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, abort
from flask_login import current_user, login_required
from collections import Counter
from app.utils import check_admin, send_internal_mail
from datetime import date
from app.logging import logger

project_bp = Blueprint('project_new', __name__)

def can_be_completed(project):
    """
    Проверяет, заполнены ли все обязательные поля для завершения проекта.
    Если есть незаполненные поля, выводит flash с их списком.
    
    Args:
        project (Project): экземпляр проекта для проверки.
    
    Returns:
        bool: True, если все обязательные поля заполнены, иначе False.
    """
    required_fields = [
        'project_number',
        'rating_id',
        'title',
        'project_type',
        'curator',
        'product_owner',
        'team',
        'deadline',
        'agile_open_date',
        'open_protocol',
        'agile_close_date',
        'close_protocol',
        'base_bank'
    ]

    mapping = {
        'project_number' : 'Номер проекта',
        'rating_id':'ID проекта в рейтинге ТБ',
        'title':'Название проекта',
        'project_type':'Тип проекта',
        'curator':'Куратор',
        'product_owner':'P.Owner (спикер)',
        'team':'Команда',
        'deadline':'Deadline',
        'agile_open_date':'Дата открытия на Agile BL',
        'open_protocol':'Номер протокола (открытие)',
        'agile_close_date':'Дата закрытия на Agile BL',
        'close_protocol':'Номер протокола (закрытие)',
        'base_bank':'Базовый Банк'
    }

    missing_fields = []

    for field in required_fields:
        if not getattr(project, field):
            miss_field = mapping.get(field)
            missing_fields.append(miss_field)
    
    if missing_fields:
        flash(f'Заполните следующие поля: {", ".join(missing_fields)} и нажмите "Сохранить"', 'warning')
        return False
    
    return True

@project_bp.route('/')
def index():
    """
    Главная страница с отображением списка проектов.
    Позволяет фильтровать проекты по статусу и куратору.
    
    Возвращает:
        Render шаблона с проектами, статусами и данными о пользователе.
    """
    user = current_user if current_user.is_authenticated else None
    is_admin = check_admin(current_user) if user else False

    query = Project.query

    status = request.args.get('status')
    curator = request.args.get('curator')

    if status:
        query = query.filter(Project.status == status)
    if curator:
        query = query.filter(Project.curator.ilike(f"%{curator}%"))

    projects = query.order_by(Project.id.desc()).all()

    project_count = len(projects)
    status_stats = Counter([p.status for p in projects])

    logger.info(f'Пользователь {"аноним" if not user else user.staff_number} просмотрел список проектов. Всего проектов: {project_count}')

    return render_template('index.html',
                           is_admin=is_admin,
                           user=user,
                           projects=projects,
                           project_count=project_count,
                           status_stats=status_stats)

@project_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """
    Создание нового проекта.
    Доступно только авторизованным пользователям.
    При успешном создании перенаправляет на главную.
    """
    form = CreateProjectForm()

    if form.validate_on_submit():
        new_project = Project(
            project_number=Project.generate_project_number(),
            title=form.title.data,
            project_type=form.project_type.data,
            curator=form.curator.data,
            product_owner=form.product_owner.data,
            team=form.team.data,
            deadline=form.deadline.data,
            agile_open_date=form.agile_open_date.data,
            open_protocol=form.open_protocol.data,
            base_bank=form.base_bank.data,
            bb=form.bb.data,
            vvb=form.vvb.data,
            dvb=form.dvb.data,
            mb=form.mb.data,
            pb=form.pb.data,
            szb=form.szb.data,
            sibb=form.sibb.data,
            srb=form.srb.data,
            ub=form.ub.data,
            ccb=form.ccb.data,
            yuzb=form.yuzb.data,
            creator=current_user.id,
            status='В работе'
        )

        db.session.add(new_project)
        db.session.commit()
        logger.info(f'Пользователь {current_user.staff_number} создал проект {new_project.project_number}')
        flash('Проект успешно создан!', 'success')
        return redirect(url_for('project_new.index'))

    return render_template('projects/create_project.html', form=form)

@project_bp.route('/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """
    Редактирование проекта.
    Разрешено только создателю проекта или администратору.
    Если проект завершен — редактировать может только админ.
    Поддерживает отдельную форму для технического продления.
    """
    project = Project.query.get_or_404(project_id)

    if project.creator != current_user.id and current_user.status != 1:
        logger.warning(f'Пользователь {current_user.staff_number} попытался редактировать проект {project.project_number} без прав')
        abort(403)
    if project.status == 'Завершен' and current_user.status != 1:
        flash('Проект может изменить только Админ', 'info')
        return redirect(url_for('project_new.view_project', project_id=project_id))
    
    old_user = Users.query.get(project.creator)
    form = EditProjectForm(obj=project)
    extension_form = TechnicalExtensionForm()

    if form.submit.data and form.validate_on_submit():
        form.populate_obj(project)
        db.session.commit()
        logger.info(f'Пользователь {current_user.staff_number} изменил проект {project.project_number}')

        updated_project = Project.query.get(project_id)
        new_user = Users.query.get(updated_project.creator)
        
        if old_user != new_user:
            send_internal_mail(
                old_user.email,
                f'Вам пришло это сообщение, так как Администратор изменил управляющего проекта {project.project_number}',
                f'Изменение управляющего проекта {project.project_number}'
            )
            send_internal_mail(
                new_user.email,
                f'Вам пришло это сообщение, так как администратор назначил Вас управляющим проекта {updated_project.project_number}',
                f'Изменение управляющего проекта {updated_project.project_number}'
            )
            logger.info(f'Изменён управляющий проекта {project.project_number} с {old_user.staff_number} на {new_user.staff_number}')

        flash('Изменения сохранены!', 'success')
        return redirect(url_for('project_new.index'))
    
    if extension_form.submit_extension.data and extension_form.validate_on_submit():
        project.deadline = extension_form.new_deadline.data
        project.tech_extensions += 1
        project.deadline_notified = False
        project.status = 'Техническое продление'
        db.session.commit()

        if old_user:
            send_internal_mail(
                'Agile_Backlog_OAPSO@omega.sbrf.ru',
                f'Пользователь {old_user.full_name} изменил Deadline до {extension_form.new_deadline.data}',
                f'Техническое продление по проекту {project.project_number}'
            )
            logger.info(f'Пользователь {old_user.staff_number} продлил проект {project.project_number} до {extension_form.new_deadline.data}')
        else:
            logger.warning(f'Пользователь не найден при продлении проекта {project.project_number}')
        
        flash('Проект продлен')
        return redirect(url_for('project_new.edit_project', project_id=project_id))

    return render_template(
        'projects/edit_project.html', 
        form=form,
        project=project, 
        extension_form=extension_form,
        user=old_user
    )


@project_bp.route('/project/<int:project_id>')
def view_project(project_id):
    """
    Просмотр детальной информации по проекту.
    Доступно всем пользователям.
    """
    user = current_user if current_user.is_authenticated else None
    is_admin = check_admin(user) if user else False
    
    project = Project.query.get_or_404(project_id)

    display_fields = [
        'project_number',
        'rating_id',
        'km_sup',
        'sprint_id',
        'title',
        'project_type',
        'curator',
        'product_owner',
        'team',
        'deadline',
        'tech_extensions',
        'agile_open_date',
        'open_protocol',
        'agile_close_date',
        'close_protocol',
        'base_bank'
    ]

    project_dict = {field: getattr(project, field) for field in display_fields}

    field_labels = { 
        'project_number' : 'Номер проекта',
        'rating_id' : 'ID проекта в рейтинге ТБ',
        'km_sup' : 'КМ в СУП',
        'sprint_id' : 'ID Спринта в реестре спринтов BL СВА',
        'title' : 'Название проекта',
        'project_type' : 'Тип проекта',
        'curator' : 'Куратор',
        'product_owner' : 'P.Owner (спикер)',
        'team' : 'Команда',
        'deadline' : 'Deadline',
        'tech_extensions' : 'Количество технических продлений',
        'agile_open_date' : 'Дата открытия на Agile BL',
        'open_protocol' : 'Номер протокола (открытие)',
        'agile_close_date' : 'Дата закрытия на Agile BL',
        'close_protocol' : 'Номер протокола (закрытие)',
        'base_bank' : 'Базовый Банк'
    }

    logger.info(f'Пользователь {"аноним" if not user else user.staff_number} просмотрел проект {project.project_number}')

    return render_template(
        'projects/view_project.html', 
        project=project, 
        is_admin=is_admin, 
        field_labels=field_labels,
        display_fields=display_fields,
        project_dict=project_dict
    )

@project_bp.route('/edit/<int:project_id>/complete', methods=['GET','POST'])
@login_required
def complete_project(project_id):
    """
    Завершение проекта — смена статуса на 'Завершен'.
    Разрешено создателю проекта или администратору.
    Проверяет обязательные поля перед завершением.
    """
    project = Project.query.get_or_404(project_id)

    if current_user.status != 1 and project.creator != current_user.id:
        abort(403)

    if not can_be_completed(project):
        return redirect(url_for('project_new.edit_project', project_id=project_id))

    project.status = 'Завершен'
    db.session.commit()

    send_internal_mail('Agile_Backlog_OAPSO@omega.sbrf.ru', f'Проект {project.title} закрылся!', f'Закрытие проекта {project.project_number}')
    
    logger.info(f'Пользователь {current_user.staff_number} завершил проект {project.project_number}')
    flash('Проект успешно завершён!', 'success')
    return redirect(url_for('project_new.view_project', project_id=project_id))
    
@project_bp.before_request
def notify_if_needed():
    """
    Проверка проектов перед каждым запросом.
    Если дедлайн или дата закрытия просрочены и проект не завершён, меняет статус на 'Задерживается'.
    Отправляет уведомления, если они ещё не были отправлены.
    """
    deadline_expired = Project.query.filter(
        (Project.deadline != None) & (Project.deadline < date.today()) & (Project.status != 'Завершен')
    ).all()

    close_expired = Project.query.filter(
        (Project.agile_close_date != None) & (Project.agile_close_date < date.today()) & (Project.status != 'Завершен')
    ).all()

    for project in deadline_expired:
        user = Users.query.get(project.creator)
        if user and not project.deadline_notified:
            send_internal_mail(user.email, f'Проект {project.title} просрочен, пожалуйста, примите меры: оформите техническое продление или закройте проект.', 'Проект просрочен')
            project.status = 'Задерживается'
            project.deadline_notified = True
            db.session.commit()
            logger.info(f'Уведомление о просрочке deadline для проекта {project.project_number} отправлено пользователю {user.staff_number}')

    for project in close_expired:
        user = Users.query.get(project.creator)
        if user and not project.close_notified:
            send_internal_mail(user.email, f'Закрытие проекта', f'Проект {project.title} нужно закрыть!')
            project.status = 'Задерживается'
            project.close_notified = True
            db.session.commit()
            logger.info(f'Уведомление о просрочке закрытия проекта {project.project_number} отправлено пользователю {user.staff_number}')