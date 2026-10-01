Testing Guide
=============

Overview
--------

The Module 4 project uses ``pytest`` for automated testing and
``pytest-cov`` for code coverage.

The test suite is designed to verify the Flask application, button behavior,
analysis formatting, database operations, scraping functions, and complete
integration workflows.

Running All Tests
-----------------

From the ``module_4`` directory, run:

.. code-block:: bash

   python -m pytest

The project's ``pytest.ini`` configuration requires 100 percent code
coverage for the Python code under ``src/``.


Test Markers
------------

Every test is assigned one of the required pytest markers:

* ``web`` - Flask pages and web-related behavior.
* ``buttons`` - Pull Data and Update Analysis button behavior.
* ``analysis`` - Analysis output and formatting.
* ``db`` - Database operations and queries.
* ``integration`` - End-to-end workflows involving multiple components.

All marked tests can be run with:

.. code-block:: bash

   python -m pytest -m "web or buttons or analysis or db or integration"


Running Individual Test Groups
------------------------------

A single category can be run by specifying its marker.

For example:

.. code-block:: bash

   python -m pytest -m web

or:

.. code-block:: bash

   python -m pytest -m db


Coverage
--------

Coverage is configured in ``pytest.ini``.

Running the complete test suite produces a coverage report for the source
code. The project requires 100 percent coverage.

The final coverage result is also recorded in ``coverage_summary.txt``.


Database Testing
----------------

Database tests verify insertion behavior, required applicant information,
duplicate handling, query results, and idempotency.

PostgreSQL integration tests use a test database configured through the
``DATABASE_URL`` environment variable.

The tests should never be pointed at a production database.


Integration Testing
-------------------

Integration tests verify that multiple parts of the application work
together.

The end-to-end tests use fake scraper records rather than accessing the live
Grad Cafe website.

The workflow verifies that fake scraped records can pass through the Flask
application, be loaded into PostgreSQL, and be used by the application.

The integration tests also verify repeated pulls containing overlapping
records. Because applicant URLs are unique, duplicate records are not
inserted again.


Deterministic Testing
---------------------

The automated tests do not depend on live internet access.

External operations are replaced with fake data or mocked behavior where
appropriate. Tests also avoid arbitrary sleep calls and manual browser
interaction.


Continuous Integration
----------------------

GitHub Actions runs the automated test suite whenever the configured workflow
is triggered.

The CI environment starts a PostgreSQL service, installs the dependencies
from ``requirements.txt``, and runs pytest with the project's coverage
requirements.

A successful GitHub Actions run confirms that the application and tests can
run in a clean automated environment.