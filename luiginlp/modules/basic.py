import os
import glob
import sys
import shutil
from luiginlp.engine import Task, Parameter, InputSlot, TargetInfo
from luiginlp.util import getlog

log = getlog()

class Symlink(Task):
    """Create a symlink"""

    filename = Parameter()
    stripextension = Parameter()
    addextension = Parameter()

    in_file = InputSlot() #input slot

    def out_file(self):
        if self.filename:
            return TargetInfo(self, self.filename)
        else:
            return self.outputfrominput(inputformat='file',stripextension=self.stripextension, addextension=self.addextension)

    def run(self):
        os.symlink(self.in_file.path(), self.out_file.path())
