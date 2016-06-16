import os
import glob
import sys
import shutil
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, StandardWorkflowComponent, registercomponent, InputComponent, Parallel, run, ComponentParameters, InputFormat
from luiginlp.util import getlog
from luiginlp.modules.pdf import Pdf2images
from luiginlp.modules.folia import Foliacat, FoliaHOCR

log = getlog()

class Tesseract(Task):
    """Does OCR on a TIFF image, outputs a hOCR file"""
    executable = 'tesseract'

    language = Parameter()
    outputdir = Parameter(default="")

    in_tiff = None #input slot

    def out_hocr(self):
        return self.outputfrominput(inputformat='tiff',inputextension=('.tif','.tiff'), outputextension='.hocr')

    def run(self):
        self.ex(self.in_tiff().path, self.out_hocr().path[:-5], #output path without hocr extension (-5), Tesseract adds it already
                l=self.language,
                c="tessedit_create_hocr=T",
        )

@registercomponent
class OCR_singlepage(StandardWorkflowComponent):
    language = Parameter()
    tiff_extension=Parameter(default='tif')
    outputdir = Parameter(default="")

    def autosetup(self):
        return Tesseract

    def accepts(self):
        return InputFormat(self, format_id='tiff', extension=self.tiff_extension, directory=True),

class TesseractOCR_document(Task):
    """OCR for a whole document (input is a directory of tiff image files (pages), output is a directory of hOCR files"""
    tiff_extension=Parameter(default='tif')
    language = Parameter()

    in_tiffdir = None #input slot

    def out_hocrdir(self):
        return self.outputfrominput(inputformat='tiffdir',inputextension='.tiffdir', outputextension='.hocrdir')

    def run(self):
        #Set up the output directory, will create it and tear it down on failure automatically
        self.setup_output_dir(self.out_hocrdir().path)

        #gather input files
        inputfiles = [ filename for filename in glob.glob(self.in_tiffdir().path + '/*.' + self.tiff_extension) ]

        #inception aka dynamic dependencies: we yield a list of tasks to perform which could not have been predicted statically
        #in this case we run the OCR_singlepage component for each input file in the directory
        yield [ OCR_singlepage(inputfile=inputfile,outputdir=self.out_hocrdir().path,language=self.language,tiff_extension=self.tiff_extension) for inputfile in inputfiles ]








@registercomponent
class ExtractPages(StandardWorkflowComponent):
    """Convert input document to a collection of TIFF images"""

    def autosetup(self):
        return Pdf2images

    def accepts(self):
        return InputFormat(self, format_id='pdf',extension='pdf')

@registercomponent
class OCR_document(StandardWorkflowComponent):

    language = Parameter()

    def autosetup(self):
        return TesseractOCR_document

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return (
            InputFormat(self, format_id='tiffdir', extension='tiffdir', directory=True),
            InputComponent(self, ExtractPages)
        )




@registercomponent
class OCR_folia(StandardWorkflowComponent):
    """OCR with FoLiA output"""
    language = Parameter()

    def setup(self, workflow, input_feeds):
        foliahocr = workflow.new_task('foliahocr', FoliaHOCR)
        foliahocr.in_hocrdir = input_feeds['hocrdir']
        foliacat = workflow.new_task('foliacat', Foliacat)
        foliacat.in_foliadir = foliahocr.out_foliadir
        return foliacat

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return InputComponent(self, OCR_document)
