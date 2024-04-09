## Podcast sökmotor

För att sökmotorn ska fungera på din dator:
1. Öppna filen `setup.py` och ändra adressen och API-nyckeln till dina värden.
2. Se till att ha podcast-filerna i en mapp som heter `podcasts`, eller döp om konstanten `DATASET_FOLDER` till vad din mapp heter.
3. Starta elasticsearch, och när den har startat, kör filen `index_dataset.py` för att skapa en index `podcast_transcripts` och börja indexera alla `.json` filer.
4. Det går nu att starta sökmotorn genom att köra filen `main.py`.


Ändringar i GUI:n görs in filen `Scenes/main_scene.py`, inuti funktionen `create_scene`.
För att skapa ett objekt (knapp, ruta, input-field etc.) skapar man först ett objekt av rätt klass, och sedan lägger man till den i scenen.

Exempel för att skapa en knapp:
1. `button = assets.Button(x=100, y=100, width=20, height=20, 
    text="Click Me!", left_click_function=foo, left_click_args=[foo, bar])`
2. `self.add_object(button)`