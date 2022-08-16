# buildt in
import os
import sys
import json
from pprint import pprint
import copy
import time

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
import Benzaiten_Common.utils as utils

dump_csv = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\preview.csv"
save_tag_chart = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\tag_breakdown.png"
save_tag_wordcloud = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\tag_wordcloud.png"
save_summary_wordcloud = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\summary_wordcloud.png"
contenst_wordcloud = "E:\\Python\\Benzaiten_mrk4\\venv\\delivered_collections\\contents_wordcloud.png"

TAG_TO_REMOVE = ["No Archive Warnings Apply", "Virtual Streamer Animated Characters", "Creator Chose Not To Use Archive Warnings"]



class Collection_data(object):

    def __init__(self, name_of_collection):
        """
        Not alot happens in the init just boot up the Datbaseclass and connected to our datacluster
        :param name_of_collection: str, the name of the collection we will be pulling data from
        """
        self.database_class = Database_Class('FF_Data_Cluster')
        self.collection_name = name_of_collection
        self.delivery_dir = os.path.join(env_object.data_delivery_folder, (name_of_collection + "_data_delivery"))
        utils.ensure_dir(self.delivery_dir)

        self.data = None

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

        with open(self.collection_json, encoding="utf8") as data_file:
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

    def make_data_frame(self, csv_location):
        """
        Makes a Pandas dataframe based on the data that exists in the metadata
        writes that data to a csv
        :return:
        """
        self.data = self.get_collection_data()

        data_columns = ["Title", "Author", "Story Summary", "chapter Amount"]

        rows = []

        # build each of our rows
        for collection in self.data:

            rowdata = [collection['MetaData']['Title'],
                       collection['MetaData']['Author'],
                       self.get_clean_summary(collection),
                       collection['MetaData']['Chapters']
                       ]
            rows.append(rowdata)

        data_frame = pd.DataFrame(rows, columns=data_columns)
        data_frame.to_csv(csv_location, encoding='utf-8')


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

        # self.make_pie_chart_of_tags(tag_data)
        # self.make_word_cloud_of_tags(tag_data)
        # self.make_wordcloud_of_summary()
        # self.make_wordcloud_of_story_contents()
        # self.get_top_authors()

        return tag_data

    def make_word_cloud_of_tags(self, tag_data, top_range=250, save_file_location=None):
        """
        Make a word cloud of the 250 most popular tags will save this to the datadelivery location when complete
        :param tag_data:
        :return:
        """
        tag_by_size = self.get_top_tags(tag_data, top_range=top_range)
        tag_wc = WordCloud(background_color='white',
                           width=1200,
                           height=700,
                           max_words=250).generate_from_frequencies(tag_by_size)

        # Make the word cloud into a plot figure and save it to disk
        plt.figure(figsize=(60, 35))
        plt.imshow(tag_wc, interpolation='bilinear')
        plt.axis('off')

        if save_file_location:
            plt.savefig(save_file_location, bbox_inches='tight')
        else:
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

    def make_pie_chart_of_tags(self, tag_data, top_number=50, save_file_location=None):
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
        tags_data_frame = pd.DataFrame(top_tags.values(), columns=cols, index=top_tags.keys())
        chart = tags_data_frame.plot(kind='pie',
                                     autopct='%1.0f%%',
                                     title="Most popular tags",
                                     subplots=True,
                                     figsize=(40,35),
                                     fontsize=35,
                                     labeldistance=None)[0].get_figure()

        if save_file_location:
            chart.savefig(save_file_location)
        else:
            chart.savefig(save_tag_chart)

        plt.close(chart)

    def make_wordcloud_of_summary(self, given_summary=None, save_file_location=None):
        """
        Make a word cloud of the summary of all the stories in the collection and save it to disk
        :return:
        """

        if given_summary:
            all_summary_text = " ".join(given_summary)
        else:
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

        if save_file_location:
            plt.savefig(save_file_location, bbox_inches='tight')
        else:
            plt.savefig(save_summary_wordcloud, bbox_inches='tight')


    def make_wordcloud_of_story_contents(self, given_contents=None, save_file_location=None):
        """
        Make a wordcloud of all of the story contents and save it to disk
        :return:
        """
        if given_contents:
            all_contents_text = " ".join(given_contents)
        else:
            data = self.get_collection_data()
            all_chapters = []
            for collection in data:
                chapter_dict = collection['Content']
                try:
                    [all_chapters.append(chapter) for chapter in chapter_dict.values()]
                except AttributeError:
                    # we have a broken structrue it most likley a list instead
                    [all_chapters.append(chapter) for chapter in chapter_dict if chapter]

            all_contents_text = " ".join(all_chapters)

        stop_words = set(STOPWORDS)
        contents_wordcloud = WordCloud(stopwords=stop_words,
                                      background_color='white',
                                      width=1200,
                                      height=700,
                                      max_words=450).generate(all_contents_text)
        plt.figure(figsize=(60, 35))
        plt.imshow(contents_wordcloud, interpolation='bilinear')
        plt.axis('off')

        if save_file_location:
            plt.savefig(save_file_location, bbox_inches='tight')
        else:
            plt.savefig(contenst_wordcloud, bbox_inches='tight')

    def clean_tags(self, tags_list):
        return [tag for tag in tags_list if tag not in TAG_TO_REMOVE]

    def get_single_tag_data(self, tag):

        collection = self.get_collection_data()
        this_tag_data = {}

        for story in collection:
            story_tags = set(self.clean_tags(story['MetaData']['Tags']))
            # If this is not prsent we have no reason to look at this story
            if tag not in story_tags:
                continue
            for s_tag in story_tags:
                # we don't need to process the data we are looking at
                if s_tag is tag:
                    continue
                # keep a count of what tags show up wih this tag
                if tag not in this_tag_data.keys():
                    this_tag_data[s_tag] = 1
                else:
                    this_tag_data[s_tag] += 1

        top_5_related = {}
        for i in range(5):
            # just in case tag data is empty
            if not this_tag_data:
                continue

            # get the top tag out and store it in our dict
            top_tag = max(this_tag_data, key=this_tag_data.get)
            top_5_related[top_tag] = this_tag_data[top_tag]
            del this_tag_data[top_tag]

        return top_5_related

    def make_author_data(self):
        data = self.get_collection_data()

        author_data = {}

        print("Creating author data")

        for collection in data:
            if not collection['Content']:
                continue

            author = collection['MetaData']['Author']
            this_author_data = author_data.get(author)
            if this_author_data:
                # add to an existing data here

                this_author_data['story_number'] = this_author_data['story_number'] + 1
                current_tags = this_author_data['Tags']
                current_tags.extend(self.clean_tags(collection['MetaData']['Tags']))
                this_author_data['Tags'] = current_tags

                current_summary =  this_author_data['summary']
                current_summary.extend([self.get_clean_summary(collection)])
                this_author_data['summary'] = current_summary

                current_chapters =  this_author_data['chapters']
                current_chapters.append(int(collection['MetaData']['Chapters']))
                this_author_data['chapters'] = current_chapters

                all_chapters = []
                chapter_dict = collection['Content']
                try:
                    [all_chapters.append(chapter) for chapter in chapter_dict.values()]
                except AttributeError:
                    [all_chapters.append(chapter) for chapter in chapter_dict if chapter]
                current_contents =  this_author_data['contents']
                current_contents.extend(all_chapters)
                this_author_data['contents'] = current_contents



                author_data[author] = this_author_data

            else:
                # make the authors data here
                a_data = {}
                a_data['story_number'] = 1
                if  collection['MetaData']['Tags']:
                    a_data['Tags'] = self.clean_tags(collection['MetaData']['Tags'])
                else:
                    a_data['Tags'] = []

                a_data['summary'] = [self.get_clean_summary(collection)]
                a_data['chapters'] = [int(collection['MetaData']['Chapters'])]

                all_chapters = []
                chapter_dict = collection['Content']
                try:
                    [all_chapters.append(chapter) for chapter in chapter_dict.values()]
                except AttributeError:
                    [all_chapters.append(chapter) for chapter in chapter_dict if chapter]

                a_data['contents'] = [" ".join(all_chapters)]

                author_data[author] = a_data

        return author_data

    def get_top_authors(self, top_range=5):
        top_authors = {}
        author_data = self.make_author_data()

        author_data_local = copy.deepcopy(author_data)

        print("Finding top authors")

        for number in range(top_range):
            higest_candiate = ["Empty", 0]
            for author in author_data_local.keys():
                if author_data[author]["story_number"] > higest_candiate[1]:
                    higest_candiate = [author, author_data[author]["story_number"]]
            top_authors[higest_candiate[0]] = author_data_local[higest_candiate[0]]
            del author_data_local[higest_candiate[0]]

        return top_authors

    def deliver_data(self):

        csv_delivery_location = os.path.join(self.delivery_dir, (self.collection_name + "_data_view.csv"))
        pie_chart_delivery_location = os.path.join(self.delivery_dir, (self.collection_name + "_tag_p_chart.png"))
        tag_cloud_delivery_location = os.path.join(self.delivery_dir, (self.collection_name + "_tag_wordcloud.png"))
        summary_cloud_delivery_location = os.path.join(self.delivery_dir, (self.collection_name + "_summary_wordcloud.png"))
        chapters_cloud_delivery_location = os.path.join(self.delivery_dir, (self.collection_name + "_chapters_wordcloud.png"))

        self.tag_data = self.get_tag_data(self.get_collection_data())

        print("making CSV")
        self.make_data_frame(csv_delivery_location)
        print("Making Pie chart of tags")
        self.make_pie_chart_of_tags(self.tag_data, save_file_location=pie_chart_delivery_location)
        print("making word cloud of tags")
        self.make_word_cloud_of_tags(self.tag_data, save_file_location=tag_cloud_delivery_location)
        print("making wordcloud of summary")
        self.make_wordcloud_of_summary(save_file_location=summary_cloud_delivery_location)
        print("Making word cloud of contents")
        self.make_wordcloud_of_story_contents(save_file_location=chapters_cloud_delivery_location)

    def deliver_top_author_anyalsis(self):

        top_authors = self.get_top_authors()

        for index, author in enumerate(top_authors.keys()):
            self.generate_data_for_author(author, top_authors[author], index+1, top_authors[author]['story_number'])


    def generate_data_for_author(self, authors_name, authors_data, pos, amount):

        author_delivery_folder = os.path.join(self.delivery_dir, "{} - {} - amount {}".format(pos,
                                                                                              authors_name,
                                                                                              amount))
        utils.ensure_dir(author_delivery_folder)

        tag_p_chart_delivery_location = os.path.join(author_delivery_folder, "{}_tag_p_chart.png".format(authors_name))
        tag_cloud_delivery_location = os.path.join(author_delivery_folder, "{}_tag_cloud.png".format(authors_name))
        summary_cloud_delivery_location = os.path.join(author_delivery_folder, "{}_summary_cloud.png".format(authors_name))
        contents_cloud_delivery_location = os.path.join(author_delivery_folder,"{}_contents_cloud.png".format(authors_name))

        tag_data = self.get_tag_data([{'MetaData': authors_data}])
        tag_amount = len(tag_data.keys())

        self.make_pie_chart_of_tags(tag_data, save_file_location=tag_p_chart_delivery_location,top_number=tag_amount)
        self.make_word_cloud_of_tags(tag_data, save_file_location=tag_cloud_delivery_location, top_range=tag_amount)
        self.make_wordcloud_of_summary(authors_data['summary'], save_file_location=summary_cloud_delivery_location)
        self.make_wordcloud_of_story_contents(authors_data['contents'], save_file_location=contents_cloud_delivery_location)







#
# collection_obj = Collection_data('Hololive_data')
# collection_obj.deliver_to_folder()
# collection_obj.deliver_data()
# collection_obj.deliver_top_author_anyalsis()