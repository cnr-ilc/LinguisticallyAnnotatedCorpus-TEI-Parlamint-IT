


# from gestoreStanza import myCoNLL


import xml.etree.ElementTree as ET
# documentazione: https://docs.python.org/3.5/library/xml.etree.elementtree.html

import pprint

from gestoreStanza import *

__dictionaryIDtoSpan = {}

class Link:

    def __init__(self, r, h, d):
        self.rel = r
        self.head = h
        self.dipen = d

    def getRel(self):
        return self.rel
    def getHead(self):
        return self.head
    def getDipen(self):
        return self.dipen





def sonOf(element) :

    #print("sonOf <-- elemen  == ",end="")
    #print(element)
    children = list(element)

    if len(children)  == 0 :
        #print("warning 0 figli: ")
        #print(element)
        return element
    elif len(children)  > 1 :
        #print("warning più figli: ")
        #print(element)
        #return children[0]
        return children[-1]
    else :
        return children[0]




def parentOf(pila) :

    #print("+++++++++++++++++")
    #print(pila[0])
    #print(pila[1])
    #print("_________________")

    #parent = pila[1]
    #pila.pop(0)  # va consumato???

    return pila.pop(0)


    #return parent


def elementTagOf(tokenConll,pilaParent,xmlIdValueToken,compound=False) :

    xmlIdAttribute = '{http://www.w3.org/XML/1998/namespace}id'
    
    if tokenConll[FIELD_TO_IDX[UPOS]] == "PUNCT":
        elementToken = ET.Element('pc')
    else:
        elementToken = ET.Element('w')

    lemma = tokenConll[FIELD_TO_IDX[LEMMA]]
    xpos = tokenConll[FIELD_TO_IDX[XPOS]]
    upos = tokenConll[FIELD_TO_IDX[UPOS]]
    feats = tokenConll[FIELD_TO_IDX[FEATS]]
    msd = ""

    #print(tokenConll)
    #print("xpos: " + xpos + " - " + "upos: " + upos)




    elementToken.set(xmlIdAttribute, xmlIdValueToken)
    if compound :   #se siamo in un elemento composto else va nel txt
        elementToken.set("norm",tokenConll[FIELD_TO_IDX[TEXT]])
    else :
        elementToken.text = tokenConll[FIELD_TO_IDX[TEXT]]
    if (lemma != "_") :
        if tokenConll[FIELD_TO_IDX[UPOS]] != "PUNCT":
            elementToken.set("lemma",lemma)
    if (xpos != "_") :
        elementToken.set("pos",xpos)
    if (upos != "_") :
        msd = "UPosTag=" + upos
        if (feats != "_") :
            msd += "|" + feats
        elementToken.set("msd", msd)
    elif (feats != "_") :
            msd +=  feats
            elementToken.set("msd",msd)


    #pilaParent.insert(0, elementToken)


    return elementToken

def isCompoundElement(token) :

    id = token[FIELD_TO_IDX[ID]]

    return (id.find("-") != -1)

def numElementInCompound(token) :

    id = token[FIELD_TO_IDX[ID]]
    idx = id.find("-")

    init = int(id[0:idx])
    end = int(id[idx+1:])

    #print("numElementInCompuond == init " +  str(init))
    #print("numElementInCompuond == end " + str(end))
    #print("numElementInCompuond == " + str(end - init + 1) )

    return end - init + 1

def myStaticDecrement():    #static var

    if not hasattr(myStaticDecrement, "counter"):
         myStaticDecrement.counter = 2

    myStaticDecrement.counter -= 1

    #print("myStaticDecrement == " + str(myStaticDecrement.counter))

    return myStaticDecrement.counter

def namedEntityAutomata(elementCurrent, tokenConll, stato, pila, xmlIdValueToken) :

    ner = tokenConll[FIELD_TO_IDX[NER]]
    tagBio = ner[0:2]  # può essere: B-, I-, E-, S-, ovvero Begin, Internal, End, Singleton
    named = ner[2:]
    nextState = 0   #stato per default

    if stato == 0:
        if tagBio == "S-":
            elementNamed = ET.SubElement(elementCurrent, 'name')
            elementNamed.set("type", named)
            pila.insert(0, elementNamed)
            elementCurrent = elementNamed
            ##attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            ##e poi elementCurrent = parentOf(pila)
            elementCurrent = parentOf(pila)
            elementCurrent = pila[0]  # non lo consuma
            return(nextState, elementCurrent)
        elif tagBio == "B-":
            elementNamed = ET.SubElement(elementCurrent, 'name')
            elementNamed.set("type", named)
            pila.insert(0, elementNamed)
            elementCurrent = elementNamed
            ##attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            ##e poi elementCurrent rimane elementNamed
            nextState = 1
            return(nextState, elementCurrent)
        elif isCompoundElement(tokenConll) :
            # sono dentro un elemento composto ma non dentro una named!!
            myStaticDecrement.counter = numElementInCompound(tokenConll) -1
            temp = elementTagOf(tokenConll, pila, xmlIdValueToken)
            elementCurrent.append(temp)
            #elementCurrent = sonOf(elementCurrent)  # l'ultimo elemento visto: OCCHIO: NON è la prep articolata
            # attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent = temp
            pila.insert(0, elementCurrent)
            nextState = 3
            return (nextState, elementCurrent)
        elif tagBio == "-":   # caso normale di default
            ##attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            ##e poi elementCurrent rimane elementCurrent
            return(nextState, elementCurrent)

    elif stato == 1:  ## ho visto un B-
        if tagBio == "I-":  # siamo all'interno di un entità nominata
            ##attacca elementTagOf(tokenConll) to elementCurrent [che è elementNamed!!]
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            nextState = 1
            return(nextState, elementCurrent)
        if tagBio == "E-":  # siamo all'ultimo elemento di un entità nominata
            ##attacca elementTagOf(tokenConll) to elementCurrent [che è elementNamed!!]
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            ##e poi elementCurrent = parentOf(pila)
            elementCurrent = parentOf(pila)
            elementCurrent = pila[0]  # non lo consuma
            return(nextState, elementCurrent)
        if tagBio == "-":  # siamo nell'elemento composto (prep articolata) interna all'entità nominata
            ## attenzione che deve andare dopo il contenuto del nodo!!!!!!
            ## per cui deve essere figlio del nodo text!?!?!?!
            elementCurrent = sonOf(elementCurrent)   # l'ultimo figlio visto di named....
            # attacca elementTagOf(tokenConll) to elementCurrent
            pila.insert(0, elementCurrent)
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken,True))
            nextState = 2
            return(nextState, elementCurrent)

    elif stato == 2:  ## sono dentro una prep articolata dentro un'entità nominata
        if tagBio == "I-":  # usciamo dal composto e vediamo un elemento interno dell' entità nominata
            elementCurrent = parentOf(pila)
            elementCurrent = pila[0]  # non lo consuma
            # attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            nextState = 1
            return(nextState, elementCurrent)
        if tagBio == "E-":  # usciamo dal composto e vediamo l'ultimo elemento dell' entità nominata
            elementCurrent = parentOf(pila)
            elementCurrent = parentOf(pila)  ##il nonno (che dovrebbe essere il nodo <name>)
            # attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken))
            elementCurrent = pila[0]  # non lo consuma
            return(nextState, elementCurrent)
        if tagBio == "-":  # siamo ancora nell'elemento composto
            # attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken,True))
            nextState = 2
            return(nextState, elementCurrent)

    elif stato == 3:  ## sono dentro un elemento composto
        if myStaticDecrement.counter > 0:  # siamo ancora nell'elemento composto
            elementCurrent.append(elementTagOf(tokenConll, pila, xmlIdValueToken,True))
            nextState = 3
            myStaticDecrement()
            return (nextState, elementCurrent)
        if myStaticDecrement.counter == 0:  # usciamo dal composto
            # attacca elementTagOf(tokenConll) to elementCurrent
            elementCurrent = parentOf(pila)
            elementCurrent.append(elementTagOf(tokenConll,pila,xmlIdValueToken,True))
            elementCurrent = pila[0] #non lo consuma
            nextState = 0
            return(nextState, elementCurrent)



def ExtractListSegFrom(fileTeiXml, tree):

    print("Call ExtractListSegFrom <-- " + fileTeiXml)

    #tree = ET.parse(fileTeiXml)
    root = tree.getroot()

    segTag = '{http://www.tei-c.org/ns/1.0}seg'
    xmlIdAttribute = '{http://www.w3.org/XML/1998/namespace}id'

    result = []

    #pippo = [elem.tag for elem in root.iter()]
    #pippo = [elem.attrib for elem in root.iter()]
    #print(pippo)

    #for segmento in root.iter(segTag):
    for segmentElement in root.iter(segTag):
        #print(segmento.attrib[xmlIdAttribute])
        #print(segmento.attrib)
        #print(segmento.text)
        #result.append((segmento.attrib[xmlIdAttribute],segmento.text))
        result.append(segmentElement)

    """
    textTag = ET.SubElement(root, "text")      # root ha 2 figli, uno con tag == text
    bodyTag = ET.SubElement(textTag, "body")   # element text ha un solo sub nodo di nome body
    for child in bodyTag:      # il nodo body ha tanti nodi div ognuno con un solo tag u
        divTag = ET.SubElement(child, "div")
        uTag =   ET.SubElement(divTag, "u")
        for segmento in uTag :
            print(segmento.attrib["xml:id"])
            print(segmento.text)
    """
    #result = [("sed1", "Io posso comprare questo libro."), ("sed2", "Il miglior giocatore della squadra.")]

    return result

def getInitSpan(misc):
    # misc è della forma: start_char=xxx|end_char=yyy
    #print(misc)

    j = misc.find("|")

    if "start" in misc and "|" in misc and j > 11:
        return misc[11:j]             # nota che |start_char=| == 11
    else :
        return "warning_getInitSpan"



def getEndSpan(misc):

    j = misc.rfind("=")

    if "end_char=" in misc :
        return misc[j+1:]
    else:
        return "warning_getEndSpan"


def elementSegXml(doc, nomeSegmento):

    #nomeFileOutput = nomeSegmento + ".ud.udner"
    #myCoNLL.write_doc2conll(doc, nomeFileOutput)
    #print("Call elementSegXml <-- " + nomeSegmento)

    global __dictionaryIDtoSpan


    xmlIdAttribute = '{http://www.w3.org/XML/1998/namespace}id'
    elementSeg = ET.Element('seg')
    elementSeg.set(xmlIdAttribute,nomeSegmento)

    pilaParent = []

    pilaParent.insert(0,elementSeg)

    numSentence = 0
    for sentence in doc.sentences:
        numSentence += 1
        xmlIdValueSentence = nomeSegmento + "." + str(numSentence)
        #print("sentence: type == ", end = "")
        #print(type(sentence))
        elementSentence = ET.SubElement(elementSeg,'s')
        elementSentence.set(xmlIdAttribute,xmlIdValueSentence)

        pilaParent.insert(0, elementSentence)

        stato = 0
        #internal = False #non dovrebbe servire più....
        linkGrp = []

        elementCurrent = elementSentence

        __tokenIDtoSpan = {}


        for token_dict in sentence.to_dict():
            token_conll = myCoNLL.convert_token_dict(token_dict)
            idToken = token_conll[FIELD_TO_IDX[ID]]
            xmlIdValueToken = xmlIdValueSentence + "." + idToken
# FIELD_TO_IDX = {ID: 0, TEXT: 1, LEMMA: 2, UPOS: 3, XPOS: 4, FEATS: 5, HEAD: 6, DEPREL: 7, DEPS: 8, MISC: 9, NER: 10}

            # costruisco il linkGrp
            if token_conll[FIELD_TO_IDX[DEPREL]] != "_" and token_conll[FIELD_TO_IDX[DEPREL]] != "<PAD>" :
                #r = token_conll[FIELD_TO_IDX[DEPREL]]
                r = token_conll[FIELD_TO_IDX[DEPREL]].replace(':','_')
                if token_conll[FIELD_TO_IDX[HEAD]] == "0" :
                    h = ""
                else :
                    h = token_conll[FIELD_TO_IDX[HEAD]]
                d = token_conll[FIELD_TO_IDX[ID]]
                a = Link(r,h,d)
                linkGrp.append(a)

            # costruisco anche   __tokenIDtoSpan
            spanInit = getInitSpan(token_conll[FIELD_TO_IDX[MISC]])
            spanEnd = getEndSpan(token_conll[FIELD_TO_IDX[MISC]])

            #print(token_conll[FIELD_TO_IDX[MISC]] + "----->" + spanInit + "-----" + spanEnd)

            __tokenIDtoSpan[xmlIdValueToken] = (spanInit,spanEnd)

            #print("namedEntityAutomata : tokenId = " + xmlIdValueToken )
            #print(pilaParent)
            (stato, elementCurrent) = namedEntityAutomata(elementCurrent, token_conll, stato, pilaParent,xmlIdValueToken)
            #print(pilaParent)

            #pilaParent.pop(0)

        #aggiunge il Group di relazioni
        elementLinkGroup = ET.SubElement(elementSentence, 'linkGrp')
        elementLinkGroup.set("targFunc", "head argument")
        elementLinkGroup.set("type", "UD-SYN")

        __tokenIdtoSpan = __dictionaryIDtoSpan[xmlIdValueSentence] = __tokenIDtoSpan


        for l in linkGrp:
            elementLink = ET.SubElement(elementLinkGroup, 'link')
            elementLink.set("ana", "ud-syn:" + l.getRel())
            if l.getHead() == "" :   # è la root
                head = "#" + xmlIdValueSentence
            else :
                head = "#" + xmlIdValueSentence + "." + l.getHead()
            dip = "#" + xmlIdValueSentence  + "." + l.getDipen()
            elementLink.set("target", head + " " + dip)

        pilaParent.pop(0)

    #ET.dump(elementSeg)

    return elementSeg


