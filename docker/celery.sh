#!/bin/bash

if [[ "${1}" == "celery" ]]; then
  celery --app=app.tasks.celery_app:celery_app_var worker --loglevel=INFO --pool=solo
elif [[ "${1}" == "flower" ]]; then
  celery --app=app.tasks.celery_app:celery_app_var flower
fi
