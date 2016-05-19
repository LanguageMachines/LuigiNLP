import luigi
import sciluigi
import logging
import inspect
from piccl.util import shellsafe

log = logging.getLogger('mainlog')

INPUTFORMATS = []
def registerformat(f):
    if f not in INPUTFORMATS:
        INPUTFORMATS.append(f)

class InvalidInput(Exception):
    pass

class InitialInput:
    """Class that encapsulates the filename of the initial input and associates proper format classes"""

    def __init__(self, inputfilename):
        self.filename = inputfilename

        self.type = None
        self.basename = self.extension = ""
        for inputclass in INPUTFORMATS:
            if inspect.isclass(inputclass) and issubclass(inputclass, InputFormat):
                if inputfilename.endswith('.' +inputclass.extension):
                    self.type = inputclass.id
                    self.basename = inputfilename[:-(len(inputclass.extension)+1)]
                    self.extension = '.' + inputclass.extension

class InputWorkflow:
    """A class that encapsulates a WorkflowComponent and is used by other components to list possible dependencies, used in WorkflowComponent.accepts(), holds parameter information to pass to sub-workflows"""
    def __init__(self, parentcomponent, Class, *args,**kwargs):
        assert inspect.isclass(Class) and issubclass(Class,WorkflowComponent)
        self.Class = Class
        self.args = args
        self.kwargs = kwargs
        #automatically transfer parameters
        for key in dir(self.Class):
            attr = getattr(self.Class, key)
            if isinstance(attr,luigi.Parameter) and key not in self.kwargs and hasattr(parentcomponent ,key):
                self.kwargs[key] = getattr(parentcomponent, key)

class InputFormat(sciluigi.ExternalTask):
    """InputFormat, an external task""" 

    def target(self):
            return TargetInfo(self, self.basename + '.' + self.extension)

    @classmethod
    def matches(cls, filename):
        return filename.endswith('.' + cls.extension)

class WorkflowComponent(sciluigi.WorkflowTask):
    """A workflow component"""

    inputfilename = luigi.Parameter()

    def initial_task(self, initialinput, **kwargs):
        if 'id' in kwargs:
            initialtask_id = kwargs['id']
            del kwargs['id']
        else:
            initialtask_id = 'initialinput'
        assert isinstance(initialinput, InitialInput)
        return self.new_task(initialtask_id, initialinput.type, basename=initialinput.basename)

    @classmethod
    def inherit_parameters(cls, ChildClass):
        for key in dir(ChildClass):
            attr = getattr(ChildClass, key)
            if isinstance(attr,luigi.Parameter) and not hasattr(cls,key):
                setattr(cls,key, attr)

    def setup(self,workflow):
        raise NotImplementedError("Override the setup method for your workflow " + self.__class__.__name__)

    def setup_input(self, workflow):
        #Can we handle the input directly?
        for input in self.accepts(): #pylint: disable=redefined-builtin
            if issubclass(input, InputFormat) and input.matches(self.inputfilename):
                initialinput = InitialInput(self.inputfilename)
                initialtask = workflow.initial_task(initialinput)
                return initialinput.type, getattr(initialtask,'out_' + initialinput.type)

        for input in self.accepts():
            if isinstance(input, InputWorkflow):
                swf = input.Class(*input.args, **input.kwargs)
            elif inspect.isclass(input) and issubclass(input, WorkflowComponent):
                #setup sub-workflow directly
                swf = input()
            elif inspect.isclass(input) and issubclass(input, InputFormat):
                continue
            else:
                raise TypeError("Invalid element in accepts(): " + str(type(input)))

            try:
                return swf.setup(workflow)
            except InvalidInput:
                pass #try next one

        #input was not handled, raise error
        raise InvalidInput("Unable to handle input " + self.inputfilename)


    def workflow(self):
        return self.setup(self)

class Task(sciluigi.Task):
    def ex(self, *args, **kwargs):
        if not hasattr(self,'executable'):
            raise Exception("No executable defined for Task " + self.__class__.__name__)

        if self.executable[-4:] == '.jar':
            cmd = 'java -jar ' + self.executable
        else:
            cmd = self.executable
        opts = []
        for key, value in kwargs.items():
            if value is None or value is False:
                continue #no value, ignore this one
            if key[0] == '_':
                key = key[1:]
            if len(key) == 1:
                key = '-' + key
            else:
                key = '--' + key
            if value is True:
                opts.append(key)
            elif isinstance(value,str):
                opts.append(key + ' ' + shellsafe(value))
            else:
                opts.append(key + ' ' + str(value))
        if opts:
            cmd += ' ' + ' '.join(opts)
        if args:
            cmd += ' ' + ' '.join(args)
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        super(Task, self).ex(cmd)

    @classmethod
    def inherit_parameters(Class, *ChildClasses):
        for ChildClass in ChildClasses:
            for key in dir(ChildClass):
                attr = getattr(ChildClass, key)
                if isinstance(attr,luigi.Parameter) and not hasattr(Class, key):
                    setattr(Class,key, attr)

class TargetInfo(sciluigi.TargetInfo):
    pass
