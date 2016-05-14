import luigi
import sciluigi
import logging
from piccl.util import shellsafe

log = logging.getLogger('mainlog')

class InitialInput:
    def __init__(self, inputfilename, *inputmaps):
        self.filename = inputfilename
        self.inputmaps= inputmaps

        self.type = None
        self.basename = self.extension = ""
        for inputmap in inputmaps:
            for extension, inputclass in inputmap.items():
                if inputfilename.endswith(extension):
                    self.type = inputclass
                    self.basename = inputfilename[:-len(extension)]
                    self.extension = extension

class WorkflowTask(sciluigi.WorkflowTask):
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
