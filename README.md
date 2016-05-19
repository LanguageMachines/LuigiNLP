PICCL (proof of concept)
================================

Proof of concept for the PICCL NLP pipeline.

Implemented using [sciluigi](https://github.com/pharmbio/sciluigi), which is in turn
based on [luigi](https://github.com/spotify/luigi).

Goals
---------

 * Abstraction of workflow/pipeline logic: a generic, scalable and adaptable solution
 * Modularisation; clear separation of all components from the workflow system itself
 * Automatic dependency resolution (similar to GNU Make, top-down)
 * Robust failure recovery: when failures occur, fix the problem and run the workflow again, tasks that have completed will not be rerun.
 * Easy to extend with new modules or workflows. Workflows can also be recombined (meta-workflows, a feature of sciluigi)
 * Traceability of all intermediate steps, retain intermediate results until explicitly discarded
 * Explicit workflow definitions 
 * Automatic parallellisation where possible
 * Keep it simple, minimize overhead for the developer of the workflow. 
 * Python-based, all workflow and component specifications are in Python rather than external.
 * Protection against shell injection attacks
 * Runnable standalone from command-line 
 * Runnable as a CLAM webservice 
    * Not sure yet whether to expose multiple CLAM webservices (one per workflow), or one monolithic one, leaning towards the former.

Architecture
----------------

The pipeline follows a goal-oriented paradigm, in which a target workflow is
specified along with an initial input, dependency workflows needed to get from
input to the target workflow are automatically found and executed.

 * A **module** (``piccl/modules/*.py``) is a collection of **workflow components** and **tasks**.
 * A **task** takes input files, parameters and produces output files, in a
   deterministic fashion, and gets an actual job done, either by invoking an
   external tool or by running Python code.  Each task defines input and output slots that correspond to input/output
   files in specific formats.
 * A **workflow component** chains one or more of tasks together for a specific
   purpose. Workflow components accept initial input (files) or the output of other specified workflow
   components. A workflow definition connects the input and
   output slots of different tasks.
 * Tasks and components may specify parameters
 * The user (or an intermediary) selects target workflow and provides input and
   initial parameters. 

Limitations
------------

* Intermediate files are not open for inspection in workflow specifications,
  only in tasks.

Directory Structure
---------------------

 * ``piccl/piccl.py`` - Main tool
 * ``piccl/modules/`` - Modules, each addressing a specific tool/goal. A module
   consists of workflow components and tasks.
 * ``piccl/inputs.py`` - Definition of initial inputs, to be used by the workflows
 * ``piccl/util.py`` - Auxiliary functions
 * ``setup.py`` - Installation script for PICCL (only covers PICCL and its direct python dependencies)
 * ``bootstrap.sh`` - Full installation script, pulls in all necessary dependencies and runs ``setup.py``, to be invoked by or from within [LaMachine](https://github.com/proycon/LaMachine)

Installation
---------------

To be used within LaMachine (https://proycon.github.io/LaMachine). This system
is not included yet at this stage so install with:

    $ python setup.py install

Usage
---------

Example, specify a workflow corresponding to your intended goal and an input file:

    $ piccl --module piccl.modules.frog Frog --inputfilename test.rst 

