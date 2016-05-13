import sciluigi
import logging
from piccl.util import shellsafe

log = logging.getLogger('mainlog')

class WorkflowTask(sciluigi.WorkflowTask):
    def initial_task(self, inputfilename, extension2inputtask, **kwargs):
        if 'id' in kwargs:
            initialtask_id = kwargs['id']
            del kwargs['id']
        else:
            initialtask_id = 'initialinput'
        Inputclass = None
        for extension, inputclass in extension2inputtask.items():
            if inputfilename.endswith(extension):
                basename  = self.inputfilename[:-len(extension)]
                Inputclass = inputclass
        if Inputclass is not None:
            return self.new_task(initialtask_id, Inputclass, basename), Inputclass
        else:
            raise Exception("Input file does not match any known pattern for this workflow")

class Task(sciluigi.Task):
    def ex(self, *args, **kwargs):
        if hasattr(self,'executable'):
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
            else:
                opts.append(key + ' ' + shellsafe(value))
        if opts:
            cmd += ' ' + ' '.join(opts)
        if args:
            cmd += ' ' + ' '.join(args)
        log.info("Running " + self.__class__.__name__ + ': ' + cmd)
        super(Task, self).ex(cmd)

class TargetInfo(sciluigi.TargetInfo):
    pass
