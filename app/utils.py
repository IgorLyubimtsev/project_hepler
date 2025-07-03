import os
import pandas as pd
import pythoncom
from datetime import datetime
from win32com import client
from app.models import Employee

BACKUP_FOLDER = os.path.join(os.path.dirname(__file__), 'backups')
MAX_BACKUPS = 5

def create_excel_backup():

    from .models import Project

    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    projects = Project.query.all()
    data = [p.to_dict() for p in projects]
    df = pd.DataFrame(data)

    filename = f'backup_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
    path = os.path.join(BACKUP_FOLDER, filename)
    df.to_excel(path, index=False)

    files = sorted(
        [f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.xlsx')],
        key=lambda x: os.path.getmtime(os.path.join(BACKUP_FOLDER, x))
    )

    while len(files) > MAX_BACKUPS:
        os.remove(os.path.join(BACKUP_FOLDER, files.pop(0)))

def check_admin(user):
    return True if user.status == 1 else 0

def send_internal_mail(recepient, body, subject='Код подтверждения'):

    pythoncom.CoInitialize()

    outlook = client.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)
    mail.To = recepient
    mail.Subject = subject
    mail.Body = body
    mail.Send()
    # mail._oleobj_.Invoke(*(64209, 0, 8, 0, 'Agile_Backlog_OAPSO@omega.sbrf.ru'))
    
    pythoncom.CoUninitialize()

def load_sva_persons(db):

    file = 'SVA_persons.xlsx'

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
    except Exception as e:
        db.session.rollback()