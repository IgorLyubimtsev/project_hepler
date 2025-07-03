import pandas as pd
import io, os
from datetime import date
from werkzeug.utils import secure_filename
from flask import redirect, url_for, request, flash, session, send_file, jsonify, Blueprint
from flask_login import current_user, logout_user
from app.extensions import db
from app.models import Project, Employee
from app.utils import check_admin, send_internal_mail
from io import BytesIO

act_bp = Blueprint('act', __name__)


def team_validator(row):
    if str(row).lower() != 'nan':
        return ';'.join([tab.zfill(8) for tab in str(row).split(';')])+';'
    else:
        return ''


@act_bp.route('/import-employees', methods=['POST'])
def import_employees():
    
    if not check_admin(current_user):
        flash('Access denied', 'danger')
        return redirect(url_for('project_new.index'))
    
    file = request.files.get('file_employee')
    if not file:
        flash('Files is not chosen', 'warning')
        return redirect(url_for('project_new.index'))
    
    try:
        df = pd.read_excel(file)
        existing_employees = {e.staff_number for e in db.session.query(Employee.staff_number).all()}
        for _, row in df.iterrows():
            row_tab = str(row['TAB_NUM']).strip().zfill(8)
            if row_tab not in existing_employees:
                emp = Employee (
                    full_name=row['FIO'],
                    staff_number=str(row['TAB_NUM']).zfill(8),
                    position=row['JOB_TITLE'],
                    department=row['DEPARTMENT'],
                    email=row['EMAIL']
                )
                db.session.add(emp) 
        db.session.commit()
        flash('Импорт завершен', "success")
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка импорта: {e}', 'danger')
    
    return redirect(url_for('project_new.index'))

@act_bp.route('/import_excel', methods=['POST'])
def import_excel():
    file = request.files.get('file')

    if not file or not file.filename.endswith('.xlsx'):
        flash('Пожалуйста, выберите файл Excel (.xlsx)', 'danger')
        return redirect(url_for('project_new.index')) 

    filename = secure_filename(file.filename)
    filepath = os.path.join('instance', filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath)
        df = df.iloc[1:].reset_index(drop=True)

        df['Дата открытия на Agile BL'] =  df['Дата открытия на Agile BL'].apply(lambda x: pd.to_datetime(x).date() if pd.notna(x) and str(x).strip() else None)
        df['Deadline'] =  df['Deadline'].apply(lambda x: pd.to_datetime(x).date() if pd.notna(x) and str(x).strip() else None)
        df['Дата закрытия на Agile BL'] =  df['Дата закрытия на Agile BL'].apply(lambda x: pd.to_datetime(x).date() if pd.notna(x) and str(x).strip() else None)
        df['КМ в СУП'] = df['КМ в СУП'].fillna('')
        df['Куратор'] = df['Куратор'].apply(lambda x: str(x).strip().zfill(8) if pd.notna(x) else '')
        df['P.Owner (Спикер)'] = df['P.Owner (Спикер)'].apply(lambda x: str(x).strip().zfill(8) if pd.notna(x) else '')
        df['ID Спринта в реестре спринтов BL СВА'] = df['ID Спринта в реестре спринтов BL СВА'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['Номер протокола (закрытие)'] = df['Номер протокола (закрытие)'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['Номер протокола (открытие)'] = df['Номер протокола (открытие)'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['ID проекта в рейтинге ТБ'] = df['ID проекта в рейтинге ТБ'].apply(lambda x: int(x) if pd.notna(x) else None)
        df['Количество технических продлений'] = df['Количество технических продлений'].fillna(0).astype(int)
        df['ББ'] = df['ББ'].fillna(0).astype(int)
        df['ВВБ'] = df['ВВБ'].fillna(0).astype(int)
        df['ДВБ'] = df['ДВБ'].fillna(0).astype(int)
        df['МБ'] = df['МБ'].fillna(0).astype(int)
        df['ПБ'] = df['ПБ'].fillna(0).astype(int)
        df['СЗБ'] = df['СЗБ'].fillna(0).astype(int)
        df['СРБ'] = df['СРБ'].fillna(0).astype(int)
        df['СибБ'] = df['СибБ'].fillna(0).astype(int)
        df['УБ'] = df['УБ'].fillna(0).astype(int)
        df['ЦЧБ'] = df['ЦЧБ'].fillna(0).astype(int)
        df['ЮЗБ'] = df['ЮЗБ'].fillna(0).astype(int)

        for _, row in df.iterrows():
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
                bb=int(row.get('ВВБ')),
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
                creator=1,
                status='Завершен' if row.get('Дата закрытия на Agile BL') < date.today() and row.get('Дата закрытия на Agile BL') else 'В работе' 
            )
            db.session.add(project)

        db.session.commit()
        flash('Импорт завершён успешно!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при импорте: {str(e)}', 'danger')

    os.remove(filepath)
    return redirect(url_for('project_new.index'))

@act_bp.route('/check-employees')
def check_employees():
    from app.models import Employee
    employees = Employee.query.all()
    return "<br>".join([f'{e.full_name} - {e.staff_number}' for e in employees])

@act_bp.route('/search_employees')
def search_employees():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = Employee.query.filter(
        Employee.full_name.ilike(f"%{query}%") |
        Employee.department.ilike(f"%{query}%") |
        Employee.position.ilike(f"%{query}%") 
    ).limit(5).all()

    return jsonify([
        {
            'label': f"{emp.full_name} ({emp.position}, {emp.department})",
            'value': emp.staff_number  # табельный номер
        }
        for emp in results
    ])

@act_bp.route('/search_employee')
def search_employee():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    matches = Employee.query.filter(Employee.full_name.ilike(f'%{query}%')).limit(5).all()
    results = [
        {
            'full_name': emp.full_name,
            'staff_number': emp.staff_number,
            'department': emp.department,
            'position': emp.position,
            'email': emp.email
        }
        for emp in matches
    ]

    return jsonify(results)

@act_bp.route('/api/employees')
def get_employees():
    query = request.args.get('query', '').lower()
    if not query:
        return jsonify([])
    
    results = Employee.query.filter(Employee.full_name.ilike(f'%{query}%')).all()
    return jsonify([
        {
            'full_name':emp.full_name,
            'staff_number':emp.staff_number,
            'position': emp.posotion,
            'department': emp.department
        } for emp in results
    ])

@act_bp.route('/admin/export_projects')
def export_projects():
    
    projects = Project.query.all()

    data = []
    for p in projects:
        data.append({
            'N п/п' : p.id,
            'Номер проекта' : p.project_number,
            'ID проекта в рейтинге ТБ' : p.rating_id,
            'КМ в СУП' : p.km_sup,
            'ID Спринта в реестре спринтов BL СВА' : p.sprint_id,
            'Название проекта' : p.title,
            'Тип проекта' : p.project_type,
            'Куратор' : p.curator,
            'P.Owner (спикер)' : p.product_owner,
            'Команда' : p.team,
            'Deadline' : p.deadline,
            'Количество технических продлений' : p.tech_extensions,
            'Дата открытия на Agile BL' : p.agile_open_date,
            'Номер протокола (открытие)' : p.open_protocol,
            'Дата закрытия на Agile BL' : p.agile_close_date,
            'Номер протокола (закрытие)' : p.close_protocol,
            'Базовый Банк' : p.base_bank,
            'ББ' : int(p.bb),
            'ВВБ' : int(p.vvb),
            'ДВБ' : int(p.dvb),
            'МБ' : int(p.mb),
            'ПБ' : int(p.pb),
            'СЗБ' : int(p.szb),
            'СибБ' : int(p.sibb),
            'СРБ' : int(p.srb),
            'УБ' : int(p.ub),
            'ЦЧБ' : int(p.ccb),
            'ЮЗБ' : int(p.yuzb)
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Projects')

    output.seek(0)

    return send_file(output, as_attachment=True,
                     download_name='projects_export.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@act_bp.route('/export_filtered', methods=['GET'])
def export_filtered():

    query = Project.query

    status = request.args.get('status')
    curator = request.args.get('curator')

    if status:
        query = query.filter(Project.status == status)
    if curator:
        query = query.filter(Project.curator.ilike(f"%{curator}%"))

    projects = query.all()

    df = pd.DataFrame([p.to_dict() for p in projects])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name='projects.xlsx')

@act_bp.route('/send_feedback', methods=['GET', 'POST'])
def send_feedback():
    # send_internal_mail('Agile_Backlog_OAPSO@omega.sbrf.ru', 'Просьба связаться возникла ошибка при работе с веб-приложением', 'Ошибка с веб-приложением')
    print('Leeter was sended')
    flash('Письмо было отправлено ')
    return redirect(url_for('project_new.index'))

@act_bp.before_request
def check_user_verified():
    if current_user.is_authenticated and not current_user.is_verified:
        logout_user()
        session.clear()
        flash('Ваша сессия была сброшена администратором', 'warning')
        return redirect(url_for('auth.login'))