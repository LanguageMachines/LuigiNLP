import glob
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, registercomponent, StandardWorkflowComponent, InputComponent, InputFormat
from luiginlp.util import getlog
from luiginlp.modules.folia import ConvertToFoLiA

log = getlog()

class Ucto_txt2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return self.outputfrominput(inputformat='txt',inputextension='.txt', outputextension='.folia.xml')

    def run(self):
        self.ex(self.in_txt().path(), self.out_folia().path,
                L=self.language,
                m=self.tok_input_sentenceperline,
                X=True)

class Ucto_txt2tok(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)
    tok_output_sentenceperline = BoolParameter(default=False)

    in_txt = None #will be linked to an out_* slot of another module in the workflow specification

    def out_tok(self):
        return self.outputfrominput(inputformat='txt',inputextension='.txt', outputextension='.tok')

    def run(self):
        self.ex(self.in_txt().path(), self.out_tok().path,
                L=self.language,
                m=self.tok_input_sentenceperline,
                n=self.tok_output_sentenceperline)

class Ucto_folia2folia(Task):
    executable = 'ucto' #external executable (None if n/a)

    #Parameters for this module (all mandatory!)
    language = Parameter()


    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return self.outputfrominput(inputformat='folia',inputextension='.folia.xml', outputextension='.tok.folia.xml')

    def run(self):
        self.ex(self.in_txt().path(), self.out_folia().path,
                L=self.language,
                F=True, #folia input
                X=True) #folia output

#################################################################################################################
# Workflow Components
#################################################################################################################

@registercomponent
class Ucto(StandardWorkflowComponent):
    """A workflow component for Ucto"""

    skip = Parameter(default="") #A parameter for the workflow, will be passed on to the tasks

    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)
    tok_output_sentenceperline = BoolParameter(default=False)

    def autosetup(self):
        return (Ucto_txt2folia, Ucto_folia2folia)

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return (
            InputFormat(self, format_id='folia', extension='folia.xml'),
            InputFormat(self, format_id='txt', extension='txt'),
            InputComponent(self, ConvertToFoLiA))


class Ucto_txt2folia_dir(Task):
    extension = Parameter(default="txt")
    language = Parameter()

    in_txtdir = None #input slot

    def out_tokfoliadir(self):
        return self.outputfrominput(inputformat='txtdir',inputextension='.txtdir', outputextension='.tok.foliadir')

    def run(self):
        #Set up the output directory, will create it and tear it down on failure automatically
        self.setup_output_dir(self.out_tokfoliadir().path)

        #gather input files
        inputfiles = [ filename for filename in glob.glob(self.in_txtdir().path + '/*.' + self.extension) ]

        #inception aka dynamic dependencies: we yield a list of tasks to perform which could not have been predicted statically
        #in this case we run the FeaturizerTask_single component for each input file in the directory
        yield [ Ucto(inputfile=inputfile,inputslot='txt',outputdir=self.out_tokfoliadir().path,language=self.language) for inputfile in inputfiles ]

class Ucto_folia2folia_dir(Task):
    extension = Parameter(default="folia.xml")
    language = Parameter()

    in_foliadir = None #input slot

    def out_tokfoliadir(self):
        return self.outputfrominput(inputformat='foliadir',inputextension='.foliadir', outputextension='.tok.foliadir')

    def run(self):
        #Set up the output directory, will create it and tear it down on failure automatically
        self.setup_output_dir(self.out_tokfoliadir().path)

        #gather input files
        inputfiles = [ filename for filename in glob.glob(self.in_foliadir().path + '/*.' + self.extension) ]

        #inception aka dynamic dependencies: we yield a list of tasks to perform which could not have been predicted statically
        #in this case we run the FeaturizerTask_single component for each input file in the directory
        yield [ Ucto(inputfile=inputfile,inputslot='folia',outputdir=self.out_tokfoliadir().path,language=self.language) for inputfile in inputfiles ]

@registercomponent
class Ucto_dir(StandardWorkflowComponent):
    """A workflow component for Ucto that operates on entire directories"""

    skip = Parameter(default="") #A parameter for the workflow, will be passed on to the tasks

    language = Parameter()
    tok_input_sentenceperline = BoolParameter(default=False)
    tok_output_sentenceperline = BoolParameter(default=False)

    def autosetup(self):
        return (Ucto_txt2folia_dir, Ucto_folia2folia_dir)

    def accepts(self):
        """Returns a tuple of all the initial inputs and other workflows this component accepts as input (a disjunction, only one will be selected)"""
        return (
            InputFormat(self, format_id='txtdir', extension='txtdir', directory=True),
            InputFormat(self, format_id='foliadir', extension='foliadir', directory=True))

