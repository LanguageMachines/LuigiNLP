import os
import logging
from sciluigi import WorkflowTask, TargetInfo
from luigi import StringParameter, BoolParameter
from piccl.modules import Frog_folia2folia, Frog_txt2folia, OpenConvert_folia
from piccl.inputs import FoLiAInput, PlainTextInput, WordInput, TEIInput
from piccl.util import replaceextension

log = logging.getLogger('mainlog')


class Frog(WorkflowTask):
    inputfilename = StringParameter()
    skip = StringParameter(default="")

    def workflow(self):
        #detect format of input file by extension
        if self.inputfilename.endswith('.folia.xml'):
            basename = self.inputfilename[:-len('.folia.xml')]
            inputformat = 'folia'
            initialinput = self.new_task('initialinput', FoLiAInput, basename='input') #input.folia.xml
        elif self.inputfilename.endswith('.txt'):
            basename = self.inputfilename[:-len('.txt')]
            inputformat = 'txt'
            initialinput = self.new_task('initialinput', PlainTextInput, basename='input')
        elif self.inputfilename.endswith('.docx'):
            basename = self.inputfilename[:-len('.docx')]
            inputformat = 'docx'
            initialinput = self.new_task('initialinput', WordInput, basename='input')
        elif self.inputfilename.endswith('.tei.xml'):
            basename = self.inputfilename[:-len('.tei.xml')]
            inputformat = 'tei'
            initialinput = self.new_task('initialinput', TEIInput, basename='input')
        else:
            raise Exception("Input file does not match any known pattern for this workflow")

        #Set up workflow to Frog for this type of input
        if inputformat == 'folia':
            frog = self.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = initialinput.out_default
        elif inputformat == 'txt':
            frog = self.new_task('frog', Frog_txt2folia,skip=self.skip )
            frog.in_txt = initialinput.out_default
        elif inputformat in ['docx','tei']:
            #Input is something OpenConvert can handle: convert to FoLiA first
            openconvert = self.new_task('openconvert',OpenConvert_folia,from_format='docx')
            openconvert.in_any = initialinput.out_default
            #Now add frog
            frog = self.new_task('frog', Frog_folia2folia,skip=self.skip )
            frog.in_folia = openconvert.out_folia

        return frog #always return the last task

