from sciluigi import Task, TargetInfo
from luigi import StringParameter, BoolParameter
from piccl.util import replaceextension


class Ucto_txt2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = StringParameter()
    tok_input_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_txt().path, '.txt','.folia.xml'))

    def run(self):
        params = ' -L' + self.language
        if self.tok_input_sentenceperline:
            params += ' -m'
        self.ex(self.executable + ' ' + params + ' '+ self.in_txt().path + ' ' + self.out_folia().path)

class Ucto_txt2tok(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = StringParameter()
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
        self.ex(self.executable + ' ' + params + ' '+ self.in_txt().path + ' ' + self.out_tok().path)

class Ucto_folia2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = StringParameter()

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return TargetInfo( replaceextension(self.in_folia().path, '.folia.xml','.tok.folia.xml'))

    def run(self):
        params = ' -L' + self.language
        params += ' -F '
        self.ex(self.executable + ' ' + params + ' '+ self.in_txt().path + ' ' + self.out_tok().path)
