from sqlalchemy import Table, Column, Integer, ForeignKey, create_engine, String
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

engine = create_engine('sqlite:///:memory:', echo=True)

class Account(Base):
    __tablename__ = 'accounts'
    name = Column(String, primary_key=True)
    children = relationship("Entry", back_populates="parent")

class Entry(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True)
    parent_name = Column(String, ForeignKey('accounts.name'))
    parent = relationship("Account", back_populates="children")

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

par = Account(name='Tois')
print(par.name)

session.close()
