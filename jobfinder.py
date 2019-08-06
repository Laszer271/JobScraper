import tags
import scraping
import argparse
import os
import oanalyzing as oa
from oanalyzing import OfferAnalyzer
import time


def update_database(searchtags_file, town, database_file, intern=False):
    search_tags_manager = tags.TagManager()
    scraper = scraping.PracujplScraper()
    search_tags_manager.load_from_file(searchtags_file)
    list_of_urls = scraper.get_urls(search_tags_manager.get_array_of_tags(), town, intern=intern)
    responses = scraper.get_responses(list_of_urls)
    scraper.scrape_all(responses, list_of_urls)
    scraper.write_to_file(database_file)


def update_results(evaluationtags_file, database_file, threshold, output_file, cleandatabase_file=''):
    evaluation_tags_manager = tags.TagManager()
    evaluation_tags_manager.load_from_file(evaluationtags_file)
    analyzer = OfferAnalyzer(evaluation_tags_manager.get_array_of_tags())
    analyzer.load_from_file(database_file)

    analyzer.calculate_points()
    analyzer.sort_by_points()
    analyzer.delete_below_threshold(threshold)
    analyzer.delete_redundant()
    analyzer.save_to_file(output_file)

    if cleandatabase_file:
        analyzer.save_to_file(cleandatabase_file, machine_mode=True)


parser = argparse.ArgumentParser(description='Uses the tags that you have given to find the jobs that best suit you')
parser.add_argument('--search_tags', type=str, default='tags/search_tags.txt', help='the text file containing the tags that would be used to search for the job')
parser.add_argument('--evaluation_tags', type=str, default='tags/evaluation_tags.txt', help='the text file containing the tags that would be used to evaluate offers that were found')
parser.add_argument('--output_file', type=str, default="results/offers.txt", help='the output file. There will be sorted list of jobs that were found')
parser.add_argument('--threshold', type=int, default=0, help='the miniumum of points that the offer has to have in evaluation for it to be shown in the output file')
parser.add_argument('--database', type=str, default='databases/database.txt', help='specifies the database that the program will use. Better to leave it be as long as you don\'t use more than one database')
parser.add_argument('--town', type=str, default='', help='determines in which town the offers are searched for')
parser.add_argument('--words_analysis_output', type=str, default='words.txt', help='write here a file if you want to see some statistics of the words that are in the database_clean')
parser.add_argument('--database_clean', type=str, default='databases/database_clean.txt')
parser.add_argument('-intern_only', dest='intern', action='store_true', help='write ths flag if you want only intern offers to be shown to you')
parser.add_argument('-no_update', dest='update', action='store_false', help='write this flag if you want to update the database')
parser.add_argument('-no_results', dest='results', action='store_false', help='write tihs flag if you don\'t want the results in the output file to be updated. For example if you only want to update the database')
parser.set_defaults(intern=False)
parser.set_defaults(update=True)
parser.set_defaults(results=True)

args = parser.parse_args()

if not os.path.exists('databases'):
    os.makedirs('databases')
if not os.path.exists('tags'):
    os.makedirs('tags')
if not os.path.exists('results'):
    os.makedirs('results')


if args.update or not os.path.exists(args.database):
    print('Updating database, please wait\n')
    start = time.time()
    update_database(args.search_tags, args.town, args.database, intern=args.intern)
    end = time.time()
    print('time updating: %.2f' % (end - start) + 's')

if args.results:
    start = time.time()
    update_results(args.evaluation_tags, args.database, args.threshold, args.output_file, args.database_clean)
    end = time.time()
    print('time updating results: %.2f' % (end - start) + 's')

if args.words_analysis_output:
    start = time.time()
    oa.analyze_words_from_offers(args.database_clean, args.words_analysis_output)
    end = time.time()
    print('time analyzing: %.2f' % (end - start) + 's')

'''
file1 = open('databases/database_clean.txt', 'r').readlines()
file2 = open('databases/database_clean_kopia.txt', 'r').readlines()
count_linii1 = 0
count_linii2 = 0
count_niezgodnosci = 0
file2 = [line[: line.rfind('\n')] for line in file2]
print(len(file1))
print(len(file2))

for line2 in file2:
    count_linii2 += 1
for line1 in file1:
    count_linii1 += 1
    line1 = line1[: line1.rfind('\n')]
    if line1 not in file2:
        count_niezgodnosci += 1
        print(line1)
print('Niezgodnosci: ' + str(count_niezgodnosci))
'''
