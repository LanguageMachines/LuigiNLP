import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import WorkflowTask, TargetInfo
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

    def workflow(self):
        #detect format of input file by extension, we pass both our inputmap as well as that of ConvertToFoLiA
        initialtask, inputtype = self.initial_task(self.inputfilename, self.inputmap, ConvertToFoLiA.inputmap)


        #Set up workflow to Frog for this type of input
        if inputtype is PlainTextInput:
            #Frog itself calls ucto to tokenize plaintext, no need to solve it here:
            frog = self.new_task('frog', Frog_txt2folia,skip=self.skip )
            frog.in_txt = initialtask.out_default
        else:
            #Stage 1/1 - Convert input to FoLiA and then call Frog  (calls another workflow)
            convert2folia = self.new_task(ConvertToFoLiA('converttofolia',ConvertToFoLiA,inputfilename=self.inputfilename))

            #Stage 2/2 - Call Frog
            frog = self.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = convert2folia.out_folia


        return frog #return the last task (mandatory)

