One of the principal aspects of a web application framework is the process of resolving a URL to some _thing_ which can either process the request or that represents the resource at that address. The process of translating “paths” into “objects” is, however, universal and not restricted to the web problem domain.

**Document Version:** 1.0b2 (20154602)

* [Introduction](#introduction)
	* [Design Goals](#design-goals) 
	* [Terminology](#terminology) 

* [Dispatch Events](#dispatch-events) 

* [Dispatch Event Producers](#dispatch-event-producers)
	* [Dispatch Middleware](#dispatch-middleware)
	* [Namespace Participation](#namespace-participation) 
	* [Plugin Registration](#plugin-registration) 
	* [Application Configuration](#application-configuration) 

* [Framework Consumers](#framework-consumers)
	* [Error Handling](#error-handling)


# Introduction

The mechanisms of dispatch are now nearly universal, centered around a few primary designs:

* **Object dispatch** is a filesystem-like dispatcher that treats classes or class instances as directories, and attributes on those objects as “files”. Frameworks such as TurboGears make principal use of this method of dispatch, and this is the de-facto standard in WebCore. It primarily involves repeated calls to `getattr()`, and can be overridden using `__getattr__` and friends. Please see the [web.dispatch.object](https://github.com/marrow/web.dispatch.object) project for details. 

* **URL routers** generally utilize lists or trees of regular expressions to directly match routes to endpoints. This is the standard for frameworks such as Pylons, Flask, and Django. These routers act as registries of known endpoints, allowing for bidirectional lookup. Most frameworks utilize _O(routes)_ worst-case complexity routers—returning a 404 after matching no routes, but checking them all—and some even iterate all routes regardless of success. WebCore 2 offers a *highly* efficient tree-based _O(depth)_ best- _and_ worst-case router implementation in the [web.dispatch.route](https://github.com/marrow/web.dispatch.route) package. 

* **Traversal** descends through mappings (dictionaries in Python) looking up each path element via dictionary `__getitem__` access and, like object dispatch, represents a filesystem-like view. This is a principal dispatcher provided by the Pyramid framework. We have an implementation of [the process](http://docs.pylonsproject.org/projects/pyramid/en/1.4-branch/narr/traversal.html) in the [web.dispatch.traversal](https://github.com/marrow/web.dispatch.traversal) package. 

In order to provide a uniform interface for the consumption of paths in "processed parts", as well as to allow for the easy migration from one dispatch method to another as descent progresses, this page serves as documentation for both the dispatcher event producer and framework consumer sides of this protocol.


## Design Goals

This protocol exists for several reasons, to:

* **Reduce recursion.** Deep call stacks make stack traces harder to parse at a glance and increases memory pressure. It's also entirely unnecessary. 

* **Simplify frameworks.** Many frameworks reimplement these processes; dispatchers are a form of lowest common denominator. Such development effort would be more efficiently spent on a common implementation, similar to the extraction of request/response objects and HTTP status code exceptions in [WebOb](http://docs.webob.org).

* **Alternate uses.** Web-based dispatch is only one possible use of these. They can, in theory, be used to traverse any object, dictionary-alike, or look up any registered object against a UNIX-like path. There are undoubtedly uses which the author of this document has not envisioned. 

* **Rapid development cycle.** Isolation of individual processes into their own packages allows for feature addition, testing, and debugging on different timescales than full framework releases.


## Terminology

This protocol makes use of a fairly broad set of distinct terminology.  Where these terms appear in this document, they should be interpreted using these definitions.

* **Consumer**, code which iterates a dispatcher making use of the intermediary or, optionally, only the final events.

* **Dispatch**, the process of looking up an object using a path. 

* **Dispatch context**, the “current object under consideration”. In object dispatch and traversal this would likely be the object to descend through. In routing dispatchers, this may be the route registry. For database-driven dispatchers, this may be `None`, as an example. 

* **Dispatch middleware**, a dispatcher whose purpose is to manage other dispatchers. Examples would include implementations of fallbacks, context-based dispatcher selection, and dispatch chains. 

* **Endpoint**, the final, resolved object matching the given path. Dispatch terminates when reaching an endpoint. 

* **Midpoint**, any of the intermediary dispatch steps. 

* **Producer**, a callable producing an iterable of dispatch events. 

* **Terminus**, the point at which a dispatcher has given up. This is an adjective to use with “endpoint” and “midpoint”, for example, a “terminus midpoint” or “terminating midpoint” is one where the dispatcher has processed some path elements, but for some reason is no longer able to proceed.


# Dispatch Events

Dispatch events are represented by 3-tuples with the following components:

* The _path_ element or elements being consumed during that step of dispatch. If multiple path elements were consumed in one step, producers **should** utilize a tuple to contain them.

* An object representing the current _dispatch context_ or endpoint, to be passed to the next dispatcher in the event of a transition. 

* A boolean value indicating if the object is the _endpoint_ or not.

It is extremely important to maintain division of labour among different dispatch mechanisms. If you find yourself with a hybrid need, please consider writing two separate dispatchers and a meta-dispatcher (a.k.a. "dispatcher middleware") to join them; this may reveal that the process to select between two (or more) dispatchers stands on its own. Signs you wish to consider this may include, but aren't limited to: relying on a series of consecutive loops and deep nesting.


# Dispatch Event Producers

Dispatchers are callable objects (such as functions, or classes implementing `__call__`) that:

* **Must** accept only two required, positional arguments: 

	* An object representing the current processing context. This will generally be the web framework’s context or request object. 

	* The object to begin dispatch on. For some configurations, this may be `None`. Generally referred to as the _dispatch context_. 

	* A `deque` of remaining path elements. A singular leading slash, if present, is stripped from URL paths prior to split to eliminate an empty string from unintentionally appearing. 

* **Must** return an iterable of tuples described in the [Dispatch Events](#dispatch-events) section.

* **May** be a generator function. The `yield` and `yield from` syntaxes are pretty, efficient, and offer up some interesting possibilities for dispatch middleware / meta-dispatchers.

The basic specification for a callable conforming to the Dispatch protocol would look like:

```python
def terminus(context, obj, path):
	return []
```

Dispatchers **should** to be implemented as a class if they offer configuration:

```python
class Terminus:
	def __init__(self):
		pass  # You would implement a configuration step here.
	
	def __call__(self, context, obj, path):
		return []
```

A PHP example of a minimal dispatcher in both simple function and configured class styles would be:

```php
function terminus($context, $path) {
	return [];
}

class Terminus {
	public function __construct() {
		// Configuration process goes here.
	}

	public function __invoke($context, $obj, $path) {
		return [];
	}
}
```

Your dispatcher may be utilized by framework consumers through direct instantiation, [plugin registration](#plugin-registration), and [application configuration](#application-configuration). Some of these approaches provide methods for configuration, but not all. In the event of a class reference without configuration an attempt will be made to instantiate without one.

In the event your dispatcher is no longer able or willing to process remaining path elements it **must** either return (if it is a generator), or raise `LookupError`. Using `LookupError` provides a convenient way to provide an explanation as to the reason for the failure, useful in logging and diagnostics.


## Dispatch Middleware

Sometimes referred to as “meta-dispatchers”, these are dispatchers whose purpose is to orchestrate other dispatchers. One simplified example is a simple dispatch attempt chain:

```python
class Chain:
	"""Use the result of the first matching dispatcher."""
	
	def __init__(self, chain):
		self.chain = chain
	
	def __call__(self, context, path):
		for dispatcher in self.chain:
			try:
				dispatch = list(dispatcher(context, path))
			except LookupError:
				dispatch = []
			
			if dispatch:
				return dispatch
		
		return []  # Must always return an iterable.	
```

This will evaluate one dispatcher, and if no match was found, continue with an attempt to dispatch on the next in the chain, and so forth.  These consume both sides of the producer/consumer API, and should thus be aware of the processes for both.


## Namespace Participation

Authors of custom dispatchers **should** populate their package or module as a member of the `web.dispatch` namespace. This provides a nice consistent interface and allows for dispatchers within more complex codebases to be clearly separated from other code.

To do this, within your source code tree construct a folder hierarchy of "web" and "dispatch", placing your own package or module under that path. Each directory should contain an `__init__.py` file whose sole contents is the following:

```python
__import__('pkg_resources').declare_namespace(__name__) # pragma: no-cover
```

If your dispatcher is non-business-critical, we encourage you to open source it and let us know so we can include it in a list somewhere!


## Plugin Registration

Register your dispatcher under the de-facto standard namespace `web.dispatch` using something similar to the following in your package's `setup.py` file:

```python
# ...

setup(
	# ...
	entry_points = {
			'web.dispatch': [
					'example = web.dispatch.example:ExampleDispatch',
				],
		}
	)
```

You can define dependencies beyond your overall package's dependencies for the entry point by appending `[label]` to the definition, where the label is one of your choosing, then adding a section to the `extras_require` section in the same file:

```python
# ...

setup(
	# ...
	extras_require = {
			'label': [
					'some_dependency',
				],
		}
	)
```

When installing your package, you can now use the form `package[label]` or `package[label]=version`, etc., and the additional dependencies will be automatically activated and pulled in. The entry point will only be available for use if those additional dependencies are met, though explicit use of the label at package installation time is _not_ required.


## Application Configuration

WebCore configuration. dispatch retry chain, defining custom configured names, use in other protocols, etc. TBD.


# Framework Consumers

Transforming a path into an object usable by your framework is a simple iterable process where frameworks:

* **Must** identify an initial path. 

* **May** identify an initial dispatch context. If none is configured, a literal `None` **must** be provided as the context to the dispatcher. 

* **May** perform any encoding necessary to protect valid path separator symbols within the path elements, then **must** eliminate a singular leading separator from the path, if present. 

* **Should** signal, through some means such as logging output or callbacks, that dispatch has begun, and **may** signal through similar means upon each step of dispatch. 

* **Must** provide the separator split path to dispatchers as a `deque` instance, or `deque` API-compatible object. 

After the above is ready to go, the process becomes:

* Construct the dispatcher if required.
* Call the dispatcher with a basic context and a path.
* Iterate the returned value consuming dispatch events as you go.
* If the third tuple element is `True`, stop iteration; you have found your endpoint.
* If iteration completes before finding an endpoint, or a `LookupError` is raised during iteration, then the dispatcher could not process the given path.

Fallback behaviours, chaining, retry, etc. are best implemented as dispatch middleware, for portability, but may be integrated at the framework consumer level.

# Loading Plugins

To load a dispatcher by name you can utilize the built-in `pkg_resources`:

```python
from pkg_resources import iter_entry_points

Dispatch = iter_entry_points('web.dispatch', 'object')[0].load()
```

You'll must handle the case of it not existing, and may optionally handle the case of multiple competing implementations existing. As a shortcut for plugin management such as the above you can use the [marrow.package](https://github.com/marrow/package) library to handle the case of passing in a dispatcher _or_ a string easily:

```python
from marrow.package.loader import load

Dispatch = load('traversal', 'web.dispatch')
```

Non-string values for the first argument are returned unaltered. The `marrow.package` library provides other plugin manangement tools that are useful for discovery and management.
