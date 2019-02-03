mockdock
========
[![Build Status](https://travis-ci.org/jensstein/mockdock.svg?branch=master)](https://travis-ci.org/jensstein/mockdock)

```mockdock``` is a dns resolver and http server usable for testing
containers.

```mockdock``` can be used with the ```--dns``` argument for ```docker
run```. It can be set to resolve all dns requests to itself, thereby
constituting a mock server for all dns-based http requests of the
container under test.

The ```integration_test``` module under the tests directory serves as
practical documentation of how ```mockdock``` can be used in a test
scenario with a docker container.

format
------

Responses to http requests are specified as json in the format
```json
{
	"domain.tld/path": {
		"data": "response data",
		"content-type": "text/plain",
		"code": 200
	},
	"domain.tld/path2": {
		"code": 500
	}
}
```
All elements in the structure are optional with the missing elements
defaulting to the values set by the HttpResponse class in the
mockdock.server module.
The response data can be passed to the server directly in the
```CONFIG_DATA``` variable or in a file with the path passed in
the ```CONFIG_PATH``` variable. The two variables are mutually
exclusive, so they cannot both be specified at the same time.
