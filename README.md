PICCL (proof of concept)
================================

Proof of concept for the PICCL NLP pipeline.

Implemented using [sciluigi](https://github.com/pharmbio/sciluigi), which is in turn
based on [luigi](https://github.com/spotify/luigi).

Goals
---------

 * Abstraction of workflow/pipeline logic: a generic, scalable and adaptable solution
 * Modularisation; clear separation of all components from the workflow system itself
 * Explicit workflow definition (as opposed to automatic workflow discovery based on the specification of the components)
 * Easy to extend with new modules or workflows. Workflows can also be recombined (meta-workflows, a feature of sciluigi)
 * Automatic parallellisation where possible (due to luigi)
 * Keep it simple, minimize overhead for the developer of the workflow
 * Runnable standalone from command-line as well as through CLAM
    * Not sure yet whether to expose multiple CLAM webservices (one per workflow), or one monolithic one, leaning towards the former.

Architecture
----------------

 * A **module** (``piccl/modules/*.py``) provides a specific component in the form
   of one or more **tasks**:
 * A **task** takes input files, parameters and produces output files, in a
   deterministic fashion. Each task defines input and output slots.
 * A **workflow** takes an initial input (``piccl/inputs.py``), parameters, and
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
