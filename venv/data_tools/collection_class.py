# buildt in
import os
import sys
import json
from pprint import pprint
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
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from wordcloud import ImageColorGenerator
from wordcloud import STOPWORDS

# Benzaiten imports
from Benzaiten_Common.DataBase import Database_Class

dump_csv = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\preview.csv"
save_tag_chart = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\tag_breakdown.png"
save_tag_wordcloud = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\tag_wordcloud.png"
save_summary_wordcloud = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\summary_wordcloud.png"

TAG_TO_REMOVE = ["No Archive Warnings Apply", "Virtual Streamer Animated Characters", "Creator Chose Not To Use Archive Warnings"]



class Collection_data(object):

    def __init__(self, name_of_collection):
        """
        Not alot happens in the init just boot up the Datbaseclass and connected to our datacluster
        :param name_of_collection: str, the name of the collection we will be pulling data from
        """
        self.database_class = Database_Class('FF_Data_Cluster')
        self.collection_name = name_of_collection
        self.collection_json = None

    def deliver_to_folder(self):
        """
        This function will pull a copy of the the collection down from the database and write it to disk as a json,
        insiode the json will be a list of dicts.
        :return:
        """
        delivery_location_file = os.path.join(env_object.data_delivery_folder, ("{}.json".format(self.collection_name)))

        if not os.path.exists(delivery_location_file):
            print("collection file already exists")
            # maybe throw up and window asking if we want to overwrite here.
            # Make the file
            with open(delivery_location_file, 'a+') as delivery_file:
                pass

        # gets the collection from the database class and writes it to a disk
        data = self.database_class.get_complete_collection(self.collection_name)
        with open(delivery_location_file, 'r+' ) as delivery_file:
            json.dump(data, delivery_file, indent=4)

        self.collection_json = delivery_location_file

    def get_collection_data(self):
        """
        function for getting data fromthe on disk json, if the json has'nt been pulled yet will
        ask to pull the data down
        :return: a lst of dicts that is a copy of the data thats on the MongoDB
        """
        if not self.collection_json:
            #try to see if we already have one for the collection

            on_dsk_cols = env_object.get_delivered_collections()
            target_col = on_dsk_cols.get(self.collection_name)
            if target_col:
                self.collection_json = target_col
            else:
                print("no delivered file found please run, deliver_to_folder first")
                return None

        with open(self.collection_json) as data_file:
            data = json.load(data_file)
        return data

    def get_clean_summary(self, collection):
        """
        The summary object can be a bit messy as it user written and not always super well encoded,
        do what we can to clean it up here
        :param collection: list of dicts, the content of ther collection from the database
        :return:
        """
        summary = collection['MetaData']['Story Summary']
        if not summary:
            # if the story authour wrote nothing in the summary we cant index into an empty list
            # so just return a blank string
            summary_clean_up = " "
        else:
            summary_clean_up = summary[0].replace("\n", " ")
        return summary_clean_up

    def make_data_frame(self):
        """
        Makes a Pandas dataframe based on the data that exists in the metadata
        writes that data to a csv
        :return:
        """
        data = self.get_collection_data()

        data_columns = ["Title", "Author", "Story Summary", "chapter Amount"]

        rows = []

        # build each of our rows
        for collection in data:

            rowdata = [collection['MetaData']['Title'],
                       collection['MetaData']['Author'],
                       self.get_clean_summary(collection),
                       collection['MetaData']['Chapters']
                       ]
            rows.append(rowdata)

        self.get_tag_data(data)

        data_frame = pd.DataFrame(rows, columns=data_columns)
        data_frame.to_csv(dump_csv, encoding='utf-8')


    def get_tag_data(self, collections):
        """
        Will count of the frequencies of each tag in the collection
        :param collections: the collection data object, list of dicts
        :return: a dict each key is a tag name with the value being an int of how often it occurs
        """
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
        self.make_wordcloud_of_summary()

        return tag_data

    def make_word_cloud_of_tags(self, tag_data):
        """
        Make a word cloud of the 250 most popular tags will save this to the datadelivery location when complete
        :param tag_data:
        :return:
        """
        tag_by_size = self.get_top_tags(tag_data, top_range=250)
        tag_wc = WordCloud(background_color='white',
                           width=1200,
                           height=700,
                           max_words=250).generate_from_frequencies(tag_by_size)

        # Make the word cloud into a plot figure and save it to disk
        plt.figure(figsize=(60, 35))
        plt.imshow(tag_wc, interpolation='bilinear')
        plt.axis('off')
        plt.savefig(save_tag_wordcloud, bbox_inches='tight')


    def get_top_tags(self, tag_data, top_range=50, with_labels=False):
        """
        Useful function for returning the most popular tags in the given tag data
        :param tag_data: dict, with each key being a tag name and the valeu being an int of how many times it appears
        :param top_range: This control how many of the top tags you want to be returned, if its 100 will retunr
        the top 100 in order most frequent  to least frequent
        :param with_labels: bool, will modify the key to inlude the number of times this tag occurs, useful for
        visual charts where you want the extact number in the label

        :return: dict the key will be the tag name and the value will be how many times it occurs in the collection.
        """
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
        """
        will make a pie chart of the tag data and save it to disk
        :param tag_data: the full tag data that you want to breakdown
        :param top_number: how many of the top tags you want to be on the pie chart, 50 is generally good,
        otherwise it becomes unreadable

        :return:
        """

        top_tags = self.get_top_tags(tag_data, with_labels=True, top_range=top_number)

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

    def make_wordcloud_of_summary(self):
        """
        Make a word cloud of the summary of all the stories in the collection and save it to disk
        :return:
        """
        data = self.get_collection_data()

        summaries = [self.get_clean_summary(col) for col in data]

        # has to be a better way to do this
        all_summary_text = " ".join(summaries)
        stop_words = set(STOPWORDS)
        summary_wordcloud = WordCloud(stopwords=stop_words,
                                      background_color='white',
                                      width=1200,
                                      height=700,
                                      max_words=450).generate(all_summary_text)
        plt.figure(figsize=(60, 35))
        plt.imshow(summary_wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.savefig(save_summary_wordcloud, bbox_inches='tight')

    def make_wordcloud_of_story_contents(self):
        """
        Make a wordcloud of all of the story contents and save it to disk
        :return:
        """
        data = self.get_collection_data()

    def make_author_leaderboard(self):
        data = self.get_collection_data()




collection_obj = Collection_data('Hololive_data')
#collection_obj.deliver_to_folder()
collection_obj.make_data_frame()