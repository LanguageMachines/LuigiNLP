import sciluigi

class WorkflowTask(sciluigi.WorkflowTask):
    def initial_task(self, inputfilename, extension2inputclass, **kwargs):
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
