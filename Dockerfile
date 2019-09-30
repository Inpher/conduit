FROM gcr.io/braided-analyst-224620/xor-machine:latest

USER root

# Update OS and install requirements

RUN apt-get update && apt-get upgrade -y && apt-get install -y python3 nginx supervisor libsnappy-dev

# Configure Flask app

ENV APP /opt/inpher/conduit

RUN mkdir -p $APP
WORKDIR $APP

COPY requirements.txt .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY app .

# Configure nginx

COPY conf/nginx.conf /etc/nginx/sites-available/conduit.conf

RUN ln -sf /etc/nginx/sites-available/conduit.conf /etc/nginx/sites-enabled/default

# Configure supervisor

COPY conf/supervisor.conf /etc/supervisor/conf.d/conduit.conf

EXPOSE 80

CMD ["supervisord"]