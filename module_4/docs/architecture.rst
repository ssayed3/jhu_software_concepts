Architecture
============

System Overview
---------------

The Module 4 application is organized into separate components for data
collection, data storage, analysis, web presentation, testing, and
documentation.

The overall data flow is:

.. code-block:: text

   Grad Cafe
       |
       v
   scrape.py
       |
       v
   applicant_data.json
       |
       v
   load_data.py
       |
       v
   PostgreSQL
       |
       v
   query_data.py / orm_queries.py
       |
       v
   Flask application (app.py)
       |
       v
   Analysis web page


Data Collection
---------------

``scrape.py`` contains the web-scraping logic used to collect graduate
admissions information.

``collect_data.py`` provides an entry point for running the data collection
process.

The scraper saves collected records to ``applicant_data.json`` before they
are loaded into the database.


Data Cleaning
-------------

``clean.py`` contains functions used to clean and extend applicant data.

The cleaning process prepares collected information for later storage and
analysis.


Database Layer
--------------

``load_data.py`` is responsible for creating the PostgreSQL applicants table
and inserting applicant records.

Applicant URLs are unique in the database. Duplicate URLs are therefore not
inserted again when overlapping data is loaded.

``models.py`` defines the SQLAlchemy database model and database connection
configuration.


Analysis Layer
--------------

The project demonstrates two approaches to querying the admissions data:

* ``query_data.py`` uses SQL queries with psycopg.
* ``orm_queries.py`` uses SQLAlchemy ORM queries.

These modules calculate the results used by the analysis page.


Web Application
---------------

``app.py`` contains the Flask application.

The application provides the ``/analysis`` page and routes for pulling new
data and updating the analysis.

The application factory, ``create_app()``, supports dependency injection so
that tests can provide fake scraper, loader, and analysis functions without
using the live website.


Concurrency
-----------

A lock is used during the scraping process to prevent overlapping scraping
operations.

If a pull or analysis update is requested while the application is busy,
the application returns HTTP status ``409`` with a busy response.


Testing Architecture
--------------------

Automated tests are stored in ``tests/``.

The test suite covers:

* Flask pages and routes.
* Pull Data and Update Analysis behavior.
* Analysis formatting.
* Database insertion and idempotency.
* Raw SQL and ORM queries.
* Scraping and cleaning functions.
* End-to-end workflows using fake scraper data and PostgreSQL.

Fake scraper data is used during automated testing so that the test suite
does not depend on live internet access.

GitHub Actions runs the automated test suite with PostgreSQL and verifies
the required code coverage.