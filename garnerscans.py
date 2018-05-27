import os
import PyPDF2

from PIL import Image, ExifTags
import warnings
warnings.filterwarnings("ignore")
from io import StringIO
from io import BytesIO
import reportlab.lib.pagesizes as pdf_sizes
import reportlab
import struct

"""
Links:
PDF format: http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf
CCITT Group 4: https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-T.6-198811-I!!PDF-E&type=items
Extract images from pdf: http://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python
Extract images coded with CCITTFaxDecode in .net: http://stackoverflow.com/questions/2641770/extracting-image-from-pdf-with-ccittfaxdecode-filter
TIFF format and tags: http://www.awaresystems.be/imaging/tiff/faq.html
"""

def tiff_header_for_CCITT(width, height, img_size, CCITT_group=4):
    tiff_header_struct = '<' + '2s' + 'h' + 'l' + 'h' + 'hhll' * 8 + 'h'
    return struct.pack(tiff_header_struct,
                       b'II',  # Byte order indication: Little indian
                       42,  # Version number (always 42)
                       8,  # Offset to first IFD
                       8,  # Number of tags in IFD
                       256, 4, 1, width,  # ImageWidth, LONG, 1, width
                       257, 4, 1, height,  # ImageLength, LONG, 1, lenght
                       258, 3, 1, 1,  # BitsPerSample, SHORT, 1, 1
                       259, 3, 1, CCITT_group,  # Compression, SHORT, 1, 4 = CCITT Group 4 fax encoding
                       262, 3, 1, 0,  # Threshholding, SHORT, 1, 0 = WhiteIsZero
                       273, 4, 1, struct.calcsize(tiff_header_struct),  # StripOffsets, LONG, 1, len of header
                       278, 4, 1, height,  # RowsPerStrip, LONG, 1, lenght
                       279, 4, 1, img_size,  # StripByteCounts, LONG, 1, size of image
                       0  # last IFD
                       )

def recurse(page, xObject, Images):
    xObject = xObject['/Resources']['/XObject'].getObject()

    imagename = "test"

    for obj in xObject:

        if xObject[obj]['/Subtype'] == '/Image':

            if xObject[obj]['/Filter'] == '/CCITTFaxDecode':
                """
                The  CCITTFaxDecode filter decodes image data that has been encoded using
                either Group 3 or Group 4 CCITT facsimile (fax) encoding. CCITT encoding is
                designed to achieve efficient compression of monochrome (1 bit per pixel) image
                data at relatively low resolutions, and so is useful only for bitmap image data, not
                for color images, grayscale images, or general data.

                K < 0 --- Pure two-dimensional encoding (Group 4)
                K = 0 --- Pure one-dimensional encoding (Group 3, 1-D)
                K > 0 --- Mixed one- and two-dimensional encoding (Group 3, 2-D)
                """
                if xObject[obj]['/DecodeParms']['/K'] == -1:
                    CCITT_group = 4
                else:
                    CCITT_group = 3
                width = xObject[obj]['/Width']
                height = xObject[obj]['/Height']
                data = xObject[obj]._data  # sorry, getData() does not work for CCITTFaxDecode
                img_size = len(data)
                tiff_header = tiff_header_for_CCITT(width, height, img_size, CCITT_group)
                #tiff_img = Image.open(StringIO(tiff_str))
                tiff_img = Image.open(BytesIO(tiff_header + data))
                #print(tiff_img._getexif())
                #with open(img_name, 'wb') as img_file:
                #    img_file.write(tiff_header + data)
                #s = BytesIO()
                #tiff_img.save(s,'PNG')
                #pdf_img = Image.open(s)
                Images.append(tiff_img)
            else:
                size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                data = xObject[obj].getData()
                if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                    mode = "RGB"
                else:
                    mode = "P"


                if xObject[obj]['/Filter'] == '/FlateDecode':
                    img = Image.frombytes(mode, size, data)
                    #img.save(imagename + ".png")
                    Images.append(img)

                elif xObject[obj]['/Filter'] == '/DCTDecode':
                    img = open(imagename + ".jpg", "wb")
                    img.write(data)
                    img.close()

                elif xObject[obj]['/Filter'] == '/JPXDecode':
                    img = open(imagename + ".jp2", "wb")
                    img.write(data)
                    img.close()

        else:
            recurse(page, xObject[obj], Images)

def TIFF2PDF(tiff_img, max_pages = 200):
    '''
    Convert a TIFF Image into a PDF.

    tiff_str: The binary representation of the TIFF.
    max_pages: Break after a number of pages. Set to None to have no limit.
    '''
    # Open the Image in PIL
    #tiff_img = Image.open(StringIO(tiff_str))

    # Get tiff dimensions from exiff data. The values are swapped for some reason.
    height, width = tiff_img.tag[0x101][0], tiff_img.tag[0x100][0]

    # Create our output PDF
    out_pdf_io = StringIO()
    c = reportlab.pdfgen.canvas.Canvas(out_pdf_io, pagesize = pdf_sizes.letter)

    # The PDF Size
    pdf_width, pdf_height = pdf_sizes.letter

    # Iterate through the pages
    page = 0
    while True:
        try:
            tiff_img.seek(page)
        except EOFError:
            break
            # Stretch the TIFF image to the full page of the PDF
        if pdf_width * height / width <= pdf_height:
            # Stretch wide
            c.drawInlineImage(tiff_img, 0, 0, pdf_width, pdf_width * height / width)
        else:
            # Stretch long
            c.drawInlineImage(tiff_img, 0, 0, pdf_height * width / height, pdf_height)
        c.showPage()
        if max_pages and page > max_pages:
            break
        page += 1
    c.save()
    return out_pdf_io.getvalue()


def extractImagesFromPdf(filename):
    pdfFile = PyPDF2.PdfFileReader(open(filename, "rb"))
    numPages = pdfFile.getNumPages()

    Images = []

    for n in range(numPages):
        page = pdfFile.getPage(n)
        recurse(n, page, Images)

    return Images

workdir = '/home/thomas/Desktop/Druckunternehmen/work'
os.chdir(workdir)
filename1 = "1.pdf"
filename2 = "2.pdf"

Images = []

Images += extractImagesFromPdf(os.path.join(workdir, filename1))
Images += extractImagesFromPdf(os.path.join(workdir, filename2))

from PIL import Image, ExifTags
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# def rotateImage(image):
#     try:
#         #image=Image.open(filepath)
#         for orientation in ExifTags.TAGS.keys():
#             if ExifTags.TAGS[orientation]=='Orientation':
#                 break
#         # exif=dict(image._getexif().items())

#         # if exif[orientation] == 3:
#         #     image=image.rotate(180, expand=True)
#         # elif exif[orientation] == 6:
#         #     image=image.rotate(270, expand=True)
#         # elif exif[orientation] == 8:
#         #     image=image.rotate(90, expand=True)
#         # #image
#         image.save(filepath)
#         #image.close()

#     except (AttributeError, KeyError, IndexError):
#         # cases: image don't have getexif
#         print("Could not get exif")


# #from StringIO import StringIO

A4 = (210, 297)

output_file_loc = "in_memory_copy.pdf"
imgDoc = canvas.Canvas(output_file_loc)
imgDoc.setPageSize(A4) # This is actually the default page size
document_width, document_height = A4

for image in Images:
    # Open the image file to get image dimensions
    #Image_file = Image.open(image)
    rotateImage(image)
    image_io = BytesIO()
    image.save(image_io, 'PNG')
    Image_file = ImageReader(image_io)
    image_width, image_height = Image_file.getSize()
    image_aspect = image_height / float(image_width)

    # Determine the dimensions of the image in the overview
    print_width = document_width
    print_height = document_width * image_aspect
    #print_height = document_height

    # Draw the image on the current page
    # Note: As reportlab uses bottom left as (0,0) we need to determine the start position by subtracting the
    #       dimensions of the image from those of the document
    imgDoc.drawImage(Image_file, document_width - print_width, document_height - print_height, width=print_width, height=print_height)

    # Inform Reportlab that we want a new page
    imgDoc.showPage()

# Save the document
imgDoc.save()
