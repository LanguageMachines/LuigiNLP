from sciluigi import Task, TargetInfo
from luigi import StringParameter, BoolParameter
import os
from piccl.util import replaceextension

class OpenConvert_folia(Task):
    executable = 'OpenConvert.jar' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    tok_input_sentenceperline = BoolParameter(default=False)
    from_format = StringParameter()

    in_any = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, ['.tei.xml', '.alto.xml','.tei', '.alto', '.xml', '.doc','.docx','.html'],'.openconvert.folia.xml'))

    def run(self):
        params = ' --from=' + self.from_format
        self.ex('java -jar ' + os.environ['VIRTUAL_ENV'] + '/java/' + self.executable + ' ' + params + ' -t ' + self.in_txt().path + ' -X ' + self.out_folia().path)
