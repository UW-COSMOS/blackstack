# Blackstack

A machine learning approach to table and figure extraction. Uses SciKit Learn's Support Vector Machines and a custom annotator to build a model for entity extraction.  

Whereas other approaches to table and figure reading depend on content to be well-structured, Blackstack ignores the issue of table and figure _data_ extraction (see [Fonduer](https://github.com/HazyResearch/fonduer)) and instead uses a format-agnostic approach to extracting entities as images that can then be used for future analysis or querying.

## Installation
### Recommended
We recommend using Blackstack via docker-compose (https://docs.docker.com/compose/install/)

### Local

Blackstack relies on a few libraries that you probably need to install, including [ghostscript](https://www.ghostscript.com) and [tesseract](https://github.com/tesseract-ocr/tesseract). If you are using MacOS and [Homebrew](https://brew.sh) you can install them as so:

````
brew install ghostscript parallel tesseract
````

[Postgres](https://www.postgresql.org) is also required. If you are using MacOS [Postgres.app](https://postgresapp.com) is suggested.

Once Postgres is installed, set up the database:
````
createdb blackstack
psql blackstack < setup/schema.sql
````

You might need to substitute in your Postgres credentials on the above commands (e.g. `createdb -U me blackstack`).

Additionally you will also need to update `config.py` with your Postgres credentials. First, make a copy of `config.py.example` and name it `config.py`:

````
cp config.py.example config.py
````

and then update `config.py` with your Postgres credentials.

Finally, install the required Python packages:

````
pip install -r requirements.txt
````

## Getting started

### Docker

The recommended way of running Blackstack is via the supplied `docker-compose.yml`. It can
be run in either `training` mode to train a new model or in `classified` mode
to apply the trained model (or the default included one) to a set of documents. The mode of running can be provided
as an environmental variable when invoking docker-compose:

````
BLACKSTACK_MODE=classified docker-compose up --no-deps --build --force-recreate
````
to apply a model.

To train a new one, the first step is to move the default data so that it doesn't
interfere with your training.

````
mv setup/02_example_data.sql setup/02_example_data.sql_bk
BLACKSTACK_MODE=training docker-compose up --no-deps --build --force-recreate
````
to train one. 

On startup, Blackstack will preprocess any documents in the `./input/` directory
and either serve them up for annotation (in training mode) or apply the model
(in classified mode).

Preprocessed output will be stored to the `./docs/` directory, and, if running in
classified mode, extractions will be stored per-document in `./docs/classified/`.

### Standalone
The tools can also be run individually if the prerequisites are installed locally.

#### Preprocessing
Before a model can be trained, documents to use as training data must be selected. If you are attempting to extract entities from a specific journal or publisher it is recommended that your training data also come from that journal or publisher. If you are trying to create a general classifier you should have a good sample of documents from across disciplines, publishers, etc.

The number of documents you choose is up to you and will influence the accuracy of the model.

To process a document for use in the annotator run the following:
````
./preprocess.sh training /path/to/your/document.pdf
````

This will create a folder `./docs/training/<document>` that contains a PNG for each page of the PDF, an HTML file that contains the Tesseract output for each page, moves the original PDF to that folder, runs statistics on the Tesseract output and stores those within Postgres.


#### Creating a model
Once your training documents have been processed you can annotate them using the Flask application in `/annotator`. To start it, simply `cd annotator` and run `python server.py` to start the application. You can then navigate to `http://localhost:5555` in your web browser to begin tagging.

You will be presented with a page from one of the training documents and a box around a section of the page. Click the button on the left that best describes that area. If you don't know or it is ambiguous select "Other".

The table on the left side of the window will display the model's current probability for each category for the given area. Stopping and restarting the tagging application will update the model with the training data you have produced.

If you'd like to play around with Blackstack without creating your own training data you can load around 5k example labels using the provided example data that were produced using heterogenous geoscience articles.

````
psql blackstack < setup/example_data.sql
````

#### Extracting entities from a PDF
Once you have created training data for the machine learning model you can run it against a PDF. To do so you must first prepare the PDF for processing similarly to the way it is prepared for use a a training document.

````
./preprocess.sh classified /path/to/a/<document>.pdf
````

This will convert the PDF to PNGs and run Tesseract on them. Once that is done you can run the extractor on it as so:

````
python extract.py ./docs/classified/document
````

The entities found will then be found in `./docs/classified/<document>/tables`


## FAQ

__Why is the figure/table/map/etc cut off or otherwise incomplete?__  
Blackstack depends on Tesseract's concept of "areas" and its ability to accurate identify them. While it is generally good at identifying blocks of text it is less consistent when there are combinations of text and graphics. Blackstack attempts to resolve some of these issues by merging adjacent "areas" that have a high probability of being related, yet issues still remain.

__Why is something that is clearly not a graphic extracted as one?__  
Tesseract can occasionally be confused by certain page layouts, especially cover pages. Since Blackstack depends on Tesseract to accurately identify "areas" it can only be as accurate as Tesseract.

__Why is the accuracy so bad on a document that isn't an academic paper?__
Blackstack was developed for table, figure, graphic, and map extraction from published academic literature. If you would like to extend it to other types of documents you will need to update the database schema and `heuristics.py` to reflect the nature of that type of document.

## Funding
Development supported by NSF ICER 1343760

## License
MIT

## Other Info
#### preprocess.sh
**Usage:**  `./preprocess.sh ~/Downloads/document.pdf`  
**Purpose:** Does the following:
+ Takes a given PDF and runs it first through ghostscript to create PNGs of each page
+ Runs each PNG through tesseract to create HTML files
+ Creates a folder within the folder `docs` with the name of the pdf, and a folder for the tesseract and png output.
+ Moves the original document to the new folder and renames it `orig.pdf`
+ Runs the output of tesseract through the script `summarize.py`

#### process.sh
**Purpose:** Runs tesseract on a given page. Not called directed - used by `preprocess.sh`  

#### summarize.py
Takes a given document, generates document-wide statistics with `helpers.summarize_document`, and runs each area in the document
through all the labeling functions in `heuristics.py`. The result is stored in the postgres table `areas`.

#### heuristics.py
Labeling functions for areas. Most return a boolean, and some an integer.

#### classifier.py
Generates a model using SciKit Learn that can b used to classify areas. Contains two methods:
+ `create()` - queries all areas and associated labels created by `annotator` and returns a model
+ `classify(<pages>, <doc_stats>)` - Takes as an input a list of pages and document-level stats generated by `helpers.summarize_document`
and returns those pages with all areas tagged with their classification.

#### annotator
A flask application that runs on port 5555 that can be used for creating training data.
