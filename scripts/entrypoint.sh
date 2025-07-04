#!/bin/bash
# entrypoint.sh

# initialize metadata DB if needed
airflow db upgrade

# create admin user if missing
airflow users create \
    --username airflow \
    --firstname Airflow \
    --lastname Admin \
    --role Admin \
    --email admin@example.org \
    --password airflow \
    || true

# run the actual Airflow command passed to the container
exec "$@"