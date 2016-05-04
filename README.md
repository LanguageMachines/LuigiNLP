PICCL (proof of concept)
================================

Proof of concept for the PICCL NLP pipeline.

Implemented using [sciluigi](https://github.com/pharmbio/sciluigi), which is in turn
based on [luigi](https://github.com/spotify/luigi).

Goals
---------

 * Abstraction of workflow/pipeline logic: a generic, scalable and adaptable solution
 * Modularisation; clear separation of all components from the workflow system itself
 * Explicit workflow definitions
 * Automatic parallellisation where possible (due to luigi)
 * Keep it simple, minimize overhead for the developer of the workflow

