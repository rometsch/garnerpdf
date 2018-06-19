#!/usr/bin/env python3
import os
import fitz
import argparse

def showPDFonNewPage(page, src, pno, pos):
	spage = src[pno]
	if spage.rotation != 0 and pos == 0:
		page.setRotation(spage.rotation)

	if pos == 1:
		rect = page.rect
		rect.y1 = rect.y1/2
	elif pos == 2:
		rect = page.rect
		rect.y0 = rect.y1/2
	else:
		rect = page.rect

	#print(spage.rotation)
	page.showPDFpage(rect, src, pno)
	#print("pos {}, {}".format(pos, rect))
	page.setRotation(0)

def findPDFrecursive(rootdir):
    paths = []
    # traverse directory, and collect the paths of PDF files
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if file[-4:] == ".pdf":
                paths.append( os.path.join( root, file) )
    return paths

def sortFiles(filenames, sep, nsort):
	""" Parse the filenames to extract an identifier to sort by.
	Given a filename 'a-b-n.ext', choose sep=- and nsort=2 to sort
	by the number n right before the extention.
	Returns an index array to access the filenames. """
	features = [s.split(sep)[nsort] for s in filenames]
	# now use a fancy sort of argsort from
	# https://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python
	return [x for x,y in sorted(enumerate(features), key = lambda x: x[1])]
	#return sorted(range(len(features)), key=features.__getitem__)

def pageOrientation(page):
	""" Get the orientation for a pymupdf page object."""
	sw, sh = page.bound()[2:]
	print('page detected with width {} x height {}'.format(sw, sh))
	if sw < sh:
		return "portrait"
	else:
		return "landscape"



parser = argparse.ArgumentParser()
parser.add_argument("outfile", help="Output file")
parser.add_argument("input", nargs="+", help="A list of files and or directories to be included. In case of a directory, it is recursively searched for pdf files.")
parser.add_argument("--sep", default="_", help="Split up the filename to try to sort files by.")
parser.add_argument("--nsort", default=-2, type=int, help="Sort the filename by the nsort-th feature in the filename as split by separator sep. Can also use negative numbers to use python list indexing.")
args = parser.parse_args()

outfile = args.outfile

pdffiles = []
for path in args.input:
    if os.path.isdir(path):
        pdffiles += findPDFrecursive(path)
    else:
        if path[-4:] == ".pdf":
            pdffiles.append(path)

# Try to sort after 3rd part in filename
try:
	idx = sortFiles([os.path.basename(s) for s in pdffiles], args.sep, args.nsort)
	pdffiles = [pdffiles[i] for i in idx]
	print([os.path.basename(s) for s in pdffiles])
except Exception as e:
	print("Something went wrong while sorting filenames, continuing without:")
	print(e)

doc = fitz.open()

pagesize="A4"
width, height = fitz.PaperSize(pagesize)



for path in pdffiles:
	print("adding {}".format(path))
	incremental = doc.pageCount > 0 # need an initial document for incremental save

	# flag for printing two landscape pages onto portrait
	isFirstLandscape = True

	src = fitz.open(path)
	for n in range(src.pageCount):
		if ( pageOrientation(src[n]) == "portrait" ):
			pos = 0
			page = doc.newPage(-1, width = width, height = height)
		else:
			print ('landscape')
			if isFirstLandscape:
				pos = 1
				isFirstLandscape = False
				page = doc.newPage(-1, width = width, height = height)
			else:
				pos = 2
				isFirstLandscape = True
				page = doc[-1]

		showPDFonNewPage(page, src, n, pos=pos)

		doc.save(outfile,
				 #garbage = 4, # eliminate duplicate objects
				 deflate = True, # compress stuff where possible
				 incremental=incremental)

	print('')

	doc = fitz.open(outfile)
