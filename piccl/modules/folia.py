import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo
from piccl.util import replaceextension

log = logging.getLogger('mainlog')

class Rst2folia(Task):
    executable = 'rst2folia' #external executable (None if n/a)

    in_rst = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, '.rst','.folia.xml'))

    def run(self):
        self.ex(self.in_rst().path,self.out_folia().path)

