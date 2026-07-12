# adiFit

Review-based fit, usage, and VOC intelligence prototype for adidas eCommerce.

`adiFit` analyzes product reviews with an LLM, extracts structured signals such as size, comfort, design/color, use case, and VOC issues, then turns them into a consumer fit advisor and an internal merchandiser dashboard.

## What It Builds

- Review analysis engine for adidas-style footwear reviews
- Size and width signal extraction
- Aspect sentiment breakdown for fit, comfort, quality, durability, delivery, design, and value
- Use-case tags such as running, walking, commute, daily, gym, and race
- Comfort and design/color tags such as cushioning, responsiveness, breathability, styling, and color/photo match
- RAG-based fit advisor with cited review evidence
- Merchandiser VOC dashboard with PDP action recommendations
- Embedding clustering for customer usage segments
- Monthly VOC trend view for issue drift and spike detection
- Lightweight evaluation using a manually labeled gold set

## Data

The current prototype uses 24 manually curated demo reviews across 3 adidas products:

- Ultraboost Light
- Samba OG
- Adizero Adios Pro 3

This avoids external review licensing issues. In a production setting, the same schema can be connected to large-scale first-party review data.

## Tech Stack

- Python
- Streamlit
- Gemini structured output
- Gemini embeddings
- In-memory cosine retrieval
- scikit-learn KMeans/PCA for clustering
- Plotly for visualization
- Pydantic schema contracts

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add a Gemini API key to `.env`:

```bash
GEMINI_API_KEY=your-api-key
```

## Run

```bash
streamlit run app.py
```

## Deliverables

- Presentation PDF: `submission/adiFit_presentation.pdf`
- Presentation HTML: `submission/adiFit_presentation.html`
- Demo video script: `submission/demo_video_script.md`

## Evaluation

Current demo evaluation:

- Reviews: 24
- Products: 3
- Size signal gold set: 24 manually labeled reviews
- Size signal accuracy: 95.8%
- Citation coverage for tested advisor cases: 100%

The citation coverage metric checks whether cited `review_id`s exist in the retrieved evidence set. It is a grounding coverage check, not a full factuality benchmark.
