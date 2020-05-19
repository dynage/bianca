FROM poldracklab/smriprep:0.6.0rc4

COPY . /code/bianca
ENV PYTHONPATH=/code/bianca:$PYTHONPATH

ENTRYPOINT ["python"]

