import os
import logging
import glob
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo, WorkflowComponent
from piccl.util import replaceextension, DirectoryHandler

log = logging.getLogger('mainlog')


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


