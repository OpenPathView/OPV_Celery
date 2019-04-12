FROM opv-tasks

ENV CELERY_BROKER redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/1
ENV CELERY_CONCURRENCY 1
ENV CELERY_CONFIG_MODULE opv_celery.celeryconfig

COPY . /source/OPV_Tasks

WORKDIR /source/OPV_Tasks

RUN pip3 install -r requirements.txt && python3 setup.py install

CMD ["/bin/bash", "-c", "/usr/local/bin/celery worker -A opv_celery.tasks.app --concurrency=${CELERY_CONCURRENCY} -b ${CELERY_BROKER} --result-backend=${CELERY_RESULT_BACKEND}"] 

