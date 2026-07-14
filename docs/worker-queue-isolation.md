# Worker Queue Isolation

CheersAI Desktop runs knowledge-base indexing through Celery queues. Keep the
dataset queues isolated from long-running maintenance work so document indexing
does not stay in `waiting` while unrelated cleanup tasks run.

## Queue Split

- Dataset worker: `priority_dataset,dataset`
- General worker:
  `priority_pipeline,pipeline,mail,ops_trace,app_deletion,plugin,workflow_storage,conversation,workflow,workflow_professional,workflow_team,workflow_sandbox,schedule_poller,schedule_executor,triggered_workflow_dispatcher,trigger_refresh_executor,retention`

## Docker Compose

`docker/docker-compose-template.yaml` and `docker/docker-compose.yaml` define
two workers:

- `worker`
- `worker_dataset`

The split is controlled by:

```env
CELERY_GENERAL_QUEUES=priority_pipeline,pipeline,mail,ops_trace,app_deletion,plugin,workflow_storage,conversation,workflow,workflow_professional,workflow_team,workflow_sandbox,schedule_poller,schedule_executor,triggered_workflow_dispatcher,trigger_refresh_executor,retention
CELERY_DATASET_QUEUES=priority_dataset,dataset
CELERY_DATASET_WORKER_AMOUNT=1
```

## Systemd

For non-Docker deployments, install both unit files:

```bash
sudo cp deploy/systemd/cheersai-worker.service /etc/systemd/system/cheersai-worker.service
sudo cp deploy/systemd/cheersai-worker-dataset.service /etc/systemd/system/cheersai-worker-dataset.service
sudo systemctl daemon-reload
sudo systemctl enable --now cheersai-worker.service cheersai-worker-dataset.service
```

`cheersai-worker.service` intentionally excludes `priority_dataset,dataset`.
`cheersai-worker-dataset.service` consumes only dataset indexing queues.

## Read-Only Monitoring

```bash
cd /home/desktop/CheersAI-Desktop/api
watch -n 10 '
set -a; . ./.env; set +a
echo "=== $(date) ==="
for q in priority_dataset dataset app_deletion conversation plugin workflow workflow_storage priority_pipeline pipeline; do
  printf "%-24s " "$q"
  redis-cli -h "${REDIS_HOST:-127.0.0.1}" -p "${REDIS_PORT:-6379}" -a "$REDIS_PASSWORD" -n 1 LLEN "$q" 2>/dev/null
done
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_DATABASE" -Atc "select indexing_status || chr(9) || count(*) from documents group by indexing_status order by 2 desc;" 2>/dev/null
.venv/bin/celery -A celery_entrypoint.celery inspect active --timeout=3 2>/dev/null | grep -E "tasks\.|routing_key|time_start|empty" | head -n 40
.venv/bin/celery -A celery_entrypoint.celery inspect reserved --timeout=3 2>/dev/null | grep -E "tasks\.|routing_key|time_start|empty" | head -n 40
'
```
