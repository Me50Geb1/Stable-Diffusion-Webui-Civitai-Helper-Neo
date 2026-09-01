# -*- coding: UTF-8 -*-
# handle msg between js and python side
import os
import json
from . import util
from modules import shared


# this is the default root path
root_path = os.getcwd()
util.printD(f"Root Path is: {root_path}")

# if path is start with "~/" means root path is under linux's user home
# so need to use os.path.expanduser("~") to get the real path
if root_path.startswith("~/"):
    user_home = os.path.expanduser("~")
    util.printD(f"Root Path is under User Home: {user_home}")
    root_path = os.path.join(user_home, root_path[2:])
    util.printD(f"Expanded Root Path is: {root_path}")




# if command line arguement is used to change model folder, 
# then model folder is in absolute path, not based on this root path anymore.
# so to make extension work with those absolute model folder paths, model folder also need to be in absolute path
folders = {
    "ti": os.path.join(root_path, "embeddings"),
    "hyper": os.path.join(root_path, "models", "hypernetworks"),
    "ckp": os.path.join(root_path, "models", "Stable-diffusion"),
    "lora": os.path.join(root_path, "models", "Lora"),
}

# Forge Neo can expose multiple checkpoint / LoRA roots. ``folders`` remains
# the primary writable destination for backwards compatibility (downloads,
# etc.), while ``model_roots`` is used for scanning and lookup.
model_roots = {k: [v] for k, v in folders.items()}

def _dedupe_existing_paths(paths):
    result = []
    seen = set()
    for path in paths:
        if not path:
            continue
        path = os.path.abspath(os.path.expanduser(str(path)))
        key = os.path.normcase(os.path.realpath(path))
        if key in seen or not os.path.isdir(path):
            continue
        seen.add(key)
        result.append(path)
    return result

def get_model_roots(model_type):
    roots = model_roots.get(model_type) or []
    if not roots and model_type in folders:
        roots = [folders[model_type]]
    return roots

exts = (".bin", ".pt", ".safetensors", ".ckpt")
info_ext = ".info"
vae_suffix = ".vae"


# get custom model path
def get_custom_model_folder():
    """Resolve model folders across A1111 / Forge / Forge Neo.

    Forge Neo may expose plural ``ckpt_dirs`` / ``lora_dirs`` options and may
    omit legacy options such as ``hypernetwork_dir``.  Older versions of this
    extension accessed those attributes directly, which could abort extension
    loading with AttributeError.

    The current Civitai Helper data model supports one root folder per model
    type.  For Neo's plural extra-folder options we keep the WebUI default root
    as the primary folder for now; this is intentional for the first
    compatibility stage.
    """
    util.printD("Get Custom Model Folder (A1111/Forge/Forge Neo compatible)")

    global folders

    # Neo moved the default embeddings directory under models/embeddings and
    # normally exposes its resolved path through cmd_opts.embeddings_dir.
    embeddings_dir = getattr(shared.cmd_opts, "embeddings_dir", None)
    if embeddings_dir and os.path.isdir(embeddings_dir):
        folders["ti"] = os.path.abspath(embeddings_dir)

    # Hypernetworks are legacy and the option is absent in some Neo builds.
    hypernetwork_dir = getattr(shared.cmd_opts, "hypernetwork_dir", None)
    if hypernetwork_dir and os.path.isdir(hypernetwork_dir):
        folders["hyper"] = os.path.abspath(hypernetwork_dir)

    # Legacy A1111 / reForge singular options.
    ckpt_dir = getattr(shared.cmd_opts, "ckpt_dir", None)
    if ckpt_dir and os.path.isdir(ckpt_dir):
        folders["ckp"] = os.path.abspath(ckpt_dir)

    lora_dir = getattr(shared.cmd_opts, "lora_dir", None)
    if lora_dir and os.path.isdir(lora_dir):
        folders["lora"] = os.path.abspath(lora_dir)

    # Forge Neo uses plural lists for additional model directories.  Scan and
    # card lookup now include those roots, while downloads still use the
    # primary folder above so the old UI remains unambiguous.
    ckpt_dirs = getattr(shared.cmd_opts, "ckpt_dirs", None) or []
    lora_dirs = getattr(shared.cmd_opts, "lora_dirs", None) or []

    model_roots["ti"] = _dedupe_existing_paths([folders["ti"]])
    model_roots["hyper"] = _dedupe_existing_paths([folders["hyper"]])
    model_roots["ckp"] = _dedupe_existing_paths([folders["ckp"], *ckpt_dirs])
    model_roots["lora"] = _dedupe_existing_paths([folders["lora"], *lora_dirs])

    for model_type, folder in folders.items():
        util.printD(f"Primary model folder [{model_type}]: {folder}")
        for extra in get_model_roots(model_type)[1:]:
            util.printD(f"Additional model folder [{model_type}]: {extra}")




# write model info to file
def write_model_info(path, model_info):
    util.printD("Write model info to file: " + path)
    with open(os.path.realpath(path), 'w') as f:
        f.write(json.dumps(model_info, indent=4))


def load_model_info(path):
    # util.printD("Load model info from file: " + path)
    model_info = None
    with open(os.path.realpath(path), 'r') as f:
        try:
            model_info = json.load(f)
        except Exception as e:
            util.printD("Selected file is not json: " + path)
            util.printD(e)
            return
        
    return model_info


# get model file names by model type
# parameter: model_type - string
# return: model name list
def get_model_names_by_type(model_type:str) -> list:
    model_names = []
    seen = set()
    for model_folder in get_model_roots(model_type):
        for root, dirs, files in os.walk(model_folder, followlinks=True):
            for filename in files:
                item = os.path.join(root, filename)
                _, ext = os.path.splitext(item)
                if ext.lower() in exts and filename not in seen:
                    seen.add(filename)
                    model_names.append(filename)
    return model_names



# return 2 values: (model_root, model_path)
def get_model_path_by_type_and_name(model_type:str, model_name:str) -> str:
    util.printD("Run get_model_path_by_type_and_name")
    if model_type not in folders.keys():
        util.printD("unknown model_type: " + model_type)
        return
    if not model_name:
        util.printD("model name can not be empty")
        return

    for folder in get_model_roots(model_type):
        for root, dirs, files in os.walk(folder, followlinks=True):
            if model_name in files:
                return (root, os.path.join(root, model_name))
    return



# get model path by model type and search_term
# parameter: model_type, search_term
# return: model_path
def get_model_path_by_search_term(model_type:str, search_term:str):
    util.printD(f"Search model of {search_term} in {model_type}")
    if model_type not in folders.keys():
        util.printD("unknow model type: " + model_type)
        return
    
    # for lora: search_term = subfolderpath + model name + ext + " " + hash. And it always start with a / even there is no sub folder
    # for ckp: search_term = subfolderpath + model name + ext + " " + hash
    # for ti: search_term = subfolderpath + model name + ext + " " + hash
    # for hyper: search_term = subfolderpath + model name
    has_hash = True
    if model_type == "hyper":
        has_hash = False
    elif search_term.endswith(".pt") or search_term.endswith(".bin") or search_term.endswith(".safetensors") or search_term.endswith(".ckpt"):
        has_hash = False

    # remove hash
    # model name may have multiple spaces
    splited_path = search_term.split()
    model_sub_path = splited_path[0]
    if has_hash and len(splited_path) > 1:
        model_sub_path = ""
        for i in range(0, len(splited_path)-1):
            model_sub_path += splited_path[i] + " "
        
        model_sub_path = model_sub_path.strip()

    if model_sub_path[:1] == "/":
        model_sub_path = model_sub_path[1:]

    model_folder_name = "";
    if model_type == "ti":
        model_folder_name = "embeddings"
    elif model_type == "hyper":
        model_folder_name = "hypernetworks"
    elif model_type == "ckp":
        model_folder_name = "Stable-diffusion"
    else:
        model_folder_name = "Lora"

    # check if model folder is already in search_term
    if model_sub_path.startswith(model_folder_name):
        # this is sd webui v1.8.0+'s search_term
        # need to remove this model_folder_name+"/"or""\\" from model_sub_path
        model_sub_path = model_sub_path[len(model_folder_name):]

        if model_sub_path.startswith("/") or model_sub_path.startswith("\\"):
            model_sub_path = model_sub_path[1:]

    if model_type == "hyper":
        if not model_sub_path.endswith(".pt"):
            model_sub_path = model_sub_path+".pt"

    for model_folder in get_model_roots(model_type):
        model_path = os.path.join(model_folder, model_sub_path)
        if os.path.isfile(model_path):
            return model_path

    util.printD("Can not find model file in configured roots: " + model_sub_path)
    return

