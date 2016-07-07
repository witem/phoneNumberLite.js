'use strict';

const phoneNumberMetadata = require("./meta/PhoneNumberMetadata.js");
const phoneNumber = require("./lib/main.js")(phoneNumberMetadata);

module.exports = phoneNumber;