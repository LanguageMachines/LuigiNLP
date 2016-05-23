import os
import logging
import glob
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, WorkflowComponent, InputWorkflow, SubWorkflow, Parallel, run
from luiginlp.util import replaceextension, DirectoryHandler
from luiginlp.modules.pdf import Pdf2images

log = logging.getLogger('mainlog')

class TesseractOCR_tiff2ocr(Task):
    """Does OCR on a TIFF image, outputs a hOCR file"""
    executable = 'tesseract'

    language = Parameter()

    in_tiff = None #input slot

    def out_hocr(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, ('.tif','.tiff'),'.hocr'))

    def run(self):
        self.ex(self.in_tiff().path, self.out_hocr().path,
                l=self.language,
                c="tessedit_create_hocr=T",
        )


class OCR_singlepage(WorkflowComponent):
    autosetup = (TesseractOCR_tiff2hocr,)

    def accepts(self):
        return (TiffInput,)

class TesseractOCR_doc(Task):
    """OCR for a while document (input is a directory of tiff image files (pages), output is a directory of hOCR files"""
    tiff_extension=Parameter(default='tif')

    in_tiffdocdir = None #input slot

    def out_hocrdocdir(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, '.tiffdocdir','.hocrdocdir'))

    def run(self):
        with DirectoryHandler(self.out_hocrdocdir().path) as dirhandler:
            #gather input files
            inputfiles = [ filename for filename in glob.glob(self.in_tiffdocdir().path + '/*.' + self.tiff_extension) ]
            #inception: we run the workflow system with a new (sub)-workflow (luiginlp.run)
            run(Parallel(component='OCR_singlepage', inputfiles=','.join(inputfiles)))
            #collect all output files
            dirhandler.collectoutput(self.in_tiffdocdir().path + '/*.hocr')



class ConvertToTiffDocDir(WorkflowComponent):
    """Convert input to a collection of TIFF images"""

    autosetup = (Pdf2images,)

    def accepts(self):
        return (PdfInput,)


class OCR_multi(WorkflowComponent):

    autosetup = (TesseractOCR_multi,)

    def accepts(self):
        return (TiffDocDirInput, InputWorkflow(self, ConvertToTiffDocDir))
