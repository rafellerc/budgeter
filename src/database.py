from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Sequence
from os import path
import tableprint as tp
from utils.exceptions import NotYetImplemented, InvalidInput, NoSuchAccount
import json

from ofxparse import OfxParser

#TODO Pass path to root as global variable
PATH_TO_ROOT = path.dirname(path.dirname(path.realpath(__file__)))

Base = declarative_base()

#SQLAlchemy cheatsheet https://www.pythonsheets.com/notes/python-sqlalchemy.html



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
#TODO Replace year/month/day for a datetime.date type
class Entry(Base):
    __tablename__ = 'entries'
    #TODO Check if the use of Sequence is enough to guarantee the uniqueness of the entries
    id_ = Column(Integer, Sequence('user_id_seq'), primary_key=True)
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

#TODO Check if it would be better to use a datatime type instead of 3 ints
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

def add_entry(session, acc_name='unknown',year=1500,month=1,day=0,
            value=0.99,descr='None',transfer='unknown',transfer_id=0):
    #TODO query the accounts table to get the account correspondent with the given name
    #TODO if no account is found, raise exception
    if acc_name not in get_accounts(session):
        #TODO Maybe give the possibility to the user of automaticaly adding the new account
        raise NoSuchAccount("There is no account in the database with the name '{}'".format(acc_name))
    entry = Entry(account_name = acc_name, year=year,month=month,day=day,
                    value=value*100, descr=descr, transfer=transfer,
                    transfer_id=transfer_id, reconciled=False)
    session.add(entry)
    session.commit()

def delete_entry():
    raise NotYetImplemented


def create_account(session, name='unknown', acc_type='Equity',currency= 'BRL',
                    descr='None'):
    """This function creates a new account in the database with the given parameters
    in the given session.
    """
    #TODO Check for consistency in all the fields.
    account = Account(name=name, acc_type=acc_type, currency=currency, descr=descr)
    session.add(account)
    session.commit()

def import_ofx(session,file_path):
    """Imports the entries in the statement of an ofx file.
    """
    with open(file_path,'rb') as fil:
        ofx = OfxParser.parse(fil)
    #This part decides which account it corresponds to.
    account = decide_account(session,ofx)
    for tran in ofx.account.statement.transactions:
        #TODO Check if there is no corresponding transaction already in the entries
        #TODO Try to reconcile?
        add_entry(session, acc_name=account,year=tran.date.year,month=tran.date.month,
                day=tran.date.day, value=tran.amount,descr=tran.memo,transfer='unknown',transfer_id=0)

def decide_account(session,ofx_parse):
    """Given an ofx parse object this function tries to figure out to which account
    it corresponds from the information contained in the ofx file. It returns the
    name of the account used in the database
    """
    #Tries to open the account metadata file
    try:
        with open(path.join(PATH_TO_ROOT,'metadata','account_metadata.json'),'r') as f:
            #The acc_dict is a dictionary that contains as keys all the active accounts and
            #as values all the corresponding aliases it might have in the ofx/qif files
            acc_dict = json.load(f)
    #If no metadata file is found it creates a dictionary that will be exported in the end
    except FileNotFoundError:
        acc_dict = {}
        for name in get_accounts(session):
            #Adds an empty list to each active account
            acc_dict[name] = []
    acc_found = None
    all_accs = get_accounts(session)
    for acc in acc_dict:
        if ofx_parse.account.number in acc_dict[acc]:
            acc_found = acc
    if acc_found == None:
        #TODO Think about the user interface in this part (maybe replace with a function to
        # get a better isolation)
        print("Choose the account that this file corresponds to:")
        i = 0
        for acc in all_accs:
            print("{} - {}".format(i, acc))
            i += 1
        ans = int(input("Enter number: "))
        acc_dict[all_accs[ans]].append(ofx_parse.account.number)
        acc_found = all_accs[ans]
    with open(path.join(PATH_TO_ROOT,'metadata','account_metadata.json'),'w') as f:
        json.dump(acc_dict, f)
    return acc_found


def get_accounts(session):
    """A method that returns the names of the active accounts in the database.
    """
    return [acc.name for acc in session.query(Account)]

if __name__ == '__main__':
    # session, engine = load_database_session('Test.db')
    session, engine = create_new_database('vei.db')
    # show_table(session,mode='accounts',by_account=['ccsp','ppsp'],between_YMD=[2016,2,1,2018,1,1])
    create_account(session, name='ppsp')
    # add_entry(session,acc_name='ccsp',descr='maluco',value=1.50)
    # add_entry(session,acc_name='',descr='vei')
    # print(get_accounts(session))
    import_ofx(session,"/home/rafael/Documents/Contabilidade/ppdf/ppdf2017-01.ofx")
    show_table(session)
    session.close()
