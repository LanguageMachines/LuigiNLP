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
        return TargetInfo(self, replaceextension(self.in_rst().path, '.rst','.folia.xml'))

    def run(self):
        self.ex(self.in_rst().path, self.out_folia().path,
            docid=os.path.basename(self.in_rst().path).split('.')[0], #first component of input filename (up to first period) will be FoLiA ID
        )

