import sys
import os
import logging
import glob
import natsort
from luigi import Parameter, BoolParameter, IntParameter
from luiginlp.engine import Task, InputFormat, WorkflowComponent, StandardWorkflowComponent, registercomponent
from luiginlp.modules.openconvert import OpenConvert_folia

log = logging.getLogger('mainlog')

class Timbl_base(Task):
    executable = 'timbl'

    algorithm = Parameter(default="IB1")
    metric = Parameter(default="O")
    weighting = Parameter(default="gr")
    distance = Parameter(default="Z")
    format = Parameter(default="Columns")
    k = IntParameter(default=1)


class Timbl_train(Timbl_base):
    in_train = None #input slot

    def out_ibase(self):
        return self.outputfrominput(inputformat='train',inputextension='.train',outputextension='.ibase')

    def out_wgt(self):
        return self.outputfrominput(inputformat='train',inputextension='.train',outputextension='.wgt')

    def out_log(self):
        return self.outputfrominput(inputformat='train',inputextension='.train',outputextension='.timbl.train.log')

    def run(self):
        self.ex(
            f=self.in_train().path,
            I=self.out_ibase().path,
            W=self.out_wgt().path,
            a=self.algorithm,
            k=self.k,
            m=self.metric,
            w=self.weighting,
            d=self.distance,
            __stdout_to=self.out_log().path)

class Timbl_test(Timbl_base):
    in_ibase = None #input slot
    in_wgt = None
    in_test = None

    def out_timbl(self):
        return self.outputfrominput(inputformat='test',inputextension='.test',outputextension='.timbl.out')

    def out_log(self):
        return self.outputfrominput(inputformat='test',inputextension='.test',outputextension='.timbl.test.log')

    def run(self):
        self.ex(
            i=self.in_ibase().path,
            t=self.in_test().path,
            w=self.in_wgt().path + ':' + self.weighting,
            o=self.out_timbl().path,
            a=self.algorithm,
            k=self.k,
            m=self.metric,
            d=self.distance,
            __stdout_to=self.out_log().path)


class Timbl_leaveoneout(Timbl_base):
    in_train = None

    leaveoneout = BoolParameter(default=False)

    def out_log(self):
        return self.outputfrominput(inputformat='train',inputextension='.train',outputextension='.timbl.leaveoneout.log')

    def run(self):
        self.ex(
            f=self.in_train().path,
            t="leave_one_out",
            a=self.algorithm,
            k=self.k,
            m=self.metric,
            w=self.weighting,
            d=self.distance,
            __stdout_to=self.out_log().path)

@registercomponent
class TimblClassifier(WorkflowComponent):
    """A Timbl classifier that takes training data, test data, and outputs the test data with classification"""

    trainfile = Parameter()
    testfile = Parameter()

    def accepts(self):
        #Note: tuple in a list, the outer list corresponds to options, while the inner tuples are conjunctions
        return [ ( InputFormat(self, format_id='train', extension='train',inputparameter='trainfile'), InputFormat(self, format_id='test', extension='test',inputparameter='testfile')) ]

    def setup(self, workflow, input_feeds):
        timbl_train = workflow.new_task('timbl_train',Timbl_train, autopass=True)
        timbl_train.in_train = input_feeds['train']

        timbl_test = workflow.new_task('timbl_test',Timbl_test, autopass=True)
        timbl_test.in_test = input_feeds['test']
        timbl_test.in_ibase = timbl_train.out_ibase
        timbl_test.in_wgt = timbl_train.out_wgt

        return timbl_test

TimblClassifier.inherit_parameters(Timbl_train)
TimblClassifier.inherit_parameters(Timbl_test)


@registercomponent
class TimblLOOClassifier(StandardWorkflowComponent):
    """A Timbl classifier that performs cross-validation (or leave one out) on the training data"""

    def accepts(self):
        return InputFormat(self, format_id='train', extension='train')

    def autosetup(self):
        return Timbl_leaveoneout

TimblLOOClassifier.inherit_parameters(Timbl_leaveoneout)



