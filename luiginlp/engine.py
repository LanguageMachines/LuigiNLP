import sys
import luigi
import sciluigi
import logging
import inspect
import argparse
from luiginlp.util import shellsafe

log = logging.getLogger('mainlog')

INPUTFORMATS = []
COMPONENTS = []

def registerformat(Class):
    assert inspect.isclass(Class) and issubclass(Class,InputFormat)
    if Class not in INPUTFORMATS:
        INPUTFORMATS.append(Class)
    return Class

def registercomponent(Class):
    assert inspect.isclass(Class) and issubclass(Class,WorkflowComponent)
    if Class not in COMPONENTS:
        COMPONENTS.append(Class)
    return Class

class InvalidInput(Exception):
    pass

class AutoSetupError(Exception):
    pass

class InitialInput:
    """Class that encapsulates the filename of the initial input and associates proper format classes"""

    def __init__(self, inputfile):
        self.filename = inputfile

        self.type = None
        self.basename = self.extension = ""
        for inputclass in INPUTFORMATS:
            if inspect.isclass(inputclass) and issubclass(inputclass, InputFormat):
                if inputfile.endswith('.' +inputclass.extension):
                    self.type = inputclass
                    self.basename = inputfile[:-(len(inputclass.extension)+1)]
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

    inputfile = luigi.Parameter()

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
        if hasattr(self, 'autosetup'):
            input_type, input_slot = self.setup_input(workflow)
            for TaskClass in self.autosetup:
                if not inspect.isclass(TaskClass) or not issubclass(TaskClass,Task):
                    raise AutoSetupError("AutoSetup expected a Task class, got " + str(type(TaskClass)))
                if hasattr(TaskClass, 'in_' + input_type):
                    passparameters = {}
                    for key in dir(TaskClass):
                        if key not in ('instance_name', 'workflow_task') and isinstance(getattr(TaskClass,key), luigi.Parameter):
                            if hasattr(self, key):
                                passparameters[key] = getattr(self,key)
                    task = workflow.new_task(TaskClass.__name__, TaskClass,**passparameters)
                    setattr(task, 'in_' + input_type, input_slot)
                    for key in dir(TaskClass):
                        if key.startswith('out_'):
                            return key[4:], task
                    raise AutoSetupError("No output slots found on " + TaskClass.__name__)
            raise AutoSetupError("No matching input slots found on specified task (looking for " + input_type + ")")
        else:
            raise NotImplementedError("Override the setup method for your workflow " + self.__class__.__name__ + " or set autosetup")

    def setup_input(self, workflow):
        #Can we handle the input directly?
        for input in self.accepts(): #pylint: disable=redefined-builtin
            if issubclass(input, InputFormat) and input.matches(self.inputfile):
                initialinput = InitialInput(self.inputfile)
                initialtask = workflow.initial_task(initialinput)
                return initialinput.type.id, getattr(initialtask,'out_' + initialinput.type.id)

        for input in self.accepts():
            if isinstance(input, InputWorkflow):
                swf = input.Class(*input.args, **input.kwargs)
            elif inspect.isclass(input) and issubclass(input, WorkflowComponent):
                #not encapsulated in InputWorkflow yet, do now
                iwf = InputWorkflow(self, input)
                swf = iwf.Class(*input.args, **input.kwargs)
            elif inspect.isclass(input) and issubclass(input, InputFormat):
                continue
            else:
                raise TypeError("Invalid element in accepts(): " + str(type(input)))

            try:
                inputtype, inputtask = swf.setup(workflow)
                return inputtype, getattr(inputtask, 'out_' + inputtype)
            except InvalidInput:
                pass #try next one

        #input was not handled, raise error
        raise InvalidInput("Unable to handle input " + self.inputfile)


    def workflow(self):
        outputtype, task = self.setup(self)
        return task

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
            if key.startswith('__'): #internal option: ignore
                continue
            delimiter = ' '
            if key[0] == '_':
                key = key[1:]
            if '__nospace' in kwargs and kwargs['__nospace']:
                delimiter = ''
            if len(key) == 1 or ('__singlehyphen' in kwargs and kwargs['__singlehyphen']):
                key = '-' + key
            else:
                key = '--' + key
                if '__useequals' in kwargs and kwargs['__useequals']:
                    delimiter = '='

            if value is True:
                opts.append(key)
            elif isinstance(value,str):
                opts.append(key + delimiter + shellsafe(value))
            else:
                opts.append(key + delimiter + str(value))
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


def getcomponentclass(classname):
    for Class in COMPONENTS:
        if Class.__name__ == classname:
            return Class
    raise Exception("No such component: " + classname)

class Parallel(sciluigi.WorkflowTask):
    """Meta workflow"""
    inputfiles = luigi.Parameter()
    component = luigi.Parameter()
    parameters = luigi.Parameter(default="")

    def workflow(self):
        tasks = []
        ComponentClass = getcomponentclass(self.component)
        for inputfile in self.inputfiles.split(','):
            tasks.append( self.new_task(self.component, ComponentClass, inputfile=inputfile) )
        return tasks

def run(*args, **kwargs):
    if 'local_scheduler' in kwargs:
        if not args:
            luigi.run(**kwargs)
        else:
            luigi.build(args,**kwargs)
    else:
        if not args:
            luigi.run(local_scheduler=True,**kwargs)
        else:
            luigi.build(args,local_scheduler=True,**kwargs)

def run_cmdline(TaskClass,**kwargs):
    if 'local_scheduler' in kwargs:
        local_scheduler = kwargs['local_scheduler']
        return local_scheduler
    else:
        local_scheduler=True
    cmdline_args = []
    for key, value in kwargs.items():
        if inspect.isclass(value):
            value = value.__name__
        cmdline_args.append('--' + key + ' ' + str(shellsafe(value)))
    luigi.run(main_task_cls=TaskClass,cmdline_args=' '.join(cmdline_args), local_scheduler=local_scheduler)




