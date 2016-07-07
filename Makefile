all: PhoneNumberMetadata.js

%.js: %.xml meta/xml2meta.py
	python meta/xml2meta.py meta/$< > meta/$@

PhoneNumberMetadata.xml:
	curl https://raw.githubusercontent.com/googlei18n/libphonenumber/master/resources/PhoneNumberMetadata.xml > meta/$@

clean:
	rm -f meta/PhoneNumberMetadata.xml 

test:
	@node tests/test.js