# MAL Reviews Scraper

Python Scripts and IPython notebooks for web scraping anime review data from [https://myanimelist.net/](https://myanimelist.net/) into a SQLite database.


### Database Schema:
![database_schema](databaseschema.PNG)


### Repo Contents:

+ `anime.db` Sample database with the SQL tables already created with ~5 pages of anime data scraped.
+ `config.py` Configuration file for controlling the sleep times between each requests.
	+ Default sleep times are set between 9-18 seconds, be courteous!
	+ Studios, tags and anime data are scraped everytime, the number of pages on the reviews section can be controlled.
+ `createtables.py` SQL queries for the above schema.
+ `malscraper.py` Main Python script for scraping the data.
+ `requirements.txt`  Requirements for this repo.
+ `MAL-database-interface.ipynb` IPython notebook for interfacing the SQL database and viewing tables in pandas.
+ `malscraper.ipynb` IPython notebook that can be used for web scraping instead of `malscraper.py`.
+ Methodology and data analysis folder:
	+ `MAL-Scraper Methodology and Data Analysis.ipynb` Detailed writeup of this project.
	
### Running the Scripts in virtualenv + pip(Windows):

+ Clone this repository.
+ Create virtual environment `python -m virtualenv venv`.
+ Start virtual environment `venv\Scripts\activate`. 
+ Install packages `pip install -r requirements.txt`.
+ Run `python malscraper.py`

### Running the Scripts in virtualenv + pip (macOS and Linux):

+ Clone this repository.
+ Create virtual environment `python3 -m virtualenv venv`.
+ Start virtual environment `source  venv/bin/activate`. 
+ Install packages `pip install -r requirements.txt`.
+ Run `python3 malscraper.py`

### Running the Scripts in Conda Environment with Ubuntu:
+ Clone this repository.
+ Create virtual environment `$> conda create --name mal-scraper python=3.6`
+ Start virtual environment `$> source activate mal-scraper`
+ Install packages `$> while read requirement; do conda install --yes $requirement; done < requirements.txt`
+ Run `malscraper.py`