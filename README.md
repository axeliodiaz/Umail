Umail
=====

Este proyecto tiene como objetivo fundamental implementar un software administrativo como herramienta en el proceso de la comunicación entre los distintos departamentos de la Universidad Nacional Experimental de los Llanos Centrales Rómulo Gallegos. Esta investigación será concebida bajo la modalidad de proyecto especial de grado, sustentando en una investigación de campo de tipo descriptivo y de tipo no experimental, apoyada en una revisión documental. Para la recolección de los datos se utilizarán las técnicas de entrevistas abiertas estructuradas y no estructuras para una observación directa y, como instrumento el cuestionario. Las técnicas de análisis a utilizar serán cuantitativas y cualitativas. El análisis del sistema actual permitió conocer el problema existente con el máximo detalle posible, detectando así deficiencias en la manera en la cual se emiten los memorándums en las distintas oficinas administrativas; problemática que solventa el desarrollo e implementación de un software que complemente la interactividad entre los departamentos a distancia y de manera privada a través de una cuenta personal para cada uno de los entes pertinentes. El sistema será desarrollado bajo el lenguaje Python en el framework Django utilizando un motor de base de datos PostgreSQL.


## Despliegue (Render free) / Deployment

Python 3.12, Django 6.1, PostgreSQL (the inbox uses `DISTINCT ON`, so SQLite is not supported).
`render.yaml` defines a free web service and a free Postgres database; `scripts/render_build.sh` installs, migrates and loads the demo fixtures.
Configuration comes from environment variables: `DATABASE_URL`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_DEBUG`.

Outbound mail uses [django-anymail](https://anymail.dev/en/stable/esps/resend/) with the Resend HTTPS API when `RESEND_API_KEY` is set (`EMAIL_BACKEND=anymail.backends.resend.EmailBackend`). Without that key, Django uses the console email backend so local and demo runs do not send real messages. Set `DEFAULT_FROM_EMAIL` if needed (default: `Umail <noreply@mail.axeldiaz.com>`). Legacy `EMAIL_HOST_*` variables are not used for sending when Resend is configured.
