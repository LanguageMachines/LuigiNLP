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

 * A **module** (``piccl/modules/*.py``) covers a particular tool in the form
   of one or more **tasks**:
 * A **task** takes input files, parameters and produces output files, in a
   deterministic fashion. Each task defines input and output slots and either
   defers work to an external tool, or contains the implementation directly.
 * A **workflow** (``piccl/workflows/*.py``) takes an initial input (``piccl/inputs.py``), parameters, and
   invokes a chain of tasks, i.e. a workflow definition connects the input and
   output slots of different tasks.
 * The user (or an intermediary) selects a workflow and provides input and
   initial parameters.

Structure
----------

 * ``piccl/piccl.py`` - Main tool
 * ``piccl/modules/`` - Modules, each addressing a specific tool
 * ``piccl/workflows/`` - Workflows, each expresses a specific pipeline that combines the above modules in some way.
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

    $ piccl --module piccl.workflows.frog Frog --inputfilename test.rst 

