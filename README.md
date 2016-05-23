LuigiNLP (proof of concept)
================================

An NLP workflow system building upon
[sciluigi](https://github.com/pharmbio/sciluigi), which is in turn based on
[luigi](https://github.com/spotify/luigi).

Proof of concept to be used for the PICCL and Quoll NLP pipelines.

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
 * Runnable as a CLAM webservice  (TODO later)
    * Not sure yet whether to expose multiple CLAM webservices (one per workflow), or one monolithic one, leaning towards the former.

Architecture
----------------

The pipeline follows a goal-oriented paradigm, in which a target workflow is
specified along with an initial input, dependency workflows needed to get from
input to the target workflow are automatically found and executed.

 * A **module** (``luiginlp/modules/*.py``) is a collection of **workflow components** and/or **tasks**.
 * A **task** takes input files, parameters and produces output files, in a
   deterministic fashion, and gets an actual job done, either by invoking an
   external tool or by running Python code.  Each task defines input and output slots that correspond to input/output
   files in specific formats. These are defined as ``in_*`` and ``out_*``
   methods on the task's class.
 * A **workflow component** chains one or more of tasks together for a specific
   purpose. Workflow components accept initial input (files) or the output of
   other specified workflow components. A workflow definition connects the
   input and output slots of different tasks by connecting the input slot of
   one to the output slot of another (through simple assignment).
 * Tasks and components may specify parameters
 * The user (or an intermediary) selects target workflow and provides input and
   initial parameters. 

Limitations
------------

* No circular dependencies allowed in workflow components
* Intermediate files are not open for inspection in workflow specifications, only within ``Task.run()``
* Parameters may not clash between workflow components, if they have the same ID, they should describe the same thing in the same manner. This does not apply to task parameters, as explicit translation may be done from component parameters to task parameters.
* Parameters from possible subworkflows may be inherited, even if they are not used eventually. Set default values for parameters wherever as possible.

Plans/TODO
-------------

* Expand autosetup to build longer sequential chains of tasks (a2b b2c c2d)
* Make certain accepted subworkflows either mandatory or forbidden based on parameter values
* Further testing...

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

Example, specify a workflow corresponding to your intended goal and an input file:

    $ luiginlp --module luiginlp.modules.frog Frog --inputfile test.rst 

A workflow can be run parallelised for multiple input files as well, the number
of workers can be explicitly set:

    $ luiginlp --module luiginlp.modules.frog Parallel --component Frog --inputfiles test.rst,test2.rst --workers 2

You can always pass component-specific parameters by using the component name
as a prefix. For instance, the Frog component takes an option ``skip``, you can
use ``--Frog-skip`` to explicitly set it.

You can also invoke LuigiNLP from within Python of course:

    import luiginlp
    from luiginlp.modules.frog import Frog
    luiginlp.run(Frog(inputfile="test.rst"))

To parallelize multiple tasks you can just do:

    import luiginlp
    from luiginlp.modules.frog import Frog
    luiginlp.run(Frog(inputfile="test.rst"), Frog(inputfile="test2.rst"))

Or use the ``Parallel`` interface:

    import luiginlp
    from luiginlp.modules.frog import Frog
    from luiginlp.engine import Parallel
    luiginlp.run(Parallel(component="Frog",inputfiles="test.rst,test2.rst"))




