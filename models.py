import os
import sqlite3
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Global Database Connection Helper
_DB_PATH = None

def get_connection():
    global _DB_PATH
    if not _DB_PATH:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        inst_dir = os.path.join(base_dir, 'instance')
        os.makedirs(inst_dir, exist_ok=True)
        _DB_PATH = os.path.join(inst_dir, 'smartcity.db')
    conn = sqlite3.connect(_DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

class BinaryClause:
    def __init__(self, sql, params):
        self.sql = sql
        self.params = list(params) if isinstance(params, (list, tuple)) else [params]

    def __or__(self, other):
        if isinstance(other, BinaryClause):
            return BinaryClause(f"({self.sql} OR {other.sql})", self.params + other.params)
        return self

    def __and__(self, other):
        if isinstance(other, BinaryClause):
            return BinaryClause(f"({self.sql} AND {other.sql})", self.params + other.params)
        return self

class Column:
    def __init__(self, name):
        self.name = name

    def desc(self):
        return f"{self.name} DESC"

    def asc(self):
        return f"{self.name} ASC"

    def __eq__(self, other):
        return BinaryClause(f"{self.name} = ?", [other])

    def __ne__(self, other):
        return BinaryClause(f"{self.name} != ?", [other])

    def ilike(self, pattern):
        return BinaryClause(f"{self.name} LIKE ?", [pattern])

    def notin_(self, values):
        placeholders = ", ".join(["?"] * len(values))
        return BinaryClause(f"{self.name} NOT IN ({placeholders})", list(values))

    def isnot(self, other):
        if other is None:
            return BinaryClause(f"{self.name} IS NOT NULL", [])
        return BinaryClause(f"{self.name} IS NOT ?", [other])

    def isnull(self):
        return BinaryClause(f"{self.name} IS NULL", [])

class SessionManager:
    def __init__(self):
        self._new_objects = []
        self._deleted_objects = []

    def add(self, obj):
        if obj not in self._new_objects:
            self._new_objects.append(obj)

    def delete(self, obj):
        if obj not in self._deleted_objects:
            self._deleted_objects.append(obj)

    def flush(self):
        self.commit()

    def commit(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            for obj in self._new_objects:
                obj._save(cursor)
            self._new_objects.clear()

            for obj in self._deleted_objects:
                obj._delete(cursor)
            self._deleted_objects.clear()

            conn.commit()
        finally:
            conn.close()

    def remove(self):
        self._new_objects.clear()
        self._deleted_objects.clear()

class QueryProperty:
    def __get__(self, instance, owner):
        return Query(owner)

class Query:
    def __init__(self, model_class):
        self.model_class = model_class
        self._filters = []
        self._order_by = None
        self._limit = None

    def filter_by(self, **kwargs):
        q = Query(self.model_class)
        q._filters = list(self._filters)
        q._order_by = self._order_by
        q._limit = self._limit
        for k, v in kwargs.items():
            q._filters.append(BinaryClause(f"{k} = ?", [v]))
        return q

    def filter(self, *conditions):
        q = Query(self.model_class)
        q._filters = list(self._filters)
        q._order_by = self._order_by
        q._limit = self._limit
        for cond in conditions:
            if isinstance(cond, BinaryClause):
                q._filters.append(cond)
            elif isinstance(cond, tuple):
                q._filters.append(BinaryClause(cond[0], cond[1:]))
            elif isinstance(cond, str):
                q._filters.append(BinaryClause(cond, []))
        return q

    def order_by(self, clause):
        q = Query(self.model_class)
        q._filters = list(self._filters)
        if hasattr(clause, 'desc'):
            q._order_by = clause.desc()
        else:
            q._order_by = str(clause)
        q._limit = self._limit
        return q

    def limit(self, n):
        q = Query(self.model_class)
        q._filters = list(self._filters)
        q._order_by = self._order_by
        q._limit = n
        return q

    def _execute(self):
        conn = get_connection()
        cursor = conn.cursor()
        sql = f"SELECT * FROM {self.model_class.__tablename__}"
        params = []

        if self._filters:
            where_clauses = []
            for bclause in self._filters:
                where_clauses.append(bclause.sql)
                params.extend(bclause.params)
            sql += " WHERE " + " AND ".join(where_clauses)

        if self._order_by:
            sql += f" ORDER BY {self._order_by}"

        if self._limit is not None:
            sql += f" LIMIT {self._limit}"

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            objects = [self.model_class._from_row(row) for row in rows]
            for obj in objects:
                db.session.add(obj)
            return objects
        finally:
            conn.close()

    def all(self):
        return self._execute()

    def first(self):
        res = self.limit(1).all()
        return res[0] if res else None

    def count(self):
        conn = get_connection()
        cursor = conn.cursor()
        sql = f"SELECT COUNT(*) as cnt FROM {self.model_class.__tablename__}"
        params = []
        if self._filters:
            where_clauses = []
            for bclause in self._filters:
                where_clauses.append(bclause.sql)
                params.extend(bclause.params)
            sql += " WHERE " + " AND ".join(where_clauses)

        try:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row['cnt'] if row else 0
        finally:
            conn.close()

    def get(self, pk_val):
        pk_name = self.model_class._pk_name
        return self.filter_by(**{pk_name: pk_val}).first()

    def get_or_404(self, pk_val):
        obj = self.get(pk_val)
        if not obj:
            from flask import abort
            abort(404)
        return obj

    def update(self, values_dict):
        """Bulk UPDATE matching rows. values_dict maps column names to new values."""
        conn = get_connection()
        cursor = conn.cursor()
        set_parts = []
        params = []
        for col, val in values_dict.items():
            set_parts.append(f"{col} = ?")
            if isinstance(val, bool):
                params.append(int(val))
            elif isinstance(val, datetime.datetime):
                params.append(_fmt_dt(val))
            else:
                params.append(val)

        sql = f"UPDATE {self.model_class.__tablename__} SET {', '.join(set_parts)}"
        if self._filters:
            where_clauses = []
            for bclause in self._filters:
                where_clauses.append(bclause.sql)
                params.extend(bclause.params)
            sql += " WHERE " + " AND ".join(where_clauses)

        try:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def delete(self):
        """Bulk DELETE matching rows."""
        conn = get_connection()
        cursor = conn.cursor()
        sql = f"DELETE FROM {self.model_class.__tablename__}"
        params = []
        if self._filters:
            where_clauses = []
            for bclause in self._filters:
                where_clauses.append(bclause.sql)
                params.extend(bclause.params)
            sql += " WHERE " + " AND ".join(where_clauses)

        try:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

class DB:
    def __init__(self):
        self.session = SessionManager()

    def init_app(self, app):
        global _DB_PATH
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite:///' in uri:
            _DB_PATH = uri.replace('sqlite:///', '')
            if _DB_PATH != ':memory:':
                os.makedirs(os.path.dirname(os.path.abspath(_DB_PATH)), exist_ok=True)

    def create_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile_number TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                is_verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS authority_users (
                authority_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                image_path TEXT,
                latitude REAL,
                longitude REAL,
                location_accuracy REAL,
                readable_address TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaint_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                notes TEXT,
                updated_at TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                service_id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                contact TEXT,
                operating_hours TEXT,
                updated_at TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcements (
                announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                affected_area TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                complaint_id INTEGER,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mobile_number TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                is_used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
            ''')
            conn.commit()
        finally:
            conn.close()

    def drop_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("DROP TABLE IF EXISTS authority_users")
            cursor.execute("DROP TABLE IF EXISTS complaints")
            cursor.execute("DROP TABLE IF EXISTS complaint_history")
            cursor.execute("DROP TABLE IF EXISTS services")
            cursor.execute("DROP TABLE IF EXISTS announcements")
            cursor.execute("DROP TABLE IF EXISTS notifications")
            cursor.execute("DROP TABLE IF EXISTS otp_verifications")
            conn.commit()
        finally:
            conn.close()

db = DB()

def _parse_dt(val):
    if not val:
        return datetime.datetime.now(datetime.timezone.utc)
    if isinstance(val, datetime.datetime):
        return val
    try:
        return datetime.datetime.fromisoformat(val)
    except Exception:
        try:
            return datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return datetime.datetime.now(datetime.timezone.utc)

def _fmt_dt(dt):
    if not dt:
        dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# =====================================================================
# 1. Citizen Users Model
# =====================================================================
class User(UserMixin):
    __tablename__ = 'users'
    _pk_name = 'user_id'

    user_id = Column('user_id')
    name = Column('name')
    mobile_number = Column('mobile_number')
    password_hash = Column('password_hash')
    email = Column('email')
    is_verified = Column('is_verified')
    created_at = Column('created_at')

    query = QueryProperty()

    def __init__(self, name='', mobile_number='', password_hash='', email=None, is_verified=False, created_at=None, user_id=None):
        self.user_id = user_id
        self.name = name
        self.mobile_number = mobile_number
        self.password_hash = password_hash
        self.email = email
        self.is_verified = bool(is_verified)
        self.created_at = _parse_dt(created_at)

    def get_id(self):
        return f"user_{self.user_id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def complaints(self):
        return Complaint.query.filter_by(user_id=self.user_id)

    @property
    def notifications(self):
        return Notification.query.filter_by(user_id=self.user_id)

    def _save(self, cursor):
        if self.user_id is None:
            cursor.execute('''
            INSERT INTO users (name, mobile_number, password_hash, email, is_verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.name, self.mobile_number, self.password_hash, self.email, 1 if self.is_verified else 0, _fmt_dt(self.created_at)))
            self.user_id = cursor.lastrowid
        else:
            cursor.execute('''
            UPDATE users SET name=?, mobile_number=?, password_hash=?, email=?, is_verified=? WHERE user_id=?
            ''', (self.name, self.mobile_number, self.password_hash, self.email, 1 if self.is_verified else 0, self.user_id))

    def _delete(self, cursor):
        if self.user_id:
            cursor.execute('DELETE FROM users WHERE user_id=?', (self.user_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            user_id=row['user_id'],
            name=row['name'],
            mobile_number=row['mobile_number'],
            password_hash=row['password_hash'],
            email=row['email'],
            is_verified=bool(row['is_verified']),
            created_at=row['created_at']
        )

# =====================================================================
# 2. Authority Users Model
# =====================================================================
class AuthorityUser(UserMixin):
    __tablename__ = 'authority_users'
    _pk_name = 'authority_id'

    authority_id = Column('authority_id')
    username = Column('username')
    password_hash = Column('password_hash')
    role = Column('role')
    created_at = Column('created_at')

    query = QueryProperty()

    def __init__(self, username='', password_hash='', role='Municipal Officer', created_at=None, authority_id=None):
        self.authority_id = authority_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.created_at = _parse_dt(created_at)

    def get_id(self):
        return f"auth_{self.authority_id}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def _save(self, cursor):
        if self.authority_id is None:
            cursor.execute('''
            INSERT INTO authority_users (username, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
            ''', (self.username, self.password_hash, self.role, _fmt_dt(self.created_at)))
            self.authority_id = cursor.lastrowid
        else:
            cursor.execute('''
            UPDATE authority_users SET username=?, password_hash=?, role=? WHERE authority_id=?
            ''', (self.username, self.password_hash, self.role, self.authority_id))

    def _delete(self, cursor):
        if self.authority_id:
            cursor.execute('DELETE FROM authority_users WHERE authority_id=?', (self.authority_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            authority_id=row['authority_id'],
            username=row['username'],
            password_hash=row['password_hash'],
            role=row['role'],
            created_at=row['created_at']
        )

# =====================================================================
# 3. Complaints Model
# =====================================================================
class Complaint:
    __tablename__ = 'complaints'
    _pk_name = 'complaint_id'

    complaint_id = Column('complaint_id')
    tracking_id = Column('tracking_id')
    user_id = Column('user_id')
    category = Column('category')
    title = Column('title')
    description = Column('description')
    image_path = Column('image_path')
    latitude = Column('latitude')
    longitude = Column('longitude')
    location_accuracy = Column('location_accuracy')
    readable_address = Column('readable_address')
    status = Column('status')
    created_at = Column('created_at')

    query = QueryProperty()

    def __init__(self, tracking_id='', user_id=None, category='', title='', description='', image_path=None,
                 latitude=None, longitude=None, location_accuracy=None, readable_address='', status='Submitted',
                 created_at=None, complaint_id=None):
        self.complaint_id = complaint_id
        self.tracking_id = tracking_id
        self.user_id = user_id
        self.category = category
        self.title = title
        self.description = description
        self.image_path = image_path
        self.latitude = latitude
        self.longitude = longitude
        self.location_accuracy = location_accuracy
        self.readable_address = readable_address
        self.status = status
        self.created_at = _parse_dt(created_at)

    @property
    def author(self):
        return User.query.get(self.user_id)

    @property
    def history(self):
        return ComplaintHistory.query.filter_by(complaint_id=self.complaint_id).order_by("updated_at DESC")

    def _save(self, cursor):
        if self.complaint_id is None:
            cursor.execute('''
            INSERT INTO complaints (tracking_id, user_id, category, title, description, image_path, latitude, longitude, location_accuracy, readable_address, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.tracking_id, self.user_id, self.category, self.title, self.description, self.image_path,
                  self.latitude, self.longitude, self.location_accuracy, self.readable_address, self.status, _fmt_dt(self.created_at)))
            self.complaint_id = cursor.lastrowid
        else:
            cursor.execute('''
            UPDATE complaints SET status=?, readable_address=?, latitude=?, longitude=?, location_accuracy=? WHERE complaint_id=?
            ''', (self.status, self.readable_address, self.latitude, self.longitude, self.location_accuracy, self.complaint_id))

    def _delete(self, cursor):
        if self.complaint_id:
            cursor.execute('DELETE FROM complaints WHERE complaint_id=?', (self.complaint_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            complaint_id=row['complaint_id'],
            tracking_id=row['tracking_id'],
            user_id=row['user_id'],
            category=row['category'],
            title=row['title'],
            description=row['description'],
            image_path=row['image_path'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            location_accuracy=row['location_accuracy'],
            readable_address=row['readable_address'],
            status=row['status'],
            created_at=row['created_at']
        )

# =====================================================================
# 4. Complaint History Model
# =====================================================================
class ComplaintHistory:
    __tablename__ = 'complaint_history'
    _pk_name = 'history_id'

    history_id = Column('history_id')
    complaint_id = Column('complaint_id')
    previous_status = Column('previous_status')
    new_status = Column('new_status')
    updated_by = Column('updated_by')
    notes = Column('notes')
    updated_at = Column('updated_at')

    query = QueryProperty()

    def __init__(self, complaint_id=None, previous_status='', new_status='', updated_by='', notes=None, updated_at=None, history_id=None):
        self.history_id = history_id
        self.complaint_id = complaint_id
        self.previous_status = previous_status
        self.new_status = new_status
        self.updated_by = updated_by
        self.notes = notes
        self.updated_at = _parse_dt(updated_at)

    def _save(self, cursor):
        if self.history_id is None:
            cursor.execute('''
            INSERT INTO complaint_history (complaint_id, previous_status, new_status, updated_by, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.complaint_id, self.previous_status, self.new_status, self.updated_by, self.notes, _fmt_dt(self.updated_at)))
            self.history_id = cursor.lastrowid

    def _delete(self, cursor):
        if self.history_id:
            cursor.execute('DELETE FROM complaint_history WHERE history_id=?', (self.history_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            history_id=row['history_id'],
            complaint_id=row['complaint_id'],
            previous_status=row['previous_status'],
            new_status=row['new_status'],
            updated_by=row['updated_by'],
            notes=row['notes'],
            updated_at=row['updated_at']
        )

# =====================================================================
# 5. Services Model (Waste, Hospital, Road)
# =====================================================================
class Service:
    __tablename__ = 'services'
    _pk_name = 'service_id'

    service_id = Column('service_id')
    service_name = Column('service_name')
    category = Column('category')
    description = Column('description')
    address = Column('address')
    latitude = Column('latitude')
    longitude = Column('longitude')
    contact = Column('contact')
    operating_hours = Column('operating_hours')
    updated_at = Column('updated_at')

    query = QueryProperty()

    def __init__(self, service_name='', category='', description='', address='', latitude=0.0, longitude=0.0,
                 contact='', operating_hours='', updated_at=None, service_id=None):
        self.service_id = service_id
        self.service_name = service_name
        self.category = category
        self.description = description
        self.address = address
        self.latitude = float(latitude or 0.0)
        self.longitude = float(longitude or 0.0)
        self.contact = contact
        self.operating_hours = operating_hours
        self.updated_at = _parse_dt(updated_at)

    @property
    def name(self): return self.service_name
    @property
    def details(self): return self.description
    @property
    def contact_number(self): return self.contact
    @property
    def emergency_contact(self): return self.contact
    @property
    def status(self): return 'Operational'

    def _save(self, cursor):
        if self.service_id is None:
            cursor.execute('''
            INSERT INTO services (service_name, category, description, address, latitude, longitude, contact, operating_hours, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.service_name, self.category, self.description, self.address, self.latitude, self.longitude,
                  self.contact, self.operating_hours, _fmt_dt(self.updated_at)))
            self.service_id = cursor.lastrowid
        else:
            cursor.execute('''
            UPDATE services SET service_name=?, category=?, description=?, address=?, latitude=?, longitude=?, contact=?, operating_hours=?, updated_at=?
            WHERE service_id=?
            ''', (self.service_name, self.category, self.description, self.address, self.latitude, self.longitude,
                  self.contact, self.operating_hours, _fmt_dt(self.updated_at), self.service_id))

    def _delete(self, cursor):
        if self.service_id:
            cursor.execute('DELETE FROM services WHERE service_id=?', (self.service_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            service_id=row['service_id'],
            service_name=row['service_name'],
            category=row['category'],
            description=row['description'],
            address=row['address'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            contact=row['contact'],
            operating_hours=row['operating_hours'],
            updated_at=row['updated_at']
        )

# =====================================================================
# 6. Announcements Model
# =====================================================================
class Announcement:
    __tablename__ = 'announcements'
    _pk_name = 'announcement_id'

    announcement_id = Column('announcement_id')
    title = Column('title')
    description = Column('description')
    category = Column('category')
    affected_area = Column('affected_area')
    created_at = Column('created_at')
    expires_at = Column('expires_at')

    query = QueryProperty()

    def __init__(self, title='', description='', category='', affected_area='', created_at=None, expires_at=None, announcement_id=None):
        self.announcement_id = announcement_id
        self.title = title
        self.description = description
        self.category = category
        self.affected_area = affected_area
        self.created_at = _parse_dt(created_at)
        self.expires_at = _parse_dt(expires_at) if expires_at else None

    @property
    def content(self): return self.description
    @property
    def priority(self): return 'Important'

    def _save(self, cursor):
        if self.announcement_id is None:
            cursor.execute('''
            INSERT INTO announcements (title, description, category, affected_area, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.title, self.description, self.category, self.affected_area, _fmt_dt(self.created_at), _fmt_dt(self.expires_at) if self.expires_at else None))
            self.announcement_id = cursor.lastrowid

    def _delete(self, cursor):
        if self.announcement_id:
            cursor.execute('DELETE FROM announcements WHERE announcement_id=?', (self.announcement_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            announcement_id=row['announcement_id'],
            title=row['title'],
            description=row['description'],
            category=row['category'],
            affected_area=row['affected_area'],
            created_at=row['created_at'],
            expires_at=row['expires_at']
        )

# =====================================================================
# 7. Notifications Model
# =====================================================================
class Notification:
    __tablename__ = 'notifications'
    _pk_name = 'notification_id'

    notification_id = Column('notification_id')
    user_id = Column('user_id')
    complaint_id = Column('complaint_id')
    message = Column('message')
    is_read = Column('is_read')
    created_at = Column('created_at')

    query = QueryProperty()

    def __init__(self, user_id=None, complaint_id=None, message='', is_read=False, created_at=None, notification_id=None):
        self.notification_id = notification_id
        self.user_id = user_id
        self.complaint_id = complaint_id
        self.message = message
        self.is_read = bool(is_read)
        self.created_at = _parse_dt(created_at)

    def _save(self, cursor):
        if self.notification_id is None:
            cursor.execute('''
            INSERT INTO notifications (user_id, complaint_id, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, self.complaint_id, self.message, 1 if self.is_read else 0, _fmt_dt(self.created_at)))
            self.notification_id = cursor.lastrowid
        else:
            cursor.execute('UPDATE notifications SET is_read=? WHERE notification_id=?', (1 if self.is_read else 0, self.notification_id))

    def _delete(self, cursor):
        if self.notification_id:
            cursor.execute('DELETE FROM notifications WHERE notification_id=?', (self.notification_id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            notification_id=row['notification_id'],
            user_id=row['user_id'],
            complaint_id=row['complaint_id'],
            message=row['message'],
            is_read=bool(row['is_read']),
            created_at=row['created_at']
        )

# =====================================================================
# 8. OTP Verifications Model
# =====================================================================
class OTPVerification:
    __tablename__ = 'otp_verifications'
    _pk_name = 'id'

    id = Column('id')
    mobile_number = Column('mobile_number')
    otp_hash = Column('otp_hash')
    expires_at = Column('expires_at')
    attempts = Column('attempts')
    is_used = Column('is_used')
    created_at = Column('created_at')

    query = QueryProperty()

    def __init__(self, mobile_number='', otp_hash='', expires_at=None, attempts=0, is_used=False, created_at=None, id=None):
        self.id = id
        self.mobile_number = mobile_number
        self.otp_hash = otp_hash
        self.expires_at = _parse_dt(expires_at)
        self.attempts = attempts
        self.is_used = bool(is_used)
        self.created_at = _parse_dt(created_at)

    def set_otp(self, plain_otp):
        self.otp_hash = generate_password_hash(str(plain_otp))

    def verify_otp(self, candidate_otp):
        now = datetime.datetime.now(datetime.timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)
        if self.is_used or now > exp:
            return False
        return check_password_hash(self.otp_hash, str(candidate_otp).strip())

    def _save(self, cursor):
        if self.id is None:
            cursor.execute('''
            INSERT INTO otp_verifications (mobile_number, otp_hash, expires_at, attempts, is_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.mobile_number, self.otp_hash, _fmt_dt(self.expires_at), self.attempts, 1 if self.is_used else 0, _fmt_dt(self.created_at)))
            self.id = cursor.lastrowid
        else:
            cursor.execute('UPDATE otp_verifications SET otp_hash=?, expires_at=?, attempts=?, is_used=? WHERE id=?', (self.otp_hash, _fmt_dt(self.expires_at), self.attempts, 1 if self.is_used else 0, self.id))

    def _delete(self, cursor):
        if self.id:
            cursor.execute('DELETE FROM otp_verifications WHERE id=?', (self.id,))

    @classmethod
    def _from_row(cls, row):
        return cls(
            id=row['id'],
            mobile_number=row['mobile_number'],
            otp_hash=row['otp_hash'],
            expires_at=row['expires_at'],
            attempts=row['attempts'],
            is_used=bool(row['is_used']),
            created_at=row['created_at']
        )

# =====================================================================
# Seed Initial Data Helper
# =====================================================================
def seed_initial_data(config=None):
    from config import Config
    auth_username = getattr(config, 'DEFAULT_AUTHORITY_USERNAME', None) or (config.get('DEFAULT_AUTHORITY_USERNAME') if hasattr(config, 'get') else None) or Config.DEFAULT_AUTHORITY_USERNAME
    auth_password = getattr(config, 'DEFAULT_AUTHORITY_PASSWORD', None) or (config.get('DEFAULT_AUTHORITY_PASSWORD') if hasattr(config, 'get') else None) or Config.DEFAULT_AUTHORITY_PASSWORD
    auth_role = getattr(config, 'DEFAULT_AUTHORITY_ROLE', None) or (config.get('DEFAULT_AUTHORITY_ROLE') if hasattr(config, 'get') else None) or Config.DEFAULT_AUTHORITY_ROLE

    # Authority User
    auth_user = AuthorityUser.query.filter_by(username=auth_username).first()
    if not auth_user:
        auth_user = AuthorityUser(
            username=auth_username,
            role=auth_role
        )
        auth_user.set_password(auth_password)
        db.session.add(auth_user)

    # Demo Citizen User (Ramesh Kumar - 9876543210)
    demo_citizen = User.query.filter_by(mobile_number='9876543210').first()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if not demo_citizen:
        demo_citizen = User(
            name='Ramesh Kumar',
            mobile_number='9876543210',
            email='ramesh.kumar@example.com',
            is_verified=True,
            created_at=now_utc - datetime.timedelta(days=7)
        )
        demo_citizen.set_password('CitizenPass@2026')
        db.session.add(demo_citizen)
        db.session.commit()

        # Seed sample complaints
        sample_complaints = [
            (
                'SCC-WST-20261102-1001',
                'Waste Management',
                'Overflowing Community Garbage Bin on 4th Main',
                'Community dumpster is completely overflowing and waste is scattered onto pedestrian walkway.',
                'Near 4th Main Junction, Koramangala 3rd Block, Bengaluru',
                12.9344, 77.6211, 15.0,
                'Resolved',
                now_utc - datetime.timedelta(days=6)
            ),
            (
                'SCC-ROD-20261105-1002',
                'Road Management',
                'Dangerous Deep Pothole Near EcoSpace Flyover',
                'Pothole filled with rainwater causing two-wheelers to slip. Needs asphalt patching.',
                'Outer Ring Road near Bellandur EcoSpace, Bengaluru',
                12.9288, 77.6845, 12.0,
                'In Progress',
                now_utc - datetime.timedelta(days=3)
            ),
            (
                'SCC-HSP-20261108-1003',
                'Hospital Services',
                'Outdated Emergency Telephone Line for Casualty Desk',
                'The landline number listed for Jayanagar General casualty was disconnected.',
                'Jayanagar General Hospital premises, Bengaluru',
                12.9234, 77.5902, 20.0,
                'Under Review',
                now_utc - datetime.timedelta(days=1)
            )
        ]

        for trk_id, cat, title, desc, addr, lat, lng, acc, st, dt in sample_complaints:
            cmp = Complaint(
                tracking_id=trk_id,
                user_id=demo_citizen.user_id,
                category=cat,
                title=title,
                description=desc,
                readable_address=addr,
                latitude=lat,
                longitude=lng,
                location_accuracy=acc,
                status=st,
                created_at=dt
            )
            db.session.add(cmp)
            db.session.commit()

            hist = ComplaintHistory(
                complaint_id=cmp.complaint_id,
                previous_status='None',
                new_status=st,
                updated_by='Municipal Desk',
                notes='Grievance recorded with supporting location data.',
                updated_at=dt
            )
            db.session.add(hist)

            if st == 'Resolved':
                notif = Notification(
                    user_id=demo_citizen.user_id,
                    complaint_id=cmp.complaint_id,
                    message=f"Your complaint {trk_id} ('{title}') has been Resolved by municipal teams.",
                    is_read=False,
                    created_at=dt
                )
                db.session.add(notif)

    # Core Services
    if Service.query.count() == 0:
        services_data = [
            ('Central Solid Waste Processing Plant', 'Waste Management', 'Mechanical composting, daily collection hub, dry and wet segregation facility.', '8th Main, Koramangala 4th Block, Bengaluru', 12.9352, 77.6245, '080-25530112', 'Daily 6:00 AM - 2:00 PM'),
            ('Indiranagar Dry Waste Collection Centre', 'Waste Management', 'Neighborhood recycling, plastic sorting, e-waste drop-off counter.', '100ft Road, HAL 2nd Stage, Indiranagar, Bengaluru', 12.9784, 77.6408, '080-25219944', 'Mon-Sat 7:00 AM - 4:00 PM'),
            ('Jayanagar Community Bio-Digester Depot', 'Waste Management', 'Biogas generation from kitchen organic refuse, ward collection depot.', '32nd Cross, 4th Block, Jayanagar, Bengaluru', 12.9298, 77.5833, '080-26638890', 'Daily 6:30 AM - 1:30 PM'),
            ('Malleshwaram Resource Recovery Facility', 'Waste Management', 'Zero-landfill pilot depot, citizen compost pickup counter.', '15th Cross, Margosa Road, Malleshwaram, Bengaluru', 12.9982, 77.5711, '080-23345512', 'Mon-Sun 6:00 AM - 3:00 PM'),
            ('Whitefield Automated Compactor Station', 'Waste Management', 'High-capacity hydraulic compactors, covered transfer containers.', 'ITPL Main Road, Hope Farm Junction, Whitefield, Bengaluru', 12.9855, 77.7432, '080-28456671', '24/7 Automated'),
            ('Victoria Multi-Speciality Government Hospital', 'Hospital Services', 'Verified 24/7 Trauma Care, 150 ICU Beds, Emergency Surgery, Cardiology & Blood Bank.', 'Fort Road, Near City Market, Kalasipalya, Bengaluru', 12.9629, 77.5753, '108 / 080-26701150', '24/7 Emergency & Inpatient'),
            ('Bowring & Lady Curzon Civil Hospital', 'Hospital Services', '24/7 Casualty Desk, Pediatrics, Gynecology, General Medicine, Diagnostic Imaging & Dialysis.', 'Lady Curzon Road, Tasker Town, Shivajinagar, Bengaluru', 12.9822, 77.6047, '108 / 080-25591325', '24/7 Emergency Services'),
            ('KC General District Hospital', 'Hospital Services', 'Maternity wing, Neonatal ICU, Orthopedic trauma, round-the-clock pharmacy.', '5th Cross, Malleshwaram West, Bengaluru', 13.0034, 77.5684, '108 / 080-23341771', '24/7 Emergency Ward'),
            ('Jayanagar General Government Hospital', 'Hospital Services', 'Cardiac ICU, Ophthalmology, Nephrology, 24-hour pathology lab and free generic pharmacy.', 'Near 4th T Block Bus Stand, Jayanagar, Bengaluru', 12.9234, 77.5902, '108 / 080-26563355', '24/7 Casualty & OPD'),
            ('Sri Jayadeva Institute of Cardiovascular Sciences', 'Hospital Services', 'Premier cardiac institute, emergency cath labs, pediatric cardiology, 24/7 CCU.', 'Bannerghatta Main Road, Jayanagar 9th Block, Bengaluru', 12.9198, 77.5991, '108 / 080-22977400', '24/7 Cardiac Emergency'),
            ('Outer Ring Road (Silk Board - Marathahalli)', 'Road Management', 'Continuous asphalt patching underway between Bellandur & Kadubeesanahalli. Speed limit 40 km/h.', 'Central Silk Board to Marathahalli Flyover, Bengaluru', 12.9279, 77.6833, '080-22942222', '24/7 Traffic Surveillance'),
            ('MG Road & Brigade Commercial Boulevard', 'Road Management', 'Newly resurfaced bituminous asphalt, smart traffic signaling, clear pedestrian walkways.', 'MG Road Metro Station to Trinity Circle, Bengaluru', 12.9756, 77.6066, '080-22942444', '24/7 Monitored - Good Condition'),
            ('Old Airport Road Repair Corridor', 'Road Management', 'Night pothole filling and storm-drain concrete reinforcement. Restricted lanes 11:00 PM - 5:00 AM.', 'Domlur Flyover to HAL Main Gate, Bengaluru', 12.9611, 77.6481, '080-22942555', 'Active Repair Zone'),
            ('West of Chord Arterial Section', 'Road Management', 'Reinforced manhole covers installed, reflective lane markings repainted, zero reported potholes.', 'Rajajinagar 1st Block to Mahalakshmi Layout, Bengaluru', 13.0078, 77.5519, '080-22942666', '24/7 Monitored - Good Condition'),
            ('Bannerghatta Main Road Transit Stretch', 'Road Management', 'Underground utility pipeline work near Guruguntepalya junction. Commuters urged to follow diversions.', 'Dairy Circle to Sagar Hospital Junction, Bengaluru', 12.9321, 77.5982, '080-22942777', 'Caution - Work In Progress')
        ]
        for s_name, cat, desc, addr, lat, lng, cont, hrs in services_data:
            s = Service(
                service_name=s_name,
                category=cat,
                description=desc,
                address=addr,
                latitude=lat,
                longitude=lng,
                contact=cont,
                operating_hours=hrs
            )
            db.session.add(s)

    # Announcements
    if Announcement.query.count() == 0:
        announcements_data = [
            ('Door-to-Door Wet & Dry Waste Segregation Drive', 'Citizens are requested to segregate waste into dry, wet, and sanitary categories before 7:30 AM handover. Free composting bins are available at ward offices.', 'Waste Management', 'All 198 Municipal Wards', now_utc - datetime.timedelta(days=1)),
            ('24/7 Emergency Hospital & Cardiac Desks Operational', 'All city government hospitals have updated emergency contact desks and ambulance units. In any critical health emergency, call 108 or direct hospital helplines immediately.', 'Hospital Services', 'Citywide Health Centers', now_utc - datetime.timedelta(days=2)),
            ('Night Resurfacing & Pothole Repair on Old Airport Road', 'Road maintenance teams are carrying out nocturnal asphalt resurfacing from 11:00 PM to 5:00 AM. Commuters are advised to exercise caution and heed detour signs.', 'Road Management', 'Old Airport Road - Domlur Corridor', now_utc - datetime.timedelta(hours=12)),
            ('Monsoon 48-Hour Rapid Pothole Patching Program', 'Citizens can report potholes with camera photographs and GPS geotags. Emergency flying squads deployed for 48-hour resolution of critical potholes.', 'Road Management', 'Major Arterial & Ring Roads', now_utc - datetime.timedelta(hours=6))
        ]
        for title, desc, cat, area, c_at in announcements_data:
            ann = Announcement(
                title=title,
                description=desc,
                category=cat,
                affected_area=area,
                created_at=c_at
            )
            db.session.add(ann)

    db.session.commit()
