import re

import pymysql.cursors
import nltk
from nltk import word_tokenize
from nltk.corpus import wordnet as wn
from string import punctuation
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem.lancaster import LancasterStemmer
from flask import Flask
from flask_restful import Api, Resource, reqparse
import json
import xlwt
from connect import connection as cn
import pprint
# nltk.download('averaged_perceptron_tagger')
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')


def create_connection_example(idPlug):
    connection = cn()

    try:
        with connection.cursor() as cursor:
            # SQL
            sql = "SELECT string FROM wp_sample"
            # Выполнить команду запроса (Execute Query).
            cursor.execute(sql)
            rows = cursor.fetchall()
            strArticleExample = json.dumps(rows)
            result = analysis(strArticleExample)
            normalization(result)
            # excel(result)
            return result
    finally:
        # Закрыть соединение (Close connection).
        connection.close()


def create_connection(idPlug):
    connection = cn()

    # resultAnalysesExample = create_connection_example(id)
    # result = {}
    listDict = []

    try:
        with connection.cursor() as cursor:
            sql = "SELECT wp_article.name, wp_article.id FROM wp_article INNER JOIN wp_journal ON " \
                  "wp_article.journal_id = wp_journal.id INNER JOIN wp_select_journal ON wp_journal.name = " \
                  "wp_select_journal.name"
            # Выполнить команду запроса (Execute Query).
            cursor.execute(sql)
            Articles = cursor.fetchall()
            for i in Articles:
                sql = "SELECT wp_article_section_text.text FROM wp_article_section_text INNER JOIN " \
                      "wp_article_section_title ON wp_article_section_text.article_title_id = " \
                      "wp_article_section_title.id INNER JOIN wp_article ON wp_article_section_title.wp_article_id = " \
                      "wp_article.id WHERE wp_article.id = " + str(i['id'])
                cursor.execute(sql)
                ArticleText = cursor.fetchall()
                strArticle = json.dumps(ArticleText)
                resultAnalyses = analysis(strArticle)
                resultNormalization = normalization(resultAnalyses)
                listDict.append(resultNormalization)
                # excel(resultAnalyses, str(i['name']))
                # resultComparison = comparison(resultAnalysesExample, resultAnalyses)
                # result[i['id']] = resultComparison
    finally:
        connection.close()
    listDict = mean(listDict)
    words1 = vector(listDict)
    excelvector(words1, listDict, Articles, "result", 0)
    excelvector(words1, listDict, Articles, "result1", 1)
    excelvector(words1, listDict, Articles, "result2", 2)
    excelvector(words1, listDict, Articles, "result3", 3)
    # excel(i, str(articles[k]['name']))

    # return result


def analysis(text):
    wnl = WordNetLemmatizer()
    stemmer = LancasterStemmer()
    words = {}
    words1 = {}
    switchTagger = {
        "NN": "n",
        "VBP": "v",
        "JJ": "a",
        "RB": "r"
    }

    text = ' '.join(filter(None, (word.strip(punctuation) for word in text.split())))
    text = text.lower()
    count = len(text.split())
    relativeWhole = 1 / count
    # print(relativeWhole)

    for word in text.split():
        if word not in stopwords.words('english') and not any(map(str.isdigit, word)):
            word = wn.morphy(word)
            if word is not None:
                words[word] = words.get(word, 0) + relativeWhole  # в словарь добавляется последнее значение суммы

    words = dict(sorted(words.items(), key=lambda x: (-x[1], x[0])))
    # pprint.pprint(words, sort_dicts=False)

    # print('---------------------------------------------------------------------------------------------------------')
    b = 0
    for i in list(words):
        if words.get(i) is None:
            continue
        b += 1
        text = word_tokenize(i)
        if switchTagger.get(nltk.pos_tag(text)[0][1]) is not None:
            # fl = False
            try:
                word1 = i + "." + switchTagger.get(nltk.pos_tag(text)[0][1]) + ".01"
                word1 = wn.synset(word1)
                d = 0
                for j in list(words):
                    if words.get(j) is None:
                        continue
                    c = len(words)
                    d += 1
                    print("count:", c, "line:", b, "row:", d)
                    if c < d or c < b:
                        print("count:", c, "line:", b, "row:", d)
                    text = word_tokenize(j)
                    if switchTagger.get(nltk.pos_tag(text)[0][1]) is not None:
                        try:
                            word2 = j + "." + switchTagger.get(nltk.pos_tag(text)[0][1]) + ".01"
                            word2 = wn.synset(word2)
                            result = word1.path_similarity(word2)
                            if result > 0.1 and result != 1.0:
                                # fl = True
                                if words.get(j) > words.get(i):
                                    # words1[i[0]] = words1.get(j[0], j[1]) + i[1]
                                    words.update({j: words.get(j) + words.get(i)})
                                    words.pop(i)
                                    # if words1.get(j[0]) is not None:
                                    #     words1.update({j[0]: words.get(j[0]) + i[1]})
                                    # else:
                                    #     words1[i[0]] = {i[0]: i[1] + j[1]}
                                else:
                                    words.update({i: words.get(j) + words.get(i)})
                                    words.pop(j)
                                    # words1[i[0]] = words1.get(i[0], i[1]) + j[1]
                                    # words.update({i[0]: words.get(i[0]) + j[1]})
                                    # if words1.get(i[0]) is not None:
                                    #     words1.update({i[0]: words.get(i[0]) + j[1]})
                                    # else:
                                    #     words1[i[0]] = {i[0]: i[1] + j[1]}
                        except Exception:
                            continue
                # words.pop(i[0])
                # if not fl:
                #     words1[i[0]] = words1.get(i[0], i[1])
            except Exception:
                continue

    #
    # print('-----------------------------------------------------------------------------------------------------------')

    sort = sorted(words.items(), key=lambda x: (-x[1], x[0]))
    words = dict(sort)
    # pprint.pprint(words1, sort_dicts=False)
    return words


def comparison(words1, words2):
    counter = 0

    n = 0
    for i in words1.items():
        k = 0
        for j in words2.items():
            try:
                word1 = i[0] + '.n.01'
                word1 = wn.synset(word1)
                word2 = j[0] + '.n.01'
                word2 = wn.synset(word2)
                result = word1.path_similarity(word2)
                if result > 0.1:
                    counter += 1
                print(i[0], j[0], result)
            except Exception:
                continue
            if k == 10:
                break
            else:
                k += 1
        if n == 10:
            break
        else:
            n += 1

    if counter >= 5:
        return True
    else:
        return False


def normalization(words):
    words1 = {}
    xmax = max(words.values())
    xmin = min(words.values())
    for i in words.items():
        norm = (i[1] - xmin) / (xmax - xmin)
        words1[i[0]] = words.get(i[0], i[1]), norm, i[1], norm

    words1 = dict(sorted(words1.items(), key=lambda x: -x[1][0]))
    # pprint.pprint(words1, sort_dicts=False)
    return words1


def mean(listDict):
    for words in listDict:
        for i in words.items():
            fl = False
            sumElem = 1
            for words1 in listDict:
                if words != words1:
                    x = words1.get(i[0])
                    if x is not None:
                        sumElem += 1
                        if not fl:
                            sumAnalyse = i[1][0] + x[0]
                            sumNormalization = i[1][1] + x[1]
                            fl = True
                        else:
                            sumAnalyse = sumAnalyse + x[0]
                            sumNormalization = sumNormalization + x[1]
                        # words[i[0]] = i[1][0], i[1][1], sumAnalyse, sumNormalization
            else:
                words[i[0]] = i[1][0], i[1][1], (sumAnalyse/sumElem)-i[1][0], (sumNormalization/sumElem)-i[1][1]

    return listDict


def excelvector(words, listDict, articles, name, index):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('result')
    k = 0
    for words1 in listDict:
        ws.write(0, k+1, str(articles[k]['name']))
        n = 0
        for i in words.items():
            if words1.get(i[0]) is not None:
                ws.write(n+1, k+1, words1.get(i[0])[index])
            else:
                ws.write(n+1, k+1, 0)
            n += 1
        result = 0
        if listDict[0] != words1:
            for i in listDict[0].items():
                if words1.get(i[0]) is not None:
                    result += i[1][index] * words1.get(i[0])[index]
        ws.write(n+1, k+1, result)
        k += 1
    n = 0
    for i in words.items():
        ws.write(n+1, 0, i[0])
        n += 1
    try:
        name = re.sub(r"[\/:*?.%!@]", "", name)
        wb.save('../ExcelPython4/' + name + '.xls')
    except OSError:
        print('Некорректное название: ' + name)


def excel(words, name):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('result')
    k = 0
    for i in words.items():
        ws.write(k, 0, i[0])
        ws.write(k, 1, i[1][0])
        ws.write(k, 2, i[1][1])
        ws.write(k, 3, i[1][2])
        ws.write(k, 4, i[1][3])
        k += 1
    try:
        name = re.sub(r"[\/:*?.%!@]", "", name)
        wb.save('../ExcelPython3/' + name + '.xls')
    except OSError:
        print('Некорректное название: ' + name)


def vector(listDict):
    words1 = {}
    for words in listDict:
        for i in words.items():
            if words1.get(i[0]) is None:
                words1[i[0]] = i[0]
    return words1


# create_connection_example(1)
create_connection(15)

