# -*- coding: UTF-8 -*-
import os
import io
import hashlib
import requests
import shutil


version = "1.13.0-neo-compat5-red"

def_headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
               "Authorization": ""}


proxies = None
civitai_api_key = ""
civitai_domain = "civitai.red"


# print for debugging
def printD(msg):
    print(f"Civitai Helper: {msg}")


def read_chunks(file, size=io.DEFAULT_BUFFER_SIZE):
    """Yield pieces of data from a file-like object until EOF."""
    while True:
        chunk = file.read(size)
        if not chunk:
            break
        yield chunk

# Now, hashing use the same way as pip's source code.
def gen_file_sha256(filname):
    printD("Use Memory Optimized SHA256")
    blocksize=1 << 20
    h = hashlib.sha256()
    length = 0
    with open(os.path.realpath(filname), 'rb') as f:
        for block in read_chunks(f, size=blocksize):
            length += len(block)
            h.update(block)

    hash_value =  h.hexdigest()
    printD("sha256: " + hash_value)
    printD("length: " + str(length))
    return hash_value



# get preview image
def download_file(url, path):
    """Download to a temporary file and replace the destination only on success.

    This prevents an interrupted/failed download from leaving a partial preview
    file that would be mistaken for a valid image on the next model scan.
    Returns True on success, otherwise False.
    """
    printD("Downloading file from: " + url)
    temp_path = path + ".part"

    try:
        # Remove a stale temporary file from an earlier interrupted run.
        if os.path.isfile(temp_path):
            os.remove(temp_path)

        r = requests.get(url, stream=True, headers=def_headers, proxies=proxies, timeout=60)
        if not r.ok:
            printD("Get error code: " + str(r.status_code))
            printD(r.text)
            return False

        with open(os.path.realpath(temp_path), 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        # An empty file is never a valid preview.  Leave no destination file so
        # the next scan automatically tries the download again.
        if not os.path.isfile(temp_path) or os.path.getsize(temp_path) == 0:
            printD("Downloaded preview is empty. It will be retried on next scan.")
            if os.path.isfile(temp_path):
                os.remove(temp_path)
            return False

        os.replace(temp_path, os.path.realpath(path))
        printD("File downloaded to: " + path)
        return True

    except Exception as e:
        printD("Download failed: " + str(e))
        printD("Preview will be retried on next scan.")
        try:
            if os.path.isfile(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return False

# get subfolder list
def get_subfolders(folder:str) -> list:
    printD("Get subfolder for: " + folder)
    if not folder:
        printD("folder can not be None")
        return
    
    if not os.path.isdir(folder):
        printD("path is not a folder")
        return
    
    prefix_len = len(folder)
    subfolders = []
    for root, dirs, files in os.walk(folder, followlinks=True):
        for dir in dirs:
            full_dir_path = os.path.join(root, dir)
            # get subfolder path from it
            subfolder = full_dir_path[prefix_len:]
            subfolders.append(subfolder)

    return subfolders


# get relative path
def get_relative_path(item_path:str, parent_path:str) -> str:
    # printD("item_path:"+item_path)
    # printD("parent_path:"+parent_path)
    # item path must start with parent_path
    if not item_path:
        return ""
    if not parent_path:
        return ""
    if not item_path.startswith(parent_path):
        return item_path

    relative = item_path[len(parent_path):]
    if relative[:1] == "/" or relative[:1] == "\\":
        relative = relative[1:]

    # printD("relative:"+relative)
    return relative
