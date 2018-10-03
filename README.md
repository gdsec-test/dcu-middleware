# DCUMiddleware

This set of classes is responsible for processing data created from the DCU REST API, enriching the report information, and routing the report to the appropriate brand service[s].
The metadata generated and saved is only used internally to assist the DCU team.

## Cloning
To clone the repository via SSH perform the following
```
git clone git@github.secureserver.net:ITSecurity/dcumiddleware.git
```

It is recommended that you clone this project into a pyvirtualenv or equivalent virtual environment.

## Installing Dependencies
To install all dependencies for development and testing simply run `make`.

## Building
Building a local Docker image for the respective development environments can be achieved by
```
make [dev, ote, prod]
```

## Deploying
Deploying the Docker image to Kubernetes can be achieved via
```
make [dev, ote, prod]-deploy
```
You must also ensure you have the proper push permissions to Artifactory or you may experience a `Forbidden` message.

## Testing
```
make test     # runs all unit tests
make testcov  # runs tests with coverage
```

## Style and Standards
All deploys must pass Flake8 linting and all unit tests which are baked into the [Makefile](Makfile).

There are a few commands that might be useful to ensure consistent Python style:

```
make flake8  # Runs the Flake8 linter
make isort   # Sorts all imports
make tools   # Runs both Flake8 and isort
```

## Built With
This project utilizes Celery, as well as the internal projects dcdatabase and CMAP Service.

## Running Locally
If you would like to run the dcumiddleware service locally, you will need to specify the following environment variables:
1. `sysenv` (dev, ote, prod)
2. `SERVICE_URL` (URL for accessing CMAP service)
3. `DB_PASS` (Password for MongoDB)
4. `BROKER_PASS` (Password for Celery)

You may also need to configure settings.py and celeryconfig.py to specify additional MongoDB and Celery settings.

DCU Middleware can then be run locally by running `python run.py`