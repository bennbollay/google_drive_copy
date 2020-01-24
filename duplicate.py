#!/usr/bin/env python3
import sys

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import googleapiclient


class NoRoot:
    """Utility class to reference files that have no root object."""
    pass


def get_files(fn, parent_id=None):
    """
    Return the files that match the path specified.  If parent_id is not
    specified, find any file that matches the filename.
    """
    if parent_id:
        qry = f"'{parent_id}' in parents and title = '{fn}' and trashed=false"
    else:
        qry = f"title = '{fn}' and trashed=false"

    file_list = drive.ListFile({'q': qry}).GetList()
    return file_list

def get_rootless_files():
    """
    A brutal query; get all the files, and select only the ones that have an
    empty parent array.
    """
    qry = "trashed=false"

    file_list = [f for f in drive.ListFile({'q': qry}).GetList() if len(f['parents']) == 0]
    return file_list


def get_only_one_file(fn, parent_id=None):
    """
    Utility function to error out if multiple files matching that name are
    found at a given location.
    """
    files = get_files(fn, parent_id)
    if len(files) > 1:
        print(f"Ambiguous path: '{path[1]}', quitting")
        sys.exit(-1)
    elif len(files) == 0:
        return None
    
    return files[0]


def get_all_files(parent_id):
    """
    Get all of the files that have the specified parent_id that are not directories.
    """
    qry = f"'{parent_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
    return drive.ListFile({'q': qry}).GetList()


def get_all_dirs(parent_id):
    """
    Get all of the directories that have the specified parent_id that are not files.
    """
    qry = f"'{parent_id}' in parents and trashed=false and mimeType = 'application/vnd.google-apps.folder'"
    return drive.ListFile({'q': qry}).GetList()


def is_dir(f):
    """
    Utility function to test if something is a directory.
    """
    return f['mimeType'] == 'application/vnd.google-apps.folder'


def get_path(path):
    """
    Walk a specified path, returning the leaf node.
    """
    if len(path) == 1:
        if path[0] == '':
            # Return the root object
            return drive.CreateFile({'id': 'root'})
        if path[0] == '.':
            # Return a NoRoot() object
            return NoRoot()

    # Things can either be under 'root', or they have an empty parent list for
    # things like shared folders.
    #
    # Try the ones with the parent first.
    file1 = get_only_one_file(path[0], 'root')

    if file1 is None:
        # If that didn't work, try the ones that are shared or have no parent.
        file_list = [f for f in get_files(path[0]) if len(f['parents']) == 0]
        if len(file_list) > 1:
            print(f'Ambiguous path {path[0]}, quitting')
            sys.exit(-1)
        elif len(file_list) == 0:
            print(f'Unable to find {path[0]}, quitting')
            sys.exit(-1)

        file1 = file_list[0]

    parent_id = file1['id']
    path = path[1:]

    for p in path:
        # Walk the rest of the tree.
        file1 = get_only_one_file(p, parent_id)
        if file1 is None:
            # Requested file wasn't found
            return None
        parent_id = file1['id']

    return file1


def get_files_recursive(path):
    """
    Get all of the files at the specified path and lower.
    """
    results = {}

    # Start with the root
    root_entry = get_path(path)

    # Asking for all of the files, even ones without a parent object
    if type(root_entry) == NoRoot:
        results['__rootless__'] = rootless = {}

        # Get all of the files that don't root off of 'root', like ones shared
        # with the user
        files = get_rootless_files()

        # Walk through the files, adding or recursing as appropriate.
        for entry in files:
            if is_dir(entry):
                rootless[entry['title']] = get_files_recursive_by_id(entry)
            else:
                rootless[entry['title']] = entry
        root_entry = drive.CreateFile({'id': 'root'})
    elif not is_dir(root_entry):
        return {'/'.join(path): root_entry}
    
    # Get all of the sub directories.
    results['/'.join(path)] = get_files_recursive_by_id(root_entry)

    return results


def get_files_recursive_by_id(root_entry):
    """
    Walk the tree starting from a specified root node, collecting
    all of the files that hang from those entries.
    """
    results = {'.': root_entry}

    # Get the files
    for file1 in get_all_files(root_entry['id']):
        results[file1['title']] = file1

    # Get the directories, and recurse
    for dir1 in get_all_dirs(root_entry['id']):
        results[dir1['title']] = get_files_recursive_by_id(dir1)

    return results


def print_tree(tree, branch='', print_files=True):
    """
    Utility function to pretty-print a collection of files.
    """
    num_files = 0
    tot_file_sz = 0
    unk_files = 0
    for f,v in tree.items():
        if type(v) == dict:
            n, s, u = print_tree(v, '/'.join([branch, f]), print_files)
            num_files += n
            tot_file_sz += s
            unk_files += u
        else:
            num_files += 1
            try:
                tot_file_sz += int(v['fileSize'])
                if print_files:
                    print(f"{int(v['fileSize'])} {'/'.join([branch, f])}")
            except KeyError:
                unk_files += 1
                if print_files:
                    print(f"0 {'/'.join([branch, f])}")

    return num_files, tot_file_sz, unk_files


def make_directory(parent_id, name):
    """
    Make a directory hung off of the specified parent object.
    """
    file1 = drive.CreateFile({'title': name, 
        "parents":  [{"id": parent_id}], 
        "mimeType": "application/vnd.google-apps.folder"})
    file1.Upload()
    return file1


def get_or_make_path(path):
    """mkdir -p"""
    parent = None
    if len(path) == 1 and path[0] == '':
        # Return the root object
        return drive.CreateFile({'id': 'root'})

    for p in path:
        parent_id = parent and parent['id'] or 'root'
        parent_title = parent and parent['title'] or 'root'
 
        file1 = get_only_one_file(p, parent_id)
        if file1 is None:
            # Make the missing directory.
            file1 = make_directory(parent_id, p)

        parent = file1

    return file1


def make_copy(dst_parent, src_file):
    """
    Copy a source file to a destination parent node.  Manually copy over some
    of the desired metadata to try to preserve as much as possible.

    Other things such as starred status aren't copied, but could.

    Some things such as originating author of comments can't be copied.

    Finally, versions can't be copied at all, without recreating the file from
    scratch piece by piece to replicate the process.
    """
    # Copy the file
    target = {'title': src_file['title'], 'parents': [{'id': dst_parent['id']}]}
    file1 = drive.auth.service.files().copy(fileId=src_file['id'], body=target).execute()

    # Save the target id, because it's used a lot.
    dst_id = file1['id']

    # Update modifiedDate
    body = {'modifiedDate': src_file['modifiedDate']}
    file1 = drive.auth.service.files().update(fileId=dst_id, modifiedDateBehavior='fromBody', setModifiedDate=True, body=body).execute()

    # Copy comments
    comments = drive.auth.service.comments().list(fileId=src_file['id']).execute()

    try:
        for comment in comments['items']:
            # Create the new comment
            replies = comment['replies']
            del comment['replies']      # comments().insert fails if the replies field is populated.

            # Save the comment with the old author's name attached.
            #
            # Note: substitute '@' with '-at-' to avoid accidentally tagging
            # people (and generating emails from them) on the copies
            comment['content'] = comment['author']['displayName'] + ": " + comment['content'].replace('@', '-at-')

            new_comment = drive.auth.service.comments().insert(fileId=dst_id, body=comment).execute()

            # Copy the replies over
            for reply in replies:
                # Google API doesn't offer any way to naturally preserve the
                # original author, so prepend it to the comment.
                content = reply['author']['displayName'] + ": " + reply['content']
                if 'verb' in reply:
                    body = {'content': content, 'verb': reply['verb']}
                else:
                    body = {'content': content}

                drive.auth.service.replies().insert(fileId=dst_id, commentId=new_comment['commentId'], body=body).execute()

        # All the comments copied successfully
        print(f"{src_file['title']}: {src_file['id']} => {dst_id}")

    except googleapiclient.errors.HttpError:
        print(f"MISSING COMMENTS: {src_file['title']}: {src_file['id']} => {dst_id}, anchor: {comment['anchor']}")
    
    return file1


def copy_to_dest(dst_parent, results):
    """
    Copy the collection of file objects in results to the
    dst_parent folder.
    """
    for f,v in results.items():
        if f == '.':
            # Ignore the self-referential directory entries
            continue
        if type(v) == dict:
            # Copy the directory and it's contents
            target = make_directory(dst_parent['id'], f)
            copy_to_dest(target, v)
        else:
            # Copy the specific file
            make_copy(dst_parent, v)


# Parse the command line arguments
if len(sys.argv) < 2:
    print('Too few parameters')
    sys.exit(-1)

src_path = ((sys.argv[1] != '/' and sys.argv[1]) or '').split('/')
dst_path = ((sys.argv[2] != '/' and sys.argv[2]) or '').split('/')

 # Authenticate
gauth = GoogleAuth()
gauth.LocalWebserverAuth()

# Drive object
drive = GoogleDrive(gauth)

# Get all the files
results = get_files_recursive(src_path)

# Make the destination
dst_parent = get_or_make_path(dst_path)

# Show a quick summary
n, s, u = print_tree(results, print_files=False)
print(f"# {n:,d} total files, {s:,d} total bytes, ({u:,d} files of unknown size)")

# Copy the files
copy_to_dest(dst_parent, results)
