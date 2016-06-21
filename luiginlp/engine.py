import sys
import os
import luigi
import sciluigi
import logging
import inspect
import argparse
import importlib
import itertools
import shutil
import glob
from luiginlp.util import shellsafe, getlog, replaceextension

log = getlog()

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

class SchedulingError(Exception):
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

class InputComponent:
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

class InputTask(sciluigi.ExternalTask):
    """InputTask, an external task"""

    format_id=luigi.Parameter()
    basename = luigi.Parameter()
    extension = luigi.Parameter()
    directory = luigi.BoolParameter()

    def out_default(self):
        return TargetInfo(self, self.basename + '.' + self.extension)


class InputFormat:
    """A class that encapsulates an initial task"""

    def __init__(self, workflow, format_id, extension, inputparameter='inputfile', directory=False, force=False):
        assert isinstance(workflow,WorkflowComponent)
        self.inputtask = None
        self.valid = False
        self.format_id = format_id
        self.extension = extension
        self.directory = directory
        if getattr(workflow,inputparameter).endswith('.' + extension) or force:
            self.basename =  getattr(workflow,inputparameter)[:-(len(extension) + 1)]
            self.valid = True

    def task(self, workflow):
        if self.valid:
            return workflow.new_task('inputtask_' + self.format_id, InputTask, basename=self.basename, format_id=self.format_id,extension=self.extension, directory=self.directory)
        else:
            raise Exception("Can't produce task for an invalid inputformat!")



class WorkflowComponent(sciluigi.WorkflowTask):
    """A workflow component"""

    startcomponent = luigi.Parameter(default="")
    inputslot = luigi.Parameter(default="")

    accepted_components = [] #additional accepted components (will be injected through the accept() method)

    @classmethod
    def accept(cls, *ChildClasses):
        for ChildClass in ChildClasses:
            if ChildClass not in cls.accepted_components:
                cls.accepted_components.append(ChildClass)

    @classmethod
    def inherit_parameters(cls, *ChildClasses):
        for ChildClass in ChildClasses:
            for key in dir(ChildClass):
                if key not in ('instance_name', 'workflow_task'):
                    attr = getattr(ChildClass, key)
                    if isinstance(attr,luigi.Parameter) and not hasattr(cls,key):
                        setattr(cls,key, attr)

    def setup(self,workflow, input_feeds):
        if hasattr(self, 'autosetup'):
            input_feeds = self.setup_input(workflow)
            if len(input_feeds) > 1:
                #print("Input feed from "  + self.__class__.__name__ + ": ", len(input_feeds), repr(input_feeds),file=sys.stderr)
                raise AutoSetupError("Autosetup only works for single input/output tasks for now")
            configuration = self.autosetup()
            input_type, input_slot = list(input_feeds.items())[0]
            if not isinstance(configuration, (list, tuple)): configuration = (configuration,)
            for TaskClass in configuration:
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
                    found = False
                    for key in dir(TaskClass):
                        if key.startswith('out_'):
                            found = True
                    if not found:
                        raise AutoSetupError("No output slots found on " + TaskClass.__name__)
                    else:
                        return task
            raise AutoSetupError("No matching input slots found for the specified task (looking for " + input_type + " on " + TaskClass.__name__ + ")")
        else:
            raise NotImplementedError("Override the setup() or autosetup() method for your workflow component " + self.__class__.__name__)

    def setup_input(self, workflow):
        #Can we handle the input directly?
        accepts = self.accepts()
        if not isinstance(accepts, (tuple, list)):
            accepts = (accepts,)
        for inputtuple in itertools.chain(accepts, self.accepted_components):
            input_feeds = {} #reset
            if not isinstance(inputtuple, tuple): inputtuple = (inputtuple,)
            for input in inputtuple: #pylint: disable=redefined-builtin
                if isinstance(input, InputFormat):
                    if (self.startcomponent and self.startcomponent != self.__class__.__name__):
                        break
                    if input.valid and (not self.inputslot or self.inputslot == input.format_id):
                        input_feeds[input.format_id] = input.task(workflow).out_default
                        #print("UPDATED INPUT_FEEDS (a)", len(input_feeds), repr(input_feeds),file=sys.stderr)
                        continue
                    else:
                        #print("BREAKING INPUT_FEEDS (a)",file=sys.stderr)
                        break
                elif isinstance(input, InputComponent):
                    swf = input.Class(*input.args, **input.kwargs)
                elif inspect.isclass(input) and issubclass(input, WorkflowComponent):
                    #not encapsulated in InputWorkflow yet, do now
                    iwf = InputComponent(self, input)
                    swf = iwf.Class(*input.args, **input.kwargs)
                else:
                    raise TypeError("Invalid element in accepts(), must be Inputformat or InputComponent, got " + str(repr(input)))

                try:
                    new_input_feeds = swf.setup_input(workflow)
                    inputtasks = swf.setup(workflow, new_input_feeds)
                    #print("SUBWORKFLOW INPUT_FEEDS (b)",len(new_input_feeds), repr(new_input_feeds),file=sys.stderr)
                except InvalidInput:
                    #print("SUBWORKFLOW INVALID INPUT (b)", file=sys.stderr)
                    break

                if isinstance(inputtasks, Task): inputtasks = (inputtasks,)
                for inputtask in inputtasks:
                    if not isinstance(inputtask, Task):
                        raise TypeError("setup() did not return a Task or a sequence of Tasks")
                    for attrname in dir(inputtask):
                        if attrname[:4] == 'out_':
                            format_id = attrname[4:]
                            if format_id in input_feeds:
                                if isinstance(input_feeds[format_id], list):
                                    input_feeds[format_id] += [getattr(inputtask, attrname)]
                                else:
                                    input_feeds[format_id] = [input_feeds[format_id], getattr(inputtask, attrname)]
                            else:
                                input_feeds[format_id] = getattr(inputtask, attrname)

                #print("UPDATED INPUT_FEEDS (c)",len(input_feeds), repr(input_feeds),file=sys.stderr)

            if len(input_feeds) > 0:
                #print("RETURNING INPUT_FEEDS (d)",len(input_feeds), repr(input_feeds),file=sys.stderr)
                return input_feeds

        #input was not handled, raise error
        raise InvalidInput("Unable to find an entry point for supplied input")

    def workflow(self):
        input_feeds = self.setup_input(self)
        output_task = self.setup(self, input_feeds)
        if output_task is None or not (isinstance(output_task, Task) or (isinstance(output_task, (list,tuple)) and all([isinstance(output_task, Task) for t in output_task]))):
            raise ValueError("Workflow setup() did not return a valid last task (or sequence of tasks), got " + str(type(output_task)))
        return output_task

    def new_task(self, instance_name, cls, **kwargs):
        #automatically inherit parameters
        if 'autopass' in kwargs and kwargs['autopass']:
            for key in dir(cls):
                if key not in ('instance_name', 'workflow_task'):
                    attr = getattr(cls, key)
                    if isinstance(attr,luigi.Parameter) and key not in kwargs and hasattr(self,key):
                        kwargs[key] = getattr(self,key)
            del kwargs['autopass']
        return super().new_task(instance_name, cls, **kwargs)

class Task(sciluigi.Task):
    def setup_output_dir(self, d):
        #Make output directory
        if os.path.exists(d):
            pass
        elif os.path.exists(d + '.failed'):
            os.rename(d +'.failed',d)
        else:
            os.mkdir(d)
        self.__output_dir = d

    def on_failure(self, exception):
        try:
            if self.__output_dir and os.path.exists(self.__output_dir):
                os.rename(self.__output_dir, self.__output_dir + '.failed')
        except AttributeError:
            pass

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
        if '__stdin_from' in kwargs:
            cmd += ' < ' + shellsafe(kwargs['__stdin_from'])
        if '__stdout_to' in kwargs:
            cmd += ' > ' + shellsafe(kwargs['__stdout_to'])
        if '__stderr_to' in kwargs:
            cmd += ' 2> ' + shellsafe(kwargs['__stderr_to'])
        super(Task, self).ex(cmd)

    @classmethod
    def inherit_parameters(Class, *ChildClasses):
        for ChildClass in ChildClasses:
            for key in dir(ChildClass):
                if key not in ('instance_name', 'workflow_task'):
                    attr = getattr(ChildClass, key)
                    if isinstance(attr,luigi.Parameter) and not hasattr(Class, key):
                        setattr(Class,key, attr)

    def outputfrominput(self, inputformat, inputextension, outputextension, outputdirparam='outputdir'):
        """Derives the output filename from the input filename, removing the input extension and adding the output extension. Supports outputdir parameter."""

        if not hasattr(self,'in_' + inputformat):
            raise ValueError("Specified inputslot for " + inputformat + " does not exist in " + self.__class__.__name__)
        inputslot = getattr(self, 'in_' + inputformat)

        try:
            inputfilename = inputslot().path
        except (AttributeError, TypeError):
            raise ValueError("Inputslot in_" + inputformat + " of " + self.__class__.__name__ + " is not connected to any output slot!")

        if hasattr(self,outputdirparam):
            outputdir = getattr(self,outputdirparam)
            if outputdir and outputdir != '.':
                return TargetInfo(self, os.path.join(outputdir, os.path.basename(replaceextension(inputfilename, inputextension,outputextension))))
        return TargetInfo(self, replaceextension(inputfilename, inputextension,outputextension))


class StandardWorkflowComponent(WorkflowComponent):
    """A workflow component that takes one inputfile"""

    inputfile = luigi.Parameter()

class TargetInfo(sciluigi.TargetInfo):
    pass


def getcomponentclass(classname):
    for Class in COMPONENTS:
        if Class.__name__ == classname:
            return Class
    raise Exception("No such component: " + classname)

class ComponentParameters(dict):
    def __init__(self, **kwargs):
        super().__init__()
        self.update(kwargs)

    def __hash__(self):
        return hash(tuple(sorted(self.items())))

class Parallel(sciluigi.WorkflowTask):
    """Meta workflow"""
    inputfiles = luigi.Parameter()
    component = luigi.Parameter()
    component_parameters = luigi.Parameter(default=ComponentParameters())

    def workflow(self):
        tasks = []
        ComponentClass = getcomponentclass(self.component)
        for inputfile in self.inputfiles.split(','):
            tasks.append( self.new_task(self.component, ComponentClass, inputfile=inputfile,**self.component_parameters) )
        return tasks

class ParallelFromDir(sciluigi.WorkflowTask):
    """Meta Workflow"""
    directory = luigi.Parameter()
    pattern = luigi.Parameter(default="*")
    component = luigi.Parameter()
    component_parameters = luigi.Parameter(default=ComponentParameters())

    def workflow(self):
        tasks = []
        ComponentClass = getcomponentclass(self.component)
        for inputfile in glob.glob(os.path.join(self.directory, self.pattern)):
            tasks.append( self.new_task(self.component, ComponentClass, inputfile=inputfile,**self.component_parameters) )
        return tasks

def run(*args, **kwargs):
    log.info("Starting workflow run")
    if 'local_scheduler' in kwargs:
        if not args:
            luigi.run(**kwargs)
        else:
            success = luigi.build(args,**kwargs)
            if not success:
                log.error("There were errors in scheduling the workflow")
                raise SchedulingError("There were errors in scheduling the workflow")
            else:
                log.info("Workflow run completed")
    else:
        if not args:
            luigi.run(local_scheduler=True,**kwargs)
        else:
            success = luigi.build(args,local_scheduler=True,**kwargs)
            if not success:
                log.error("There were errors in scheduling the workflow")
                raise SchedulingError("There were errors in scheduling the workflow")
            else:
                log.info("Workflow run completed")

def run_cmdline(TaskClass,**kwargs):
    if 'local_scheduler' in kwargs:
        local_scheduler = kwargs['local_scheduler']
    else:
        local_scheduler=True
    if 'module' in kwargs:
        importlib.import_module(kwargs['module'])
        del kwargs['module']
    cmdline_args = []
    for key, value in kwargs.items():
        if inspect.isclass(value):
            value = value.__name__
        cmdline_args.append('--' + key + ' ' + str(shellsafe(value)))
    kwargs = {}
    if local_scheduler:
        kwargs['local_scheduler'] = True
    luigi.run(main_task_cls=TaskClass,cmdline_args=' '.join(cmdline_args), **kwargs)




