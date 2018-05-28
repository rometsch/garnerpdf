import os
import fitz
import argparse

def showPDFonNewPage(trgt, src, pno):
	spage = src[pno]
	page.showPDFpage(trgt.rect, src, pno)

def findPDFrecursive(rootdir):
    paths = []
    # traverse directory, and collect the paths of PDF files
    for root, dirs, files in os.walk(rootdir):
        for file in files:
            if file[-4:] == ".pdf":
                paths.append( os.path.join( root, file) )
    return paths

parser = argparse.ArgumentParser()
parser.add_argument("outfile", help="Output file")
parser.add_argument("input", nargs="+", help="A list of files and or directories to be included. In case of a directory, it is recursively searched for pdf files.")
args = parser.parse_args()

outfile = args.outfile

pdffiles = []
for path in args.input:
    if os.path.isdir(path):
        pdffiles += findPDFrecursive(path)
    else:
        if path[-4:] == ".pdf":
            pdffiles.append(path)


doc = fitz.open()

pagesize="A4"
width, height = fitz.PaperSize(pagesize)



for path in pdffiles:
	print("adding {}".format(path))
	incremental = doc.pageCount > 0 # need an initial document for incremental save

	src = fitz.open(path)
	for n in range(src.pageCount):
		page = doc.newPage(-1, width = width, height = height)
		showPDFonNewPage(page, src, n)

		doc.save(outfile,
				 #garbage = 4, # eliminate duplicate objects
				 deflate = True, # compress stuff where possible
				 incremental=incremental)

	doc = fitz.open(outfile)
