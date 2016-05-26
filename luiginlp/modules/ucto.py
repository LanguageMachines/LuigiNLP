import logging
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, registercomponent, WorkflowComponent, Inputcomponent, InputFormat
from luiginlp.util import replaceextension
from luiginlp.modules.folia import ConvertToFoLiA

log = logging.getLogger('mainlog')

class Ucto_txt2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_txt().path, '.txt','.folia.xml'))

    def run(self):
        self.ex(self.in_txt().path(), self.out_folia().path,
                L=self.language,
                m=self.tok_input_sentenceperline,
                X=True,
        )

class Ucto_txt2tok(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)
    tok_output_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_tok(self):
        return TargetInfo(self, replaceextension(self.in_txt().path, '.txt','.tok'))

    def run(self):
        self.ex(self.in_txt().path(), self.out_tok().path,
                L=self.language,
                m=self.tok_input_sentenceperline,
                n=self.tok_output_sentenceperline,
        )

class Ucto_folia2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_folia().path, '.folia.xml','.tok.folia.xml'))

    def run(self):
        self.ex(self.in_txt().path(), self.out_folia().path,
                L=self.language,
                F=True, #folia input
                X=True, #folia output
        )

#################################################################################################################
# Workflow Components
#################################################################################################################

@registercomponent
class Ucto(WorkflowComponent):
    """A workflow component for Ucto"""

    skip = Parameter(default="") #A parameter for the workflow, will be passed on to the tasks

    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)
    tok_output_sentenceperline = BoolParameter(default=False)

    def autosetup(self):
        return (Ucto_txt2folia, Ucto_folia2folia)

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return (
            InputFormat(self, format_id='folia', extension='folia.xml'),
            InputFormat(self, format_id='txt', extension='txt'),
            InputComponent(self, ConvertToFoLiA)
        )
