from sqlalchemy.dialects.mssql import BIT
from fabric import db
from sqlalchemy import Integer
from flask_login import UserMixin


class APIRoutesUser(db.Model, UserMixin):
    """
    This table contains the admin (users who access the routes console) details
    """
    __tablename__ = 'APIRoutesUser'

    Id = db.Column(Integer, primary_key=True)
    Username = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Password = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)

    def get_id(self):
        """
        This function overrides the get_id function of UserMixin class
        to make the column 'Id' as the user id.
        @return: Id column.
        """
        return (self.Id)


class APIRoute(db.Model):
    """
    This table contains the list of APIs available in the project.
    """
    __tablename__ = 'APIRoutes'

    Id = db.Column(Integer, primary_key=True)
    Route = db.Column(db.String(100, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Method = db.Column(db.String(10, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    Desc = db.Column(db.String(200, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    EgRequestBody = db.Column(db.String(1000, 'SQL_Latin1_General_CP1_CI_AS'))
    APIGroup = db.Column(db.String(30, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    IsCompleted = db.Column(BIT)
