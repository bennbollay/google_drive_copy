# Google Drive API File Copy Tool

Recursively duplicate files in Google Drive as best as the API allows.

Which isn't much.

# Installation

Follow the instructions
[here](https://pythonhosted.org/PyDrive/quickstart.html) for using OAuth2.0
authentication.  Save the `client_secrets.json` file in the current directory.

Install the PyDrive package:

```
$ pip3 install -r requirements.txt
```

# Usage

```
$ python3 duplicate.py src/path path/to/dst
```

It will first authenticate through OAuth2.0, usually using your browser.

The tool will then proceed to copy all of the files, recursively, from `src/path`
to `path/to/dst`.  Comments will, largely, be recreated in doc files but will
probably fail in spreadsheets or slides.  All comments will have the current
authorized user as the originating author, with the original author added to
the text field.

Any comments that do fail will generate a log message that can be used to
manually copy the remaining files:

```
MISSING COMMENTS: Salary and Scouting Datapoints: 1GgYidkrTnAvKtS0Cf_Ada9WgOdVQaQiVQhzC9-kE3UU => 1iKGtGdCFJlKeShqr8uUfI8rYFj4qivYVo59kc9-ZzqQ, anchor: {"type":"workbook-range","uid":0,"range":"371362317"}
```

The UI now allows comments to be copied (preserving attestation), so that's the
preferred way of resolving MISSING COMMENTS files.

The published API may, in the future, be good enough to actually copy a file,
but for now it's pretty minimal.
