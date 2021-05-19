# Web metric consumer-publisher

- [What it does](#what-it-does)
- [Out of scope](#out-of-scope)
- [Known issues](#known-issues)
- [ToDo](#todo)

## What it does?
Implements a service that consumes messages from Kafka broker and sends them 
to postgresql database. Service can be started separately or used like a package.

## Out of scope
- scaling this service. Although it could be a bottle-neck in a real-life system,
it hardly makes any sense in this setup. Assumption is that scaling if needed is done by load-balancer
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

## ToDo:
- create CI for unit test execution
- create CI for integration test execution (?)
