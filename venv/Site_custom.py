import os
import sys
import pathlib

class env(object):
    def __init__(self):
        self.env_dir = os.path.dirname(pathlib.Path(__file__).resolve())
        self.chrome_driver_path = os.path.join(self.env_dir, "chromedriver.exe")
        self.ingested_log_path = os.path.join(self.env_dir, "Benzaiten_Common\\Ingested_Log.json")
        self.config_path = os.path.join(self.env_dir, "config.json")
        self.data_delivery_folder = os.path.join(self.env_dir, "delivered_collections")
        self.set_env_paths()


    def set_env_paths(self):
        packages = []
        packages.append(self.env_dir)
        # site packages
        packages.append(os.path.join(self.env_dir, "Lib", "site-packages"))
        # common folder
        packages.append(os.path.join(self.env_dir, "Benzaiten_Common"))
        # ui folder
        packages.append(os.path.join(self.env_dir, "Benzaiten_UI"))
        # webscrapers
        packages.append(os.path.join(self.env_dir, "webscraper_modules"))
        # data tools
        packages.append(os.path.join(self.env_dir, "data_tools"))
        print("**************\n This is packages", packages)

        sys_paths = [sys.path.append(package) for package in packages]
        return sys_paths

    def get_delivered_collections(self):

        list_of_files = os.listdir(self.data_delivery_folder)

        collections_data = {}
        for file in list_of_files:
            if file.endswith(".json"):
                file_name = os.path.split(os.path.basename(file))[0]
                collections_data[file_name] = file

        return collections_data
