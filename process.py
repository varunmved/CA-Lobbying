import re
import pandas as pd
import json
import requests_cache
import requests
from bs4 import BeautifulSoup

requests_cache.install_cache('google')
requests_cache.install_cache('bee_cache')

googleArticleList = []

'''
@param string filename
@return DataFrame df
'''
def readFile(filename):
    df = pd.read_csv(filename)
    df = df.fillna('')
    return df

'''
@param string searchTerm
@param string site
@param boolean useLiteral
'''
def createSearchQuery(searchTerm, useLiteral=True):
    literalStr = "%22"
    #siteStr = "+site:"
    termString = splitSearchTerm(searchTerm)
    if useLiteral == False:
        literalStr = ""
    query = literalStr + termString + literalStr #siteStr
    print(query)
    #site
    return query

'''
@param list searchTerm
@return string plusString
'''
def splitSearchTerm(searchTerm):
    if str(searchTerm) == '':
        return searchTerm
    else:
        searchTermList = searchTerm.split()
        plusString = ""
        for term in searchTermList:
            plusString += term + "+"
        return plusString

'''
@param string query
'''
def runSearch(query):
    searchUrl = "https://www.googleapis.com/customsearch/v1?q="
    cx = "&cx=013182954640320586502:2ru_2p3uep4"
    key = "&key=AIzaSyBfyhDRE9PPka6Rc4X4QQCS91L2X-_UIJg"
    result = requests.get(searchUrl + query + key + cx)
    return result

'''
@param request result
@returns list l
'''
def parseResult(searchTerm, result):
    a = result.text
    jresp = json.loads(a)
    print(jresp)
    #use this for relevance
    l = []
    outputDict = {}
    #print(jresp)

    if jresp['searchInformation']['totalResults'] == '0':
        outputDict['company'] = searchTerm
        outputDict['title'] = None
        outputDict['link'] = None
        outputDict['snippet'] = None
        outputDict['relevance'] = -1
        l.append(outputDict)

    else:
        j = jresp['items'][0]
        outputDict = {}
        outputDict['company'] = searchTerm
        outputDict['title'] = j['title']
        if 'sacbee' in j['link']:
            outputDict['link'] = j['link']
        else:
            outputDict['link'] = None
        outputDict['snippet'] = j['snippet']
        outputDict['relevance'] = 1
        l.append(outputDict)

    return outputDict
    #return l[0]

'''
@param dictionary d
@returns None
'''
def buildDataFrameFromDict(d, searchTerm):
    googleArticleList.append(d)

'''
@param string searchTerm
'''
def getGoogleResponses(searchTerm):
    query = createSearchQuery(searchTerm)
    result = runSearch(query)
    l = parseResult(searchTerm, result)
    return l

'''
@param dictionary
@returns string
'''
def getApiLink(d):
    return d['link']

'''
@param string url
@returns string body
'''
def getArticleBody(url):
    if url is None:
        return ""

    a = requests.get(url)

    #get the article body and title
    soup = BeautifulSoup(a.text)
    article = soup.find_all(id = "content-body-")
    sections = []

    #add all the <p> into a list
    for row in article:
        sections.append(row.get_text(strip=True))

    string = ""

    for elements in sections:
        string += elements

    return string

'''
@param string textBlob
'''
def getRelevanceCounts(textBlob):
    l = ['law', 'bill', 'regulation', 'congress']
    relevanceCount = 0
    for words in textBlob:
        words = preprocess(words)
        if words in l:
           relevanceCount += 1
    return relevanceCount

'''
@param string
'''
def preprocess(str_in):
    b = ""
    for a in str_in.split():
        lower = a.lower()
        lower = re.sub(r"[^\w\s]", '', lower)
        b += lower + " "
    return b

'''
@TODO: finish the driver
@ driver to run the program
'''
def run():
    df = readFile('minilobby.csv')
    #df = df.head()
    df['api'] = df['Client'].apply(getGoogleResponses)
    df['link'] = df['api'].apply(getApiLink)
    df['articleBody'] = df['link'].apply(getArticleBody)
    df['relevantCount'] = df['articleBody'].apply(getRelevanceCounts)
    df.sort(['relevantCount'], ascending=False)
    df.to_csv("test2.csv")
    return df

df = run()
