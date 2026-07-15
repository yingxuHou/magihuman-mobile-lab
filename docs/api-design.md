# API Design Notes

If on-device inference is not feasible, the fallback architecture is a mobile app that submits generation jobs to a GPU backend.

## Draft Endpoints

- `POST /tasks`: create a generation task.
- `GET /tasks/{task_id}`: check status and progress.
- `GET /tasks/{task_id}/result`: fetch the generated video.
- `DELETE /tasks/{task_id}`: remove task assets.

## Draft Task States

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`

