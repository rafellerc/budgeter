import codecs
from ofxparse import OfxParser

with codecs.open('file.ofx') as fileobj:
    ofx = OfxParser.parse(fileobj)
