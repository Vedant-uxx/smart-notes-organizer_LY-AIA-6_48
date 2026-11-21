DETAILS ---->
Vedant Santosh Jadhav 
ADT24SOCBD141
Roll no 48
LY-AIA-6

# 🗂️ Smart Notes Organizer

Paste notes from many places → get them **grouped by topic** with an auto-generated **heading for each group**, as clean **Markdown**.

## Problem
Notes end up scattered across chats, docs, emails and sticky notes. Finding or reusing them means manually sorting everything.

## Solution
1. Paste all your notes (one per line, or separated by blank lines).
2. The app numbers the notes and prompts an LLM (Claude) to cluster them and name each cluster.
3. The model returns note **indices** (not rewritten text), so no note is ever altered or lost.
4. The app renders Markdown with `##` headings and bullet points.

An **offline fallback** (TF-IDF + KMeans) runs with no API key. Its headings are keyword-based and rougher than the LLM's.

## Example
Input:
```
- Buy milk, eggs and bread
- Use virtualenv to isolate Python dependencies
- Grocery list: tomatoes, onions, rice
- Write unit tests with pytest
```
Output (LLM backend):
```markdown
# Organized Notes

## Groceries
- Buy milk, eggs and bread
- Grocery list: tomatoes, onions, rice

## Python Development
- Use virtualenv to isolate Python dependencies
- Write unit tests with pytest
```

## Project structure
```
smart-notes-organizer/
├── smart_notes/
│   ├── organizer.py   # parsing, LLM + local clustering, Markdown rendering
│   └── cli.py         # command-line interface
├── app.py             # Streamlit web UI
├── tests/             # pytest tests
├── sample_notes.txt
├── requirements.txt
└── .env.example
```

## Setup
```bash
git clone https://github.com/<Vedant-uxx>/smart-notes-organizer.git
cd smart-notes-organizer
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here               # optional; omit for offline mode
```

## Usage
**CLI**
```bash
python -m smart_notes sample_notes.txt -o organized_notes.md      # auto backend
python -m smart_notes sample_notes.txt -b local                   # offline
cat notes.txt | python -m smart_notes -b llm                      # from stdin
```
**Web app**
```bash
streamlit run app.py
```
**As a library**
```python
from smart_notes import organize_notes
print(organize_notes(open("sample_notes.txt").read(), backend="llm"))
```

## Configuration
| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Enables the LLM backend (used automatically when set) |
| `SMART_NOTES_MODEL` | Override the Claude model (default `claude-sonnet-5-5`) |

## Tests
```bash
python -m pytest -q
```

## Limitations / future work
- Very large note sets may exceed one prompt; add batching.
- Local backend quality is limited; swap in sentence embeddings for better clusters.
- Ideas: file upload (PDF/DOCX), nested sub-topics, export to Notion/Obsidian.

## License
MIT

## Using Groq instead of Anthropic
Set GROQ_API_KEY (and optionally GROQ_MODEL, e.g. the model ID shown by Groq's model list). If GROQ_API_KEY is set, the app uses Groq; otherwise it uses ANTHROPIC_API_KEY; with neither, it runs the offline fallback.

