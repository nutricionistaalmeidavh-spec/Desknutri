FROM python:3.12-slim
WORKDIR /app
COPY license_server/requirements.txt /app/license_server/requirements.txt
RUN pip install --no-cache-dir -r /app/license_server/requirements.txt
COPY license_server /app/license_server
ENV NUTRIDESK_LICENSE_DATA=/data
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn","license_server.main:app","--host","0.0.0.0","--port","8000","--proxy-headers"]
