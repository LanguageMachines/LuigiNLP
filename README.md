LuigiNLP (proof of concept)
================================

An NLP workflow system building upon
[sciluigi](https://github.com/pharmbio/sciluigi), which is in turn based on
[luigi](https://github.com/spotify/luigi).

Proof of concept to be used for the PICCL and Quoll NLP pipelines.

This is a solution for either a single computing node or a cluster of nodes
(Hadoop, SLURM, not tested yet). The individual components are not webservices,
nor is data passed around. This ensures minimal overhead and higher performance.

Goals
---------

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

Architecture
----------------

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

![LuigiNLP Architecture](https://raw.githubusercontent.com/LanguageMachines/LuigiNLP/master/architecture.png)

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

Limitations
------------

* No circular dependencies allowed in workflow components
* Intermediate files are not open for inspection in workflow specifications, only within ``Task.run()``

Directory Structure
---------------------

 * ``luiginlp/luiginlp.py`` - Main tool
 * ``luiginlp/modules/`` - Modules, each addressing a specific tool/goal. A module
   consists of workflow components and tasks.
 * ``luiginlp/util.py`` - Auxiliary functions
 * ``setup.py`` - Installation script for LuigiNLP (only covers LuigiNLP and its direct python dependencies)
 * ``bootstrap.sh`` - Full installation script, pulls in all necessary dependencies and runs ``setup.py``, to be invoked by or from within [LaMachine](https://github.com/proycon/LaMachine)

Installation
---------------

Install as follows:

    $ python setup.py install

Many of the implemented modules rely on software distributed as part of
[LaMachine](https://proycon.github.io/LaMachine), so LuigiNLP is best used from
within a LaMachine installation. LuigiNLP itself will be included in LaMachine
when it is mature enough.

Usage
---------

Example, specify a workflow corresponding to your intended goal and an input file. Workflows may take extra parameters (``--skip`` for Frog in this case):

    $ luiginlp --module luiginlp.modules.frog Frog --inputfile test.rst --skip p

A workflow can be run parallelised for multiple input files as well, the number
of workers can be explicitly set:

    $ luiginlp --module luiginlp.modules.frog Parallel --component Frog --inputfiles test.rst,test2.rst --workers 2 --skip p

You can always pass component-specific parameters by using the component name
as a prefix. For instance, the Frog component takes an option ``skip``, you can
use ``--Frog-skip`` to explicitly set it.

You can also invoke LuigiNLP from within Python of course:

```python
import luiginlp
from luiginlp.modules.frog import Frog
luiginlp.run(Frog(inputfile="test.rst",skip='p'))
```

To parallelize multiple tasks you can just do:

```python
import luiginlp
from luiginlp.modules.frog import Frog
luiginlp.run(
    Frog(inputfile="test.rst",skip='p'),
    Frog(inputfile="test2.rst",skip='p'),
)
```
        
Or use the ``Parallel`` interface:

```python
import luiginlp
from luiginlp.modules.frog import Frog
from luiginlp.engine import Parallel, ComponentParameters
luiginlp.run(
    Parallel(component="Frog",inputfiles="test.rst,test2.rst",
        component_parameters=ComponentParameters(skip='p')
    )
)
```


Here's an example of running an OCR workflow for a scanned PDF file (requires the tools ``pdfimages`` and
``Tesseract``):

    $ luiginlp --module luiginlp.modules.ocr OCR_document --inputfile OllevierGeets.pdf --language eng

Writing tasks and components for LuigiNLP
=============================================

In order to plug in your own tools into LuigiNLP, you will need to do
several things:

* Create a new module that groups your code (inside LuigiNLP these reside in ``luiginlp/modules/*.py``, but you may just as well have a module in an external Python project)
* Write one or more tasks, tasks are classes derived from ``luiginlp.engine.Task``
* Write one or more workflow components that chain tasks together, workflow components are classes derived from ``luiginlp.engine.WorkflowComponent``

Let's begin by writing a simple task that invokes the tokeniser
[ucto](https://languagemachines.github.io/ucto) to convert plain text to
tokenised plain text. We prescribe that the plain text document has the
extension ``txt`` and tokenised text has the extension ``tok``. The tokeniser
takes one mandatory parameter: the language the text is in.

```python
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
        #Output slots always return TargetInfo instances pointing to the
        #output file, we derive the name of the output file from the input
        #file, and replace the extension
        return TargetInfo(self, replaceextension(self.in_txt().path, '.txt','.tok')) 

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
```

We can now turn this task into a simple component that we can invoke:

```python
from luiginlp.engine import WorkflowComponent, InputFormat

class Ucto(WorkflowComponent):
    #parameters for the task, most are just passed on to the task(s)
    language = Parameter()

    #The accepts methods return what input formats or other input components are accepted as input. It may return multiple values (in a tuple/list), the one that matches with the specified input is chosen
    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt')

    #Autosetup constructs a workflow for you automatically based on the tasks you specify. If you specify a tuple of multiple tasks, the one fitting the input will be executed.
    def autosetup(self):
        return Ucto_txt2tok
```

Assuming you wrote all this in a ``mymodule.py`` file, you now can invoke this
workflow component on a text document as follows:

    $ luiginlp --module mymodule Ucto --inputfile test.txt --language en

Ucto does not just support plain text input, it can also handle input in the
[FoLiA](https://proycon.github.io/folia) format, an XML-based format for linguistic
annotation. We could write a task ``Ucto_folia2tok`` that runs ucto in this
manner. Suppose we did that, we could extend our workflow component as
follows:

```python
    def accepts(self):
        return InputFormat(self, format_id='txt',extension='txt'), InputFormat(self, format_id='folia', extension='folia.xml')

    def autosetup(self):
        return Ucto_txt2tok, Ucto_folia2tok
```

Now the workflow component will be able automatically figure out which of the tasks to run based on the supplied input, allowing us to do:

    $ luiginlp --module mymodule Ucto --inputfile test.folia.xml --language en

What about any other file format? Ucto itself can only handle plain text or
FoLiA. What if our input text is in PDF format, MarkDown format, or God forbid,
in MS Word format? We could solve this problem by writing a
``ConvertToPlaintext`` component that handles a multitude of formats and simply
instructs ucto to accept the plaintext output from that component. We need some extra imports
and would then modify the ``accepts()`` to tie in the component: 

```python
from luiginlp.engine import InputComponent
from some.other.module import ConvertToPlaintext
```

```python
    def accepts(self):
        return (
            InputFormat(self, format_id='txt',extension='txt'),
            InputFormat(self, format_id='folia', extension='folia.xml'), 
            InputComponent(self, ConvertToPlaintext) #you can pass parameters using keyword arguments here
        )
```

Our ucto component thus-far has been fairly simple, we first used ``autosetup()`` to
wrap a single task, and later to choose amongst two tasks. Let's look at a more
explicit example with actual task chaining. 

Suppose we want the Ucto component to lowercase our text before passing it on
to the actual task that invokes ucto. We can write a simple lowercase task as
follows, for this one we just use Python and call no external tools (i.e. we
set no ``executable`` and do not call ``ex()``):

```python
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
        return TargetInfo(self, replaceextension(self.in_txt().path, '.txt','.lowercased.txt')) 

    #Define the run method, this will be called to do the actual work
    def run(self):
        #We do the work in Python itself
        #TargetInfo instances can be opened as file objects
        with self.in_txt().open('r',encoding=self.encoding) as inputfile
            with self.out_txt().open('w',encoding=self.encoding) as outputfile:
                outputfile.write(inputfile.read().lower())
                    
```

Now we go back to our Ucto component, we forget about the FoLiA part for a
bit, and we set up explicit chaining using ``setup()`` instead of
``autosetup()``, which is a bit more work but gives us complete control over
everything.


```python
from luiginlp.engine import WorkflowComponent, InputFormat

class Ucto(WorkflowComponent):
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

        #set up ucto and feed the output of the lower caser to it
        #explicitly pass any parameters we want to propagate
        ucto = workflow.new_task('ucto', Ucto_txt2tok, language=self.language) 
        ucto.in_txt = lowercaser.out_txt

        #always return the last task(s)
        return ucto
```



Plans/TODO
-------------

* Expand autosetup to build longer sequential chains of tasks (a2b b2c c2d)
* Support multiple components simulteanously in ``accepts()``
* [tentative] Integration with [CLAM](https://github.com/proycon/clam) to automatically
  create webservices of workflow components
* Further testing...
