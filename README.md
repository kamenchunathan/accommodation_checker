# Accomodation App checker

=======

A simple python script that polls my school site checking for a form
which means that application has opened and sends an SMS message to my personal number

The script can be launched by running 

```sh
docker build -t accommodation_checker . \
    && docker run \
    -v "$(pwd)"/logs:/app/logs \
    --name spitting_mathers \
    --env-file .env \
    accommodation_checker 
 ```
