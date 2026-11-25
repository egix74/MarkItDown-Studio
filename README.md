# MarkItDown Studio per Windows

## Eseguibile per Windows a 64 bit

Apri `MarkItDown Studio.exe` con un doppio clic. L'eseguibile include
Python e le librerie dell'app e può essere spostato in un'altra cartella.

## Avvio dal sorgente

Tieni `studio.py` e `Avvia MarkItDown Studio.vbs` nella stessa cartella.
Fai doppio clic sul launcher per aprire l'app senza console. Il launcher usa
`%USERPROFILE%\markitdown-env\Scripts\pythonw.exe` e richiede Windows Script Host.

## Installazione e diagnostica

Se l'ambiente esiste già e contiene le dipendenze, puoi usare direttamente il launcher.
Per creare l'ambiente su un altro PC Windows con Python 3.11 e il launcher `py`,
esegui in PowerShell:

```powershell
py -3.11 -m venv "$HOME\markitdown-env"
& "$HOME\markitdown-env\Scripts\python.exe" -m pip install "PySide6==6.12.0" "markitdown[all]==0.1.9"
```

Se l'ambiente esiste e mancano componenti per alcuni formati, esegui solo
il comando di installazione. Se la finestra non si apre, dalla cartella
dell'app esegui questo comando per vedere l'errore:

```powershell
& "$HOME\markitdown-env\Scripts\python.exe" .\studio.py
```

## Uso

1. Seleziona più file nella stessa finestra. Aggiungi le cartelle una per volta dal pulsante oppure trascina più file e cartelle insieme da Esplora file.
2. Attiva **Includi sottocartelle** per cercare anche al loro interno.
3. Scegli se salvare accanto agli originali o in un'unica cartella.
4. Premi **Converti in Markdown**. Il riquadro dei risultati mostra destinazioni ed errori per file.

I risultati sono in UTF-8. Se il nome esiste, l'app crea un nome numerato
come `documento (2).md`, anche quando due originali hanno lo stesso nome.
Tema, ricorsione e cartelle preferite vengono ricordati per l'utente Windows.
Tutti i file individuati vengono inoltrati a MarkItDown in modalità locale,
con plugin disattivati. I formati non supportati compaiono tra gli errori.
I PDF basati su scansioni possono richiedere OCR separato.
