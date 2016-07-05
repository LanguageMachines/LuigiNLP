import sys
import os
import unittest
import glob
import shutil
import luiginlp
from luiginlp.engine import Task, StandardWorkflowComponent, PassParameters, InputFormat, InputComponent, InputSlot, Parameter, IntParameter, registercomponent, Parallel
from luiginlp.util import getlog, chunk

log = getlog()


class VoweleaterTask(Task):
    """Example of a task that invokes an external tool and uses stdin and stdout. This one simply removes vowels from a text."""
    executable = 'sed'
    in_txt = InputSlot()
    encoding = Parameter(default='utf-8')

    def out_txt(self):
        return self.outputfrominput(inputformat='txt',stripextension='.txt',addextension='.novowels.txt')

    def run(self):
        self.ex(e='s/[aeiouAEIOU]//g',__stdin_from=self.in_txt().path,__stdout_to=self.out_txt().path)


@registercomponent
class Voweleater(StandardWorkflowComponent):
    def autosetup(self):
        return VoweleaterTask

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

Voweleater.inherit_parameters(VoweleaterTask)

#class SplitTask(Task):
#    inputfiles = Parameter()
#    component = Parameter()
#    passparameters = PassParameters()
#
#    def out_split(self):
#        return TargetInfo(self, self.basename + '.' + self.extension)
#
#    def run(self):
#        ComponentClass = getcomponentclass(self.component)
#        yield [ ComponentClass(inputfile=inputfile,outputdir=self.out_txtdir().path) for inputfile in inputfiles ]





class ScaleTestTask(Task):

    in_txtdir = InputSlot()
    n = IntParameter()

    def out_txtdir(self):
        return self.outputfrominput(inputformat='txtdir',stripextension='.txtdir',addextension='.out.txtdir')


    def run(self):
        self.setup_output_dir(self.out_txtdir().path)

        #gather input files
        log.info("Collecting input files...")
        inputfiles = [ os.path.join(self.in_txtdir().path, str(i) + '.txt') for i in range(1,self.n+1) ]
        log.info("Collected " + str(len(inputfiles)) + " input files")

        #inception aka dynamic dependencies: we yield a list of tasks to perform which could not have been predicted statically
        #in this case we run the OCR_singlepage component for each input file in the directory

        chunks = [ Parallel(component='Voweleater',inputfiles=','.join(inputfiles_chunk),passparameters=PassParameters(outputdir=self.out_txtdir().path)) for inputfiles_chunk  in chunk(inputfiles, 1000) ]
        log.info("Scheduling chunks: " + str(len(chunks)))
        yield chunks

        #yield [ Voweleater(inputfile=inputfile,outputdir=self.out_txtdir().path) for inputfile in inputfiles ]



class ScaleTest(StandardWorkflowComponent):

    n = IntParameter()

    def accepts(self):
        return InputFormat(self, format_id='txtdir',extension='txtdir', directory=True)

    def autosetup(self):
        return ScaleTestTask



if __name__ == '__main__':
    workdir = sys.argv[1]
    n = int(sys.argv[2])
    if not os.path.exists(workdir):
        os.mkdir(workdir)
    print("Preparing, making input files",file=sys.stderr)
    for i in range(1, n+1):
        print(i,file=sys.stderr)
        filename = workdir + '/' + str(i) + '.txt'
        if not os.path.exists(filename):
            with open(filename,'w',encoding='utf-8') as f:
                f.write("test")

    luiginlp.run(ScaleTest(inputfile=workdir,n=n),workers=5)


