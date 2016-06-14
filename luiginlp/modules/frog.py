import os
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, InputComponent, InputFormat, StandardWorkflowComponent, registercomponent
from luiginlp.util import replaceextension, getlog
from luiginlp.modules.folia import ConvertToFoLiA

log = getlog()


class Frog_txt2folia(Task):
    """A task for Frog: Takes plaintext input and produces FoLiA output"""
    executable = 'frog' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    tok_input_sentenceperline = BoolParameter(default=False)
    skip = Parameter(default="")

    in_txt = None #input slot placeholder (will be linked to an out_* slot of another module in the workflow specification)

    def out_folia(self):
        """The output slot, for FoLiA"""
        return TargetInfo(self, replaceextension(self.in_txt().path, '.txt','.frogged.folia.xml'))

    def run(self):
        #execute a shell command, python keyword arguments will be passed as option flags (- for one letter, -- for more)
        # values will be made shell-safe.
        # None or False values will not be propagated at all.
        self.ex(
            t=self.in_txt().path, #the path of the input file  (accessed through the input slot)
            X=self.out_folia().path, #the path of the output file (accessed through the output slot)
            id=os.path.basename(self.in_txt().path).split('.')[0], #first component of input filename (up to first period) will be FoLiA ID
            skip=self.skip if self.skip else None,
            n=self.tok_input_sentenceperline)


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
            skip=self.skip if self.skip else None)

#################################################################################################################
# Workflow Components
#################################################################################################################

@registercomponent
class Frog(StandardWorkflowComponent):
    """A workflow component for Frog"""

    skip = Parameter(default="") #A parameter for the workflow, will be passed on to the tasks

    def autosetup(self):
        return (Frog_txt2folia, Frog_folia2folia)

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return (
            InputFormat(self, format_id='folia', extension='folia.xml'),
            InputFormat(self, format_id='txt', extension='txt'),
            InputComponent(self, ConvertToFoLiA)
        )


    #Commented out the below setup() method because autosetup generates this code automatically now
    #Leaving it here as a reference, as autosetup won't suffice for more complex workflows or when slot/parameter mappings are needed

    #def setup(self, workflow, input_feeds):   
    #    """The actual workflow specification"""
    #    #setup the input, invokes dependency workflows when needed
    #    for input_type, input_slot in input_feeds.items()
    #       if input_type == 'txt':
    #            frog = workflow.new_task('frog', Frog_txt2folia,skip=self.skip ) #add a task, passing parameters
    #            frog.in_txt = input_slot #set the input slot of the task to that of the workflow component
    #       elif input_type == 'folia':
    #            frog = workflow.new_task('frog', Frog_folia2folia,skip=self.skip ) #add a task, passing parameters
    #            frog.in_folia = input_slot #set the input slot of the task to that of the workflow component
    #       return frog #return the last task of the workflow (mandatory!)

