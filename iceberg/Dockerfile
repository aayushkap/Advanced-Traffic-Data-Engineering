FROM --platform=linux/x86_64 python:3.10

RUN pip install -U pathway
RUN pip install kafka-python
RUN pip install pyiceberg boto3 sqlalchemy psycopg2

COPY ./iceberg-etl.py iceberg-etl.py
COPY ./init-iceberg.py init-iceberg.py
COPY ./wait-for-db.py wait-for-db.py
COPY ./wait-for-brokers.py wait-for-brokers.py

CMD ["sh", "-c", "python -u wait-for-db.py && python -u init-iceberg.py && python -u wait-for-brokers.py && python -u iceberg-etl.py"]