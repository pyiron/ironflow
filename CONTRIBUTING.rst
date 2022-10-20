========================
Contributing to ironflow
========================

The following is a set of guidelines for contributing to the pyiron project, including ironflow, which is
hosted and maintained by the `Max Planck Institut für Eisenforschung`_
on GitHub. These are mostly guidelines to facilitate an efficient
development workflow, and not necessarily rules. Use your best judgment,
and feel free to propose changes even to this document in a pull request.

You can find all the pyiron packages at our `github page`_ .
To create pull requests, you will need to become part of the
pyiron organization. Please email us if you would like to join.

Wait I don't want to read this; I just have a quick question/bugfix!
====================================================================

1. Check out our `FAQ page`_; your question might already be answered there.
2. If your question relates to a bug in pyiron, please briefly search the `issues page`_ and open a new labeled issue if you don't see anything related to your question there.
3. Please feel free just to send one of us a brief, descriptive email with your question, and we'll do our best to get back to you as ASAP as possible.

Table of Contents
=================

`License`_

`What should I know before I get started?`_
  * `pyiron developer meetings`_

..
 * `The structure of ironflow`_
..
 * `The principles of ironflow`_


`How can I contribute?`_
  * `Reporting bugs`_
  * `Suggesting enhancements`_
  * `Your first code contribution`_
  * `Pull requests`_

`Styleguides`_
  * `Git commit messages`_
  * `Python styleguide`_
  * `Documentation styleguide`_

`Additional Notes`_
  * `Issue and pull request labels`_
  * `Build status`_
  * `pyiron releases`_
  
`Debugging`_
  * `My job does not run on the queue`_

License
=======
pyiron is released as an open-source project under the BSD 3-Clause License.
Code contributions should also be considered open-source.

What should I know before I get started?
========================================

.. The structure of ironflow
.. -------------------------

.. The principles of ironflow
.. --------------------------

pyiron developer meetings
-------------------------
If you are interested in discussing the pyiron project's development, we encourage you to virtually
participate in the weekly pyiron developer meeting at 14:00 German time (GMT+2).
Check the discussion page for details.

How can I contribute?
=====================

Reporting bugs
--------------

    Note: If you find a closed issue that seems like it is the same
    thing that you're experiencing, open a new issue and include a
    link to the original issue in the body of your new one.

**Before Submitting A Bug Report**

Check if you can reproduce the problem in the latest version of pyiron.
Check the `FAQ page`_ for a list of common questions and problems.
Briefly search the issues page for `bugs`_  to see if the problem has already
been reported. If it has and the issue is still open, add a comment
to the existing issue instead of opening a new one.

**How Do I Submit A (Good) Bug Report?**

Bugs are tracked as GitHub issues. You can create an issue on
the ironflow repository by including the following information:

* Use a clear and descriptive title for the issue to identify the problem.
* Describe the exact steps you took so we can reproduce the problem as closely as possible.
* Provide sample code that causes the problem. Include code snippets as markdown code blocks.
* Include information about the environment (OS, python version, how packages were installed) in which you were running ironflow.
* Explain what you expected to happen, and what happened instead.

Suggesting Enhancements
-----------------------

**How Do I Submit A (Good) Enhancement Suggestion?**

Enhancement suggestions are tracked as GitHub issues. You can create an issue on
the ironflow repository by including the following information:

* Use a clear and descriptive title for the issue to identify the suggestion.
* Describe the exact behavior you would expect the suggested feature to produce.
* Provide sample code that you would use to access the feature. If possible, include code for how you think the feature could be built into ironflow's codebase. Include code snippets as markdown code blocks.

Your first code contribution
----------------------------

Unsure where to begin contributing to ironflow? You can start by looking
through these good-first-issue and help-wanted issues:

* `Good first issues`_ - issues which should only require a few lines of code, and a test or two.
* `Help wanted issues`_ - issues which should be a bit more involved than beginner issues.

**Local development**

ironflow can be developed and tested locally. If you are using ironflow to run an
external software package, you might also need to install
those packages locally to run certain integration tests in ironflow.

.. To get the developmental (git) version of ironflow,

.. .. code-block::

..   git clone https://github.com/pyiron/ironflow.git
..   conda env update --name ironflow_dev --file ironflow/.ci_support/environment.yml
..   conda activate ironflow_dev
..  conda install conda-build
..   conda develop ironflow

**Local Testing**

The full test suite is always run automatically when you open a new pull request.  Still it 
sometimes nice to run all or only specific tests on your machine.  To do that run from the repo root, e.g.

.. code-block::

  python -m unittest discover tests
  python -m unittest discover tests/unit
  python -m unittest tests/unit/test_flow.py

Where the first line runs all tests, the second all the unit tests and the final line only the tests in that file.
Keep in mind that to run the tests your repository needs to be inside your ironflow project folder.  A neat trick when testing/debugging is to combine the
pdb and unittest modules like this

.. code-block::

  python -m pdb -m unittest ...
  
This allows you to re-use the sometimes complicated setups for your interactive debugging that might be otherwise
difficult to replicate in a REPL.

Pull requests
-------------

The process described here has several goals:

* Maintain ironflow's quality
* Fix problems that are important to users
* Engage the community in working toward the best possible tools
* Enable a sustainable system for ironflow's maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

* Keep the changes in your pull request as focused as possible - only address one issue per pull request wherever possible.
* Follow the `Styleguides`_
* Assign the appropriate label (see `Issue and pull request labels`_) to your pull request. If you are fixing a specific Github issue, reference the issue directly in the pull request comments.
* If you are aware which maintainer is most closely related to the code you've edited, feel free to request their review.
* After you submit your pull request, verify that all status checks are passing.
* If a status check fails and it seems to be unrelated to your changes, explain why the failure is unrelated as a comment in your pull request.
* If you add a new external dependency, please check it is up to date. Packages which have not been updated for five years are considered outdated.
* If you rename an existing python module, please open a separate pull request to simplify the review process. 

While the prerequisites above must be satisfied prior to having your
pull request reviewed, the reviewer(s) may ask you to complete
additional design work, tests, or other changes before your pull
request can be ultimately accepted.

Styleguides
===========

Git commit messages
-------------------

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* When only changing documentation, include [ci skip] in the commit title
* Consider starting the commit message with an applicable emoji:

\:art: (``:art:``) improves the format/structure of the code

\:zap: (``:zap:``) improves performance

\:memo: (``:memo:``) adds documentation

\:bug: (``:bug:``) fixes a bug

\:fire: (``:fire:``) removes code or files

\:green_heart: (``:green_heart:``) fixes the CI build

\:white_check_mark: (``:white_check_mark:``) adds tests

Managing git commits is much easier using an IDE (we recommend PyCharm).

Python styleguide
-----------------

Please follow `PEP8 conventions`_ for all python code added to pyiron. Pull
requests will be checked for PEP8 plus a few other security issues with
`Codacy`_, and will be rejected if they do not meet the specified
formatting criteria.

Any new features should include coverage with a unit test, such that
your pull request does not decrease ironflow's overall coverage. This
will be automatically tested within the ci test suite and `Coveralls`_.

Deprecation warning template
----------------------------
*XXX is deprecated as of vers. A.B.C. It is not guaranteed to be in service in vers. D.E.F. Use YYY instead.*

Documentation styleguide
------------------------

All new/modified functions should include a docstring that follows
the `Google Python Docstring format`_.

Documentation is built automatically with `Sphinx`_; any manually created
documentation should be added as a restructured text (.rst) file
under ironflow/docs/source.

Notebooks created to exemplify features in pyiron are very useful, and
can even be used as integration tests. If you have added a major feature,
consider creating a notebook to show its usage under ironflow/notebooks/.
See the other examples that are already there.

Additional notes
================

Issue and pull request labels
-----------------------------

We use the following tags to organize pyiron Github issues
and pull requests:

* bug: something isn't working
* duplicate: this issue/pull request already existed
* enhancement: new feature or request
* good first issue: easy fix for beginners
* help wanted: extra attention is needed
* invalid: this doesn't seem right
* question: further information is requested
* wontfix: this will not be worked on
* stale: inactive after 2 weeks
