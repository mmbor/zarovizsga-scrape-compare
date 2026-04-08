# zarovizsga-scrape-compare
Scrapes the zarovizsga database and allows for comparison with older scrapes to identify changes

## IMPROVED VERSION OF:
- Greekdoctor javascript scraper:https://github.com/greekdoctor/finalexam-questioncollector-js/tree/main
- German programs JSON comparitor

Why is it better? Requires to only run once, compared to hours using previous scripts

## How does the program work?
It has two programs:
1) A javascript command that pulls all questions from the database, and saves it as JSON files for each subtopic
2) A python script comparing previous pulls with most recent


## How to run it?
1) Have atleast two scrapes from the database (execute javascript in console on webbrowser)
2) Run the comparer20_borka.py, however changing the JSON file paths to yours (default: old=Test1; new=Test2)

## Known problems:
- Some may have problem with loading python module jsondiff (Talk with chatGPT how you want to solve that.)
- Does not recgonize deleted questions (Not the worst thing in the world to have some extra questions.)
- Dowloads may be chaotic in diffrents systems/browsers, change the dowload path in web browser settings before each scrape


## Futureproofing ideas:
- If they change the id (or subID) for the topics, the javascript scraper will not work.


## HM
