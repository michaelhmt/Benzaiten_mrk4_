print("Doing imports and setting env:...")
import sys
import os
import json
import traceback

def set_env():
    current_location = os.getcwd()
    package_folder = os.path.dirname(current_location)
    common_folder = os.path.join(package_folder, "Benzaiten_Common")
    sys.path.append("E:\\Python\\Benzaiten_mrk4\\venv\\Lib\\site-packages")
    sys.path.append(package_folder)
    sys.path.append(common_folder)

set_env()
import Scrpaer

def launch_scraper_via_ui(log_path):
    with open(log_path, "r") as log_file:
        launch_args = json.load(log_file)

    launch_args = eval(launch_args)
    print("This is launch_args: ", launch_args)
    print("This is its type: ", type(launch_args))
    if not launch_args:
        print("No launch args given aborting.")
    else:
        print("Launching web scraper...")
        try:
            Scrpaer.iterate(page_to_start_with=int(launch_args['page_to_start']),
                            limt=int(launch_args['page_limt']),
                            add_to_db=int(launch_args['add_to_db']),
                            searchPage_constant=launch_args['target_url'],
                            debug_mode=launch_args['debug'])
        except Exception:
            print("Could not start Web scraper, got the following error: \n", traceback.format_exc())

# if __name__ == '__main__':
#     launch_scraper_via_ui()