API
===

The API is pretty simple. Essentially, there are 3 kinds of functions, each
of which make a modular component in a pipeline.

.. mermaid::

   flowchart LR
       A[Release Source] -- Releases --> B[Support Filter]
       B -- Dict (package info) --> C[Output]


The functions types are the Release Source, the Support Filter, and the
Output. The output of one function is the input to the next. The output of
the Release Source is a list of :class:`.Release` objects, which is the
input to the Support Filter. The output of the Support Filter is a dict with
a particular structure, which we refer to as the "package info" dict. It is
also the input to the Output function.

.. toctree::
   :maxdepth: 1

   sources
   filters
   main
   output
   cli
   utils
   
