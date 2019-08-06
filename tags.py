import codecs


class TagManager:
    def __init__(self):
        self.tags = []

    def append_tag(self, tag_name, val=0):
        self.tags.append(Tag(tag_name, val))

    def clear_tags(self):
        self.tags = []

    def save_to_file(self, filename):
        file = codecs.open(filename, 'w+')

        for tag in self.tags:
            file.write(tag.name + '|' + str(tag.value) + '\n')
        file.close()

    def load_from_file(self, filename, clear_current=False):
        file = codecs.open(filename, "r")

        if clear_current:
            self.clear_tags()

        for line in file:
            index = line.find('|')
            self.tags.append(Tag(line[: index], int(line[index+1:])))
        file.close()

    def get_tag_index(self, tag_name):
        i = 0
        for tag in self.tags:
            if tag.name == tag_name:
                break
            i += 1
        return i

    def delete_tag(self, tag_name):
        del self.tags[self.get_tag_index(tag_name)]

    def change_value(self, tag_name, new_val):
        self.tags[self.get_tag_index(tag_name)].value = new_val

    def get_array_of_tags(self):
        return self.tags

    def sort_tags(self, reverse_order=True):
        self.tags.sort(key=lambda tag: tag.value, reverse=reverse_order)


class Tag:

    def __init__(self, name, value=0):
        self.name = name
        self.value = value
