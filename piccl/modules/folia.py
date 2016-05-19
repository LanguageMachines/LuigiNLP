import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo, WorkflowComponent
from piccl.util import replaceextension
from piccl.modules.openconvert import OpenConvert_folia
from piccl.inputs import TEIInput, WordInput, ReStructuredTextInput

log = logging.getLogger('mainlog')

class ConvertToFoLiA(WorkflowComponent):
    def accepts(self):
        return (TEIInput,WordInput,ReStructuredTextInput)

    def setup(self, workflow):
        input_type, input_slot = self.setup_input(workflow)
        if input_type in ('docx', 'tei'):
            #Input is something OpenConvert can handle: convert to FoLiA first
            openconvert = workflow.new_task('openconvert',OpenConvert_folia,from_format=input_type)
            openconvert.in_any = input_slot
            return 'folia', openconvert #always return last task
        elif input_type == 'rst':
            rst2folia = workflow.new_task('rst2folia',Rst2folia)
            rst2folia.in_rst = input_slot
            return 'folia', rst2folia #always return last task


class Rst2folia(Task):
    executable = 'rst2folia' #external executable (None if n/a)

    in_rst = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, '.rst','.folia.xml'))

    def run(self):
        self.ex(self.in_rst().path, self.out_folia().path,
            docid=os.path.basename(self.in_rst().path).split('.')[0], #first component of input filename (up to first period) will be FoLiA ID
        )

