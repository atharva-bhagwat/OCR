import numpy as np
from cv2 import cv2
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from img2pdf import convert
from natsort import natsorted
import os, argparse, shutil

counter = 1
image_storage = './pages/'
ocr_storage = './result/'
final_pdf = 'Result.pdf'

class GenerateImages:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
    def main(self):
        global counter, image_storage
        print('Getting pages...')
        pages = convert_from_path(self.pdf_path)
        for page in pages:
            filename = 'page'+str(counter)+'.jpg'
            page.save(image_storage+filename,'JPEG')
            counter += 1

class Ocr:
    def __init__(self):
        self.pages = os.listdir(image_storage)

    def main(self):
        print('Performing OCR...')
        for page in self.pages:
            image = cv2.imread(image_storage + page)
            # color change to greyscale
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # smoothen image
            blur = cv2.GaussianBlur(grey, (13,13), 0)
            # greyscale to b/w with BINARY_INV, THRES_OTSU finds threshold dynamically
            thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]
            # generate rect kernel of (5,5)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
            # dialte -> thickens the characters
            dilate = cv2.dilate(thresh, kernel, iterations=4)
            # draw boundaries
            # RETR_EXTERNAL -> outter most boundary, CHAIN_APPROX_SIMPLE -> stores just the 4 points(saves memory)
            contours = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = contours[0] if len(contours) == 2 else contours[1]
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.imwrite(ocr_storage+page,image)

class ToText:
    def __init__(self):
        global image_storage, ocr_storage
        self.text_file = 'Text.txt'
        self.pages = os.listdir(image_storage)
        self.final_pages = os.listdir(ocr_storage)

    def to_Text(self):
        file = open(self.text_file, 'a')
        self.pages = natsorted(self.pages)
        for page in self.pages[:1]:
            print('Writing...')
            text = str((pytesseract.image_to_string(Image.open(image_storage + page))))
            file.write(text)
        file.close()

    def generate_pdf(self):
        global final_pdf
        print('Converting to PDF...')
        image_list = []
        self.final_pages = natsorted(self.final_pages)
        for page in self.final_pages:
            image_list.append(ocr_storage + page)
        with open(final_pdf,"wb") as file:
	        file.write(convert(image_list))
        file.close()

    def main(self):
        self.to_Text()
        self.generate_pdf()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PDF path')
    parser.add_argument('--path', required=True, help='PDF path')
    args = parser.parse_args()

    if not os.path.exists(image_storage):
        os.makedirs(image_storage)
    if not os.path.exists(ocr_storage):
        os.makedirs(ocr_storage)

    generate_pages = GenerateImages(args.path)
    generate_pages.main()
    ocr = Ocr()
    ocr.main()
    to_text = ToText()
    to_text.main()

    if os.path.exists(image_storage):
        shutil.rmtree(image_storage, ignore_errors=True)
    if os.path.exists(ocr_storage):
        shutil.rmtree(ocr_storage, ignore_errors=True)

    print('DONE!')


            
