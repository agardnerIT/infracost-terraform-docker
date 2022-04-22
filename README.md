# infracost-terraform-docker

Python base container with:

- requests module
- pyyaml module
- infracost CLI
- terraform CLI

## Known Improvements / Changes
- Logic to create generic topology entities in Dynatrace should live as a seperate docker image and / or be in Monaco and / or be on the [dynatrace-service](https://github.com/keptn-contrib/dynatrace-service)
- Logic to push metrics to Dynatrace should be as a seperate docker image and / or as a capability of the [dynatrace-service](https://github.com/keptn-contrib/dynatrace-service)

## Build
```
docker build -t gardnera/python:infracostv1 .
```
