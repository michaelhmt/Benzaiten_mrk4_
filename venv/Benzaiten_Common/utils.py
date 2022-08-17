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


def word_count_of_story(story_dict):
    # type: (dict) -> int
    story_chapter_dict = story_dict['Content']
    story_str = ""
    for _, chapter in story_chapter_dict.items():
        story_str += chapter
    return len(story_str)
