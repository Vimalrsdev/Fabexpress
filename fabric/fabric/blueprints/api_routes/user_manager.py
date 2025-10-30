from .models import APIRoutesUser
from fabric import login_manager, db


@login_manager.user_loader
def load_user(id):
    """
    This function helps the Flask-Login to load the user details from the database.
    @param id: user id.
    @return: Valid user if user is found else None.
    """
    admin = db.session.query(APIRoutesUser).filter_by(Id=id).first()
    if admin is not None:
        return admin
    else:
        return None
