import requests
from winmagic import magic
import PyPDF2
import re
import textdistance
import time
import xlrd
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from textblob import TextBlob
from nltk.probability import FreqDist
import unicodedata
################################################################
###################### Uma funcao para cada formato
################################################################



def padrao_utf8(frase):
    texto_limpo = unicodedata.normalize('NFKD', frase)
    return str.lower(u"".join([c for c in texto_limpo if not unicodedata.combining(c)]))


def get_pdf():
    texto = []
    try:
        leitor = PyPDF2.PdfFileReader(open('Dataset/dataset', 'rb'))
        try:
            for pagina in range(leitor.numPages):
                documento = leitor.getPage(pagina)
                documento = documento.extractText()
                texto.append(documento)
        except:
            print("PDF Codigficado")
    except:
        print("File type not PDF!")
    return(texto)
#a
def get_csv():
    texto = []
    try:
        #chardet.detect('dataset')
        encoding = (re.search(r'([^\s]+)',(magic.from_file("Dataset/dataset", mime=False))).group(0)).lower()
        if encoding == 'iso-8859':
            encoding = 'latin-1'
        for linha in open('Dataset/dataset', encoding=encoding).readlines():
            leitor = (str(linha).strip().split(';'))
            for palavra in leitor:
                #texto.append(padrao_utf8(palavra))
                texto.append(palavra)
    except:
        print("File type not CSV!")
    return(texto)


def get_html():
    texto=[]
    try:
        leitor = BeautifulSoup(open('Dataset/dataset', 'rb'),"html.parser")
        paragrafos = leitor.find_all('p')
        for frase in paragrafos:
            texto.append(str([re.sub(r'<.+?>',r'',str(a)) for a in frase]))
    except:
        print("File type not HTML!")
    return(texto)

def get_xls():
    texto=[]
    try:
        encoding = (re.search(r'([^\s]+)',(magic.from_file("Dataset/dataset", mime=False))).group(0)).lower()
        book = xlrd.open_workbook("Dataset/dataset",encoding_override=encoding)
        for sheet in range(book.nsheets):
            sh = book.sheet_by_index(sheet)
            for rx in range(sh.nrows):
                for cell in sh.row_values(rx):
                    texto.append(str(cell))
    except:
        print("File type not XLS or XLSX!")
    return(texto)

# =============================================================================
# Stem
# =============================================================================

#Funcao para extrair o radical das palavras
def radical(lista):
    from nltk.stem.snowball import SnowballStemmer
    radical = []
    stemmer = SnowballStemmer("portuguese")
    for palavra in lista:
        radical.append(stemmer.stem(palavra))
    return(radical)


################################################################
###################### API do Ckan
################################################################

pagina = requests.get('http://35.184.224.70/api/action/package_list').json()
base = 'http://35.184.224.70/dataset/'
acumulado = {}

for dataset in pagina.get('result'):
    print(base+dataset)
    sobre_dataset = requests.get(f'http://35.184.224.70/api/3/action/package_show?id={dataset}').json()
    for loop in range(len(sobre_dataset.get('result')['resources'])):
        #print(sobre_dataset.get('result')['resources'][loop].get('url'))
        url = sobre_dataset.get('result')['resources'][loop].get('url')
        download = requests.get(url, allow_redirects=True)
        open('Dataset/dataset', 'wb').write(download.content)
        if sobre_dataset.get('result')['resources'][loop].get('url')[-4:] == '.pdf':
            coleta = get_pdf()
        elif sobre_dataset.get('result')['resources'][loop].get('url')[-4:] == '.csv':
            coleta = get_csv()
        elif sobre_dataset.get('result')['resources'][loop].get('url')[-4:] == '.xls' or sobre_dataset.get('result')['resources'][loop].get('url')[-4:] == 'xlsx':
            coleta = get_xls()
        else:
            coleta = get_html()

        if coleta != '':
            if base+dataset in acumulado:
                # append the new number to the existing array at this slot
                acumulado[base+dataset].append(coleta)
            else:
                acumulado[base+dataset] = coleta





# =============================================================================
# Limpando o texto (matem acentuacao)
# =============================================================================
#from translate import Translator
# translator= Translator(from_lang="portuguese",to_lang="english")
# translation = translator.translate("Insecto")
# print translation


#corpus_completo = []
corpus_stem = {}
#translator = Translator()
for key, value in acumulado.items():
    token = (' '.join(re.findall(r'(\b[A-Za-zÀ-ÿ]{3,20}\b)', str(value).lower().replace("\\n",' ')))).split()
    if token != []:
        vinte = ' '.join(token[:20])
        blob = TextBlob(vinte)
        if blob.detect_language() != 'pt':
            token = (str(blob.translate(to="pt"))).split()
    clean = [word for word in token if word not in stopwords.words('portuguese')]
    #corpus_completo.append(clean)
    if key in corpus_stem:
        # append the new number to the existing array at this slot
        corpus_stem[key].append(radical(clean))
    else:
        corpus_stem[key] = radical(clean)
    #corpus_stem.append(radical(clean))



# =============================================================================
# TF-IDF
# =============================================================================
corpus = corpus_stem.copy()

soma = 0 ##### soma = 3.444.365
for i in corpus_stem.values():
    #print(i)
    for x in i:
        soma += len(x)

wordSet = set().union(*corpus.values())
#len(wordSet) # 22.340

wordSet = set().union(*corpus.values())
#len(wordSet) # 22.340

newDict = {}
for key in corpus.keys():
    newDict[key] = dict.fromkeys(wordSet, 0)


#newDict[key]['minist']

for i in newDict.keys():
    for word in corpus[i]:
        newDict[i][word]+=1

#len(newDict.get(i))

# TF
def computeTF(wordDict, bow):
    try:
        tfDict = {}
        bowCount = len(bow)
        for word, count in wordDict.items():
            tfDict[word] = count/float(bowCount)
    except:
        print('Error')
    return tfDict

def computeIDF(docList):
    import math
    idfDict = {}
    N = len(docList)

    idfDict = dict.fromkeys(docList[0].keys(), 0)
    for doc in docList:
        for word, val in doc.items():
            if val > 0:
                idfDict[word] += 1

    for word, val in idfDict.items():
        idfDict[word] = math.log10(N / float(val))

    return idfDict




tfidf = {}
for i in newDict.keys():
    tfidf[i] = computeTF(newDict.get(i), corpus.get(i))


count = 0
for key in tfidf.keys():
    print(key)
    fdist = FreqDist(tfidf.get(key))
    for word in fdist:
        if fdist[word] > 0.009:
            print(word, round(fdist[word],3))
            count += 1

# =============================================================================
# Top keywords
# =============================================================================
count = 1
with open('tags_versao_4.rdf','a') as rdf:
    rdf.write('''<?xml version="1.0" encoding="UTF-8"?>

<rdf:RDF
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcat="http://www.w3.org/ns/dcat#"
    xmlns:dct="http://purl.org/dc/terms/"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">''')

    pagina = requests.get('http://35.184.224.70/api/action/package_list').json()
    base = 'http://35.184.224.70/dataset/'


    for dataset, key in zip(pagina.get('result'), tfidf.keys()):
        sobre_dataset = requests.get(f'http://35.184.224.70/api/3/action/package_show?id={dataset}').json()
        name_dataset = padrao_utf8(sobre_dataset.get('result')['title'])
        description = padrao_utf8(sobre_dataset.get('result')['notes'])[:600]
        print(base+dataset)
        dataset_url = base+dataset
        rdf.write(f'''
    <dcat:Dataset rdf:about="{dataset_url}">
        <dct:title>{name_dataset}</dct:title>
        <dct:description>{description}</dct:description>''')

        fdist = FreqDist(tfidf.get(key))
        for word in fdist:
            if fdist[word] > 0.009:
                #print(word, round(fdist[word],3))
                coleta = requests.get(f'http://agrovoc.uniroma2.it/agrovoc/rest/v1/search/?query={word}*&lang=pt',timeout=10).json()
                #time.sleep(5)
                if coleta.get('results') != []:
                        total = {}
                        label = {}
                        for linha in range(len(coleta.get('results'))):
                            #print(linha)

                            total[coleta.get('results')[linha].get('uri')] = textdistance.jaro_winkler(word,coleta.get('results')[linha].get('prefLabel'))

                            label[coleta.get('results')[linha].get('uri')] = coleta.get('results')[linha].get('prefLabel')

                        top = FreqDist(total)
                        top1 = (top.most_common(1)[0][0])
                        print(word, label[top1], top.most_common(1)[0][0], top.most_common(1)[0][1])
                        rdf.write(f'''
        <dcat:keyword rdf:resource="{top1}"></dcat:keyword>''')

        for resource in sobre_dataset.get('result')['resources']:
            resource_url = padrao_utf8(resource.get('url'))
            resource_name = padrao_utf8(resource.get('name'))
            resource_desc = padrao_utf8(resource.get('description'))
            resource_format = padrao_utf8(resource.get('format'))
            rdf.write(f'''
        <dcat:distribution>
            <dcat:Distribution rdf:about="{resource_url}">
                <dct:title>{resource_name}</dct:title>
                <dct:description>{resource_desc}</dct:description>
                <dct:format>{resource_format}</dct:format>
            </dcat:Distribution>
        </dcat:distribution>''')

        time.sleep(5)
        print(count)
        count += 1
        rdf.write(f'''
    </dcat:Dataset>''')

    rdf.write(f'''
</rdf:RDF>
''')
