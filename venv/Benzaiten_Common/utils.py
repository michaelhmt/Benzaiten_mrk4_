import os


def ensure_dir(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            return True
        except:
            return False
    else:
        return True
