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
 * Easy to extend with new modules (workflow componentes & tasks).
 * Traceability of all intermediate steps, retain intermediate results until explicitly discarded
 * Explicit workflow definitions 
 * Automatic parallellisation of tasks where possible
 * Keep it simple, minimize overhead for the developer of the workflow, use Pythonic principles,
 * Python-based, all workflow and component specifications are in Python rather than external.
 * Protection against shell injection attacks in tasks
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
which input files it accepts directly. This enables you to either run the
component either directly on an input file, or have the input go through other
components first for necessary preprocessing. The dependency resolution
mechanism will automatically chose a path based on the specified input and
selected parameters.

A workflow component consists of a specification that chains together
**tasks**. Whereas a workflow component represents a more comprehensive piece
of work that is defined in a context of other components, a **task** represents
the smallest unit of work and is defined **independently** of any other tasks
or components.  A task consists of one or more input slots, corresponding to
input files of a particular type, one or more output slots corresponding to
output files of a particular type, and parameters. The task performs an actual
job, either by invoking an external tool, or by running Python code directly.
Chaining together tasks in the definition of the workflow component is done by
connecting output slots of one task, to input slots of the other. 

The simplest instance of a workflow component is just one that accepts one
particular type of input file and sets up just a single task. 

The architecture is visualised in the following scheme:

![LuigiNLP Architecture](https://raw.githubusercontent.com/LanguageMachines/LuigiNLP/master/architecture.png)

Tasks and workflow components may take **parameters**. These are available
within a task's ``run()`` method to either be propagated on to an external tool
or to steer the code itself. At the component level, parameters may also be used to influence
task composition, though often they are just passed on the the tasks. 

Both tasks and workflow components are defined in a **module** (in the Python
sense of the word), which simply groups several tasks and workflow components together.

LuigiNLP relies heavily on filename extensions. Input formats are matched on
the basis of an extension, and generally each task reads a file and outputs
a file with a new extension. Re-use of the same filename (i.e. writing output to the
input file), is **strictly forbidden**! 

It is important to understand that the actual input files are only open for
inspection when a Task in executed (its ``run()`` method is invoked).  During
workflow composition in a component (in its ``setup()`` method),  files can not
be inspected as the composition by definition preceeds the existence of any
files, and the process has to proceed deterministically.

Limitations
------------

* No circular dependencies allowed in workflow components
* Intermediate files are not open for inspection in workflow specifications, only within ``Task.run()``
* Parameters may not clash between workflow components, if they have the same ID, they should describe the same thing in the same manner. This does not apply to task parameters, as explicit translation may be done from component parameters to task parameters.
* Parameters from possible subworkflows may be inherited, even if they are not used eventually, set default values for parameters wherever as possible.


Directory Structure
---------------------

 * ``luiginlp/luiginlp.py`` - Main tool
 * ``luiginlp/modules/`` - Modules, each addressing a specific tool/goal. A module
   consists of workflow components and tasks.
 * ``luiginlp/inputs.py`` - Definition of initial inputs, to be used by the workflows
 * ``luiginlp/util.py`` - Auxiliary functions
 * ``setup.py`` - Installation script for LuigiNLP (only covers LuigiNLP and its direct python dependencies)
 * ``bootstrap.sh`` - Full installation script, pulls in all necessary dependencies and runs ``setup.py``, to be invoked by or from within [LaMachine](https://github.com/proycon/LaMachine)

Installation
---------------

Install as follows:

    $ python setup.py install

Many of the implemented modules rely on software distributed as part LaMachine
(https://proycon.github.io/LaMachine), so LuigiNLP is best used from within a
LaMachine installation. LuigiNLP itself will be included in LaMachine when it
is mature enough.

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

    import luiginlp
    from luiginlp.modules.frog import Frog
    luiginlp.run(Frog(inputfile="test.rst",skip='p'))

To parallelize multiple tasks you can just do:

    import luiginlp
    from luiginlp.modules.frog import Frog
    luiginlp.run(
        Frog(inputfile="test.rst",skip='p'),
        Frog(inputfile="test2.rst",skip='p'),
    )
        

Or use the ``Parallel`` interface:

    import luiginlp
    from luiginlp.modules.frog import Frog
    from luiginlp.engine import Parallel, ComponentParameters
    luiginlp.run(
        Parallel(component="Frog",inputfiles="test.rst,test2.rst",
            component_parameters=ComponentParameters(skip='p')
        )
    )


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

..TODO..

Plans/TODO
-------------

* Expand autosetup to build longer sequential chains of tasks (a2b b2c c2d)
* Make certain accepted subworkflows either mandatory or forbidden based on parameter values
* Integration with [CLAM](https://github.com/proycon/clam) to automatically
  create webservices of workflow components
* Further testing...
