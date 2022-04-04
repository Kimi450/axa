# axa
Get axa quotes automatically with certain assumptions.

# Build

#### To build a helm chart:
```
docker build -t <USERNAME>/<REPO> .
docker push <USERNAME>/<REPO>:<VERSION>
cd charts
helm install <RELEASE_NAME> .
```
or edit the below file and run it
```
./build_and_install.sh
```

#### To test:
```
docker build -t kimi450/axa-test . && docker run --rm -p 8000:8000 kimi450/axa-test
```

# Usage
```
usage: axa [-h] [--annual-distance ANNUAL_DISTANCE] [--first-name FIRST_NAME] [--last-name LAST_NAME] [--date-of-birth DATE_OF_BIRTH] [--phone-number PHONE_NUMBER] [--email EMAIL] [--occupation OCCUPATION] [--eir-code EIR_CODE] [--license-held LICENSE_HELD]
           [--registrations [REGISTRATIONS [REGISTRATIONS ...]]] [--prometheus-client-port PROMETHEUS_CLIENT_PORT] [--config-file CONFIG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --config-file CONFIG_FILE
                        Config file instead of inputting all the required parameters

group_args:
  Group of required arguments if no config file is provided

  --annual-distance ANNUAL_DISTANCE
                        Annual distance driven (exactly as seen on the website)
  --first-name FIRST_NAME
                        Your first name
  --last-name LAST_NAME
                        Your last name
  --date-of-birth DATE_OF_BIRTH
                        Your date of birth in format yyyy-mm-dd
  --phone-number PHONE_NUMBER
                        Your phone number
  --email EMAIL         Your email ID
  --occupation OCCUPATION
                        You occupation (exactly as seen on the website)
  --eir-code EIR_CODE   Your eircode
  --license-held LICENSE_HELD
                        Time license held for (exactly as seen on the website)
  --registrations [REGISTRATIONS [REGISTRATIONS ...]]
                        Registrations of cars to get quotes for
  --prometheus-client-port PROMETHEUS_CLIENT_PORT
                        Port at which the Prometheus client server runs
```

# Website form information
|Question|Assumption|Comments|
|--|--|--|
|Do you know the car's registration number?|YES|Non-configurable|
|Registration number||Configurable. Example: `08C100`|
|Is this your car|YES|Non-configurable|
|Will this car be used for business purposes?|NO|Non-configurable|
|Will this car be used for commuting to work?|YES|Non-configurable|
|How many kilometres do you drive per year?||Configurable, exactly as seen on the website. Example: `Up to 10,000 km`|
|Title|MR|Non-configurable|
|First Name||Configurable. Example: `John`|
|Last Name||Configurable. Example: `Doe`|
|Date of birth||Configurable. Example: `1950-12-25`|
|Email address||Configurable. Example: `email@email.com`|
|Phone number||Configurable. Example: `0899999999`|
|What is your employment status?|EMPLOYED|Non-configurable|
|What is your occupation?||Configurable, exactly as seen on the website. Example: `Software Developer`|
|Please enter your address or Eircode||Configurable. Example: `T11WDL1`|
|What type of household do you live in?|RENTED ACCOMODATION|Non-configurable|
|Choose your current driving licence|ROI (PROVISIONAL)|Non-configurable|
|Have you completed the Essential Driver Training?|NO|Non-configurable|
|How long have you held this license?||Configurable, exactly as seen on the website. Example: `Less than 1 year`|
|Do you have any penalty points?|NO|Non-configurable|
|What was your most recent insurance?|NO PREVIOUS INSURANCE|Non-configurable|
|Do you or anyone living at your address have another policy insured with AXA?|NO|Non-configurable|
|I have read and accept the assumptions.|CHECKED|Non-configurable|

# Metrics
Need to bring up the `ServiceMonitor` CRD in the same namespace of prometheus.