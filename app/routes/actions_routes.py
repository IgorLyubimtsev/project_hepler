import pandas as pd
import io, os
from datetime import date
from werkzeug.utils import secure_filename
from flask import redirect, url_for, request, flash, session, send_file, jsonify, Blueprint
from flask_login import current_user, logout_user
from app.extensions import db
from app.models import Project, Employee
from app.utils import check_admin, send_internal_mail
from app.logging import logger

act_bp = Blueprint('act', __name__)

def file_prepare(filepath):
    """
    Обрабатывает Excel-файл, нормализует и конвертирует значения для загрузки в БД.

    :param filepath: Путь к Excel-файлу.
    :return: pd.DataFrame с подготовленными значениями.
    """

    required_columns = [
        'Дата открытия на Agile BL', 'Deadline', 'Дата закрытия на Agile BL',
        'КМ в СУП', 'Куратор', 'P.Owner (Спикер)', 'ID Спринта в реестре спринтов BL СВА',
        'Номер протокола (закрытие)', 'Номер протокола (открытие)', 'ID проекта в рейтинге ТБ',
        'Количество технических продлений', 'ББ', 'ВВБ', 'ДВБ', 'МБ', 'ПБ', 'СЗБ',
        'СРБ', 'СибБ', 'УБ', 'ЦЧБ', 'ЮЗБ'
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f'В таблице отсутствуют обязательные колонки: {", ".join(missing)}')
        flash(f'В таблице отсутствуют обязательные колонки: {", ".join(missing)}', 'danger')
        return
    
    df = pd.read_excel(filepath)
    df = df.iloc[1:].reset_index(drop=True)

    try:
        df['Дата открытия на Agile BL'] = df['Дата открытия на Agile BL'].apply(lambda x: pd.to_datetime(x).date() if pd.notna(x) and str(x).strip() else None)
        df['Deadline'] = df['Deadline'].apply(lambda x: pd.to_datetime(x).date() if pd.notna(x) and str(x).strip() else None)
        df['Дата закрытия на Agile BL'] = df['Дата закрытия на Agile BL'].apply(lambda x: pd.to_datetime(x).date() if pd.notna(x) and str(x).strip() else None)
        df['КМ в СУП'] = df['КМ в СУП'].fillna('')
        df['Куратор'] = df['Куратор'].apply(lambda x: str(x).strip().zfill(8) if pd.notna(x) else '')
        df['P.Owner (Спикер)'] = df['P.Owner (Спикер)'].apply(lambda x: str(x).strip().zfill(8) if pd.notna(x) else '')
        df['ID Спринта в реестре спринтов BL СВА'] = df['ID Спринта в реестре спринтов BL СВА'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['Номер протокола (закрытие)'] = df['Номер протокола (закрытие)'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['Номер протокола (открытие)'] = df['Номер протокола (открытие)'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['ID проекта в рейтинге ТБ'] = df['ID проекта в рейтинге ТБ'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['Количество технических продлений'] = df['Количество технических продлений'].fillna(0).astype(int)

        banks = ['ББ', 'ВВБ', 'ДВБ', 'МБ', 'ПБ', 'СЗБ', 'СРБ', 'СибБ', 'УБ', 'ЦЧБ', 'ЮЗБ']
        for col in banks:
            df[col] = df[col].fillna(0).astype(int)

    except Exception as e:
        logger.error(f'Ошибка при импорте данных в Базу Данных: {e}')
        flash('Ошибка в данных импортируемой таблицы', 'danger')

    return df

def team_validator(row):
    """
    Форматирует строку с табельными номерами участников команды.

    :param row: Строка с табельными номерами, разделёнными точкой с запятой.
    :return: Строка табельных номеров, дополненных до 8 символов.
    """
    if str(row).lower() != 'nan':
        return ';'.join([tab.zfill(8) for tab in str(row).split(';')]) + ';'
    else:
        return ''

@act_bp.route('/import-employees', methods=['POST'])
def import_employees():
    """
    Импортирует сотрудников из Excel-файла в БД.
    Доступно только администраторам.
    """
    if not check_admin(current_user):
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('project_new.index'))

    file = request.files.get('file_employee')
    if not file:
        flash('Файл не выбран', 'warning')
        return redirect(url_for('project_new.index'))

    try:
        df = pd.read_excel(file)
        existing_employees = {e.staff_number for e in db.session.query(Employee.staff_number).all()}
        for _, row in df.iterrows():
            row_tab = str(row['TAB_NUM']).strip().zfill(8)
            if row_tab not in existing_employees:
                emp = Employee(
                    full_name=row['FIO'],
                    staff_number=row_tab,
                    position=row['JOB_TITLE'],
                    department=row['DEPARTMENT'],
                    email=row['EMAIL']
                )
                db.session.add(emp)
        db.session.commit()
        flash('Импорт завершен', "success")
        logger.info('Данные по сотрудникам были добавлены')

    except Exception as e:
        db.session.rollback()
        flash('Ошибка импорта', 'danger')
        logger.error(f'Ошибка при импорте сотрудников в БД: {e}')

    return redirect(url_for('project_new.index'))

@act_bp.route('/import_excel', methods=['POST'])
def import_excel():
    """
    Импортирует проекты из Excel-файла в БД.
    Доступно только администраторам.
    """
    if not check_admin(current_user):
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('project_new.index'))

    file = request.files.get('file')
    if not file or not file.filename.endswith('.xlsx'):
        flash('Пожалуйста, выберите файл Excel (.xlsx)', 'danger')
        return redirect(url_for('project_new.index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join('instance', filename)
    file.save(filepath)

    try:
        df = file_prepare(filepath)
        for _, row in df.iterrows():
            try:   
                project = Project(
                    project_number=row.get('Номер проекта'),
                    rating_id=row.get('ID проекта в рейтинге ТБ'),
                    km_sup=row.get('КМ в СУП'),
                    sprint_id=row.get('ID Спринта в реестре спринтов BL СВА'),
                    title=row.get('Название проекта'),
                    project_type=row.get('Тип проекта'),
                    curator=row.get('Куратор'),
                    product_owner=row.get('P.Owner (Спикер)'),
                    team=team_validator(row.get('Команда')),
                    deadline=row.get('Deadline'),
                    tech_extensions=row.get('Количество технических продлений'),
                    agile_open_date=row.get('Дата открытия на Agile BL'),
                    open_protocol=row.get('Номер протокола (открытие)'),
                    agile_close_date=row.get('Дата закрытия на Agile BL'),
                    close_protocol=row.get('Номер протокола (закрытие)'),
                    base_bank=row.get('Базовый Банк'),
                    bb=int(row.get('ББ')),
                    vvb=int(row.get('ВВБ')),
                    dvb=int(row.get('ДВБ')),
                    mb=int(row.get('МБ')),
                    pb=int(row.get('ПБ')),
                    szb=int(row.get('СЗБ')),
                    sibb=int(row.get('СибБ')),
                    srb=int(row.get('СРБ')),
                    ub=int(row.get('УБ')),
                    ccb=int(row.get('ЦЧБ')),
                    yuzb=int(row.get('ЮЗБ')),
                    creator=current_user.id,
                    status='Завершен' if row.get('Дата закрытия на Agile BL') < date.today() and row.get('Дата закрытия на Agile BL') else 'В работе'
                )
                db.session.add(project)
            except Exception as e:
                logger.error(f'Ошибка в строке проекта: {e}')

        db.session.commit()
        flash('Импорт завершён успешно!', 'success')
        logger.info('Импорт проектов завершен')

    except Exception as e:
        db.session.rollback()
        flash('Ошибка при импорте', 'danger')
        logger.error(f'Ошибка при импорте проектов: {e}')

    finally:
        try:
            os.remove(filepath)
        except Exception as e:
            logger.error(f'Ошибка удаления файла {filepath}: {e}')

    return redirect(url_for('project_new.index'))

@act_bp.route('/check-employees')
def check_employees():
    """
    Вспомогательный маршрут для отладки:
    отображает всех сотрудников с их ФИО и табельными номерами в виде строки HTML.
    
    Returns:
        str: Список сотрудников в виде HTML-строки.
    """
    employees = Employee.query.all()
    return "<br>".join([f'{e.full_name} - {e.staff_number}' for e in employees])

@act_bp.route('/search_employees')
def search_employees():
    """
    Поиск сотрудников по ФИО, должности или отделу.
    Возвращает максимум 5 результатов с label и значением табельного номера.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # Безопасная фильтрация с использованием ilike, ограничение на 5 результатов
    results = Employee.query.filter(
        (Employee.full_name.ilike(f"%{query}%")) |
        (Employee.department.ilike(f"%{query}%")) |
        (Employee.position.ilike(f"%{query}%"))
    ).limit(5).all()

    return jsonify([
        {
            'label': f"{emp.full_name} ({emp.position}, {emp.department})",
            'value': emp.staff_number
        }
        for emp in results
    ])

@act_bp.route('/search_employee')
def search_employee():
    """
    Поиск сотрудников по ФИО.
    Возвращает максимум 5 результатов с подробными данными.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    matches = Employee.query.filter(Employee.full_name.ilike(f'%{query}%')).limit(5).all()

    return jsonify([
        {
            'full_name': emp.full_name,
            'staff_number': emp.staff_number,
            'department': emp.department,
            'position': emp.position,
            'email': emp.email
        }
        for emp in matches
    ])

@act_bp.route('/api/employees')
def get_employees():
    """
    Поиск сотрудников по ФИО (используется в API).
    
    Query Params:
        query (str): строка поиска (приводится к lower).
    
    Returns:
        Response: JSON-массив с результатами поиска (ФИО, табельный, должность, отдел).
    """
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify([])

    results = Employee.query.filter(Employee.full_name.ilike(f'%{query}%')).all()

    return jsonify([
        {
            'full_name': emp.full_name,
            'staff_number': emp.staff_number,
            'position': emp.position,
            'department': emp.department
        }
        for emp in results
    ])

@act_bp.route('/export_filtered', methods=['GET'])
def export_filtered():
    """
    Экспорт отфильтрованных проектов в Excel.

    Query Params:
        status (str, optional): фильтрация по статусу.
        curator (str, optional): фильтрация по куратору (поиск по вхождению).
    
    Returns:
        Response: Excel-файл с отфильтрованными проектами.
    """
    query = Project.query

    status = request.args.get('status')
    curator = request.args.get('curator')

    if status:
        query = query.filter(Project.status == status)
    if curator:
        query = query.filter(Project.curator.ilike(f"%{curator}%"))

    projects = query.all()
    df = pd.DataFrame([p.to_dict() for p in projects])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='projects.xlsx')

@act_bp.route('/send_feedback', methods=['GET', 'POST'])
def send_feedback():
    """
    Отправка письма с жалобой/фидбеком через внутреннюю почту.
    
    Использует send_internal_mail. Отображает flash-сообщение.
    
    Returns:
        Response: редирект на главную страницу.
    """
    try:
        send_internal_mail(
            'Agile_Backlog_OAPSO@omega.sbrf.ru',
            'Просьба связаться возникла ошибка при работе с веб-приложением',
            'Ошибка с веб-приложением'
        )
        flash('Письмо было отправлено')
    except Exception as e:
        logger.error(f'Ошибка при отправке сообщения: {e}')
        flash('Письмо не было отправлено из-за внутренней ошибки')

    return redirect(url_for('project_new.index'))

@act_bp.before_request
def check_user_verified():
    """
    Проверка статуса верификации пользователя перед каждым запросом.
    Если пользователь не верифицирован — сессия сбрасывается.
    """
    if current_user.is_authenticated and not current_user.is_verified:
        logout_user()
        session.clear()
        flash('Ваша сессия была сброшена администратором', 'warning')
        return redirect(url_for('auth.login'))