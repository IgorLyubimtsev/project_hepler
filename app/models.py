import threading
from app.extensions import db
from datetime import datetime
from flask_login import UserMixin

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_number = db.Column(db.String(10), unique=True, nullable=False)

    rating_id = db.Column(db.Integer)
    km_sup = db.Column(db.String(11))
    sprint_id = db.Column(db.Integer)
    title = db.Column(db.String(200), nullable=False)

    project_type = db.Column(db.String(10), nullable=False)
    curator = db.Column(db.String(8), nullable=False)
    product_owner = db.Column(db.String(8), nullable=False)
    team = db.Column(db.String(500), nullable=False)

    deadline = db.Column(db.Date, nullable=False)
    tech_extensions = db.Column(db.Integer, default=0)

    agile_open_date = db.Column(db.Date, nullable=False)
    open_protocol = db.Column(db.Integer, nullable=False)

    agile_close_date = db.Column(db.Date)
    close_protocol = db.Column(db.Integer)

    base_bank = db.Column(db.String(5), nullable=False)

    bb = db.Column(db.Boolean, default=False)
    vvb = db.Column(db.Boolean, default=False)
    dvb = db.Column(db.Boolean, default=False)
    mb = db.Column(db.Boolean, default=False)
    pb = db.Column(db.Boolean, default=False)
    szb = db.Column(db.Boolean, default=False)
    sibb = db.Column(db.Boolean, default=False)
    srb = db.Column(db.Boolean, default=False)
    ub = db.Column(db.Boolean, default=False)
    ccb = db.Column(db.Boolean, default=False)
    yuzb = db.Column(db.Boolean, default=False)

    creator = db.Column(db.Integer, nullable=False)
    deadline_notified = db.Column(db.Boolean, default=False)
    close_notified = db.Column(db.Boolean, default=False)

    status = db.Column(db.String(25), nullable=False, default='В работе')
    
    create_at = db.Column(db.DateTime, default=datetime.utcnow())

    def generate_project_number():
        current_year = datetime.now().year
        last_project = Project.query.order_by(Project.id.desc()).first()
        if last_project and last_project.project_number:
            last_number = int(last_project.project_number.split('_')[-1])
            next_number = last_number + 1
        else:
            next_number = 1

        return f'{current_year}_{str(next_number).zfill(2)}'


    def to_dict(self):
        return {
            'N п/п' : self.id,
            'Номер проекта' : self.project_number,
            'ID проекта в рейтинге ТБ' : self.rating_id,
            'КМ в СУП' : self.km_sup,
            'ID Спринта в реестре спринтов BL СВА' : self.sprint_id,
            'Название проекта' : self.title,
            'Тип проекта' : self.project_type,
            'Куратор' : self.curator,
            'P.Owner (спикер)' : self.product_owner,
            'Команда' : self.team,
            'Deadline' : self.deadline,
            'Количество технических продлений' : self.tech_extensions,
            'Дата открытия на Agile BL' : self.agile_open_date,
            'Номер протокола (открытие)' : self.open_protocol,
            'Дата закрытия на Agile BL' : self.agile_close_date,
            'Номер протокола (закрытие)' : self.close_protocol,
            'Базовый Банк' : self.base_bank,
            'ББ' : self.bb,
            'ВВБ' : self.vvb,
            'ДВБ' : self.dvb,
            'МБ' : self.mb,
            'ПБ' : self.pb,
            'СЗБ' : self.szb,
            'СибБ' : self.sibb,
            'СРБ' : self.srb,
            'УБ' : self.ub,
            'ЦЧБ' : self.ccb,
            'ЮЗБ' : self.yuzb
        }

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    staff_number = db.Column(db.String(8), unique=True, nullable=False)
    position = db.Column(db.String(150))
    department = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True)

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    staff_number = db.Column(db.String(8), unique=True, nullable=False)
    position = db.Column(db.String(150))
    department = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True)
    status = db.Column(db.Integer, nullable=False, default=0)
    verification_code = db.Column(db.String(6))
    is_verified = db.Column(db.Boolean, default=False)

    def populate_from_employee(self, employee):
        self.id = employee.id
        self.full_name = employee.full_name
        self.staff_number = employee.staff_number
        self.position = employee.position
        self.department = employee.department
        
    def get_id(self):
        return str(self.id)
    
def run_import_in_thread(app):
    with app.app_context():
        try:
            from app.utils import load_sva_persons
            load_sva_persons(db)
        except Exception as e:
            print(f'[Импорт сотрудников] Ошибка: {e}')

def register_background_tasks(app):
    thread = threading.Thread(target=run_import_in_thread, args=(app, ))
    thread.start()