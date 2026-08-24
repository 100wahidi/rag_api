create extension if not exists vector;
create extension if not exists pgmq;

create table if not exists public.embedding_jobs (
    id bigint generated always as identity primary key,
    job_id bigint,
    schema_name text not null,
    table_name text not null,
    row_id bigint not null,
    content_function text not null,
    embedding_column text not null,
    status text not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    error_message text
);

create table if not exists public.embedding_queue (
    id bigint generated always as identity primary key,
    payload jsonb not null,
    created_at timestamptz not null default now(),
    processed_at timestamptz
);

create or replace function public.enqueue_embedding_job(
    p_schema_name text,
    p_table_name text,
    p_row_id bigint,
    p_content_function text,
    p_embedding_column text
)
returns bigint
language plpgsql
as $$
declare
    v_job_id bigint;
begin
    insert into public.embedding_jobs (
        schema_name,
        table_name,
        row_id,
        content_function,
        embedding_column,
        status
    ) values (
        p_schema_name,
        p_table_name,
        p_row_id,
        p_content_function,
        p_embedding_column,
        'pending'
    ) returning id into v_job_id;

    return v_job_id;
end;
$$;

create or replace function public.notify_embedding_queue()
returns trigger
language plpgsql
as $$
begin
    perform pg_notify('embedding_jobs_channel', json_build_object(
        'schema_name', NEW.schema_name,
        'table_name', NEW.table_name,
        'row_id', NEW.row_id,
        'content_function', NEW.content_function,
        'embedding_column', NEW.embedding_column,
        'job_id', NEW.id
    )::text);
    return new;
end;
$$;

create trigger trg_embedding_queue_notify
after insert on public.embedding_jobs
for each row
when (new.status = 'pending')
execute function public.notify_embedding_queue();

create or replace function public.process_embedding_job(p_payload jsonb)
returns void
language plpgsql
as $$
begin
    update public.embedding_jobs
    set status = 'processing',
        updated_at = now()
    where id = (p_payload->>'job_id')::bigint;
end;
$$;
