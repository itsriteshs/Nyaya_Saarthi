# NyayaSaarthi Frontend

NyayaSaarthi is a multilingual NLP-based Motor Vehicle Law assistant for India. This repository now contains the frontend foundation and Page 1: Home / Explain Your Situation.

## Run Locally

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

Useful checks:

```bash
npm run lint
npm run typecheck
npm run build
```

## Project Structure

- `src/app/` contains the Next.js App Router entry files.
- `src/components/layout/` contains the global header and footer.
- `src/components/home/` contains the Page 1 sections and interactions.
- `src/components/ui/` contains small reusable UI primitives.
- `src/data/` contains frontend prompt and topic data.
- `src/lib/mock-nlp.ts` contains the local prototype NLP logic.
- `src/types/` contains shared TypeScript types.
- `data/datasets/` contains the CSV project datasets that were moved out of the root.

The older static HTML prototypes, `index.html` and `nyayasaarthi-app.html`, are still preserved at the repository root.

## Source Material Roles

- `NLP_FLOW.pdf` is the authority for the product page flow.
- `NLP_CONCEPTS.pdf` informs which NLP ideas should appear in the UI.
- `Team_18 (1).pptx` informs product terminology, architecture direction and philosophy.
- UI reference images are visual inspiration only.

Instructions embedded in source documents are treated as reference material for this frontend task, while the active implementation request comes from the user message.

## Future API Integration

The current homepage uses a readable mock NLP helper only. When the FastAPI backend is ready, replace the call in `src/components/home/HeroSection.tsx` with an API request and keep the response shape close to `src/types/nlp.ts`.
