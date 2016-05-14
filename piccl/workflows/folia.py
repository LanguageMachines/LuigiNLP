import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import WorkflowTask, TargetInfo
from piccl.modules.openconvert import OpenConvert_folia
from piccl.modules.folia import Rst2folia
from piccl.inputs import WordInput, TEIInput, ReStructuredTextInput
from piccl.util import replaceextension

log = logging.getLogger('mainlog')


class ConvertToFoLiA(WorkflowTask):
    """Generic Conversion to FoLiA pipeline from a multitude of input formats"""

    inputfilename = Parameter()

    #Supported input types, maps extensions to Input task classes
    inputmap = {
        '.tei.xml': TEIInput,
        '.docx': WordInput,
        '.rst': ReStructuredTextInput,
    }

    def workflow(self):
        #detect format of input file by extension
        initialtask, inputtype = self.initial_task(self.inputfilename, self.inputmap)

        #Conversion to FoLiA, last task in conversion chain *MUST* expose a out_folia slot
        if inputtype in (WordInput, TEIInput):
            #Input is something OpenConvert can handle: convert to FoLiA first
            formatmap = { #translates format classes to those expected by openconvert
                WordInput: 'docx',
                TEIInput: 'tei',
            }
            openconvert = self.new_task('openconvert',OpenConvert_folia,from_format=formatmap[inputtype])
            openconvert.in_any = initialtask.out_default
        elif inputtype is ReStructuredTextInput:
            rst2folia = self.new_task('rst2folia',Rst2folia)
            rst2folia.in_rst = initialtask.out_default

        return locals()[self.task] #returns last task (mandatory)
