import os
import logging
import glob
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo, WorkflowComponent
from piccl.util import replaceextension, DirectoryHandler
from piccl.modules.pdf import Pdf2Images

log = logging.getLogger('mainlog')

class ConvertToTiffDocDir(WorkFlowComponent)
    """Convert input to a collection of TIFF images"""

    def accepts(self):
        return (PdfInput,)

    def setup(self):
        """The actual workflow specification"""
        #setup the input, invokes dependency workflows when needed
        input_type, input_slot = self.setup_input(workflow)
        if input_type == 'pdf':
            pdf2images = workflow.new_task('pdf2images', Pdf2images)
            pdf2images = input_slot #set the input slot of the task to that of the workflow component
            return 'tiffdocdir', pdf2images #return the type of output  and the last task of the workflow (mandatory!), the last task must have an out_* slot named as specified here.

class OCR(WorkflowComponent):
    def accepts(self):
        return (TiffDocDirInput, InputWorkflow(self, ConvertToTiffDocDir))

    def setup(self):
        """The actual workflow specification"""
        #setup the input, invokes dependency workflows when needed
        input_type, input_slot = self.setup_input(workflow)
        if input_type == 'tiffdocdir':
            pdf2images = workflow.new_task('pdf2images', Pdf2images)
            pdf2images = input_slot #set the input slot of the task to that of the workflow component




class TesseractOCR(Task):
    """Does OCR on a TIFF image, outputs a hOCR file"""
    executable = 'tesseract'

    language = Parameter()

    in_tif = None #input slot

    def out_hocr(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, ('.tif','.tiff'),'.hocr'))

    def run(self):
        self.ex(self.in_tiff().path, self.out_hocr().path,
                l=self.language,
                c="tessedit_create_hocr=T",
        )


