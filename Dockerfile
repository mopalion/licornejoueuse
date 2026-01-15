FROM python:3.14

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

ENTRYPOINT ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "licornejoueuse.wsgi"]
#CMD ["sleep", "3600"]
