FROM python:3

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies:
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install
RUN playwright install-deps
# Run the application:
COPY src .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "3000", "-e", "DATADIR=/data/", "app:app"]