# Web metric consumer-publisher

- [What it does](#what-it-does)

- [How to run](#how-to-run)
  - [Command line options](#command-line-options)

- [Out of scope](#out-of-scope)

- [Known issues](#known-issues)

## What it does

Implements a service that consumes messages from Kafka broker and sends them 
to postgresql database. Service can be started separately or used like a package.

## How to run

This is a python program, therefore you need Python3.9 for the execution and pipenv of version 2020.11.15 or close
for the creation of virtual environment
To run service with default parameters from shell, go to service project root filder and run:
```console
$pipenv shell
$python3.9 src/service.py
```

### Command line options

Service takes the default values of it's settings from config/service.yaml file and partially from it's own body.
For convenience, there's a possbility to overwrite most of these params using keyword arguments.
To get help, from the project root
```console
$pipenv shell
$python src/service.py --help
usage: service.py [-h] [--topic TOPIC] [--cycles CYCLES] [--sleep SLEEP]

optional arguments:
  -h, --help       show this help message and exit
  --topic TOPIC    topic name to publish, no quotes. Defaults to website-metrics
  --cycles CYCLES  number of cycles to run, infinite if not specified
  --sleep SLEEP    seconds to wait between broker polling, defaults to service.yaml settings
```

## Out of scope

- scaling this service. Although it could be a bottle-neck in a real-life system, it hardly
  makes any sense in this setup. Assumption is that scaling if needed is done by load-balancer
  partially mitigated by sending updates in bursts

- implementation of a consumer service as a microservice. Although in a real system this would support
  scaling and, when combined with message queue, ensure the delivery, this hardly makes sense because of
  over-complication of the setup. It's assumed that service stores messages in RAM and the loss of
  portion of these messages because of service failure is not critical.

- script to set up, configure, run and delete Kafka broker and Postgresql services

- rolling out local kafka service in order to execute integration tests on local environment

- testing kafka consumer with Aiven kafka broker (only done on E2E level)

- full test coverage

## Known issues

- if there's at least one message with corrupted format, the entire readout by consumer-publisher service
  will be rejected by DB and not posted. Not fixed because of lack of time and low importance

- Smoke test for Kafka consumer fails with SSL error. The reason is unclear.
  Possible workaround - to use SASL authentification instead of providing certificates
