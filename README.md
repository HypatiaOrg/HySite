# HySite

A website and database for elemental abundance measurements of the [HypatiaCatalog.com](https://hypatiacatalog.com). 
This is a multi-service repository that contains all the data-sciences, API, and web development code.

Our documentation is at [GitHub wiki](https://github.com/HypatiaOrg/HySite/wiki). 
See this for installing and running this repository.

To report a bug or request and upgrade see [Issue Reports and Feature Requests](https://github.com/HypatiaOrg/HySite/issues)

For all interactions, be aware of our [Code of Conduct](https://github.com/HypatiaOrg/HySite/blob/main/CODE_OF_CONDUCT.md),
which is based on the [Contributor Covenant](https://www.contributor-covenant.org/). 
We are providing services beacuse we love astronomy and data, so please be respectful and kind to yourself as well as others so we can build something together.

Our [Apache 2.0 License](https://github.com/HypatiaOrg/HySite/blob/main/LICENSE), we welcome you to fork our repository and make your own version of our code.

## How the server deploys this

The production server pulls `main` weekly and deploys it only after a test: the job lives in the server's
repository, HyRoute (`update/update.sh`), and uses this repository's own tools, `scripts/refresh_versions.py`
for the newest images and packages (written to `versions.env` and the `requirements.lock` files, which git
ignores), `compose.test.yaml` with the sample database for the test stack, and `scripts/smoke_test.py` for
the checks. The wiki page "Keeping the server up to date" explains the job; to run it now on the server:
`~/HyRoute/update/run.sh`.
