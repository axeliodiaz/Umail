web: python manage.py collectstatic --noinput; gunicorn umail.wsgi; python manage.py syncdb; python manage.py migrate; python manage.py loaddata */fixtures/* 
