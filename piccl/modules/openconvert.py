import os
import logging
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo
from piccl.util import replaceextension

log = logging.getLogger('mainlog')

class OpenConvert_folia(Task):
    executable = 'OpenConvert.jar' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    from_format = Parameter()

    in_any = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, ['.tei.xml', '.alto.xml','.tei', '.alto', '.xml', '.doc','.docx','.html', '.epub'],'.openconvert.folia.xml'))

    def run(self):
        params = ' --from=' + self.from_format
        cmd = 'java -jar ' + os.environ['VIRTUAL_ENV'] + '/java/' + self.executable + ' ' + params + ' -t ' + self.in_txt().path + ' -X ' + self.out_folia().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)

class OpenConvert_tei(Task):
    executable = 'OpenConvert.jar' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    from_format = Parameter()

    in_any = None #will be linked to an out_* slot of another module in the workflow specification

    def out_tei(self):
        return TargetInfo( replaceextension(self.in_txt().path, ['.folia.xml', '.alto.xml','.tei', '.alto', '.xml', '.doc','.docx','.html', '.epub'],'.openconvert.tei.xml'))

    def run(self):
        params = ' --from=' + self.from_format
        log.info("Running " + self.__class__.__name__)
        cmd = 'java -jar ' + os.environ['VIRTUAL_ENV'] + '/java/' + self.executable + ' ' + params + ' -t ' + self.in_txt().path + ' -X ' + self.out_folia().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)

