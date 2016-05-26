import os
import logging
import glob
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, WorkflowComponent, registercomponent, InputComponent, Parallel, run, ComponentParameters, InputFormat
from luiginlp.util import replaceextension, DirectoryHandler
from luiginlp.modules.pdf import Pdf2images
from luiginlp.modules.folia import Foliacat

log = logging.getLogger('mainlog')

class TesseractOCR_tiff2hocr(Task):
    """Does OCR on a TIFF image, outputs a hOCR file"""
    executable = 'tesseract'

    language = Parameter()

    in_tiff = None #input slot

    def out_hocr(self):
        return TargetInfo(self, replaceextension(self.in_tiff().path, ('.tif','.tiff'),'.hocr'))

    def run(self):
        self.ex(self.in_tiff().path, self.out_hocr().path[:-5], #output path without hocr extension (-5), Tesseract adds it already
                l=self.language,
                c="tessedit_create_hocr=T",
        )

@registercomponent
class OCR_singlepage(WorkflowComponent):
    language = Parameter()
    tiff_extension=Parameter(default='tif')

    def autosetup(self):
        return TesseractOCR_tiff2hocr

    def accepts(self):
        return InputFormat(self, format_id='tiff', extension=self.tiff_extension, directory=True),

class TesseractOCR_document(Task):
    """OCR for a whole document (input is a directory of tiff image files (pages), output is a directory of hOCR files"""
    tiff_extension=Parameter(default='tif')
    language = Parameter()

    in_tiffdir = None #input slot

    def out_hocrdir(self):
        return TargetInfo(self, replaceextension(self.in_tiffdir().path, '.tiffdir','.hocrdir'))

    def run(self):
        with DirectoryHandler(self.out_hocrdir().path) as dirhandler:
            #gather input files
            inputfiles = [ filename for filename in glob.glob(self.in_tiffdir().path + '/*.' + self.tiff_extension) ]
            #inception: we run the workflow system with a new (sub)-workflow (luiginlp.run)
            run(Parallel(component='OCR_singlepage', inputfiles=','.join(inputfiles), component_parameters=ComponentParameters(language=self.language, tiff_extension=self.tiff_extension)))
            #collect all output files
            dirhandler.collectoutput(self.in_tiffdir().path + '/*.hocr')



@registercomponent
class ConvertToTiffDir(WorkflowComponent):
    """Convert input to a collection of TIFF images"""

    def autosetup(self):
        return Pdf2images

    def accepts(self):
        return InputFormat(self, format_id='pdf',extension='pdf')

@registercomponent
class OCR_document(WorkflowComponent):

    language = Parameter()

    def autosetup(self):
        return TesseractOCR_document

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return (
            InputFormat(self, format_id='tiffdir', extension='tiffdir', directory=True),
            InputComponent(self, ConvertToTiffDir)
        )




@registercomponent
class OCR_folia(WorkflowComponent):
    """OCR with FoLiA output"""
    language = Parameter()

    def setup(self, workflow):
        input_format_id, input_slot = self.setup_input(workflow)
        foliahocr = workflow.new_task('foliahocr', FoliaHOCR)
        foliahocr.in_hocrdir = input_slot
        foliacat = workflow.new_task('foliacat', Foliacat)
        foliacat.in_foliadir = foliahocr.out_foliadir
        return 'folia', foliacat

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return InputComponent(self, OCR_document)
