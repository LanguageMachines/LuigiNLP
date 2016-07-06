import os
import glob
import natsort
import subprocess
import pickle
from luiginlp.engine import Task, TargetInfo, InputFormat, StandardWorkflowComponent, registercomponent, InputSlot, Parameter, BoolParameter, IntParameter, PassParameters, ParallelBatch
from luiginlp.util import getlog, recursive_glob, waitforslot, waitforcompletion, replaceextension, chunk
from luiginlp.modules.openconvert import OpenConvert_folia

log = getlog()

@registercomponent
class ConvertToFoLiA(StandardWorkflowComponent):
    def accepts(self):
        return (
            InputFormat(self, format_id='tei', extension='tei.xml'),
            InputFormat(self, format_id='docx', extension='docx'),
            InputFormat(self, format_id='rst', extension='rst'),
            InputFormat(self, format_id='alpinodocdir', extension='alpinodocdir',directory=True),
        )

    def setup(self, workflow, input_feeds):
        for input_format_id, input_feed in input_feeds.items():
            if input_format_id in ('docx','tei'):
                #Input is something OpenConvert can handle: convert to FoLiA first
                openconvert = workflow.new_task('openconvert',OpenConvert_folia,from_format=input_format_id)
                openconvert.in_any = input_feed
                return openconvert #always return last task
            elif input_format_id == 'rst':
                rst2folia = workflow.new_task('rst2folia',Rst2folia)
                rst2folia.in_rst = input_feed
                return rst2folia #always return last task
            elif input_format_id == 'alpinodocdir':
                alpino2folia = workflow.new_task('alpino2folia',Alpino2folia)
                alpino2folia.in_alpinodocdir = input_feed
                return alpino2folia #always return last task


class Rst2folia(Task):
    executable = 'rst2folia' #external executable (None if n/a)

    in_rst = InputSlot() #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return self.outputfrominput(inputformat='rst',stripextension='.rst', addextension='.folia.xml')

    def run(self):
        self.ex(self.in_rst().path, self.out_folia().path,
            docid=os.path.basename(self.in_rst().path).split('.')[0]) #first component of input filename (up to first period) will be FoLiA ID

class Folia2html(Task):
    executable = 'folia2html' #external executable (None if n/a)

    in_folia = InputSlot() #will be linked to an out_* slot of another module in the workflow specification

    def out_html(self):
        return self.outputfrominput(inputformat='folia',stripextension='.folia.xml', addextension='.html')

    def run(self):
        self.ex(self.in_folia().path,
            o=self.out_html().path)

class Folia2txt(Task):
    executable = 'folia2txt' #external executable (None if n/a)

    sentenceperline = BoolParameter(default=False)
    paragraphperline = BoolParameter(default=False)
    retaintokenisation = BoolParameter(default=False)

    in_folia = InputSlot() #will be linked to an out_* slot of another module in the workflow specification

    def out_html(self):
        return self.outputfrominput(inputformat='folia',stripextension='.folia.xml', addextension='.txt')

    def run(self):
        self.ex(self.in_folia().path,
            o=self.out_html().path,
            s=self.sentenceperline,
            p=self.paragraphperline,
            t=self.retaintokenisation)

class Alpino2folia(Task):
    executable = 'alpino2folia'

    in_alpinodocdir = InputSlot()

    def out_folia(self):
        return self.outputfrominput(inputformat='alpinodocdir',stripextension='.alpinodocdir', addextension='.folia.xml')

    def run(self):
        alpinofiles = [ alpinofile for alpinofile in sorted(glob.glob(self.in_alpinodocdir().path + '/*.xml'),key=lambda x: int(os.path.basename(x).split('.')[0])) ] #collect all alpino files in collection
        args = alpinofiles + [self.out_folia().path] #last argument is folia output
        self.ex(*args)


class Foliacat(Task):
    executable = 'foliacat'

    extension = Parameter(default='folia.xml')

    in_foliadir = InputSlot()

    def out_folia(self):
        return self.outputfrominput(inputformat='foliadir',stripextension='.foliadir', addextension='.folia.xml')

    def run(self):
        foliafiles = [ filename for filename in natsort.natsorted(glob.glob(self.in_foliadir().path + '/*.' + self.extension)) ]
        self.ex(*foliafiles,
                o=self.out_folia().path,
                i=self.out_folia().path.split('.')[0]) #first component of filename acts as document ID


class FoliaHOCR(Task):
    """Converts a directory of hocr files to a directory of FoLiA files"""
    executable = "FoLiA-hocr"

    threads = Parameter(default=1)

    in_hocrdir = InputSlot()

    def out_foliadir(self):
        """Directory of FoLiA document, one per hOCR file"""
        return self.outputfrominput(inputformat='hocrdir',stripextension='.hocrdir', addextension='.foliadir')

    def run(self):
        self.setup_output_dir(self.out_foliadir().path)
        self.ex(self.in_hocrdir().path,
                t=self.threads,
                O=self.out_foliadir().path)

class FoliaValidatorTask(Task):
    executable = "foliavalidator"
    folia_extension = Parameter(default='folia.xml')

    in_folia = InputSlot()

    def out_validator(self):
        return self.outputfrominput(inputformat='folia',stripextension=self.folia_extension, addextension='.folia-validation-report.txt')

    def run(self):
        #If an explicit outputdir is given, ensure the directory for the output file exists (including any intermediate directories)
        if self.outputdir:
            self.setup_output_dir(os.path.dirname(self.out_validator().path))

        #Run the validator
        self.ex(self.in_folia().path,
            __stderr_to=self.out_validator().path,
            __ignorefailure=True) #if the validator fails (it does when the document is invalid),  we ignore it as that is a valid result for us

class FoliaValidatorDirTask(Task):
    executable = "foliavalidator"
    in_foliadir = InputSlot()
    folia_extension = Parameter(default='folia.xml')
    validatorthreads = IntParameter(default=1)

    def out_validationsummary(self):
        return self.outputfrominput(inputformat='foliadir',stripextension='.foliadir', addextension='.folia-validation-summary.txt')

    def out_state(self):
        return self.outputfrominput(inputformat='foliadir',stripextension='.foliadir', addextension='.foliavalidatordirtask.state.pickle')


    def on_failure(self, exception):
        if os.path.exists(self.out_state().path):
            os.unlink(self.out_state().path)
        return super().on_failure(exception)

    def run(self):
        #gather input files
        if self.outputdir and not os.path.exists(self.outputdir): os.makedirs(self.outputdir)

        if os.path.exists(self.out_state().path):
            log.info("Collecting input files from saved state...")
            with open(self.out_state().path,'rb') as f:
                inputfiles = pickle.load(f)
        else:
            log.info("Collecting input files...")
            inputfiles = recursive_glob(self.in_foliadir().path, '*.' + self.folia_extension)
            log.info("Collected " + str(len(inputfiles)) + " input files")
            with open(self.out_state().path,'wb') as f:
                pickle.dump(inputfiles,f)

        log.info("Scheduling validators")
        if self.outputdir:
            passparameters = PassParameters(folia_extension=self.folia_extension,replaceinputdir=self.in_foliadir().path, outputdir=self.outputdir)
        else:
            passparameters = PassParameters(folia_extension=self.folia_extension)

        for inputfiles_batch in chunk(inputfiles,1000): #schedule in batches of 1000 so we don't overload the scheduler
            yield ParallelBatch(component='FoliaValidator',inputfiles=inputfiles_batch,passparameters=passparameters)

        log.info("Collecting output files...")
        #Gather all output files
        if self.outputdir:
            outputfiles = recursive_glob(self.outputdir, '*.folia-validation-report.txt')
        else:
            outputfiles = recursive_glob(self.in_foliadir().path, '*.folia-validation-report.txt')

        log.info("Writing summary")
        with open(self.out_validationsummary().path,'w',encoding='utf-8') as f_summary:
            for outputfilename in outputfiles:
                with open(outputfilename, 'r',encoding='utf-8') as f:
                    success = False
                    for line in f:
                        if line.startswith('Validated successfully'):
                            success = True
                            break
                if success:
                    f_summary.write(outputfilename + ": OK\n")
                else:
                    f_summary.write(outputfilename + ": ERROR\n")

@registercomponent
class FoliaValidator(StandardWorkflowComponent):
    folia_extension = Parameter(default='folia.xml')

    def accepts(self):
        return (
            InputFormat(self, format_id='folia', extension=self.folia_extension),
            InputFormat(self, format_id='foliadir', extension='foliadir'))

    def autosetup(self):
        return FoliaValidatorTask, FoliaValidatorDirTask

FoliaValidator.inherit_parameters(FoliaValidatorTask, FoliaValidatorDirTask)
