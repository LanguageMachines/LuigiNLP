import os
import logging
import glob
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, WorkflowComponent, registercomponent
from luiginlp.util import replaceextension
from luiginlp.modules.openconvert import OpenConvert_folia
from luiginlp.inputs import TEIInput, WordInput, ReStructuredTextInput,AlpinoDocDirInput

log = logging.getLogger('mainlog')

@registercomponent
class ConvertToFoLiA(WorkflowComponent):
    def accepts(self):
        return (TEIInput,WordInput,ReStructuredTextInput,AlpinoDocDirInput)

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
        elif input_type == 'alpinodocdir':
            alpino2folia = workflow.new_task('alpino2folia',Alpino2folia)
            alpino2folia.in_alpinodocdir = input_slot
            return 'folia',  alpino2folia #always return last task


class Rst2folia(Task):
    executable = 'rst2folia' #external executable (None if n/a)

    in_rst = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_rst().path, '.rst','.folia.xml'))

    def run(self):
        self.ex(self.in_rst().path, self.out_folia().path,
            docid=os.path.basename(self.in_rst().path).split('.')[0], #first component of input filename (up to first period) will be FoLiA ID
        )

class Alpino2folia(Task):
    executable = 'alpino2folia'

    in_alpinodocdir = None

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_alpinodocdir().path, '.alpinodocdir','.folia.xml'))

    def run(self):
        alpinofiles = [ alpinofile for alpinofile in sorted(glob.glob(self.in_alpinodocdir().path + '/*.xml'),key=lambda x: int(os.path.basename(x).split('.')[0])) ] #collect all alpino files in collection
        args = alpinofiles + [self.out_folia().path] #last argument is folia output
        self.ex(*args)



