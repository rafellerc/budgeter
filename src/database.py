from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from os import path

#TODO Pass path to root as global variable
PATH_TO_ROOT = path.dirname(path.dirname(path.realpath(__file__)))

Base = declarative_base()

#Table Accounts, contains all the accounts held by the user (Ex: SavingsAccount, CreditCard)
class Account(Base):
    __tablename__ = "accounts"
    name = Column(String,primary_key=True)
    #The acc_type specifies the account into 5 types: Assets, Liabilities, Income, Expenses and Equity
    #TODO Check if it belongs to some of the specified types
    acc_type = Column(String)
    #The currency is given in: BRL, USD, EUR
    currency = Column(String)
    descr = Column(String)
    entries = relationship("Entry", back_populates="account")

    def __repr__(self):
        return "<Account(name={}, type={}, currency={}, description={})>".format(self.name,self.acc_type,self.currency,self.descr)

#This table describes all the entries set by the user
class Entry(Base):
    __tablename__ = 'entries'
    id_ = Column(Integer, primary_key=True)
    account_name = Column(String,ForeignKey('accounts.name'))
    account = relationship("Account", back_populates="entries")
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    #IMPORTANT: All values must be stored as integers for lossless storage, so when writing
    #the values always multiply them by 100 to convert cents to integers. (Ex: BRL 1,50 = 150)
    #Apparently SQLite has no support for Numeric or Decimal type
    value = Column(Integer)
    descr = Column(String)
    transfer = Column(String)
    transfer_id = Column(Integer)
    reconciled = Column(Boolean)

    def __repr__(self):
        return "<Entry(Account:{},Date:{}/{}/{},Value:{},Transfer:{},Description:{})>".format(self.account.name,self.day,
                                self.month,self.year,self.value/100,self.transfer,self.descr)


def load_database_session(db_name,verbose=False):
    """Loads the database

        Returns
        -------
        session : sqlalchemy.orm.session.Session
		          Session instance.
	    engine : sqlalchemy.engine.Engine
		          Engine instance.
    """
    #Here we're assuming that the database files are in the 'data' folder
    db_path = "sqlite:///" + path.join(PATH_TO_ROOT,'data',db_name)
    engine = create_engine(db_path, echo=verbose)
    Session = sessionmaker(bind=engine, autoflush=False)
    session = Session()
    Base.metadata.create_all(engine)
    return session, engine

def create_new_database(db_name,verbose=False):
    """Creates a new database
    """
    db_path = "sqlite:///" + path.join(PATH_TO_ROOT,'data',db_name)
    engine = create_engine(db_path, echo=verbose)

    #Creates all the tables in the given engine
    Base.metadata.create_all(engine)

    #Creates the Session maker object and then start a session
    Session = sessionmaker(bind=engine)
    session = Session()
    return session, engine

def show_table(session,)

if __name__ == '__main__':
    session, engine = load_database_session('Tois.db')
    for entries in session.query(Entry).filter(Entry.account_name == 'ccsp'):
        print(entries)

    session.close()
