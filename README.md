# Storyboard Maker

You fill in six fields and a local LLM writes a storyboard: 4 to 6 scenes, then an ending that reveals something about the main character and stops on a cliffhanger.

The six fields:

| Field | Example |
|---|---|
| Main character | Mara Voss |
| Revealed at the end | has been an android all along |
| Supporting character 1 | Lark |
| Supporting character 2 | Theo Black |
| Plot | a space station losing power one deck at a time |
| Theme | identity |

Each field offers presets from `data.json`, and you can type your own text into any of them. The **Randomize** button picks a preset for every field, which is a quick way to try combinations.

The model runs on your machine through [Ollama](https://ollama.com). Nothing is sent to an online service, and there are no API keys.

## Requirements

- Python 3.10 or newer. The app uses only the standard library, so there is nothing to `pip install`.
- Ollama with the `llama3.2:3b` model, about 2 GB.

```
winget install Ollama.Ollama
ollama pull llama3.2:3b
```

## Run it

```
python app.py
```

Then open http://localhost:8000. Ollama has to be running first. It usually starts with Windows from the tray icon. If it isn't running, start it with `ollama serve`.

On a CPU, one storyboard takes about a minute.

## Run it in Docker

Ollama stays on your PC. The container reaches it at `host.docker.internal`, which works on Docker Desktop.

```
docker build -t storyboard .
docker run -d --name storyboard -p 8000:8000 storyboard
```

`docker stop storyboard` stops it and `docker start storyboard` brings it back.

## Settings

All three are environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `MODEL` | `llama3.2:3b` | Any model you have pulled into Ollama |
| `OLLAMA_URL` | `http://localhost:11434` | Where Ollama listens (the Docker image sets `http://host.docker.internal:11434`) |
| `HOST` | `127.0.0.1` | Address the web server binds to (the Docker image sets `0.0.0.0`) |

The 3B model sometimes hints at the reveal instead of stating it. `llama3.1:8b` follows the instructions more closely but is slower. `llama3.2:1b` is faster and looser.

```
ollama pull llama3.1:8b
docker run -d -p 8000:8000 -e MODEL=llama3.1:8b storyboard
```

## How it works

`app.py` sends your six inputs to Ollama's `/api/chat` endpoint along with a JSON schema. The schema requires a `scenes` array and an `ending` object with separate `description`, `reveal`, and `cliffhanger` fields. Keeping the reveal and the cliffhanger in their own fields means the model can't leave them out or blur them into the last scene. If the reply is missing any of them, the app asks the model once more, then returns an error.

| File | Contents |
|---|---|
| `app.py` | Web server, prompt, and Ollama call |
| `index.html` | The form and the storyboard view |
| `data.json` | Preset test data: 5 main characters, 5 reveals, 6 supporting characters, 5 plots, 5 themes |
| `test_app.py` | Tests |

To add presets, edit `data.json` and reload the page.

## Tests

```
python test_app.py
```

The tests check that every input reaches the prompt, using 10 random preset combinations and one custom story. They also check that incomplete model replies are rejected. If Ollama is running, the last test generates a real storyboard and validates it. If Ollama isn't running, that test is skipped.
