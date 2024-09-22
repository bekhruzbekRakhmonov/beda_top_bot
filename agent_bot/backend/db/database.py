from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def init_db(app):
    engine = create_engine(app.config['DATABASE_URL'])
    Base.metadata.create_all(engine)
    app.session = sessionmaker(bind=engine)()


def get_session():
    from flask import current_app
    return current_app.session
