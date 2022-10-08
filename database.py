import logging.config

from config import POSTGRES_DATABASE, DATABASE

import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, Numeric, Text, BigInteger
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime

database = DATABASE['database']
user = DATABASE['username']
password = DATABASE['password']

# Set up logging
logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


# Set up logging


def create_dataox_db(db_name, user_name, user_password):
    try:
        # Create connection with PostgreSQL
        connection = psycopg2.connect(**POSTGRES_DATABASE)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        # Create cursor for working with database
        cursor = connection.cursor()

        # Create user
        sql_create_user = f'''
                            CREATE ROLE {user_name} WITH
                            LOGIN
                            NOSUPERUSER
                            CREATEDB
                            NOCREATEROLE
                            INHERIT
                            NOREPLICATION
                            CONNECTION LIMIT -1
                            PASSWORD '{user_password}';
                           '''

        logger.info('Database user has been created successfully!!!')
        cursor.execute(sql_create_user)

        # Create database
        sql_create_database = f'''
                               CREATE DATABASE {db_name}
                               WITH OWNER {user_name}
                               ENCODING 'UTF8';
                              '''
        cursor.execute(sql_create_database)

        # Set privileges to user
        sql_grant_privileges_to_user = f'''
                                        GRANT ALL ON DATABASE {db_name}
                                        TO {user_name};
                                        '''
        cursor.execute(sql_grant_privileges_to_user)

    except (Exception, Error) as error:
        logger.debug("Error during work with PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()

    logger.info('Database has been created successfully!!!')


def make_engine():
    # db_string = 'postgresql+psycopg2://root:pass@localhost/mydb'
    # db_string = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
    # dialect = 'postgresql'
    # driver = 'psycopg2'
    # db_uri = f'{dialect}+{driver}://{user}:{password}@{host}:{port}/{database}'
    db_uri = URL.create(**DATABASE)
    # engine = create_engine(URL(**DATABASE), echo=True)
    # logger.debug(f'engine: {engine}')
    engine = create_engine(db_uri, echo=True)
    return engine


def get_item_ids(engine):
    session = Session(bind=engine)
    item_ids = session.query(Items.id).all()
    item_ids_tuple = set((item[0] for item in item_ids))
    logger.debug(f'Items_ids tuple received from DB: {len(item_ids_tuple)}')
    session.close()
    return item_ids_tuple


def write_to_db(metadata, engine, data):
    session = Session(bind=engine)
    # Connect to DB table
    items_table = Table('Items', metadata, autoload=True, autoload_with=engine)
    ins = items_table.insert()

    items = data.values()

    for item in items:
        session.execute(ins, item)
        session.commit()
    session.close()
    logger.info('Data saved into table items!')


Base = declarative_base()
# Connect to DB
engine = make_engine()
metadata = MetaData(engine)


class Items(Base):
    __tablename__ = 'Items'
    id = Column(BigInteger, primary_key=True)
    data_vip_url = Column(String(512), nullable=False)
    image_url = Column(String(512), nullable=True)
    title = Column(String(255), nullable=False)
    description_min = Column(String(1024), nullable=False)
    description_tagline = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    beds = Column(String(255), nullable=False)
    price = Column(Integer, nullable=True)
    currency = Column(String(255), nullable=True)
    city = Column(String(255), nullable=False)
    intersections = Column(String(512), nullable=True)
    rental_type = Column(String(200), nullable=False)
    publish_date = Column(DateTime(), nullable=False)
    add_date = Column(DateTime(), default=datetime.now,
                      onupdate=datetime.now)


if __name__ == '__main__':
    create_dataox_db(database, user, password)

    # Create table
    Base.metadata.create_all(engine)
    get_item_ids(engine)
