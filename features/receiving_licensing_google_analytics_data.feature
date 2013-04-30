Feature: Receiving licensing google analytics data
	In order to get information about the user journey
	As a service manager
	I want to send the data to the performance platform


	Scenario: Should understand licensing google analytics data
		Given I have the data in "<licensing_ga_data.json>"
	     when I post the data to "/licensing"
	     Then I should get back a status of "200"


	      and  the stored data should contain "<count_of_the_number_of_items>" "<key_of_item>" equaling "<val_of_item>"
		
			