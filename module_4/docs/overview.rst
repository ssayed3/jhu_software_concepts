Overview and Setup
==================

Project Overview
----------------

Module 4 extends the Grad Cafe application developed in the previous modules.
The project focuses on automated testing, code coverage, continuous integration,
and software documentation.

The application collects graduate admissions data, stores the data in a
PostgreSQL database, performs analysis, and displays the results through a
Flask web application.

Project Structure
-----------------

The main project directories are:

* ``src/`` - Application source code.
* ``tests/`` - Automated pytest tests.
* ``docs/`` - Sphinx documentation.
* ``.github/workflows/`` - GitHub Actions continuous integration workflow.

Installation
------------

Create and activate a Python virtual environment, then install the project
dependencies:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Database Setup
--------------

The application uses PostgreSQL for persistent data storage. PostgreSQL must
be installed and running before using the database-dependent features.

The database connection can be configured using the ``DATABASE_URL``
environment variable.

For example:

.. code-block:: bash

   export DATABASE_URL="postgresql://username@/module4_test_db"

Environment Variables
---------------------

``DATABASE_URL``
   Specifies the PostgreSQL database connection URL.

``DB_USER``
   Specifies the PostgreSQL user when the default database URL is used.

Running the Application
-----------------------

From the ``module_4`` directory, run:

.. code-block:: bash

   python -m src.app

Then open the local Flask application in a web browser.

Running the Tests
-----------------

Run the complete test suite with:

.. code-block:: bash

   python -m pytest

The test configuration requires 100 percent coverage of the Python code
under ``src/``.