#!/bin/bash

python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

chown -R ec2-user:nginx /var/www

# Note: assuming port 8080 is open, you can test that the app will
# run under uwsgi manually using the following
# uwsgi --socket 0.0.0.0:8080 --protocol=http -w wsgi:app

mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf-orig
cp config/nginx.conf /etc/nginx/nginx.conf

cp config/my-whiskies.conf /etc/nginx/conf.d/my-whiskies.conf

cp config/my-whiskies.service /etc/systemd/system/my-whiskies.service

mkdir /var/log/uwsgi
chown -R ec2-user:nginx /var/log/uwsgi

systemctl start my-whiskies.service
systemctl enable my-whiskies.service

systemctl restart nginx
systemctl enable nginx

export FLASK_APP=my-whiskies
flask db upgrade

echo "Install complete"
