import os
import pandas as pd
import pythoncom
from datetime import datetime
from win32com import client
from app.models import Employee
from app.logging import logger

BACKUP_FOLDER = os.path.join(os.path.dirname(__file__), 'backups')
MAX_BACKUPS = 5


def create_excel_backup():
    """
    Создаёт резервную копию таблицы проектов в формате Excel в папке backups.
    Хранит не более MAX_BACKUPS последних файлов, удаляя самые старые.
    """
    from .models import Project

    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    projects = Project.query.all()
    data = [p.to_dict() for p in projects]
    df = pd.DataFrame(data)

    filename = f'backup_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
    path = os.path.join(BACKUP_FOLDER, filename)
    df.to_excel(path, index=False)

    # Получаем список файлов резервных копий, отсортированный по дате изменения
    files = sorted(
        [f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.xlsx')],
        key=lambda x: os.path.getmtime(os.path.join(BACKUP_FOLDER, x))
    )

    # Удаляем самые старые файлы, если их больше MAX_BACKUPS
    while len(files) > MAX_BACKUPS:
        os.remove(os.path.join(BACKUP_FOLDER, files.pop(0)))

def check_admin(user):
    """
    Проверяет, является ли пользователь администратором.
    Возвращает True, если user.status == 1, иначе False.
    """
    return user.status == 1

def send_internal_mail(recipient, body, subject='Код подтверждения'):
    """
    Отправляет письмо через Outlook (локальный клиент).
    Использует COM интерфейс Windows.

    :param recipient: email получателя
    :param body: текст письма
    :param subject: тема письма (по умолчанию 'Код подтверждения')
    """
    pythoncom.CoInitialize()
    try:
        outlook = client.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        mail.To = recipient
        mail.Subject = subject
        mail.Body = body
        mail.Send()
    finally:
        pythoncom.CoUninitialize()


def load_sva_persons(db):
    """
    Загружает список сотрудников из Excel-файла 'SVA_persons.xlsx'.
    Добавляет новых сотрудников в базу, пропуская уже существующих.

    :param db: объект SQLAlchemy для работы с БД
    """
    file = 'SVA_persons.xlsx'

    try:
        df = pd.read_excel(file)
        existing_employees = {e.staff_number for e in db.session.query(Employee.staff_number).all()}
        for _, row in df.iterrows():
            staff_number = str(row['TAB_NUM']).strip().zfill(8)
            if staff_number not in existing_employees:
                emp = Employee(
                    full_name=row['FIO'],
                    staff_number=staff_number,
                    position=row['JOB_TITLE'],
                    department=row['DEPARTMENT'],
                    email=row['EMAIL']
                )
                db.session.add(emp)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Ошибка загрузки сотрудников] {e}")