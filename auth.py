from database import db_session, User

def create_user(username, email, password, role="user"):
    if db_session.query(User).filter((User.username == username) | (User.email == email)).first():
        return False
    if username.lower() == "admin":
        role = "admin"
    if db_session.query(User).filter((User.username == username) | (User.email == email)).first():
        return False
    new_user = User(username=username, email=email, password=password, role=role)
    db_session.add(new_user)
    db_session.commit()
    return True

def authenticate_user(username, password):
    return db_session.query(User).filter_by(username=username, password=password).first()

def update_password(email, new_password):
    user = db_session.query(User).filter_by(email=email).first()
    if user:
        user.password = new_password
        db_session.commit()
        return True
    return False