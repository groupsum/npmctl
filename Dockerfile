FROM python:3.13-slim

WORKDIR /app
COPY packages/npmctl /app/packages/npmctl
RUN pip install --no-cache-dir /app/packages/npmctl

ENTRYPOINT ["npmctl"]
