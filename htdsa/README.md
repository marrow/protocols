# HTTP Digital Signature Algorithm

> Draft 2015-18-B

A light-weight digital signature algorithm for cryptographic verification of HTTP requests and responses, secured RPC, and SSO.


## Abstract

This document specifies an experimental and simplified HTTP digital signature algorithm for requests and responses designed to protect against common attacks and provide the fundamental layer for authorized API access and account authentication/authorization.


## Introduction

This document describes a pre-exchanged public/private digital signature algorithm used to authenticate HTTP requests from known third parties, and for those third parties to authenticate the HTTP response returning from the server.  Special attention has been paid to MITM attacks: mitigated through the use of end-to-end SSL/TLS channel encryption with verified certificates in addition to dedicated client-server signing key pairs.


## Rationale and Goals

Existing technologies exist which purport to increase security while individually handling authentication (OpenID), authorization (OAuth), or a mixture of the two (OAuth 2).  The problem with these technologies is that of design-by-committee.  The major influencers of these standards has been enterprise, which generally means they're severely over-engineered, hideously difficult to configure securely, and exhibit bugs which result in multiple incompatible independent implementations, most notably with OAuth 2.  Additionally, because of the taint of enterprise added to those committees, the standards tend to be kitchen sinks of various proposals: OAuth 2 includes support for SASL.

The problems with these "entrenched" standards include the fact that one of the core authors of OAuth 2 left the project and had his name stripped from all documents on the way out.  He has a good presentation on some of the failures of the protocol.

This proposal covers the primary use cases (starting with authenticated API/RPC calls) of these more complicated protocols, while excluding features that have been better implemented in other standards, such as OAuth 1's use of custom data encryption (in addition to the typical use of SSL/TLS) and without the complexity that results in OAuth 2's 70+ page security analysis whitepaper and multiple (incompatible) hot fix implementations, such as Facebook's, Google's, Yahoo!'s, and Twitter's.

JSON Web Tokens (JWT) suffer from [some pretty extreme issues](https://auth0.com/blog/2015/03/31/critical-vulnerabilities-in-json-web-token-libraries/) and is similarly over-engineered, requiring expansive trees of logic to be compatible, allowing a signature algorithm of "none", giving control over the choice of algorithm to the attacker, sports an extensive list of algorithms, and requires some truly silly Base64-encoded JSON blobs.

SAML is an insanely complex XML and X.509-based protocol.  This protocol is effectively a restricted subset of SAML in terms of how it operates, without any of that XML overhead.


## Application (Client) Implementation Details

An application is any third-party software which wishes to issue RPC/API calls against a server utilizing this protocol.  Applications must:

1. Generate and securely store a 256-bit ECDSA key and store information as indicated by the authentication/authorization process.
   1. Use the NIST curves.
   2. Use the SHA-256 hashing algorithm.
   3. Share the public key with the server out-of-band, generally through a web interface.
2. On each request:
   1. Perform request canonicalization by combining (using UNIX newlines) the following:
      1. The request's HTTP method, upper-case, e.g.: `GET`
      2. The request's `Date` header.  The request will be rejected outright by the server if the `Date` header is out-of-bounds by more than 30 seconds using an atomic-synchronized (NTP) clock.
      3. The request URI, e.g.: `https://example.com/api/endpoint`
      4. The HTTP request body.
   2. Submit the HTTP request with two additional HTTP headers:
      1. `X-Service` — the unique identifier assigned to your application when exchanging keys.
      2. `X-Signature` — the result of digitally signing the aforementioned canonicalized data.  May, depending on client and server capabilities, be sent as a chunked transfer HTTP header trailer.  The signature should be hex encoded.
   3. Verify the response `X-Signature` header using the pre-exchanged application-specific public key.
   4. Discard responses which do not validate.


## Server Implementation Details

A server is any software service which wishes to respond to RPC/API calls from applications utilizing this protocol.  Servers must:

1. Maintain a database of registered applications and their public keys.
2. Generate and securely store a 256-bit ECDSA public/private key pair unique to each registered application.
   1. Use the NIST curves.
   2. Use the SHA-256 hashing algorithm.
   3. Share the public key of this pair with the client out-of-band, generally through a web interface.
3. Before processing the request:
   1. Ensure the `X-Service` and `X-Signature` keys are present.
   2. Validate the `X-Signature` against the canonical data as defined in the application section.
4. After processing the request:
   1. Ensure the returned data is either empty or valid JSON data.
   2. Canonicalize the response by combining (using UNIX newlines) the following:
      1. The requesting service ID, from the `X-Service` header.
      2. The HTTP method of the request, upper-case.
      3. The response's `Date` header.
      4. The request's endpoint URI.
      5. The response body.
   3. Add an `X-Signature` header that is the result of signing the canonical data using the application-specific server key.
5. Discard requests which fail validation by returning a `400 Bad Request` status code with explanation string in the body.


## Implementations

The official implementation of the above protocol in Python is available from this package.  A [PHP implementation](https://github.com/marrow/htdsa-php/) is also available.

Additional implementations may be available.


##  Old Links

* [Semi-RFC for header/body signatures of HTTP requests.](https://gist.github.com/amcgregor/db76655c47b5f550dee0)
* [Example implementation in Python.](https://gist.github.com/amcgregor/12d79d2cfb039275b337)
