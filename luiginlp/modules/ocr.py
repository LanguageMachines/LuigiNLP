import os
import logging
import glob
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, WorkflowComponent, InputWorkflow, Parallel, run, ComponentParameters
from luiginlp.util import replaceextension, DirectoryHandler
from luiginlp.inputs import PdfInput, TiffInput, TiffDocDirInput
from luiginlp.modules.pdf import Pdf2images

log = logging.getLogger('mainlog')

class TesseractOCR_tiff2hocr(Task):
    """Does OCR on a TIFF image, outputs a hOCR file"""
    executable = 'tesseract'

    language = Parameter()

    in_tiff = None #input slot

    def out_hocr(self):
        return TargetInfo(self, replaceextension(self.in_tiff().path, ('.tif','.tiff'),'.hocr'))

    def run(self):
        self.ex(self.in_tiff().path, self.out_hocr().path,
                l=self.language,
                c="tessedit_create_hocr=T",
        )

class OCR_singlepage(WorkflowComponent):
    language = Parameter()

    autosetup = (TesseractOCR_tiff2hocr,)

    def accepts(self):
        return (TiffInput,)

class TesseractOCR_document(Task):
    """OCR for a whole document (input is a directory of tiff image files (pages), output is a directory of hOCR files"""
    tiff_extension=Parameter(default='tif')
    language = Parameter()

    in_tiffdocdir = None #input slot

    def out_hocrdocdir(self):
        return TargetInfo(self, replaceextension(self.in_tiffdocdir().path, '.tiffdocdir','.hocrdocdir'))

    def run(self):
        with DirectoryHandler(self.out_hocrdocdir().path) as dirhandler:
            #gather input files
            inputfiles = [ filename for filename in glob.glob(self.in_tiffdocdir().path + '/*.' + self.tiff_extension) ]
            #inception: we run the workflow system with a new (sub)-workflow (luiginlp.run)
            run(Parallel(component='OCR_singlepage', inputfiles=','.join(inputfiles), component_parameters=ComponentParameters(language=self.language)))
            #collect all output files
            dirhandler.collectoutput(self.in_tiffdocdir().path + '/*.hocr')



class ConvertToTiffDocDir(WorkflowComponent):
    """Convert input to a collection of TIFF images"""

    autosetup = (Pdf2images,)

    def accepts(self):
        return (PdfInput,)


class OCR_document(WorkflowComponent):

    language = Parameter()
    autosetup = (TesseractOCR_document,)

    def accepts(self):
        return (TiffDocDirInput, InputWorkflow(self, ConvertToTiffDocDir))
