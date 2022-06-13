# disunity

Python framework for Discord interactions using a web server

# Installation
`pip install disunity`

# Introduction to Disunity
```python
import disunity

server = disunity.DisunityServer()

if __name__ == '__main__':
    server.run()
```

Using packages
```python
import disunity
import pathlib

server = disunity.DisunityServer()

@server.before_serving
def load_packages():
    for package in [f"{f.parent}.{f.stem}" for f in pathlib.Path("packages").glob("*.py")]:
        server.load_package(package)

if __name__ == '__main__':
    server.run()

```

# Setting up a package

```python
from disunity import package, utils

class FirstPackage(package.Package):
    def __init__(self, app):
        self.app = app

    @package.Package.command('ping', utils.SLASH_COMMAND)
    async def ping(self, ctx):
        return await ctx.callback("Pong!")

def setup(app):
    app.register_package(FirstPackage(app))

```

# Disclaimer

This will require that you already have hosting service for the server to run on as well as a domain to host the server on. If you have neither of these, an alternative would be to host on Heroku using a web application with Gunicorn. 

# Side note

The server will receive interactions to the `/interactions` endpoint of your server. It will look like this: `https://example.com/interactions`. Once you run the server, put the url with the added interactions endpoint into the `interactions` URL on your app located in the Discord developer portal.

