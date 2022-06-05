# buildt in
import os
import sys
import json
from pprint import pprint
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import copy

# env settings
def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
set_env()
import Site_custom
env_object = Site_custom.env()

# site packages
import pandas as pd

# Benzaiten imports
from Benzaiten_Common.DataBase import Database_Class

dump_csv = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\preview.csv"
save_tag_chart = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\tag_breakdown.png"
save_tag_wordcloud = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\tag_wordcloud.png"

TAG_TO_REMOVE = ["No Archive Warnings Apply", "Virtual Streamer Animated Characters", "Creator Chose Not To Use Archive Warnings"]



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

    def make_data_frame(self):
        if not self.collection_json:
            #try to see if we already have one for the collection

            on_dsk_cols = env_object.get_delivered_collections()
            target_col = on_dsk_cols.get(self.collection_name)
            if target_col:
                self.collection_json = target_col
            else:
                print("no delivered file found please run, deliver_to_folder first")
                return

        with open(self.collection_json) as data_file:
            data = json.load(data_file)

        data_columns = ["Title", "Author", "Story Summary", "chapter Amount"]

        rows = []

        for collection in data:

            summary = collection['MetaData']['Story Summary']
            if not summary:
                summary_clean_up = " "
            else:
                summary_clean_up = summary[0].replace("\n", " ")

            rowdata = [collection['MetaData']['Title'],
                       collection['MetaData']['Author'],
                       summary_clean_up,
                       collection['MetaData']['Chapters']
                       ]
            rows.append(rowdata)

        self.get_tag_data(data)

        data_frame = pd.DataFrame(rows, columns=data_columns)
        data_frame.to_csv(dump_csv, encoding='utf-8')
        #pprint(self.get_tag_data(data))


    def get_tag_data(self, collections):
        tag_data = {}

        for collection in collections:
            tags = collection['MetaData']['Tags']
            for tag in tags:
                if tag in TAG_TO_REMOVE:
                    continue
                if tag == 'Hololive':
                    continue
                if not tag_data.get(tag):
                    # we have not seen this tag before add it to the dict
                    tag_data[tag] = 1
                else:
                    tag_data[tag] = tag_data[tag] + 1

        self.make_pie_chart_of_tags(tag_data)
        self.make_word_cloud_of_tags(tag_data)

        return tag_data

    def make_word_cloud_of_tags(self, tag_data):
        tag_by_size = self.get_top_tags(tag_data, top_range=250)
        print("This is tag data for the word cloud: ", tag_by_size)
        tag_wc = WordCloud(background_color='white',
                           width=1200,
                           height=700,
                           max_words=250).generate_from_frequencies(tag_by_size)

        plt.figure(figsize=(60, 35))
        plt.imshow(tag_wc, interpolation='bilinear')
        plt.axis('off')
        plt.savefig(save_tag_wordcloud, bbox_inches='tight')


    def get_top_tags(self, tag_data, top_range=50, with_labels=False):
        top_tags = {}

        tag_data_local = copy.deepcopy(tag_data)

        for number in range(top_range):
            highest_index = [index for index, item in enumerate(tag_data_local.values()) if item == max(tag_data_local.values())][0]
            all_tags =  [tag for tag in tag_data_local.keys()]
            highest_tag = all_tags[highest_index]

            if with_labels:
                top_tags[highest_tag + " [{}]".format(tag_data_local[highest_tag]) ]  = tag_data_local[highest_tag]
            else:
                top_tags[highest_tag] = tag_data_local[highest_tag]

            del tag_data_local[highest_tag]

        return top_tags

    def make_pie_chart_of_tags(self, tag_data, top_number = 50):

        top_tags = self.get_top_tags(tag_data, with_labels=True)

        #labels = [tag + " [{}]".format(top_tags[tag]) for tag in top_tags.keys()]

        cols = ["total occurrences"]
        print("This is top tags: ", top_tags)
        tags_data_frame = pd.DataFrame(top_tags.values(), columns=cols, index=top_tags.keys())
        chart = tags_data_frame.plot(kind='pie',
                                     autopct='%1.0f%%',
                                     title="Most popular tags",
                                     subplots=True,
                                     figsize=(40,35),
                                     fontsize=35,
                                     labeldistance=None)[0].get_figure()
        chart.savefig(save_tag_chart)


collection_obj = Collection_data('Hololive_data')
#collection_obj.deliver_to_folder()
collection_obj.make_data_frame()