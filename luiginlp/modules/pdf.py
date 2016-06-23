import logging
import glob
import natsort
import os
from luiginlp.engine import Task, TargetInfo, StandardWorkflowComponent, InputSlot, Parameter, BoolParameter
from luiginlp.util import replaceextension, DirectoryHandler

log = logging.getLogger('mainlog')


class Pdf2images(Task):
    """Extract images from a PDF document to a set of TIFF images"""
    executable = 'pdfimages' #external executable (None if n/a)

    in_pdf = InputSlot() #will be linked to an out_* slot of another module in the workflow specification

    def out_tiffdir(self):
        return self.outputfrominput(inputformat='pdf',stripextension='.pdf',addextension='.tiffdir')

    def run(self):
        #we use a DirectoryHandler that takes care of creating a temporary directory to hold all output and renames it to the final directory when all succeeds, and cleaning up otherwise
        with DirectoryHandler(self.out_tiffdir().path) as dirhandler:
            self.ex(self.in_pdf().path, dirhandler.directory+'/' + os.path.basename(self.in_pdf().path).split('.')[0] , #output to temporary directory and a file prefix
                tiff=True,
                p=True,
                __singlehyphen=True, #use single-hypens even for multi-letter options
            )

class CollatePDF(Task):
    """Collate multiple PDF files together"""
    executable = 'pdftk'

    naturalsort = BoolParameter(default=True) #do a natural sort of all pdfs in the input directory

    in_pdfdir = InputSlot()

    def out_pdf(self):
        return self.outputfrominput(inputformat='pdfdir',stripextension='.pdfdir',addextension='.pdf')

    def run(self):
        pdf_files = [ pdffile for pdffile in glob.glob(self.in_pdfdir().path + '/*.pdf') ] #collect all pdf files in collection
        if self.naturalsort:
            pdf_files = natsort.natsorted(pdf_files)
        args = pdf_files + ['output',self.out_pdf().path]
        self.ex(*args)

