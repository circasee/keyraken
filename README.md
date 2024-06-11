# Keyraken: The Keyring Kraken CLI

![Keyraken Banner](./keyraken.png)

> A Python-powered CLI for managing secure keyring collections on Linux — fast, flexible, and a little bit ferocious.

---

## 🐙 Overview

**Keyraken** is a command-line tool for managing secure credentials in keyring collections. Built for developers, hackers, and sysadmins, it provides full CRUD support for items with attribute filtering, logic-based queries, and optional secrets — all via Python and D-Bus.

---

## ✨ Features

- 🔐 Create new items in a keyring collection  
- 🔍 Read items using label, path, or JSON attribute filters  
- ♻️ Update attributes or secrets with `--replace` or merge  
- 🗑 Delete items or individual attributes  
- 📋 List everything in a collection  
- 🔧 Unlock, relock, or create new keyring collections  

---

## 📦 Installation

```bash
git clone https://github.com/circasee/keyraken.git
cd keyraken
pip install -r requirements.txt
```

Keyraken requires a Linux system and depends on `dbus-python` and `SecretStorage`.

---

## 🚀 Usage Examples

### Show Help

```bash
python keyraken.py --help
```

### Create a New Keyring Collection

```bash
python keyraken.py new my_collection
```

This will create a new keyring collection named `my_collection`.

By default, your system may trigger a password prompt via the GUI (e.g., GNOME Keyring). 
This behavior can occur even without the `--password` flag, depending on the OS and backend implementation.

To explicitly request a password prompt (when supported):

```bash
python keyraken.py new my_collection --password
```

> 🛡️ **Note:** The `--password` flag triggers your system's graphical prompt (via D-Bus) to set a password lock.

### Create a New Item

```bash
python keyraken.py create my_collection my_label \
  --attributes '{"username": "user123", "email": "user@example.com"}' \
  --secret "my_secret_password"
```

If you omit the `--secret` option, Keyraken will prompt you securely for input using the command line:

```bash
python keyraken.py create my_collection my_label \
  --attributes '{"username": "user123", "email": "user@example.com"}'
```

You’ll see:

```text
Enter secret (input will be hidden): 
```

This ensures the secret is hidden during entry and not exposed in shell history.

### Read an Item

```bash
python keyraken.py read my_collection --attributes '{"username": "user123"}'
```

```json
{
  "label": "my_label",
  "attributes": {
    "email": "user@example.com",
    "username": "user123",
    "xdg:schema": "org.freedesktop.Secret.Generic"
  },
  "secret": "my_secret_password"
}
```

### Read Multiple Items with OR Logic

```bash
python keyraken.py read my_collection \
  --attributes '{"username": "user123"}' \
  --multiple --logic OR
```

```json
[
  {
    "label": "my_label",
    "attributes": {
      "email": "user@example.com",
      "username": "user123",
      "xdg:schema": "org.freedesktop.Secret.Generic"
    },
    "secret": "my_secret_password"
  },
  {
    "label": "my_label2",
    "attributes": {
      "email": "user@example.com",
      "username": "user123",
      "xdg:schema": "org.freedesktop.Secret.Generic"
    },
    "secret": "my_secret_password"
  }
]
```

### Update an Item

```bash
python keyraken.py update my_collection \
  --attributes '{"username": "user123"}' \
  --new_secret "new_secret_password" \
  --new_attributes '{"email": "new_email@example.com"}'
```

### Replace Attributes of an Item

```bash
python keyraken.py update my_collection \
  --attributes '{"username": "user123"}' \
  --new_attributes '{"email": "new_email@example.com"}' \
  --replace
```

### Delete an Item

```bash
python keyraken.py delete my_collection --attributes '{"username": "user123"}'
```

### Delete Specific Attributes of an Item

```bash
python keyraken.py delete my_collection \
  --attributes '{"username": "user123"}' \
  --delete_attributes '{"email": ""}'
```

### List All Items

```bash
python keyraken.py list my_collection
```

---

## 📘 Usage Reference

<details>
<summary><code>--help</code> output</summary>

```text
                   //######################\\ 
                 /#######qprjjl#qprjjl\#######\ 
               #######qprjjl/qprjjl\qprjjl######
             ####/qprjjl/qprjjl#qprjjl\qprjjl\####
            ###7170726a6a6c////#####7170726a6a6c###
          ##7170726a6a6c 7170726a6a6c 7170726a6a6c##
         ##//0o161 0o160 0o162 0o152 0o152 0o154\\\##
        ##////0o161 0o160 0o162 0o152 0o152 0o154\\\##
        ##01110001#01110000 01110010 01101010#011010##
        ##10/01101:::::100#01110001#0111:::::0001\\##
         ##01110000:: :::01110010#0110::: ::1010\\##
          ##01101010#01101100#01110001#01110000//##
            ####01110010#01101010#01101010#######
              #######01101100#00000000#########
              ## 00 0000 00# #00 0000####00## [ca.
            ### ##   ### ### ### ## ##   #####    see]
           ### ##   ## #### ###### ####   ## ##
          ## ## #   ## # #### ### ## ##   # ####
        ## ##  #    ## ## #### #### ###    #  ####
       ## #   ##  ### # ## # ## ##  ###   ##  ## ##
       ## ##  ##   ## #  ## ##   #   ##   ##   ## ##
       ## ##   #   ##  ##   ## ###   ##   #    ## ##
        ## ##   #  ##  ###  # ##     ##  #    ## ##
         ## ###  #  ##     #   #    ##  #   ### ##
          ## ###  #  ####        ####  #   ### ##
           ### ##   #  #####    ## ##  #  ## ###
             ### ##       ###  ###    #  ## ##
               ### ##       #  #       ## ##
                 ## ####           ##### #
                  c  ## ###     ### ##   e
                     ir  ###   # #  e
                         ca     s   

             ~ Release [1.0.0] the Keyraken! ~

usage: keyraken.py [--help] [--unlock] [--relock] {create,read,update,delete,list,new} ...

Keyraken: The Keyring Kraken CLI (https://github.com/circasee/keyraken)

positional arguments:
  {create,read,update,delete,list,new}
    create              Create a new item in the collection
    read                Read an item
    update              Update an item
    delete              Delete an item or specific attributes of an item
    list                List all items
    new                 Create a new keyring collection

optional arguments:
  --help                Show this help message and exit
  --unlock              Unlock the collection via service prompt
  --relock              Relock the collection if unlocked
```

</details>

---

## ✍️ Credits

Written and created by [circasee](https://github.com/circasee).  
© 2025 circasee. Licensed under the Apache 2.0 License.  

Support for this project was provided in part by artificial intelligences like  
[Chatty Kat](https://www.openai.com/chatgpt).

---

## 📄 License

This project is licensed under the [Apache License, Version 2.0](LICENSE).

See the [NOTICE](NOTICE) file for important attribution information, 
including third-party materials and assets with different licensing terms.

> **Note:** The `keyraken.png` image is © 2025 circasee. **All rights reserved.**  
> It is not covered by the Apache License. Redistribution, modification, or reuse of the image is prohibited without prior written permission from the author.
