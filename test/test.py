import os
import unittest
from luigi import Parameter
import luiginlp
from luiginlp.engine import Task, StandardWorkflowComponent, InputFormat


class LowercaseTask(Task):
    in_txt = None
    encoding = Parameter(default='utf-8')

    def out_txt(self):
        return self.outputfrominput(inputformat='txt',inputextension='.txt',outputextension='.lowercase.txt')

    def run(self):
        with open(self.in_txt().path,'r',encoding=self.encoding) as f_in:
            with open(self.out_txt().path,'w',encoding=self.encoding) as f_out:
                f_out.write(f_in.read().lower())

class LowerCaser(StandardWorkflowComponent):
    def autosetup(self):
        return LowercaseTask

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

LowerCaser.inherit_parameters(LowercaseTask)


class LowerCaser2(StandardWorkflowComponent):
    def setup(self, workflow, input_feeds):
        lowercaser = workflow.new_task('lowercaser',LowercaseTask, autopass=True)
        lowercaser.in_txt = input_feeds['txt']
        return lowercaser

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

LowerCaser2.inherit_parameters(LowercaseTask)


class SingleComponentTest(unittest.TestCase):
    def setUp(self):
        with open('/tmp/test.txt','w',encoding='utf-8') as f:
            f.write("THIS IS A TEST")

    def tearDown(self):
        for filename in ('/tmp/test.txt','/tmp/test.lowercase.txt'):
            if os.path.exists(filename):
                os.unlink(filename)

    def test10(self):
        """Single task in single component, with autosetup"""
        luiginlp.run(LowerCaser(inputfile='/tmp/test.txt'))

    def test20(self):
        """Single task in single component, with autosetup, passing parameter"""
        luiginlp.run(LowerCaser(inputfile='/tmp/test.txt', encoding='ascii'))

    def test30(self):
        """Single task in single component, with setup"""
        luiginlp.run(LowerCaser2(inputfile='/tmp/test.txt'))

    def test40(self):
        """Single task in single component, with setup, passing parameter with autopass"""
        luiginlp.run(LowerCaser2(inputfile='/tmp/test.txt', encoding='ascii'))

if __name__ == '__main__':
    unittest.main()
