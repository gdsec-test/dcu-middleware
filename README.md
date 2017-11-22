# DCUMiddleware

This set of classes is responsible for processing data created from the DCU REST API, 
and enriching the report information, and routing the report to the appropriate brand service[s].
The metadata generated and saved is only used internally to assist the DCU team.

## Cloning
To clone the repo, use git, and set up a python virtualenv:
```
git clone git@github.secureserver.net:ITSecurity/dcumiddleware.git
virtualenv virt_dcumiddleware
source virt_dcumiddleware/bin/activate
cd dcumiddleware
```

## Installing Dependencies
Install private pips and main project dependencies:
```
pip install -r private_pips.txt
pip install -r requirements.txt
```
If you also wish to run test suites, install the test dependencies:
```
pip install -r test_requirements.txt
```

## Building
To build an Ubuntu 16.10 based Docker container for development run:
```
make dev
```
Similiar targets exist for ote and prod.

## Deploy
To deploy the container to kubernetes run one of the deploy targets
```
make [prod,ote,dev]-deploy
```

## Testing
To run all tests
```
nosetests
```

## Built With
This project utilizes Celery, as well as the internal projects dcdatabase, cmap_service, and blindAl