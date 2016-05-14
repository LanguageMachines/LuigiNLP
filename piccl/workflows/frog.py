import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import WorkflowTask, TargetInfo, InitialInput
from piccl.modules.frog import Frog_folia2folia, Frog_txt2folia
from piccl.modules.openconvert import OpenConvert_folia
from piccl.modules.folia import Rst2folia
from piccl.workflows.folia import ConvertToFoLiA
from piccl.inputs import FoLiAInput, PlainTextInput, WordInput, TEIInput, ReStructuredTextInput
from piccl.util import replaceextension

log = logging.getLogger('mainlog')


class Frog(WorkflowTask):
    inputfilename = Parameter()
    skip = Parameter(default="")

    #Map of extensions to input classes
    inputmap = {
        '.folia.xml': FoLiAInput,
        '.txt': PlainTextInput,
    }

    def setup(self, workflow):
        #detect format of input file by extension, we pass both our inputmap as well as that of ConvertToFoLiA, adding more possible input formats
        initialinput = InitialInput(self.inputfilename, self.inputmap, ConvertToFoLiA.inputmap)

        #Set up workflow to Frog for this type of input
        if initialinput.type is PlainTextInput:
            #Set up the initial task, always exposes an out_default slot
            initialtask = workflow.initial_task(initialinput)

            #Frog itself calls ucto to tokenize plaintext, no need to solve it here:
            frog = workflow.new_task('frog', Frog_txt2folia,skip=self.skip )
            frog.in_txt = initialtask.out_default
        else:
            if initialinput.type is FoLiAInput:
                #Set up the initial task, always exposes an out_default slot
                initialtask = workflow.initial_task(initialinput)
                out = initialtask.out_default
            else:
                #Stage 1/1 - Convert input to FoLiA and then call Frog  (defers to another workflow that takes care of the initial task)                
                convert2folia = workflow.new_subworkflow(ConvertToFoLiA, inputfilename=self.inputfilename)
                out = convert2folia.out_folia

            #Stage 2/2 - Call Frog
            frog = workflow.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = out

        return frog #return the last task (mandatory!)

Frog.inherit_parameters(ConvertToFoLiA) #inherit additional parameters from the specified dependency
