import logging
from luigi import Parameter, BoolParameter
from piccl.engine import Task, TargetInfo
from piccl.util import replaceextension

log = logging.getLogger('mainlog')

class Ucto_txt2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, '.txt','.folia.xml'))

    def run(self):
        params = ' -L' + self.language
        if self.tok_input_sentenceperline:
            params += ' -m'
        cmd = self.executable + ' ' + params + ' '+ self.in_txt().path + ' ' + self.out_folia().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)

class Ucto_txt2tok(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)
    tok_output_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_tok(self):
        return TargetInfo( replaceextension(self.in_txt().path, '.txt','.tok'))

    def run(self):
        params = ' -L' + self.language
        if self.tok_input_sentenceperline:
            params += ' -m'
        if self.tok_output_sentenceperline:
            params += ' -n'
        cmd = self.executable + ' ' + params + ' '+ self.in_txt().path + ' ' + self.out_tok().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)

class Ucto_folia2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_folia().path, '.folia.xml','.tok.folia.xml'))

    def run(self):
        params = ' -L' + self.language
        params += ' -F '
        cmd = self.executable + ' ' + params + ' '+ self.in_txt().path + ' ' + self.out_tok().path
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        self.ex(cmd)
