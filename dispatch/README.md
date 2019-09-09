One of the principal aspects of a web application framework is the process of resolving a URL to some _thing_ which can either process the request or that represents the resource at that address. The process of translating “paths” into “objects” is, however, universal and not restricted to the web problem domain.

**Document Version:** 1.2 (20190908)

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

The mechanisms of dispatch are nearly universal, centered around a few primary designs:

* **Object dispatch** is a filesystem-like dispatcher that considers classes or class instances as directories, and attributes on those instances as “files”. Frameworks such as [TurboGears](https://turbogears.readthedocs.io/en/tg2.3.12/turbogears/controllers.html#writing-controllers) make principal use of this method of dispatch (though with explicit “exposing” of methods to permit access to from the web) and this is the de-facto standard in WebCore. It primarily involves repeated calls to `getattr()`, and can be overridden using the standard Python object model: [`__getattr__` and friends](https://docs.python.org/3/reference/datamodel.html#customizing-attribute-access). Please see the [web.dispatch.object](https://github.com/marrow/web.dispatch.object) project for details. 

* **URL routers** generally utilize lists or trees of regular expressions to directly match routes to endpoints. This is the standard for frameworks such as Pylons, Flask, and Django. These routers act as registries of known endpoints, allowing for bidirectional lookup. Most frameworks utilize _O(routes)_ worst-case complexity routers—returning a 404 after matching no routes, but after having evaluated them all—and some even iterate all routes regardless of success to detect unintentional multiple matches. WebCore 2 offers a *highly* efficient tree-based _O(depth)_ best- _and_ worst-case router implementation in the [web.dispatch.route](https://github.com/marrow/web.dispatch.route) package. 

- **Traversal** descends through mappings (dictionaries in Python) looking up each path element via dictionary `__getitem__` access and, like object dispatch, represents a filesystem-like view. This is a principal dispatcher provided by the Pyramid framework. We have an implementation of [the process](http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html) in the [web.dispatch.traversal](https://github.com/marrow/web.dispatch.traversal) package. See also: [much ado about traversal](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/muchadoabouttraversal.html).

* **REST dispatch** uses the HTTP verb present in a web request to determine which endpoint should be utilized; this is often baked into the URL router in other implementations, but is distinct under this protocol.  An example implementation compatible with WebOb `request` attributes on the context (i.e. WebCore) is available in the [web.dispatch.resource](https://github.com/marrow/web.dispatch.resource) package.

An unusual case can arise in non-web contexts:

* **Command-line argument parser as dispatch.**  What is a command-line `argv` but a dispatchable/traversable path, intermixed with named and positional arguments to collect?

In order to provide a uniform interface for the consumption of paths in "processed parts", as well as to allow for the easy migration from one dispatch method to another as descent progresses, this page serves as documentation for both the dispatcher event producer and framework consumer sides of this protocol.

Additionally, as of revision 1.2 of this protocol, a mechanism is exposed to introspect a dispatchable hierarchy. Paths of descent may be probed for reachable leaves, and access properties of those leaves as may be useful to service an HTTP `OPTIONS` request, or to generate documentation or interfaces at runtime.


## Design Goals

This protocol exists for several reasons, to:

* **Reduce recursion.** Deep call stacks make stack traces harder to parse at a glance and increases memory pressure. It's also entirely unnecessary.

* **Simplify frameworks.** Many frameworks reimplement these processes; dispatchers are a form of lowest common denominator. Such development effort would be more efficiently spent on a common implementation, similar to the extraction of request/response objects and HTTP status code exceptions in [WebOb](http://docs.webob.org) or [Werkzeug](https://werkzeug.palletsprojects.com).

* **Alternate uses.** Web-based dispatch is only one possible use of these. They can, in theory, be used to traverse any object, dictionary-alike, or look up any registered object against a UNIX-like path, or simple iterable of strings, from any source. There are undoubtedly uses which the author of this document has not envisioned. 

* **Rapid development cycle.** Isolation of individual processes into their own packages allows for feature addition, testing, and debugging on different timescales than full framework releases.


## Terminology

This protocol makes use of a fairly broad set of distinct terminology.  Where these terms appear in this document, they should be interpreted using these definitions.

* **Consumer**, code which iterates a dispatcher making use of the intermediary or, optionally, only the final events.

* **Crumb**, a yielded artifact (a named tuple) representing a step in dispatch, as yielded by a _producer_ and utilized by a _consumer_, possibly mutated or replaced by _middleware_.

* **Dispatch**, the process of looking up an object using a path.

* **Dispatch context**, the “current object under consideration”. In object dispatch and traversal this would likely be the object to descend through. In routing dispatchers, this may be the route registry. For database-driven dispatchers, this may be `None`, as an example.

* **Dispatch middleware**, a dispatcher whose purpose is to manage other dispatchers. Examples would include implementations of fallbacks, context-based dispatcher selection, and dispatch chains. Must speak and understand both sides of the protocol, as a mediator between a consumer and producer.

* **Endpoint**, the final, resolved object matching the given path. Dispatch terminates when reaching an endpoint.

* **Midpoint**, any of the intermediary dispatch steps.

* **Producer**, a callable producing an iterable of dispatch events.

* **Terminus**, the point at which a dispatcher has given up. This is an adjective to use with “endpoint” and “midpoint”, for example, a “terminus midpoint” or “terminating midpoint” is one where the dispatcher has processed some path elements, but for some reason is no longer able to proceed.

## Framework Flow

A given web framework (or other library making portable re-use of Dispatch) SHOULD provide a mechanism to register callbacks (or "listeners") to handle certain events.  The recommended minimum set:

* Notify that dispatch is being prepared, prior to invoking the dispatcher, which itself may instantiate or otherwise manipulate the hierarchy.

* Notify on each dispatch event generated, as we “visit” each midpoint during descent.

* Notify that dispatch is complete and has resolved a given object. (Or failed to resolve an object.)


## Dispatch Events

**Changed in 1.2.**

Dispatch events are represented by 6-element named tuples with the following components:

```python
(dispatcher, origin, path, endpoint, handler, options)
```

* A reference to the `dispatcher` instance that generated the event.

* The dispatch `origin`, or initial object upon which dispatch was attempted. The "root" of the hierarchy.

* The `path` element or elements that were consumed (or None) during this step of dispatch, represented by a PurePosixPath.

* A flag identifying if this event is the terminus, that the `endpoint` has been found.

* An object representing the current _dispatch context_ or endpoint, to be passed to the next dispatcher in the event of a transition, or used as the result.

* A final contained value, `options`, may be determined by context. On the web, this would be a literal `set` of valid HTTP verbs for this endpoint for use in servicing an `OPTIONS` request. Reference the individual dispatchers for more information on the uses of this attribute.  (Other information about the endpoint can be probed from the `handler` directly via the [`inspect` module](https://docs.python.org/3/library/inspect.html).)

A compatible implementation is provided in the `web.dispatch` helper package, importable via `from web.dispatch.core import Crumb`.

It is extremely important to maintain division of labour among different dispatch mechanisms. If you find yourself with a hybrid need, please consider writing two separate dispatchers and a meta-dispatcher (a.k.a. "dispatcher middleware") to join them; this may reveal that the process to select between two (or more) dispatchers stands on its own. Signs you wish to consider this may include, but aren't limited to: relying on a series of consecutive loops and deep nesting.


## Dispatch Event Producers

Dispatchers are callable objects (such as functions, or classes implementing `__call__`) that:

* **Must** accept only two required, positional arguments: 

	* An object representing the current processing context. This will generally be the web framework’s context or request object. 

	* The object to perform dispatch upon. For some configurations or dispatchers, this may be `None`. Generally referred to as the _dispatch context_. 

	* A `deque` of remaining path elements to process. A singular leading slash, if present, is stripped from URL paths prior to split to eliminate an empty string from unintentionally appearing. 

* **Must** return an iterable of tuples described in the [Dispatch Events](#dispatch-events) section when invoked.

* **May** be a generator function. The `yield` and `yield from` syntaxes are pretty, efficient, and offer up some interesting possibilities for simplified dispatch middleware / meta-dispatchers.

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


## Tracing Introspection

A substantial addition in revision 1.2 is the addition of a `trace` protocol. Given a dispatchable object, identify what is reachable from there. A simple example using Object Dispatch, where the `None` argument represents the "dispatch context":

```python
>>> def sample(context): ...
>>> list(ObjectDispatch().trace(None, sample))
[Crumb(dispatcher=ObjectDispatch(0x4451111248, protect=True),
	origin=<function sample at 0x109542440>,
	endpoint=True,
	handler=<function sample at 0x109542440>)]
```

Attempting to dispatch on a function, which is by definition an endpoint, results in only one possible destination, the function itself. Notice that the "directory listing" (since this is almost equivalent to performing a `ls` or `dir` on a filesystem directory, or `dir()` call on object) is expressed as Crumbs with relative paths.

```python
>>> class Sample:
>>>     class nested: ...
>>>     def example(self): ...
>>>     def second(self): ...

>>> list(ObjectDispatch().trace(None, Sample))
[Crumb(dispatcher=ObjectDispatch(0x4451111248, protect=True),
	origin=<class '__main__.Sample'>,
	path=PurePosixPath('example'),
	endpoint=True,
	handler=<function Sample.example at 0x109e96170>),
Crumb(dispatcher=ObjectDispatch(0x4451111248, protect=True),
	origin=<class '__main__.Sample'>,
	path=PurePosixPath('nested'),
	endpoint=False,
	handler=<class '__main__.Sample.nested'>),
Crumb(dispatcher=ObjectDispatch(0x4451111248, protect=True),
	origin=<class '__main__.Sample'>,
	path=PurePosixPath('second'),
	endpoint=True,
	handler=<function Sample.second at 0x109abf9e0>)]
```

Note that the tracing produced is not exhaustive; for example, the `nested` class has no members; it _would_ be a terminus if dispatch down that branch is attempted, but a single level trace can't really know that.  Attempting a trace of that branch's `handler` would reveal no results.

### "Dynamic Path Segments"

Paths often contain "variable elements", e.g. `/user/{id}/ping` represents a variable named "id" present within the path.  When tracing, variable elements are possible, and MUST be expressed by dispatchers the using this notation. If there is a known regular expression pattern associated with the variable match, use curly brace notation with the pattern colon-separated from the variable name, e.g. `"{id:[0-9]+}"`.

Object Dispatch provides an example of this when encountering a class implementing a `__getattr__` method.  E.g. if `class Users` implements `def __getattr__(self, id):` then the path segment will be named `"{id}"`.  When utilizing Resource Dispatch, the name would be sourced from the `__getitem__` method, instead.

```python
>>> class Sample:
>>>     def __getitem__(self, potato): ...

>>> list(ObjectDispatch().trace(None, Sample))
[Crumb(dispatcher=ObjectDispatch(0x4451111248, protect=True),
	origin=<class '__main__.Sample'>,
	path=PurePosixPath('{potato}'),
	endpoint=False,
	handler=<function Sample.__getattr__ at 0x1095c5680>)]
```

In these cases the "handler" represents the callable which resolves the variable during dispatch.


## Namespace Participation

Authors of custom dispatchers **should** populate their package or module as a member of the `web.dispatch` namespace. This provides a nice consistent interface and allows for dispatchers within more complex codebases to be clearly separated from other code.

For details on packaging up your project to cooperate in these namespaces, please [see the official Python Packaging documentation on "native namespace packages"](https://packaging.python.org/guides/packaging-namespace-packages/#native-namespace-packages).

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


## Application Use

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
* If the `endpoint` value of the event is `True`, stop iteration; you have found your endpoint.
* If iteration completes before finding an endpoint, or a `LookupError` is raised during iteration, then the dispatcher could not process the given path.

Fallback behaviours, chaining, retry, etc. are best implemented as dispatch middleware, for portability, but may be integrated at the framework consumer level.

# Loading Plugins

To load a dispatcher by name you can utilize the built-in `pkg_resources`:

```python
from pkg_resources import iter_entry_points

Dispatch = iter_entry_points('web.dispatch', 'object')[0].load()
```

You must handle the case of it not existing, and may optionally handle the case of multiple competing implementations existing. The `load()` call will raise an exception if the optional dependencies for the entry point are not met. As a shortcut for plugin management such as the above you can use the [marrow.package](https://github.com/marrow/package) library to handle the case of passing in a dispatcher _or_ a string easily:

```python
from marrow.package.loader import load

Dispatch = load('traversal', 'web.dispatch')
```

Non-string values for the first argument are returned unaltered. The `marrow.package` library provides other plugin management tools that are useful for discovery and management.
