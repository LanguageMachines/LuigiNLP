import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import WorkflowTask, TargetInfo, InitialInput
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


    def setup(self, workflow):
        #detect format of input file by extension
        initialinput = InitialInput(workflow.inputfilename, self.inputmap)
        #Set up initial task
        initialtask = workflow.initial_task(initialinput)

        #Conversion to FoLiA, last task in conversion chain *MUST* expose a out_folia slot
        if initialinput.type in (WordInput, TEIInput):
            #Input is something OpenConvert can handle: convert to FoLiA first
            formatmap = { #translates format classes to values expected in --from parameter of openconvert
                WordInput: 'docx',
                TEIInput: 'tei',
            }
            openconvert = workflow.new_task('openconvert',OpenConvert_folia,from_format=formatmap[initialinput.type])
            openconvert.in_any = initialtask.out_default
            return openconvert #always return last task
        elif initialinput.type is ReStructuredTextInput:
            rst2folia = workflow.new_task('rst2folia',Rst2folia)
            rst2folia.in_rst = initialtask.out_default
            return rst2folia #always return last task

