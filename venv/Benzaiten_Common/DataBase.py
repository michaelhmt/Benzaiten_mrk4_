#site packages 
import pymongo

class Database_Class(object):
    def __init__(self, databasename):
        self.client = pymongo.MongoClient("mongodb+srv://Asalem:z7$d8BsHeTeL&#Ynq@cluster0.wn9uy.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.database_name = "{0}".format(databasename)
        self.database = self.client[self.database_name]


    def add_to_database(self,itemToAdd, targetCollection, print_IDs = True):

        if type(targetCollection) != str:
            print("collection needs to be a string")
            return None

        database_collection = self.database[targetCollection]

        if type(itemToAdd) == list and len(itemToAdd) > 1:
            # assume it a list of dicts so add many to Db
            try:
                add_op = database_collection.insert_many(itemToAdd)
                if print_IDs:
                    print(add_op.inserted_ids)
                return True
            except:
                print("well that did'nt work")

        else:
            try:
                add_op = database_collection.insert_one(itemToAdd)
                if print_IDs:
                    print(add_op.inserted_ids)
                return True
            except:
                print("well that did'nt work")
