from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from os import path
import tableprint as tp
from utils.exceptions import NotYetImplemented, InvalidInput

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

def show_table(session,mode='entries',by_account='all',between_YMD=[]):
    """This function displays the contents of the database tables according
    to the specifications of the caller. If mode 'accounts' is chosen, all the
    other parameters are ignored and the function displays the accounts table.
    If mode 'entries' is chosen, the entries of the indicated accounts in the
    indicated interval are shown.

    Parameters
    ----------
    session: sqlalchemy.orm.session.Session
            The current database session
    option: String in ['entries','accounts']
            The option indicates which table is going to be displayed
    by_account: [String]
            A list of the accounts whose entries will be shown. If you want
            to show all available accounts set 'all'.
            Ex: ['ccsp','ppsp']
    between_YMD: [Integer,Integer,Integer,Integer,Integer,Integer]
            The start date and end date (inclusive) of the entries. It must
            always be of the form year month day with 6 integers.
            Ex: [2017,10,05,2017,12,25] corresponds to: from 5 october 2017
            to 25 december 2017.

    """
    if mode == 'accounts':  #This mode prints the Accounts table
        rows = []
        headers = ['name','type','currency','description']
        #Queries for all rows of Accounts table
        for acc in session.query(Account):
            rows.append([acc.name,acc.acc_type,acc.currency,acc.descr])
        tp.table(rows,headers)
    #This mode prints Entries table
    elif mode == 'entries':
        headers = ['Date','id','account','transfer','reconciled','value','description']
        #Prints entries from all accounts
        if by_account == 'all':
            for acc in session.query(Account):
                print('\n|____{}____|'.format(acc.name))
                rows = []
                for ent in session.query(Entry).filter(Entry.account_name == acc.name):
                    rows.append(["{}/{}/{}".format(ent.day,ent.month,ent.year),ent.id_,
                        ent.account_name,ent.transfer,ent.reconciled,ent.value/100,ent.descr])
                tp.table(rows,headers)
        else:
            #Filters the accounts to only those indicated by the caller
            for acc in session.query(Account).filter(Account.name.in_(by_account)):
                print('\n|____{}____|'.format(acc.name))
                rows = []
                #Queries the table with the specified accounts and orders it from old to recent
                #by comparing the complete dates (Ex: 20171231 < 20180101)
                for ent in session.query(Entry).order_by(Entry.year*10000+Entry.month*100+Entry.day).filter(Entry.account_name == acc.name):
                    Min,Max,date = (0,0,0)
                    if len(between_YMD)==6:
                        Min = between_YMD[0]*10000+between_YMD[1]*100+between_YMD[2]
                        Max = between_YMD[3]*10000+between_YMD[4]*100+between_YMD[5]
                        date = ent.year*10000+ent.month*100+ent.day
                    print((date>=Min and date<=Max),date)
                    #Checks if all entries should be taken or if the entry is in the specified range
                    if len(between_YMD)==0 or (date>=Min and date<=Max):
                        rows.append(["{}/{}/{}".format(ent.day,ent.month,ent.year),ent.id_,
                            ent.account_name,ent.transfer,ent.reconciled,ent.value/100,ent.descr])
                tp.table(rows,headers)
    else:
        raise InvalidInput

def add_entry():
    raise NotYetImplemented
def add_account():
    raise NotYetImplemented

if __name__ == '__main__':
    session, engine = load_database_session('Tois.db')
    show_table(session,mode = 'tois',by_account=['ccsp','ppsp'],between_YMD=[2016,2,1,2018,1,1])

    session.close()
