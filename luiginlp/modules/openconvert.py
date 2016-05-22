import os
import logging
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo
from luiginlp.util import replaceextension

log = logging.getLogger('mainlog')

class OpenConvert_folia(Task):
    executable = 'OpenConvert.jar' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    from_format = Parameter()

    in_any = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo(self, replaceextension(self.in_any().path, ['.tei.xml', '.alto.xml','.tei', '.alto', '.xml', '.doc','.docx','.html', '.epub'],'.openconvert.folia.xml'))

    def run(self):
        self.ex(
                _from=self.from_format, #any underscore will be removed (only to prevent clash with python reserved keyword)
                t=self.in_any().path,
                X=self.out_folia().path
        )

class OpenConvert_tei(Task):
    executable = 'OpenConvert.jar' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    from_format = Parameter()

    in_any = None #will be linked to an out_* slot of another module in the workflow specification

    def out_tei(self):
        return TargetInfo(self, replaceextension(self.in_txt().path, ['.folia.xml', '.alto.xml','.tei', '.alto', '.xml', '.doc','.docx','.html', '.epub'],'.openconvert.tei.xml'))

    def run(self):
        self.ex(
                _from=self.from_format, #any underscore will be removed (only to prevent clash with python reserved keyword)
                t=self.in_any().path,
                X=self.out_folia().path
        )

