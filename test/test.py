import sys
import os
import unittest
from luigi import Parameter
import luiginlp
from luiginlp.engine import Task, StandardWorkflowComponent, InputFormat, InputComponent


class LowercaseTask(Task):
    """A simple task, implemented in python"""

    in_txt = None
    encoding = Parameter(default='utf-8')

    def out_txt(self):
        return self.outputfrominput(inputformat='txt',inputextension='.txt',outputextension='.lowercase.txt')

    def run(self):
        with open(self.in_txt().path,'r',encoding=self.encoding) as f_in:
            with open(self.out_txt().path,'w',encoding=self.encoding) as f_out:
                f_out.write(f_in.read().lower())

class Lowercaser(StandardWorkflowComponent):
    """Component wrapping a single task, using autosetup()"""

    def autosetup(self):
        return LowercaseTask

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

Lowercaser.inherit_parameters(LowercaseTask)


class Lowercaser2(StandardWorkflowComponent):
    """Component wrapping a single task, using setup()"""

    def setup(self, workflow, input_feeds):
        lowercaser = workflow.new_task('lowercaser',LowercaseTask, autopass=True)
        lowercaser.in_txt = input_feeds['txt']
        return lowercaser

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

Lowercaser2.inherit_parameters(LowercaseTask)

class VoweleaterTask(Task):
    """Example of a task that invokes an external tool and uses stdin and stdout. This one simply removes vowels from a text."""
    executable = 'sed'
    in_txt = None
    encoding = Parameter(default='utf-8')

    def out_txt(self):
        return self.outputfrominput(inputformat='txt',inputextension='.txt',outputextension='.novowels.txt')

    def run(self):
        self.ex(e='s/[aeiouAEIOU]//g',__stdin_from=self.in_txt().path,__stdout_to=self.out_txt().path)


class Voweleater(StandardWorkflowComponent):
    def autosetup(self):
        return VoweleaterTask

    def accepts(self):
        return (InputFormat(self, format_id='txt',extension='txt'), InputComponent(self, Lowercaser))

Voweleater.inherit_parameters(VoweleaterTask)

class LowercaseVoweleater(StandardWorkflowComponent):
    """A component that chains two tasks"""

    def setup(self, workflow, input_feeds):
        lowercaser = workflow.new_task('lowercaser',LowercaseTask, autopass=True)
        lowercaser.in_txt = input_feeds['txt']
        voweleater = workflow.new_task('voweleater',VoweleaterTask, autopass=True)
        voweleater.in_txt = lowercaser.out_txt
        return voweleater #always return the last task

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

LowercaseVoweleater.inherit_parameters(VoweleaterTask, LowercaseTask)




#------------------------------------------------------------------------------------------------------------

def testfilecontents(filename, contents):
    if not os.path.exists(filename): return False
    with open(filename,'r') as f:
        actualcontents = f.read()
    if actualcontents == contents:
        return True
    else:
        print("CONTENT MISMATCH, GOT: ", actualcontents, ", EXPECTED: ", contents, file=sys.stderr)
        return False



class Test1(unittest.TestCase):
    def setUp(self):
        with open('/tmp/test.txt','w',encoding='utf-8') as f:
            f.write("THIS IS A TEST")

    def tearDown(self):
        for filename in ('/tmp/test.txt','/tmp/test.lowercase.txt','/tmp/test.novowels.txt', '/tmp/test.lowercase.novowels.txt'):
            if os.path.exists(filename):
                os.unlink(filename)

    def test10(self):
        """Single task in single component, with autosetup"""
        luiginlp.run(Lowercaser(inputfile='/tmp/test.txt'))
        self.assertTrue(testfilecontents('/tmp/test.lowercase.txt', 'this is a test'))

    def test20(self):
        """Single task in single component, with autosetup, passing parameter"""
        luiginlp.run(Lowercaser(inputfile='/tmp/test.txt', encoding='ascii'))
        self.assertTrue(testfilecontents('/tmp/test.lowercase.txt', 'this is a test'))

    def test30(self):
        """Single task in single component, with setup"""
        luiginlp.run(Lowercaser2(inputfile='/tmp/test.txt'))
        self.assertTrue(testfilecontents('/tmp/test.lowercase.txt', 'this is a test'))

    def test40(self):
        """Single task in single component, with setup, passing parameter with autopass"""
        luiginlp.run(Lowercaser2(inputfile='/tmp/test.txt', encoding='ascii'))
        self.assertTrue(testfilecontents('/tmp/test.lowercase.txt', 'this is a test'))

    def test50(self):
        """Single task in single component, task calling external tool"""
        luiginlp.run(Voweleater(inputfile='/tmp/test.txt'))
        self.assertTrue(testfilecontents('/tmp/test.novowels.txt', 'THS S  TST'))

    def test60(self):
        """Two chained tasks in single component"""
        luiginlp.run(LowercaseVoweleater(inputfile='/tmp/test.txt'))
        self.assertTrue(testfilecontents('/tmp/test.lowercase.novowels.txt', 'ths s  tst'))

    def test70(self):
        """Two chained components, with explicit startcomponent"""
        luiginlp.run(Voweleater(inputfile='/tmp/test.txt',startcomponent='Lowercaser'))
        self.assertTrue(testfilecontents('/tmp/test.lowercase.novowels.txt', 'ths s  tst'))


if __name__ == '__main__':
    unittest.main()
