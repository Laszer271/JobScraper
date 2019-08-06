import codecs
import re


class OfferAnalyzer:

    def __init__(self, array_of_tags):
        self.tags = array_of_tags
        self.titles = []
        self.descriptions = []
        self.links = []
        self.points = []

    def load_from_file(self, database):
        file = codecs.open(database, 'r', encoding='latin-1')
        lines = file.readlines()
        for line in lines:
            line = line.split(sep='|')
            self.titles.append(line[0])
            self.descriptions.append(line[1])
            self.links.append(line[2].replace('\n', ''))
        file.close()

    def load_from_lists(self, titles_list, descriptions_list, urls_list):
        self.titles = titles_list
        self.descriptions = descriptions_list
        self.links = urls_list
        self.points = []

    def calculate_points(self):
        tag_in_title_multiple = 1.5
        for title, description in zip(self.titles, self.descriptions):
            points = 0
            for tag in self.tags:
                name = tag.name.lower()

                reg_expression = r'\b%s(?![a-z])' % re.escape(name)

                if re.search(reg_expression, title.lower()):
                    points += int(tag.value * tag_in_title_multiple)
                elif re.search(reg_expression, description.lower()) and points > 0:
                    points += tag.value


            if points < 0:
                points = 0
            self.points.append(points)

    def save_to_file(self, filename, append=False, machine_mode=False):
        if append:
            file = codecs.open(filename, 'a+', encoding='latin-1')
        else:
            file = codecs.open(filename, 'w+', encoding='latin-1')

        if machine_mode:
            for points, title, description, link in zip(self.points, self.titles, self.descriptions, self.links):
                file.write(str(points) + '|' + title + '|' + description + '|' + link + '\n')
        else:
            for points, title, description, link in zip(self.points, self.titles, self.descriptions, self.links):
                file.write('Points: ' + str(points) + '\nTitle:\n' + title + '\nDescription:\n' + description
                           + '\nLink: ' + link + '\n\n')

        file.close()

    def sort_by_points(self, reverse_order=True):
        array = self.get_array()

        array.sort(key=lambda offer: offer[0], reverse=reverse_order)

        self.clear_offers()
        for offer in array:
            self.points.append(offer[0])
            self.titles.append(offer[1])
            self.descriptions.append(offer[2])
            self.links.append(offer[3])

    def get_array(self):
        array = []
        for points, title, description, link in zip(self.points, self.titles, self.descriptions, self.links):
            array.append((points, title, description, link))

        return array

    def delete_redundant(self):
        array = self.get_array()
        list_of_offers = []
        temp_list = []

        current_points = 0
        for offer in array:
            if offer[0] != current_points:
                current_points = offer[0]

                for temp_offer in temp_list:
                    list_of_offers.append(temp_offer)

                temp_list = [offer]
            elif offer not in temp_list:
                temp_list.append(offer)

        for temp_offer in temp_list:
            list_of_offers.append(temp_offer)

        self.clear_offers()
        for offer in list_of_offers:
            self.points.append(offer[0])
            self.titles.append(offer[1])
            self.descriptions.append(offer[2])
            self.links.append(offer[3])

    def delete_below_threshold(self, threshold):
        new_points = []
        new_titles = []
        new_descriptions = []
        new_links = []

        for points, title, description, link in zip(self.points, self.titles, self.descriptions, self.links):
            if points >= threshold:
                new_points.append(points)
                new_titles.append(title)
                new_descriptions.append(description)
                new_links.append(link)

        self.points = new_points
        self.titles = new_titles
        self.descriptions = new_descriptions
        self.links = new_links

    def clear_offers(self):
        self.points.clear()
        self.titles.clear()
        self.descriptions.clear()
        self.links.clear()


def analyze_words_from_offers(clean_database, tag_analysis_results):
    file = codecs.open(clean_database, 'r', encoding='latin-1')

    temp_points = []
    temp_titles = []
    for line in file:
        temp = line.split(sep='|')
        temp_points.append(int(temp[0]))
        temp_titles.append(temp[1])

    file.close()

    evaluated_words = []
    new_words = []
    new_count = []
    new_points = []
    new_points_squared = []

    for points, title in zip(temp_points, temp_titles):
        temp_array = split_title(title)

        for word in temp_array:
            if len(word) > 1:
                if word not in new_words:
                    new_words.append(word)
                    new_count.append(1)
                    new_points.append(points)
                    new_points_squared.append(points ** 2)
                else:
                    index = new_words.index(word)
                    new_count[index] += 1
                    new_points[index] += points
                    new_points_squared[index] += points ** 2
    threshold = 0
    for word, count, points, points_squared in zip(new_words, new_count, new_points, new_points_squared):
        evaluated_words.append((word, count, points, points_squared))
        if count > threshold:
            threshold = count
    threshold = threshold ** (1./3.)

    evaluated_words.sort(key=lambda x: x[3] / x[1], reverse=True)
    file = codecs.open(tag_analysis_results, 'w', encoding='latin-1')
    for word in evaluated_words:
        if word[1] > threshold:
            file.write(str(word[3]) + '  /  ' + str(word[1]) + '  -  ' + word[0] + '\n')
    file.close()


def split_title(title):
    title = title.replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('\\u0026', '&').lower()
    return title.split()
