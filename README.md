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

Comments that tag a particular user using the `user@example.com` syntax will
have the text changed to `user-at-example.com` to avoid re-tagging the user.

Any comments that do fail will generate a log message that can be used to
manually copy the remaining files:

NOTE: There are two special paths that can be used:

1. `/` indicates the root folder, which is all files that are findable in My Drive.
2. `.` indicates all files, including those that are not in the root folder.  This includes files that are shared with you but haven't been "added" to My Drive.

It's trivial to add additional options to handle some of those variations, but as a general recommendation if you're moving files from one account to another, move all of the files in the originating account into a directory, share that directory with the new account, and then `duplicate.py old_account_dir Backups/`.  This will create a new tree owned by the authorized user.

```
MISSING COMMENTS: Salary and Scouting Datapoints: 1GgYidkrTnAvKtS0Cf_Ada9WgOdVQaQiVQhzC9-kE3UU => 1iKGtGdCFJlKeShqr8uUfI8rYFj4qivYVo59kc9-ZzqQ, anchor: {"type":"workbook-range","uid":0,"range":"371362317"}
```

The UI now allows comments to be copied (preserving attestation), so that's the
preferred way of resolving MISSING COMMENTS files.

The published API may, in the future, be good enough to actually copy a file,
but for now it's pretty minimal.
