from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

#Initializes the Base object to construct Tables
Base = declarative_base()
#Initializes engine. It may be initialized in memory ('sqlite:///:memory:') or in
#a file 'sqlite:///filename'
engine = create_engine('sqlite:///:memory:', echo=True)

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
    value = Column(Integer)
    descr = Column(String)
    transfer = Column(String)
    transfer_id = Column(Integer)
    reconciled = Column(Boolean)

    def __repr__(self):
        return "<Entry(Account:{},Date:{}/{}/{},Value:{},Transfer:{},Description:{})>".format(self.account.name,self.day,
                                self.month,self.year,self.value/100,self.transfer,self.descr)



#Creates all the tables in the given engine
Base.metadata.create_all(engine)

#Creates the Session maker object and then start a session
Session = sessionmaker(bind=engine)
session = Session()

ccsp = Account(name='ccsp',acc_type='Assets',currency="BRL",descr="Conta Corrente São Paulo")
ppsp = Account(name='ppsp',acc_type='Assets',currency="BRL",descr="Poupança São Paulo")
foodBr = Account(name='foodBr',acc_type='Expenses',currency="BRL",descr="Despesas com comida em reais")

mcDo = Entry(id_=216489,account_name='ccsp',year=2017,month=12,day=23,value=-2500,
            descr='Lanche no McDo',transfer='foodBr',transfer_id=None,reconciled=False)
transf = Entry(id_=54982,account_name='ccsp',year=2017,month=11,day=27,value=-20000,
            descr='Transferencia da CC para Poupança',transfer='ppsp',transfer_id=None,reconciled=False)
session.add_all([ccsp,ppsp,mcDo,transf])
session.commit()

# for instance in session.query(Entry).filter(Entry.day == 23):
#     print(instance.account_name, instance.value)
print('\n')
print('\n')
for entries in ccsp.entries:
    print(entries)


#Closes session after all the operations are done
session.close()
