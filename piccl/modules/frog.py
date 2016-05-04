import os
import logging
from sciluigi import Task, TargetInfo
from luigi import StringParameter, BoolParameter
from piccl.util import replaceextension

log = logging.getLogger('mainlog')

class Frog_txt2folia(Task):
    executable = 'frog' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    tok_input_sentenceperline = BoolParameter(default=False)
    skip = StringParameter(default="")

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, '.txt','.frogged.folia.xml'))

    def run(self):
        params = ""
        if self.skip:
            params += ' --skip=' + self.skip
        if self.tok_input_sentenceperline:
            params += ' -n'
        folia_id = os.path.basename(self.in_txt().path).split('.')[0] #first component of input filename (up to first period) will be FoLiA ID
        params += ' --id=' + folia_id
        cmd = self.executable + ' ' + params + ' -t ' + self.in_txt().path + ' -X ' + self.out_folia().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)


class Frog_folia2folia(Task):
    executable = 'frog' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    skip = StringParameter(default="")

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, '.folia.xml','.frogged.folia.xml'))

    def run(self):
        params = ""
        if self.skip:
            params += ' --skip=' + self.skip
        cmd = self.executable + ' ' + params + ' -t ' + self.in_folia().path + ' -X ' + self.out_folia().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)
