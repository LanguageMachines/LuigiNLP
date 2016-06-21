.. image:: http://applejack.science.ru.nl/lamabadge.php/LuigiNLP
   :target: http://applejack.science.ru.nl/languagemachines/

*************
LuigiNLP
*************

An NLP workflow system building upon
**sciluigi** (https://github.com/pharmbio/sciluigi), which is in turn based on
**luigi** (https://github.com/spotify/luigi).

This started out as a proof of concept intended to be used for the PICCL and
Quoll NLP pipelines developed at Radboud University Nijmegen.

This is a solution for either a single computing node or a cluster of nodes
(Hadoop, SLURM, not tested yet). The individual components are not webservices,
nor is data passed around. This ensures minimal overhead and higher performance.

=========
Goals
=========

* Abstraction of workflow/pipeline logic: a generic, scalable and adaptable solution
* Modularisation; clear separation of all components from the workflow system itself
* Automatic dependency resolution (similar to GNU Make, top-down)
* Robust failure recovery: when failures occur, fix the problem and run the workflow again, tasks that have completed will not be rerun.
* Easy to extend with new modules (i.e. workflow components & tasks).
* Traceability of all intermediate steps, retain intermediate results until explicitly discarded
* Explicit workflow definitions 
* Automatic parallellisation of tasks where possible
* Keep it simple, minimize overhead for the developer of the workflow, use Pythonic principles,
* Python-based, all workflow and component specifications are in Python rather than external.
* Protection against shell injection attacks for tasks that invoke external tools
* Runnable standalone from command-line 

==============
Architecture
==============

LuigiNLP follows a **goal-oriented** paradigm. The user invokes the workflow
system by specifying a target **workflow component** along with an initial
input file. Given the target and an initial input file, a sequence of workflow
components will be automatically found that leads from initial input to the
desired goal, processing the data each step of the way. Workflow components are
defined in a *backwards* manner, as is also common in tools such as GNU Make.
Each component expresses which other components it **accepts** as input, or
which input files it accepts directly. This enables you to run the
component either directly on an input file, or have the input go through other
components first for necessary preprocessing. The dependency resolution
mechanism will automatically chose a path based on the specified input and
selected parameters.

A workflow component consists of a specification that chains together
**tasks**. Whereas a workflow component represents a more comprehensive piece
of work that is defined in a context of other components, a **task** represents
the smallest unit of work and is defined **independently** of any other tasks
or components, making it a highly reusable part. A task consists of one or more
input slots, corresponding to input files of a particular type, one or more
output slots corresponding to output files of a particular type, and
parameters. A workflow component only glues together different tasks, the task
performs an actual job, either by invoking an external tool, or by running
Python code directly. Chaining together tasks in the definition of the
workflow component is done by connecting output slots of one task, to input
slots of the other. 

The architecture is visualised in the following scheme:

.. image:: https://raw.githubusercontent.com/LanguageMachines/LuigiNLP/master/architecture.png
    :alt: LuigiNLP Architecture
    :align: center

Tasks and workflow components may take **parameters**. These are available
within a task's ``run()`` method to either be propagated to an external tool
or to be handled within Python directly. At the component level, parameters may also be used to influence
task composition, though often they are just passed on to the tasks. 

The simplest instance of a workflow component is just one that accepts one
particular type of input file and sets up just a single task. 

Both tasks and workflow components are defined in a **module** (in the Python
sense of the word), which simply groups several tasks and workflow components together.

LuigiNLP relies heavily on filename extensions. Input formats are matched on
the basis of an extension, and generally each task reads a file and outputs
a file with a new extension. Re-use of the same filename (i.e. writing output to the
input file), is **strictly forbidden**! 

It is important to understand that the actual input files are only open for
inspection when a Task is executed (its ``run()`` method is invoked).  During
workflow composition in a component (in its ``setup()/autosetup()`` method),  files can not
be inspected as the composition by definition preceeds the existence of any
files, and the whole process has to proceed deterministically.

=============
Limitations
=============

* No circular dependencies allowed in workflow components
* Intermediate files are not open for inspection in workflow specifications, only within ``Task.run()``

====================
Directory Structure
====================

 * ``luiginlp/luiginlp.py`` - Main tool
 * ``luiginlp/modules/`` - Modules, each addressing a specific tool/goal. A module
   consists of workflow components and tasks.
 * ``luiginlp/util.py`` - Auxiliary functions
 * ``setup.py`` - Installation script for LuigiNLP (only covers LuigiNLP and its direct python dependencies)
 * ``bootstrap.sh`` - Full installation script, pulls in all necessary dependencies and runs ``setup.py``, to be invoked by or from within **LaMachine** (https://github.com/proycon/LaMachine)

==============
Installation
==============

Install as follows:

    $ python setup.py install

(If this fails due to a ``python-daemon`` error, just run it again. There is a
problem in that package)

Many of the implemented modules rely on software distributed as part of
LaMachine (https://proycon.github.io/LaMachine), so LuigiNLP is best used from
within a LaMachine installation. LuigiNLP itself is included in LaMachine as
well.

===========
Usage
===========

Example, specify a workflow corresponding to your intended goal and an input file. Workflows may take extra parameters (``--skip`` for Frog in this case)::

    $ luiginlp Frog --module luiginlp.modules.frog --inputfile test.rst --skip p

A workflow can be run parallelised for multiple input files as well, the number
of workers should be explicitly set::

    $ luiginlp Parallel --module luiginlp.modules.frog --component Frog --inputfiles test.rst,test2.rst --workers 2 --skip p

You can always pass component-specific parameters by using the component name
as a prefix. For instance, the Frog component takes an option ``skip``, you can
use ``--Frog-skip`` to explicitly set it.

You can also invoke LuigiNLP from within Python of course:

.. code-block:: python

    import luiginlp
    from luiginlp.modules.frog import Frog
    luiginlp.run(Frog(inputfile="test.rst",skip='p'))

To parallelize multiple tasks you can just do:

.. code-block:: python

    import luiginlp
    from luiginlp.modules.frog import Frog
    luiginlp.run(
        Frog(inputfile="test.rst",skip='p'),
        Frog(inputfile="test2.rst",skip='p'))
        
Or use the ``Parallel`` interface:

.. code-block:: python

    import luiginlp
    from luiginlp.modules.frog import Frog
    from luiginlp.engine import Parallel, ComponentParameters
    luiginlp.run(
        Parallel(component="Frog",inputfiles="test.rst,test2.rst",
            component_parameters=ComponentParameters(skip='p')
        )
    )


Here's an example of running an OCR workflow for a scanned PDF file (requires the tools ``pdfimages``, 
``Tesseract``, ``FoLiA-hocr`` and ``foliacat``, the latter two are a part of LaMachine)::

    $ luiginlp --module luiginlp.modules.ocr OCR_folia --inputfile OllevierGeets.pdf --language eng

LuigiNLP automatically finds a sequence of components leading from your input
file (provided it's name matches whatever convention you use) to the target
component. You may, however, force an inputfile by setting the ``--inputslot``
parameter to some input format ID. This can be useful if you want to feed an
input file that does not comply to your naming convention. 
You may also specify a ``--startcomponent`` to explicitly state which component
should be the first one, this may be useful in cases of ambiguity where
multiple paths are possible (the first possibility would be otherwise be chosen).

Writing tasks and components for LuigiNLP
=============================================

In order to plug in your own tools into LuigiNLP, you will need to do
several things:

* Create a new module that groups your code (inside LuigiNLP these reside in ``luiginlp/modules/*.py``, but you may just as well have a module in an external Python project)
* Write one or more tasks, tasks are classes derived from ``luiginlp.engine.Task``
* Write one or more workflow components that chain tasks together, workflow components are classes derived from ``luiginlp.engine.WorkflowComponent``, you usually want to derive from ``luiginlp.engine.StandardWorkflowComponent`` which is a standard component that takes one inputfile as parameter.

Let's begin by writing a simple task that invokes the tokeniser
*ucto* (https://languagemachines.github.io/ucto) to convert plain text to
tokenised plain text. We prescribe that the plain text document has the
extension ``txt`` and tokenised text has the extension ``tok``. The tokeniser
takes one mandatory parameter: the language the text is in.

.. code-block:: python
    from luiginlp.engine import Task
    from luigi import Parameter

    class Ucto_txt2tok(Task):
        #This task invokes an external tool (ucto), set the executable to invoke
        executable = 'ucto' 

        #Parameters for this task
        language = Parameter()

        #this is the input slot for plaintext files, input slots are always set
        #to None and are connected to output slots of other tasks by a workflow
        #component
        in_txt = None 

        #Define an output slot, output slots are methods that start with out_
        def out_tok(self): 
            #Output slots should call outputforminput() to automatically derive the output file
            #from the input file, typically by removing the input extension and
            #adding a new *and distinct* output extension. The inputformat
            #parameter must correspond to an input slot (in_txt in this case).
            #If an outputdir parameter is defined in the task, it is automatically
            #supported.
            return self.outputfrominput(inputformat='txt',inputextension='.txt',outputextension='.tok')

        #Define the run method, this will be called to do the actual work
        def run(self):
            #Here we run the external tool. This will invoke the executable
            #specified. Keyword arguments are passed as option flags (-L in
            #this case). Positional arguments are passed as such (after option flags).
            #All parameters are available on the Task instance
            #Values will be passed in a shell-safe manner, protecting against injection attacks
            self.ex(self.in_txt().path, self.out_tok().path,
                    L=self.language,
            )

We can now turn this task into a simple component that we can invoke:

.. code-block:: python
    from luiginlp.engine import StandardWorkflowComponent, InputFormat

    class Ucto(StandardWorkflowComponent):
        #parameters for the task, most are just passed on to the task(s)
        language = Parameter()

        #The accepts methods return what input formats or other input components are accepted as input. It may return multiple values (in a tuple/list), the one that matches with the specified input is chosen
        def accepts(self):
            return InputFormat(self, format_id='txt',extension='txt')

        #Autosetup constructs a workflow for you automatically based on the tasks you specify. If you specify a tuple of multiple tasks, the one fitting the input will be executed.
        def autosetup(self):
            return Ucto_txt2tok

Assuming you wrote all this in a ``mymodule.py`` file, you now can invoke this
workflow component on a text document as follows::

    $ luiginlp Ucto --module mymodule --inputfile test.txt --language en

Ucto does not just support plain text input, it can also handle input in the
*FoLiA* format (https://proycon.github.io/folia), an XML-based format for linguistic
annotation. We could write a task ``Ucto_folia2tok`` that runs ucto in this
manner. Suppose we did that, we could extend our workflow component as
follows:

.. code-block:: python

    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt'), InputFormat(self, format_id='folia', extension='folia.xml')

    def autosetup(self):
        return Ucto_txt2tok, Ucto_folia2tok

Now the workflow component will be able automatically figure out which of the tasks to run based on the supplied input, allowing us to do::

    $ luiginlp Ucto --module mymodule --inputfile test.folia.xml --language en

What about any other file format? Ucto itself can only handle plain text or
FoLiA. What if our input text is in PDF format, MarkDown format, or God forbid,
in MS Word format? We could solve this problem by writing a
``ConvertToPlaintext`` component that handles a multitude of formats and simply
instructs ucto to accept the plaintext output from that component. We need some extra imports
and would then modify the ``accepts()`` to tie in the component: 

.. code-block:: python

    from luiginlp.engine import InputComponent
    from some.other.module import ConvertToPlaintext

.. code-block:: python

    def accepts(self):
        return (
            InputFormat(self, format_id='txt',extension='txt'),
            InputFormat(self, format_id='folia', extension='folia.xml'), 
            InputComponent(self, ConvertToPlaintext) #you can pass parameters using keyword arguments here
        )

Our ucto component thus-far has been fairly simple, we first used ``autosetup()`` to
wrap a single task, and later to choose amongst two tasks. Let's look at a more
explicit example with actual task chaining. 

Suppose we want the Ucto component to lowercase our text before passing it on
to the actual task that invokes ucto. We can write a simple lowercase task as
follows, for this one we just use Python and call no external tools (i.e. we
set no ``executable`` and do not call ``ex()``):

.. code-block:: python
    from luiginlp.engine import Task
    from luigi import Parameter

    class LowercaseText(Task):
        #Parameters for this task
        language = Parameter()
        encoding = Parameter(default='utf-8')

        in_txt = None 

        #Define an output slot, output slots are methods that start with out_
        def out_txt(self): 
            #We add a lowercased prefix to the extension
            #The output file may NEVER be equal to the input file
            return self.outputfrominput(inputformat='txt',inputextension='.txt',outputextension='.lowercased.txt')

        #Define the run method, this will be called to do the actual work
        def run(self):
            #We do the work in Python itself
            #Input and output slots can be opened as file objects
            with self.in_txt().open('r',encoding=self.encoding) as inputfile
                with self.out_txt().open('w',encoding=self.encoding) as outputfile:
                    outputfile.write(inputfile.read().lower())

Now we go back to our Ucto component, we forget about the FoLiA part for a
bit, and we set up explicit chaining using ``setup()`` instead of
``autosetup()``, which is a bit more work but gives us complete control over
everything.


.. code-block:: python
    from luiginlp.engine import StandardWorkflowComponent, InputFormat

    class Ucto(StandardWorkflowComponent):
        #parameters for the task, most are just passed on to the task(s)
        language = Parameter()

        #The accepts methods return what input formats or other input components are accepted as input. It may return multiple values (in a tuple/list), the one that matches with the specified input is chosen
        def accepts(self):
            return (
                InputFormat(self, format_id='txt',extension='txt'),
                InputComponent(self, ConvertToPlaintext) #you can pass parameters using keyword arguments here
            )

        #Setup a workflow chain manually
        def setup(self, workflow, input_feeds):
            #input_feeds will be a dictionary of format_id => output_slot 

            #set up the lower caser and feed the input to it
            lowercaser = workflow.new_task('lowercaser',LowercaseText)
            lowercaser.in_txt = input_feeds['txt']

            #set up ucto and feed the output of the lower caser to it.
            #we explicitly pass any parameters we want to propagate
            #if you instead want to implicitly pass all parameters with matching names
            #between component and task, just set keyword argument autopass=True
            ucto = workflow.new_task('ucto', Ucto_txt2tok, language=self.language) 
            ucto.in_txt = lowercaser.out_txt

            #always return the last task(s)
            return ucto

Dynamic dependencies aka Inception
-----------------------------------

Workflows are static in the sense that based on the format of the input file
and all given parameters, all workflow components and tasks are assembled
deterministically. This means that, within a components ``setup()`` method, it
is not possible to inspect input/intermediate files nor adjust the flow based
on file contents.

At times, however, more dynamic workflows are needed. In such cases, the common
theme is that input data has to be inspected and decisions made accordingly.
The **only** stage at which input files can be inspected is in a task's
``run()`` method. Fortunately, there are facilities here to implement more
dynamic dependencies, a task's ``run()`` method is allowed to **yield** (in the
Python sense of the word) a list of other tasks that it depends on.

A good example would be if we create a new tokenisation component that does not
just take an input file, but takes a **directory** containing input files and
produces a directory of output files. The proper way to implement this is to
reuse the component that performs on the individual files (i.e. our ``Ucto``
component).  Consider the following task and component:

.. code-block:: python

    import glob
    from luiginlp.engine import Task, StandardWorkflowComponent
    from luigi import Parameter

    class Ucto_txtdir2tokdir(Task):
        language = Parameter()

        in_txtdir = None

        def out_tokdir(self):
            return self.outputfrominput(inputformat='txtdir',inputextension='.txtdir',outputextension='.tokdir')
        
        def run(self):
            #setup the output directory
            # this creates the directory and also moved it out of the way again when failures occur in this task
            self.setup_output_dir(self.out_tokdir().path)

            #gather input files
            inputfiles = [ filename for filename in glob.glob(self.in_txtdir().path + '/*.txt' ]

            #inception aka dynamic dependencies: we yield a list of components which could not have been predicted statically
            #in this case we run the Ucto component for each input file in the directory
            yield [ Ucto(inputfile=inputfile,outputdir=self.out_tokdir().path,language=self.language) for inputfile in inputfiles ]


    class Ucto_collection(StandardWorkflowComponent):
        def accepts(self):
            return (
                InputFormat(self, format_id='txtdir',extension='txtdir', directory=True),
            )

        def autosetup(self):
            return Ucto_txtdir2tokdir


The magic happens in the task's ``run()`` method, as that it the only stage
where we can examine the contents of any input files, in this case: the contents
of the input directory. First we set up the output directory with a call to
``self.setup_output_dir()``. This creates the directory if it doesn't exist
yet, but also makes sure the directory is stashed away when the task fails,
ensuring you can always rerun the pipeline if happens to break off. (in
technical terms, this preserves idempotency). 

Mext, we construct a list of all the txt files in the directory. We use this
list to yield a **list** of components to run, one component for each input file.
Now, when the task's ``run()`` method is called, a series of components will be
scheduled and run **in parallel** (up to the number of workers).

You may be tempted to yield the components individually one by one, but that
won't result in parallisation, you must really yield an entire list (or tuple).

Note that we added an ``outputdir`` parameter to the Ucto component which we
hadn't implemented yet. This is necessary to ensure all individual output files
end up in the directory that groups our output. The Ucto component should
simply pass this parameter on to the ``Ucto_txt2tok`` task, and there we
just add it as an optional parameter as follows. The ``outputfrominput()``
method automatically supports this parameter.

.. code-block:: python

    class Ucto_txt2tok(Task):
        outputdir = Parameter(default="")

Assuming you have a collecting of text files in a directory ``corpus.txtdir/``,
you can now invoke LuigiNLP as follows and end up with a ``corpus.tokdir/``
directory with tokenised output texts::

    $ luiginlp Ucto_collection --module mymodule --inputfile corpus.txtdir --language en --workers 4

Note the ``--workers`` parameter, which is the generic way to tell LuigiNLP how
many workers may run in parallel. You will want to explicitly set this to a
value that approximates the number of free CPU cores as the default value is
one (no parallellisation).

-----------------------------
Inheriting parameters
-----------------------------

Components often inherit parameters from the tasks they wrap. When you use
``autosetup()``, parameters with the matching names are automatically passed
from component to task. Similarly, if you use ``workflow.new_task()`` in your
setup method, you can set the keyword argument ``autopass=True`` to also
accomplish this.

Still, you actually need to which parameters on the component.
This can be done in the usual way, but if a task already defines them, you may want to inherit the parameters automatically and prevent any code duplication. This is done as follows:

.. code-block:: python

    class MyComponent(WorkflowComponent):
        ...
    MyComponent.inherit_parameters(MyTask1,MyTask2,MyTask3)

Note that the ``inherit_parameters()`` call is not part of the class definition (not in class scope) but placed after it.

-----------------------------
Multiple inputs 
-----------------------------

Tasks may defined multiple input slots (and multiple output slots). Components
may accept multiple inputs similtaneously as well. Consider for example a
classifier that takes a training file and a test file. Components can not use
``autosetup()`` in this case, but you need to explicitly define a ``setup()``
method.

To define multiple concurrent inputs, group them together in a tuple and return
this as part of a list or tuple from ``accepts()``. The following example
components is for a classifier, it takes two inputs (``trainfile`` and
``testfile``) rather than the standard ``inputfile`` pre-defined in
``StandardWorkflowComponent`` (this class is therefore subclassed from
``WorkflowComponent`` instead, which does not predefine ``inputfile``).

Note furthermore that the ``InputFormat`` tuple contains the ``inputparameter``
keyword argument that binds the proper inputformat to the proper parameter (the
default was ``inputparameter="inputfile"`` so we never needed it before).


.. code-block:: python

    @registercomponent
    class TimblClassifier(WorkflowComponent):
        """A Timbl classifier that takes training data, test data, and outputs the test data with classification"""

        trainfile = Parameter()
        testfile = Parameter()

        def accepts(self):
            #Note: tuple in a list, the outer list corresponds to options (just one here), while the inner tuples are conjunctions
            return [ ( InputFormat(self, format_id='train', extension='train',inputparameter='trainfile'), InputFormat(self, format_id='test', extension='test',inputparameter='testfile')) ]

        def setup(self, workflow, input_feeds):
            timbl_train = workflow.new_task('timbl_train',Timbl_train, autopass=True)
            timbl_train.in_train = input_feeds['train']

            timbl_test = workflow.new_task('timbl_test',Timbl_test, autopass=True)
            timbl_test.in_test = input_feeds['test']
            timbl_test.in_ibase = timbl_train.out_ibase
            timbl_test.in_wgt = timbl_train.out_wgt

            return timbl_test

We have not defined the tasks here, but you can infer that the ``Timbl_train``
task has at least two output slots, and ``Timbl_test`` has two input slots.


==================
Troubleshooting
==================

* *Everything is run sequentially, nothing is parallelised?* -- Did you explicitly
supply a ``workers`` parameter with the desired maximum number of threads? Otherwise just one worker will be used and everything is sequential. If
you did supply multiple workers, it may just  be the case that there is simply nothing to run in parallel
in your invoked workflow.
* *I get no errors but nothing seems to run when I rerun my workflow?* -- If all output files already exist, then the workflow has nothing to do. You will need to explicitly delete your output if you want to rerun things that have already been produced succesfully.
* *error: unrecognized argument* -- You are passing an argument that
  is not known to the target component. Perhaps you forgot to inherit certain
  parameters from tasks to components using ``inherit_parameters()``?
* *RuntimeError: Unfulfilled dependency at run time* -- This error says that the
  specified task or component has not delivered the output files that were
  promised by the output slots. You should ensure all of the promised files are
  delivered and there are no typos in the filenames/extensions.
* *InvalidInput: Unable to find an entry point for supplied input* -- The
  filename you specified can not be matched with one of the input formats. Are
  you supplying the right file and that your target component has a possible
  path to that input (through ``accepts()``). Either make sure it has the expected extension
  so it is automatically detected. You may also explicitly supply an
  ``inputslot`` parameter with the ID of the format, possibly in combination
  with a ``startcomponent`` parameter with the name of the component you want
  to start with. 
* *ValueError: Workflow setup() did not return a valid last task (or sequence of
  tasks)* or *TypeError: setup() did not return a Task or a sequence of Tasks* -- At the end of your component's ``setup()``
  method you must return the last task instance, or a list of the last task
  instances. Is a return statement missing?
* *Exception: Input item is neither callable, TargetInfo, nor list: None*. --
  All ``out_*()`` methods must return a ``TargetInfo`` instance, which is
  usually achieved by returning whatever ``outputfrominput()`` returns. Is a
  return statement missing in an output slot?
* *ValueError: Inputslot .... of ..... is not connected to any output
  slot!* -- You forgot to connect the specified input slot of the specified
  task to an output slot (in a components ``setup()`` method). All input slots must be satisfied.
* *ValueError: Specified inputslot for ... does not exist in ....* -- Your call
  to ``outputfrominput()`` has a ``inputformat`` argument that does not
  correspond to any of the input slots. If you have an input slot ``in_x``, the
  inputformat should be ``x``.
* *Exception: No executable defined for .....* -- You are invoking the ``ex()``
  method to execute through the shell but the Task's class does not specify an
  executable to run. Set ``executable = "yourexecutable"`` in the class.
* *TypeError: Invalid element in accepts(), must be InputFormat or
InputComponent* -- Your component's accepts() method returns something it
 shouldn't, you may return a list/tuple of InputFormat or InputComponent
 instances, you may also includes tuples grouping multiple InputFormats or
 InputComponents in case the component takes multiple input files.
* *AutoSetupError: AutoSetup expected a Task class* -- Your components ``autosetup()`` method must return either a single Task class (not an instance) or a list/tuple of Task classes.
* *AutoSetupError: No outputslot found on ....* -- The task you are returning in a component's ``autosetup()`` method has no output slots (one or more ``out_*()`` methods).
* *AutoSetupError: AutoSetup only works for single input/output tasks now* -- You can not use ``autosetup()`` for components that take multiple input files, use ``setup()`` instead.
* *AutoSetupError: No matching input slots found for the specified task*  -- Autosetup was not able to automatically connect any of the supplied input formats or input components (those in ``accept()``) to one of the tasks defined in ``autosetup()``, there is probably a mismatch between format names (outputslot using a different format id than the inputslot). Use the ``setup()`` method instead of ``autosetup()`` and connect everything explicitly there.
* *NotImplementedError: Override the setup() or autosetup() method for your workflow component* -- Each component must define a ``setup()`` or ``autosetup()`` method, it is missing here.


============
Plans/TODO
============

* Expand autosetup to build longer sequential chains of tasks (a2b b2c c2d)
* [tentative] Integration with `CLAM <https://github.com/proycon/clam>`_ to automatically
  create webservices of workflow components
* Further testing...
