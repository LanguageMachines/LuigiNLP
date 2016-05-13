import os
import logging
from luigi import StringParameter, BoolParameter
from piccl.engine import WorkflowTask, TargetInfo
from piccl.modules.frog import Frog_folia2folia, Frog_txt2folia
from piccl.modules.openconvert import OpenConvert_folia
from piccl.inputs import FoLiAInput, PlainTextInput, WordInput, TEIInput
from piccl.util import replaceextension

log = logging.getLogger('mainlog')


class Frog(WorkflowTask):
    inputfilename = StringParameter()
    skip = StringParameter(default="")

    def workflow(self):
        #detect format of input file by extension
        initialtask, inputtype = self.initial_task(self.inputfilename, {
            '.folia.xml': FoLiAInput,
            '.txt': PlainTextInput,
            '.tei.xml': TEIInput,
            '.docx': WordInput,
        })

        #Set up workflow to Frog for this type of input
        if inputtype is FoLiAInput:
            #Frog can handle FoLiA
            frog = self.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = initialtask.out_default
        elif inputtype is PlainTextInput:
            #Frog itself calls ucto to tokenize plaintext, no need to solve it here:
            frog = self.new_task('frog', Frog_txt2folia,skip=self.skip )
            frog.in_txt = initialtask.out_default
        elif inputtype in (WordInput, TEIInput):
            #Input is something OpenConvert can handle: convert to FoLiA first
            openconvert = self.new_task('openconvert',OpenConvert_folia,from_format='docx')
            openconvert.in_any = initialtask.out_default

            #Now add frog
            frog = self.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = openconvert.out_folia

        return frog #always return the last task

