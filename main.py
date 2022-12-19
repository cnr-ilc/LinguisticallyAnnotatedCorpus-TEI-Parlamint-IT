
import io
import os
import sys
import stanza

from gestoreXml import *
from gestoreStanza import *

from gestoreXml import __dictionaryIDtoSpan

import json

from lxml import etree

import pprint

from itertools import tee
from itertools import pairwise

from pathlib import Path

import os.path

from stanza.pipeline.core import DownloadMethod


from stanza.models.common.doc import Document
from stanza.utils.conll import CoNLL

#fileLogName = "log.txt"
#fileLog = open(fileLogName, 'a', encoding='utf-8')

def isCompound(xmlId) :

    idx = xmlId.rfind(".")

    return (xmlId.find("-",idx) != -1)


def addJoin(sentence):

    global __dictionaryIDtoSpan

    xmlIdAttribute = '{http://www.w3.org/XML/1998/namespace}id'
    keySentence = sentence.get(xmlIdAttribute)
    __tokenIdtoSpan = __dictionaryIDtoSpan[keySentence]

    # prima costruisco la mappa associativa tra __joinMap : ID ---> bool
    # che per ogni elemento token node (solo i <w> e <pc> ?) associa true o false all'xml:id
    # a seconda che debba essere settato join=right oppure no

    __joinMap  = {}

    cercaSuccessivoDelComposto = False
    keyInSospeso = ""
    spanEndKeyinSospeso = ""

    lastKey = ""

    # print("entro in addJoin con sentence id == " + keySentence)

    # pprint.pprint(__tokenIdtoSpan)


    #elements = __tokenIdtoSpan.iter()
    for current, next in pairwise(__tokenIdtoSpan.items()):
        # print(type(current))
        # print(current)
        # print(type(next))
        # print(next)
        currentKey = current[0]
        spanEndCurrent = current[1][1]
        spanInitNext = next[1][0]
        lastKey = next[0]
        if isCompound(currentKey):
            cercaSuccessivoDelComposto = True
            keyInSospeso = currentKey
            spanEndKeyinSospeso = spanEndCurrent
        if cercaSuccessivoDelComposto and spanInitNext.isdigit() :
            __joinMap[keyInSospeso] = (spanEndKeyinSospeso == spanInitNext)
            cercaSuccessivoDelComposto = False
            keyInSospeso = ""
            spanEndKeyinSospeso = ""
        __joinMap[currentKey] = (spanEndCurrent == spanInitNext)
        # print(__joinMap[currentKey])

    # dovrebbe mancare l'ultimo elemento da settare....
    # sempre che sia entrato nell'iterazione con pairwise ovvero almeno 2 elementi....
    if len(__tokenIdtoSpan) == 1 :
        key = list(__tokenIdtoSpan.keys())[0]
        __joinMap[key] = False
    else :
        __joinMap[lastKey] = False


    # attenzione questa stampa è dentro la cartella della seduta......
    # tf = open("fileLogJson.txt", "a")
    # json.dump(__joinMap, tf, indent=4)
    # tf.close()

    # pprint.pprint(__joinMap)



    # ora si setta il campo join....

    #for tokenNode in sentence:
    for tokenNode in sentence.iter():
        if tokenNode.tag == "w" or tokenNode.tag == "pc":
            key = tokenNode.get(xmlIdAttribute)
            print(key)
            if __joinMap[key]:
                tokenNode.set("join","right")


    return sentence


def mainValidate() :

    annoSedute = sys.argv[1]

    #schemaRelaxNG = sys.argv[2]

    dirSchemaRelaxNG = "C:\\MinGW\\msys\\1.0\\home\\Roberto\\zonaVisualC++2006_source_projc\\Parlamint_2\\schema\\"

    #os.chdir(dirSchemaRelaxNG)

    schema_TEI = dirSchemaRelaxNG + "ParlaMint-TEI.rng"
    schema_ana = dirSchemaRelaxNG + "ParlaMint-TEI.ana.rng"
    #mySchema = dirSchemaRelaxNG + "ParlaMint_mySchema.rng"

    with open(schema_ana) as f:
    #with open(schema_TEI) as f:
        relaxng_doc = etree.parse(f)



    relaxng = etree.RelaxNG(relaxng_doc)

    with open("2013_prova\ParlaMint-IT_2013-03-16-LEG17-Sed-2.ana.xml") as g:
    #with open("..\\ZonaPython\\2013_prova\\prova_validazione.xml") as g:
    #with open("2013_redux\ParlaMint-IT_2013-03-15-LEG17-Sed-1.ana.xml") as g:
    #with open("2013_redux\ParlaMint-IT_2013-03-15-LEG17-Sed-1.xml") as g:
        doc = etree.parse(g)

    if not print(relaxng.validate(doc)) :
        print(relaxng.error_log)




def main():


    #stanza.download('it')  # download it model
    #nlp = stanza.Pipeline('it')  # initialize it neural pipeline
    nlp = stanza.Pipeline('it', download_method=DownloadMethod.REUSE_RESOURCES)

    ET.register_namespace('','http://www.tei-c.org/ns/1.0')

    annoSedute = sys.argv[1]

    DirectoryParent = os.getcwd()

    for filename in os.listdir(annoSedute):
        os.chdir(DirectoryParent)
        os.chdir(annoSedute)
        if not os.path.isdir(filename) and filename.find(".ana.xml") == -1 and filename.find("fileLogJson") == -1:
            # e nemmeno un file già analizzato....
            # e nemmeno il file di Log
            # print("primo Ciclo for " + filename, end=" ")
            # print(os.getcwd())
            outDirectorySeduta = Path(filename).stem
            if not os.path.isdir(outDirectorySeduta): # controllo che non sia stata già creata
                os.mkdir(outDirectorySeduta)  # crea una directory con lo stesso nome della seduta
            # CURR_DIR = os.getcwd()
            # print(CURR_DIR)
            tree = ET.parse(filename)
            #segAndTestoPairList = ExtractListSegFrom(filename, tree)
            segmentList = ExtractListSegFrom(filename, tree)
            os.chdir(outDirectorySeduta)
            #for (segmento, testo) in segAndTestoPairList:
            for segmentElement in segmentList:
                # print("   secondo Ciclo for with " + segmento, end = " ")
                # print(os.getcwd())
                id_segmento = segmentElement.attrib['{http://www.w3.org/XML/1998/namespace}id']
                testo = segmentElement.text
                nomeFileOutput = id_segmento + ".ud.udner"
                doc = nlp(testo)
                myCoNLL.write_doc2conll(doc, nomeFileOutput)

                newElementSegment = elementSegXml(doc, id_segmento)

                segmentElement.text = "" #  cancello il testo di segmentElement

                for sentence in newElementSegment:
                    sentence = addJoin(sentence)
                    segmentElement.append(sentence)

            os.chdir(DirectoryParent)
            os.chdir(annoSedute)
            tree.write(Path(filename).stem + ".ana.xml",encoding="UTF-8")

    #fileLog.close()

    tf = open("fileLogJson.txt", "a")
    json.dump(__dictionaryIDtoSpan, tf, indent=4)
    tf.close()








main()
#mainValidate()

