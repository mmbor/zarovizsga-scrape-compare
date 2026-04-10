# zarovizsga-scrape-compare
Scrapes the zarovizsga database and allows for comparison with older scrapes to identify changes

## IMPROVED VERSION OF:
- Greekdoctor javascript scraper:https://github.com/greekdoctor/finalexam-questioncollector-js/tree/main
- German programs JSON comparitor

Why is it better? Requires to only run once, compared to hours using previous scripts

## How does the program work?
It has two programs:
1) A javascript command that pulls all questions from the database, and saves it as JSON files for each subtopic
2) A python program comparing previous pulls with most recent and generates the differences as a PDF

+) A python program that can turn each of the .JSON files into a .tsv which can be imported to ANKI
-- The name of the anki cards are a bit messy, but it will say the topic, but not subtopic. Just change in anki.


## How to run it?
1. Visit the website logged in
2. Open the consol
3. Type in the scrape_topicseparator.js   
-- Ensure the correct IDs are set, refference: scraper_topicIDS.txt
-- manualy change if they have changed theirs as well
-- It dowloads all .json files in your webbrowsers preffered location, change this to a separate folder

4. Archive the dowload
-- anki_generator includes a script for mass convertion to anki cards

New questions has been announced?
1. Repeat afformentioned process
2. Load booth versions of the questionbank into the folder with the compare_xxx.py script
3. Run the compare_xxx.py script
4. A pdf is generated with the differences


## Known problems:
- Some may have problem with loading python module jsondiff (Talk with chatGPT how you want to solve that.)
- Inconsistently recgonize deleted questions (Not the worst thing in the world to have some extra questions.)
- Sometime recognizes new questions as just changed (Still works kinda)
- Dowloads may be chaotic in diffrents systems/browsers, change the dowload path in web browser settings before each scrape


## Futureproofing ideas:
- If they change the id (or subID) for the topics, the javascript scraper will not work.


## HM
