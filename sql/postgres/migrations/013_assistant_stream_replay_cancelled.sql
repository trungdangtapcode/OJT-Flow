-- Allow Assistant stream replays to distinguish user cancellation from failure.

alter table if exists ojtflow.assistant_stream_replays
    drop constraint if exists assistant_stream_replays_status_check;

alter table if exists ojtflow.assistant_stream_replays
    add constraint assistant_stream_replays_status_check check (
        status in ('completed', 'failed', 'cancelled')
    );
