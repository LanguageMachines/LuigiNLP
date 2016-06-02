import os
import logging
import glob
import natsort
from luigi import Parameter, BoolParameter, IntParameter
from luiginlp.engine import Task, TargetInfo, InputFormat, WorkflowComponent, registercomponent
from luiginlp.util import replaceextension, DirectoryHandler
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
        return TargetInfo(self, replaceextension(self.in_train().path, '.train','.ibase'))

    def out_wgt(self):
        return TargetInfo(self, replaceextension(self.in_train().path, '.train','.wgt'))

    def out_log(self):
        return TargetInfo(self, replaceextension(self.in_train().path, '.train','.train.log'))


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
            __stdout_to=self.out_log().path
        )

class Timbl_test(Timbl_base):
    in_ibase = None #input slot
    in_wgt = None
    in_test = None

    def out_timbl(self):
        return TargetInfo(self, replaceextension(self.in_test().path, '.test','.timbl.out'))

    def out_log(self):
        return TargetInfo(self, replaceextension(self.in_test().path, '.test','.test.log'))

    def run(self):
        self.ex(
            i=self.in_base().path,
            w=self.in_wgt().path + ':' + self.weighting,
            o=self.out_timbl().path,
            a=self.algorithm,
            k=self.k,
            m=self.metric,
            d=self.distance,
            __stdout_to=self.out_log().path
        )


class Timbl_crossvalidate(Timbl_base):
    in_ibase = None #input slot
    in_wgt = None

    leaveoneout = BoolParameter(default=False)

    def out_log(self):
        return TargetInfo(self, replaceextension(self.in_ibase().path, '.ibase','.crossvalidation.log'))

    def run(self):
        self.ex(
            i=self.in_base().path,
            t="leave_one_out" if self.leaveoneout else "cross_validate"
            a=self.algorithm,
            k=self.k,
            m=self.metric,
            w=self.in_wgt().path + ':' + self.weighting,
            d=self.distance,
            __stdout_to=self.out_log().path
        )

@registercomponent
class TimblClassifier(WorkflowComponent):
    """A Timbl classifier that takes training data, test data, and outputs the test data with classification"""

    def accepts(self):
        return (
            InputFormat(self, format_id='train', extension='train'),
            InputFormat(self, format_id='test', extension='test'),
        )

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
class TimblCVClassifier(WorkflowComponent):
    """A Timbl classifier that performs cross-validation (or leave one out)"""

    def accepts(self):
        return (
            InputFormat(self, format_id='train', extension='train'),
            InputFormat(self, format_id='test', extension='test'),
        )

    def setup(self, workflow, input_feeds):
        timbl_train = workflow.new_task('timbl_train',Timbl_train, autopass=True)
        timbl_train.in_train = input_feeds['train']

        timbl_cv = workflow.new_task('timbl_cv',Timbl_crossvalidate, autopass=True)
        timbl_cv.in_ibase = timbl_train.out_ibase
        timbl_cv.in_wgt = timbl_train.out_wgt

        return timbl_cv

TimblCVClassifier.inherit_parameters(Timbl_train)
TimblCVClassifier.inherit_parameters(Timbl_crossvalidate)


