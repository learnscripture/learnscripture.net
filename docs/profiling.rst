Memory and speed profiling
==========================

Flamegraphs can be produced by doing::

  pip install flamegraph
  python -m flamegraph -o perf.log ./your_script.py

  flamegraph.pl --fontsize 10 perf.log > perf.svg

flamegraph.pl is available from https://github.com/brendangregg/FlameGraph

Then view ``perf.svg`` in a web browser.

For PyPy, use vmprof::

   pip install vmprof

   python -m vmprof --web ./your_script

See https://vmprof.readthedocs.io/en/latest/vmprof.html#module-level-functions
