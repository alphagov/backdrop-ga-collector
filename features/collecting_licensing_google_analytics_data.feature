Feature: Collecting licensing google analytics data
    In order to get information about the user journey
    As a service manager
    I want to send the data to the performance platform


    Scenario: Should get user journey start and end data
        Given Google Analytics returns "response_one.json" as response
         When I run the collector with "<query config>" "<start date>" "<end date>"
         Then it should post to "<licensing bucket>":
            |{ "_start_at": ""}|
            |{ "_start_at": ""}|
            |{ "_start_at": ""}|
          And it should exit with a success status


    Scenario: Should not post data when google analytics returns an empty response
        Given Google Analytics returns an empty response
         When I run the collector with "<query config>" "<start date>" "<end date>"
         Then it should not post the data to "<licensing bucket>"
          And it should exit with a success status



    # Should we test for corner cases in feature tests
    Scenario: Should not post data and record an error when Google Analytics returns invalid data 
        Given Google Analytics returns an invalid response                     # what does this mean?
         When I run the collector with "<query config>" "<start date>" "<end date>"
         Then it should not post the data to "<licensing bucket>"
          And it should exit with a failure status


    Scenario: Should log an error if it fails to send data to write api
        Given Google Analytics returns "response_one.json" as response
         When I run the collector with "<query config>" "<start date>" "<end date>"
          And the post fails
         Then it should exit with a failure status
