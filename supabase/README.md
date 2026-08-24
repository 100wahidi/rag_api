# Supabase Embedding Automation Pipeline

This folder contains the Supabase side of the embedding automation pipeline used by the project.

## 1. Architecture Overview

The workflow is built around a simple queue pattern:

1. A row is inserted or updated in a table that needs semantic embedding generation.
2. A trigger fires and emits a notification to a Postgres channel.
3. The notification is consumed by an Edge Function or worker.
4. The worker reads the source content, generates an embedding using a model such as `gte-small`.
5. The embedding is written back into the target vector column.
6. The queue job is marked completed or failed.

This pattern keeps the database as the source of truth and turns embedding generation into an asynchronous pipeline.

## 2. Trigger-based queueing

The SQL file in `supabase/sql/001_embedding_pipeline.sql` creates:

- `public.embedding_jobs`
- `public.embedding_queue`
- `public.enqueue_embedding_job(...)`
- `public.notify_embedding_queue()`
- a trigger named `trg_embedding_queue_notify`

The trigger is important because it means every new pending job is automatically pushed into the event pipeline without manual orchestration from the app server.

Example:

```sql
select public.enqueue_embedding_job(
  'public',
  'documents',
  42,
  'get_document_text',
  'embedding'
);
```

The row is inserted into `public.embedding_jobs`, and then the trigger sends a Postgres notification for downstream processing.

## 3. Queue and job lifecycle

The logic is intentionally split into two stages:

- job registration: database record created with status = `pending`
- job processing: worker pulls the payload and updates the status to `processing`
- success/failure: final status is recorded and the worker logs the result

This gives you observability and retry-friendly behavior.

## 4. Edge Function

The edge function in `supabase/functions/hello-world/index.ts` is the worker. It is designed to:

- receive an array of jobs as JSON
- validate input with Zod
- fetch row content from the source table
- generate an embedding
- update the table row with the vector value
- delete the job from the queue once complete

The core pattern is:

```ts
const session = new Supabase.ai.Session('gte-small')
const embedding = await session.run(text, { mean_pool: true, normalize: true })
```

This is where the text becomes a vector representation used by semantic retrieval.

## 5. Why this matters for RAG

The generated embeddings are later used for similarity search in the retrieval layer. In practice:

- new documents or profile artifacts are inserted
- embeddings are generated asynchronously
- vector search is used to find the most relevant content for a user request

That is the backbone of the RAG pipeline in this project.

## 6. Best practices

- keep the queue job small and focused
- store one source of truth for content and vector target columns
- validate payloads before processing
- handle job retries and errors explicitly
- keep the embedding model version pinned for reproducibility

## 7. Typical flow in the repo

```text
App / API
   -> inserts or updates source row
   -> enqueue job via SQL function
   -> trigger fires
   -> Edge Function processes job
   -> vector column updated
   -> retrieval service queries similarity
```

This is the standard trigger + queue + edge-function model for a Supabase-based embedding pipeline.
