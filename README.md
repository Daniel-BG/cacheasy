# Cacheasy
An easy to use cache simulator for python. Cacheasy is built with teaching in mind, tracing the data as it moves through the memory hierarchy, as well as gathering statistics about accesses, hits, misses, and many more.

It supports the following features:
* Main memory simulation
* Any number of cache levels
* Victim cache
* Write back / write through
* Write allocate / no write allocate
* Multiple replacement policies (FIFO/LRU/MRU/Random)
* Configurable number of sets and ways per cache level

It is built on top of a command line interface supporting:
* Running scripts
* Read / write simulation and burst operations
* Parameter configuration
* Interactive prompt

# Dependencies
You can install all the dependencies via pip: `cmd2`, `numpy` and `colorama`

# How to use
After downloading the code and installing the dependencies, the program will be ready to run. To run it, either enter interactive mode:

> python cacheasy.py

Or you can also run it with a script

> python cacheasy.py "run_script \<script\>"

As an example, let's see the output of running the previous command, with the script `ejesp3.chs`

![Screenshot after running `python3 cacheasy.py "run_script ejesp3.chs`.](https://github.com/Daniel-BG/cacheasy/blob/master/res/example.png)

The simulator outputs a log of the different types of operations (accesses, misses, block transfers...) after each request (`read`/`write`) to the memory system. To see the statistics at any time, you can run the `show_state` command which will print information about the addresses contained in the cache, as well as its metrics.