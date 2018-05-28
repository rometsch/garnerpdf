import os
import fitz
import argparse

def showPDFonNewPage(trgt, src, pno, pagesize="A4"):

    spage = src[pno]

    width, height = fitz.PaperSize(pagesize)
    page = trgt.newPage(-1, width = width, height = height)

    page.showPDFpage(page.rect, src, pno)


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dirs", nargs='*', default=[], help='directory to search recisively for pdf files')
parser.add_argument("-f", "--files", nargs='*', default= [], help='list of files to include')
args = parser.parse_args()

outfile = 'out.pdf'

pdffiles = args.files

for dir in args.dirs:
    l = os.listdir(dir)
    pdffiles += [os.path.join(dir, s) for s in l if s[-4:] == ".pdf"]

doc = fitz.open()

for path in pdffiles:
    print("process {}".format(path))
    incremental = doc.pageCount > 0 # need an initial document for incremental save

    src = fitz.open(path)
    for n in range(src.pageCount):
        showPDFonNewPage(doc, src, n)

    doc.save(outfile,
             #garbage = 4, # eliminate duplicate objects
             deflate = True, # compress stuff where possible
             incremental=incremental)

    doc = fitz.open(outfile)
