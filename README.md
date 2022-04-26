# infracost-terraform-docker

# Aim
Allows infracost to be used as part of a Keptn continuous delivery workflow such as the following. The infracost metrics are generated in the `costcompliance` step and pushed to a backend (currently supports Dynatrace) then the Keptn quality gate can use those metrics in the `evaluation` step to pass / fail the run:

```
apiVersion: "spec.keptn.sh/0.2.2"
kind: "Shipyard"
metadata:
  name: "shipyard-sockshop"
spec:
  stages:
    - name: "dev"
      sequences:
        - name: "delivery"
          tasks:
            - name: "costcompliance"
            - name: "deployment"
              properties:
                deploymentstrategy: "blue_green_service"
            - name: "test"
              properties:
                teststrategy: "functional"
            - name: "evaluation"
            - name: "release"
```

## Details

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
