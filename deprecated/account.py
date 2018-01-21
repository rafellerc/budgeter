import pandas as pd
import numpy as np
import utils.exceptions #Change to src.utils.exceptions

class Account(object):
    """
    """
    def __init__(self,name,user_id,currency):
        self.name = name
        self.user_id = user_id
        self.currency = currency
        self.table = pd.DataFrame(columns=['Date','id','description','transfer','transfer_id','Reconciled','Value'])

    def add_entry(self,date,entry_id,description,transfer,transfer_id,reconciled,value):
        """The date entry should be YMD: '20171105'
        """
        #TODO Check consistency of entry
        self.table.loc[len(self.table)]=[date,entry_id,description,transfer,transfer_id,reconciled,value]

    def update_entry(self,entry_id,field,new_value):
        if field not in ['Date','id','description','transfer','transfer_id','Reconciled','Value']:
            raise InexistentField('The field you are trying to modify does not exist')
        elif field == 'id':
            raise ProtectedVariableException("You are not supposed to change the id of an entry")
        else:
            index = np.where(self.table["id"]==entry_id)[0]
            if len(index)==1:
                index = int(index)
                self.table.at[index,field]=new_value
            else:
                raise InexistentRecord('The given id does not correspond to any recorded entry')

    def reconcile(self,entry_id,set_to=True):
        self.update_entry(entry_id,'Reconciled',set_to)

    def delete_entry(self,entry_id):
        

if __name__ == '__main__':
    print("Begin test")
    acc = Account('CC',1,'BRL')
    acc.add_entry('20171101',1,'tois','CC',None,False,200)
    acc.add_entry('20171105',2,'toiz','CC',None,False,150)
    print(acc.table)
    acc.update_entry(2,'Value',500)
    print(acc.table)
    acc.reconcile(2)
    print(acc.table)
