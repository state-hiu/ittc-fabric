ITTC Fabric Script (ittc-fabric)
================

## Description

Fabric script for managing ITTC infrastructure.

### CyberGIS
The [Humanitarian Information Unit](https://hiu.state.gov/Pages/Home.aspx) has been developing a sophisticated geographic computing infrastructure referred to as the CyberGIS. The CyberGIS provides highly available, scalable, reliable, and timely geospatial services capable of supporting multiple concurrent projects.  The CyberGIS relies on primarily open source projects, such as PostGIS, GeoServer, GDAL, [GeoGig](http://geogig.org/), OGR, and OpenLayers.  The name CyberGIS is dervied from the term geospatial cyberinfrastructure.

### Imagery to the Crowd
The Imagery to the Crowd Initiative (ITTC) is a core initiative of the [Humanitarian Information Unit](https://hiu.state.gov/Pages/Home.aspx).  Through ITTC, HIU publishes high-resolution commercial satellite imagery, purchased by the United States Government, in a web-based format that can be easily mapped by volunteers.  These imagery services are used by volunteers to add baseline geographic data into OpenStreetMap, such as roads and buildings.  The imagery processing pipeline is built from opensource applications, such as TileCache and GeoServer.  All tools developed by HIU for ITTC, are also open source, such as this repo.

## Installation

Follow directions at http://www.fabfile.org/installing.html to install fabric.  On Ubuntu you can most easily run, `sudo apt-get install fabric`.

You'll also need to install [fabtools](https://github.com/ronnix/fabtools) with `sudo pip install fabtools`.

You'll also need to install [boto](https://github.com/boto/boto), the python AWS library, with `sudo pip install boto`.

Create a `servers.py` file in the same directory as the `fabfile.py`.  `servers.py` is in `.gitignore` so will not be committed.  This file includes connection and other information, so that fab commands are streamlined.

```javascript
ITTC_SERVERS = {
    "frontdoor": {
        "ident":  "~/auth/keys/frontdoor.pem",
        "host": "frontdoor.example.com",
        "user": "ubuntu",
        "name": "Front Door"
    },
    "tilejet": {
        "ident":  "~/auth/keys/tilejet.pem",
        "host": "tilejet.example.com",
        "user": "ubuntu",
        "name": "TileJet Proxy"
    },
    "tileserver_frontend": {
        "ident":  "~/auth/keys/tileserver-frontend.pem",
        "host": "tileserver-frontend.example.com",
        "user": "ubuntu",
        "name": "Tile Server Frontend"
    },
    "tileserver_backend": {
        "ident":  "~/auth/keys/tileserver-backend.pem",
        "host": "tileserver-backend.example.com",
        "user": "ubuntu",
        "name": "Tile Server Backend"
    }
}
```

### AWS

If you'd like to receive notifications after tasks are completed via AWS Simple Notification Service (SNS), you need to create a `aws.py` file in the same directory as below.

```
AWS_SETTINGS = {
    "iam": {
        "testuser": {
            "AWS_ACCESS_KEY_ID": "XXX",
            "AWS_SECRET_ACCESS_KEY": "XXX+XXX"
        }
    }
    "topics": {
        "test":"arn:aws:sns:us-XXX-X:XXX:XXX"
    }
}
```

## Usage

Cd into the main directory with the `fabfile.py`.  When you call fab, start with the name of the server (frontdoor, tilejet, tileserver_frontend, and tileserver_backend) so that the host and identity key are loaded automatically from `servers.py`.

To see a list of tasks run:

```
fab -l
```

To see the long description of a task run:

```
fab -d taskname
```

A few examples:

```
fab frontdoor restart_nginx
fab tilejet restart
fab tileserver_frontend add_cache
fab tileserver_frontend restart_apache
fab tileserver_backend restart_geoserver
fab tileserver_backend upload_files:local=test.txt,drop=~/drop,tries=3,user=ubuntu,group=ubuntu
```

## Contributing

We are currently accepting pull requests for this repository. Please provide a human-readable description with a pull request and update the README.md file as needed.

## License

This project constitutes a work of the United States Government and is not subject to domestic copyright protection under 17 USC § 105.

However, because the project utilizes code licensed from contributors and other third parties, it therefore is licensed under the MIT License. http://opensource.org/licenses/mit-license.php. Under that license, permission is granted free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the conditions that any appropriate copyright notices and this permission notice are included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
