# buildt in
import os
import sys
import json

# env settings
def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
set_env()
import Site_custom
env_object = Site_custom.env()

#Benzaiten imports
from Benzaiten_Common.DataBase import Database_Class



class Collection_data(object):

    def __init__(self, name_of_collection):
        self.database_class = Database_Class('FF_Data_Cluster')
        self.collection_name = name_of_collection
        self.collection_json = None

    def deliver_to_folder(self):
        delivery_location_file = os.path.join(env_object.data_delivery_folder, ("{}.json".format(self.collection_name)))

        if not os.path.exists(delivery_location_file):
            print("collection file already exists")
            # maybe throw up and window asking if we want to overwrite here.
            # Make the file
            with open(delivery_location_file, 'a+') as delivery_file:
                pass

        data = self.database_class.get_complete_collection(self.collection_name)
        print(data)
        with open(delivery_location_file, 'r+' ) as delivery_file:
            json.dump(data, delivery_file, indent=4)

        self.collection_json = delivery_location_file

    

collection_obj = Collection_data('Hololive_data')
collection_obj.deliver_to_folder()