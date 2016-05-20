import os
import logging
import glob
import natsort
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo, WorkflowComponent
from piccl.util import replaceextension, DirectoryHandler
from piccl.modules.openconvert import OpenConvert_folia
from piccl.inputs import TEIInput, WordInput, ReStructuredTextInput,AlpinoDocDirInput

log = logging.getLogger('mainlog')


class pdf2images(Task):
    """Converts a PDF document to a set of TIFF images (one per page)"""
    executable = 'pdfimages' #external executable (None if n/a)

    in_pdf = None #will be linked to an out_* slot of another module in the workflow specification

    def out_tiffdir(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, '.pdf','.tiffdir'))

    def run(self):
        #we use a DirectoryHandler that takes care of creating a temporary directory, renaming it to the final directory when all succeeds, and cleaning up otherwise
        with DirectoryHandler(self.out_tiffdir().path) as dirhandler:
            self.ex(self.in_pdf().path, dirhandler.directory, #output to temporary directory
                tiff=True,
                p=True, #include page numbers in output filenames
                __singlehyphen=True, #use single-hypens even for multi-letter options
            )

class collatepdf(Task):
    """Collate multiple PDF files together"""
    executable = 'pdftk'

    naturalsort = luigi.BoolParameter(default=True) #do a natural sort of all pdfs in the input directory

    in_pdfdir = None

    def out_pdf(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, '.pdfdir','.pdf'))

    def run(self):
        pdf_files = [ pdffile for pdffile in glob.glob(self.in_pdfdir().path + '/*.pdf') ] #collect all pdf files in collection
        if self.naturalsort:
            pdf_files = natsort.natsorted(pdf_files)
        args = pdf_files + ['output',self.out_pdf().path]
        self.ex(*args)

