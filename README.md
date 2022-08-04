# ankUNpops
## Anki Country Populations (UN)

This is the code used to generate the Anki Country Populations (UN) shared deck.

How it works:

1. The module `un_api.py` downloads up-to-date information with an API call to the United Nations Population Division, 
2. then formats the information and stores it in a .json file.
3. Another module `generate_anki.py` reads the data and generates an Anki deck.
