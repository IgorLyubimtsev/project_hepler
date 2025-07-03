import threading
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

class Project(db.Model):
    """
    Модель проекта (основной объект системы).
    Хранит всю информацию, необходимую для управления, фильтрации и экспорта проектов.
    """
    id = db.Column(db.Integer, primary_key=True)
    project_number = db.Column(db.String(10), unique=True, nullable=False)

    rating_id = db.Column(db.Integer)  # ID проекта в рейтинге ТБ
    km_sup = db.Column(db.String(11))  # ID проекта в СУП
    sprint_id = db.Column(db.Integer)  # ID спринта
    title = db.Column(db.String(200), nullable=False)

    project_type = db.Column(db.String(10), nullable=False)
    curator = db.Column(db.String(8), nullable=False)  # Табельный номер
    product_owner = db.Column(db.String(8), nullable=False)  # Табельный номер
    team = db.Column(db.String(500), nullable=False)  # Список табельных через ;

    deadline = db.Column(db.Date, nullable=False)
    tech_extensions = db.Column(db.Integer, default=0)

    agile_open_date = db.Column(db.Date, nullable=False)
    open_protocol = db.Column(db.Integer, nullable=False)
    agile_close_date = db.Column(db.Date)
    close_protocol = db.Column(db.Integer)

    base_bank = db.Column(db.String(5), nullable=False)

    # Чекбоксы банков-участников
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

    creator = db.Column(db.Integer, nullable=False)  # ID пользователя, создавшего проект
    deadline_notified = db.Column(db.Boolean, default=False)  # Уведомление о дедлайне отправлено
    close_notified = db.Column(db.Boolean, default=False)  # Уведомление о закрытии отправлено

    status = db.Column(db.String(25), nullable=False, default='В работе')  # Статус проекта
    create_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def generate_project_number():
        """
        Генерация уникального номера проекта формата: <год>_<порядковый номер>
        Например: 2025_01
        """
        current_year = datetime.now().year
        last_project = Project.query.order_by(Project.id.desc()).first()
        if last_project and last_project.project_number:
            try:
                last_number = int(last_project.project_number.split('_')[-1])
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1
        return f'{current_year}_{str(next_number).zfill(2)}'

    def to_dict(self):
        """
        Преобразует объект проекта в словарь, используемый для экспорта (например, в Excel).
        """
        return {
            'N п/п': self.id,
            'Номер проекта': self.project_number,
            'ID проекта в рейтинге ТБ': self.rating_id,
            'КМ в СУП': self.km_sup,
            'ID Спринта в реестре спринтов BL СВА': self.sprint_id,
            'Название проекта': self.title,
            'Тип проекта': self.project_type,
            'Куратор': self.curator,
            'P.Owner (спикер)': self.product_owner,
            'Команда': self.team,
            'Deadline': self.deadline,
            'Количество технических продлений': self.tech_extensions,
            'Дата открытия на Agile BL': self.agile_open_date,
            'Номер протокола (открытие)': self.open_protocol,
            'Дата закрытия на Agile BL': self.agile_close_date,
            'Номер протокола (закрытие)': self.close_protocol,
            'Базовый Банк': self.base_bank,
            'ББ': self.bb,
            'ВВБ': self.vvb,
            'ДВБ': self.dvb,
            'МБ': self.mb,
            'ПБ': self.pb,
            'СЗБ': self.szb,
            'СибБ': self.sibb,
            'СРБ': self.srb,
            'УБ': self.ub,
            'ЦЧБ': self.ccb,
            'ЮЗБ': self.yuzb
        }


class Employee(db.Model):
    """
    Таблица сотрудников, используется как источник данных при регистрации пользователей.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    staff_number = db.Column(db.String(8), unique=True, nullable=False)
    position = db.Column(db.String(150))
    department = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True)


class Users(db.Model, UserMixin):
    """
    Таблица пользователей системы (зарегистрированных через форму).
    Атрибут `status`: 0 - обычный пользователь, 1 - администратор.
    """
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    staff_number = db.Column(db.String(8), unique=True, nullable=False)
    position = db.Column(db.String(150))
    department = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True)

    status = db.Column(db.Integer, nullable=False, default=0)  # 0 - user, 1 - admin
    verification_code = db.Column(db.String(6))  # код подтверждения email
    is_verified = db.Column(db.Boolean, default=False)  # подтвержден ли пользователь

    def populate_from_employee(self, employee):
        """
        Заполняет поля пользователя на основе сотрудника из таблицы Employee.
        """
        self.id = employee.id
        self.full_name = employee.full_name
        self.staff_number = employee.staff_number
        self.position = employee.position
        self.department = employee.department

    def get_id(self):
        """Метод для flask-login, возвращает ID как строку."""
        return str(self.id)


def run_import_in_thread(app):
    """
    Фоновая задача для импорта сотрудников из SVA.
    Вызывается при запуске приложения.
    """
    with app.app_context():
        try:
            from app.utils import load_sva_persons
            load_sva_persons(db)
        except Exception as e:
            print(f'[Импорт сотрудников] Ошибка: {e}')


def register_background_tasks(app):
    """
    Регистрирует фоновую задачу в отдельном потоке.
    """
    thread = threading.Thread(target=run_import_in_thread, args=(app,))
    thread.start()
