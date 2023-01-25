import os
import fitz
import pdfplumber
from pikepdf import Pdf
import docx
import io
from PIL import Image


class PDF_Tool:
    def extract_images(files, output_path):

        pdf_file = fitz.open(files)

        for page_index in range(len(pdf_file)):
            # get the page itself
            page = pdf_file[page_index]
            # get image list
            image_list = page.get_images()

            for image_index, img in enumerate(image_list, start=1):
                # get the XREF of the image
                xref = img[0]
                # extract the image bytes
                base_image = pdf_file.extract_image(xref)
                image_bytes = base_image["image"]
                # get the image extension
                image_ext = base_image["ext"]
                # load it to PIL
                image = Image.open(io.BytesIO(image_bytes))
                # save it to local disk

                image.save(open(f"{output_path}/image{page_index + 1}_{image_index}.{image_ext}", "wb"))

    def convert_to_docx(files, file_path):
        docx_file = docx.Document()
        pdf_file = pdfplumber.open(files)

        for page_index in range(0, len(pdf_file.pages)):
            docx_file.add_paragraph(pdf_file.pages[page_index].extract_text())
        docx_file.save(file_path)

    def convert_to_txt(files, text_file):
        pdf_file = pdfplumber.open(files)

        for page_index in range(0, len(pdf_file.pages)):
            with open(text_file, 'a') as f:
                f.write('\n\n')
                f.write('Seite {}\n\n'.format(page_index + 1))
                f.write(pdf_file.pages[page_index].extract_text())

    def split_files(files, output_path):
        pdf = Pdf.open(files)

        for n, page in enumerate(pdf.pages):
            dst = Pdf.new()
            dst.pages.append(page)
            dst.save(f'{output_path}/Seite-{n + 1}.pdf')

    def merge_files(files, output_path):
        pdf = Pdf.new()
        for file in files:
            src = Pdf.open(file)
            pdf.pages.extend(src.pages)
        pdf.save(output_path)
