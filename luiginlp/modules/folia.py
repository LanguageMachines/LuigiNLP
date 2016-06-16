import os
import glob
import natsort
from luigi import Parameter, BoolParameter
from luiginlp.engine import Task, TargetInfo, InputFormat, StandardWorkflowComponent, registercomponent
from luiginlp.util import getlog
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

    in_rst = None #will be linked to an out_* slot of another module in the workflow specification

    def out_folia(self):
        return self.outputfrominput(inputformat='rst',inputextension='.rst', outputextension='.folia.xml')

    def run(self):
        self.ex(self.in_rst().path, self.out_folia().path,
            docid=os.path.basename(self.in_rst().path).split('.')[0]) #first component of input filename (up to first period) will be FoLiA ID

class Folia2html(Task):
    executable = 'folia2html' #external executable (None if n/a)

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_html(self):
        return self.outputfrominput(inputformat='folia',inputextension='.folia.xml', outputextension='.html')

    def run(self):
        self.ex(self.in_folia().path,
            o=self.out_html().path)

class Folia2txt(Task):
    executable = 'folia2txt' #external executable (None if n/a)

    sentenceperline = BoolParameter(default=False)
    paragraphperline = BoolParameter(default=False)
    retaintokenisation = BoolParameter(default=False)

    in_folia = None #will be linked to an out_* slot of another module in the workflow specification

    def out_html(self):
        return self.outputfrominput(inputformat='folia',inputextension='.folia.xml', outputextension='.txt')

    def run(self):
        self.ex(self.in_folia().path,
            o=self.out_html().path,
            s=self.sentenceperline,
            p=self.paragraphperline,
            t=self.retaintokenisation)

class Alpino2folia(Task):
    executable = 'alpino2folia'

    in_alpinodocdir = None

    def out_folia(self):
        return self.outputfrominput(inputformat='alpinodocdir',inputextension='.alpinodocdir', outputextension='.folia.xml')

    def run(self):
        alpinofiles = [ alpinofile for alpinofile in sorted(glob.glob(self.in_alpinodocdir().path + '/*.xml'),key=lambda x: int(os.path.basename(x).split('.')[0])) ] #collect all alpino files in collection
        args = alpinofiles + [self.out_folia().path] #last argument is folia output
        self.ex(*args)


class Foliacat(Task):
    executable = 'foliacat'

    extension = Parameter(default='folia.xml')

    in_foliadir = None

    def out_folia(self):
        return self.outputfrominput(inputformat='foliadir',inputextension='.foliadir', outputextension='.folia.xml')

    def run(self):
        foliafiles = [ filename for filename in natsort.natsorted(glob.glob(self.in_foliadir().path + '/*.' + self.extension)) ]
        self.ex(*foliafiles,
                o=self.out_folia().path,
                i=self.out_folia().path.split('.')[0]) #first component of filename acts as document ID


class FoliaHOCR(Task):
    """Converts a directory of hocr files to a directory of FoLiA files"""
    executable = "FoLiA-hocr"

    threads = Parameter(default=1)

    in_hocrdir = None

    def out_foliadir(self):
        """Directory of FoLiA document, one per hOCR file"""
        return self.outputfrominput(inputformat='hocrdir',inputextension='.hocrdir', outputextension='.foliadir')

    def run(self):
        self.setup_output_dir(self.out_foliadir().path)
        self.ex(self.in_hocrdir().path,
                t=self.threads,
                O=self.out_foliadir().path)
