from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///users.db', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
db_session = Session()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.now)

class Rating(Base):
    __tablename__ = "ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)

class SavedCourse(Base):
    __tablename__ = "saved_courses"
    user_id = Column(Integer, primary_key=True)
    course_id = Column(String, primary_key=True)
    saved_at = Column(DateTime, default=datetime.now)

class SavedCourseActivity(Base):
    __tablename__ = "saved_course_activity"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

class ViewedCourse(Base):
    __tablename__ = "viewed_courses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(String, nullable=False)
    viewed_at = Column(DateTime, default=datetime.now)

def save_course(user_id, course_id):
    existing = db_session.query(SavedCourse).filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    if not existing:
        new_save = SavedCourse(user_id=user_id, course_id=course_id)
        db_session.add(new_save)
        # Log activity
        activity = SavedCourseActivity(
            user_id=user_id,
            course_id=course_id,
            action='saved'
        )
        db_session.add(activity)
        db_session.commit()
        return True
    return False

def unsave_course(user_id, course_id):
    deleted = db_session.query(SavedCourse).filter_by(
        user_id=user_id, course_id=course_id
    ).delete()
    if deleted > 0:
        # Log activity
        activity = SavedCourseActivity(
            user_id=user_id,
            course_id=course_id,
            action='unsaved'
        )
        db_session.add(activity)
        db_session.commit()
        return True
    db_session.commit()
    return False

def get_saved_courses(user_id):
    saved = db_session.query(SavedCourse).filter_by(user_id=user_id).all()
    return [s.course_id for s in saved]

def add_viewed_course(user_id, course_id):
    # Always create new entry instead of updating
    new_view = ViewedCourse(user_id=user_id, course_id=course_id)
    db_session.add(new_view)
    db_session.commit()

def get_viewed_courses(user_id, limit=10):
    viewed = db_session.query(ViewedCourse).filter_by(user_id=user_id)\
               .order_by(ViewedCourse.viewed_at.desc()).limit(limit).all()
    return [v.course_id for v in viewed]

Base.metadata.create_all(engine)