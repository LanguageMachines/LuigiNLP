import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo, InputWorkflow, WorkflowModule
from piccl.util import replaceextension
from piccl.inputs import FoLiAInput, PlainTextInput

log = logging.getLogger('mainlog')

class Frog(WorkflowModule):
    skip = Parameter(default="")

    def accepts(self):
        return (FoLiAInput, PlainTextInput, InputWorkflow(ConvertToFoLiA) )

    def setup(self, workflow):
        input_type, input_slot = self.setup_input(workflow)
        if input_type == 'txt':
            frog = workflow.new_task('frog', Frog_txt2folia,skip=self.skip )
            frog.in_txt = input_slot
        elif input_type == 'folia':
            frog = workflow.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = input_slot
        return 'folia', frog #return the type of output and the last task (mandatory!)

class Frog_txt2folia(Task):
    executable = 'frog' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    tok_input_sentenceperline = BoolParameter(default=False)
    skip = Parameter(default="")

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_txt().path, '.txt','.frogged.folia.xml'))

    def run(self):
        self.ex(
            t=self.in_txt().path,
            X=self.out_folia().path,
            id=os.path.basename(self.in_txt().path).split('.')[0], #first component of input filename (up to first period) will be FoLiA ID
            skip=self.skip if self.skip else None,
            n=self.tok_input_sentenceperline,
        )


class Frog_folia2folia(Task):
    executable = 'frog' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    skip = Parameter(default="")

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_folia().path, '.folia.xml','.frogged.folia.xml'))

    def run(self):
        self.ex(
            x=self.in_folia().path,
            X=self.out_folia().path,
            skip=self.skip if self.skip else None,
        )
