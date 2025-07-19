#!/usr/bin/env python3
"""
Keyraken: The Keyring Kraken CLI
================================

by circasee (https://github.com/circasee).
"""

import atexit
import platform
import sys

if platform.system() != "Linux":
    print(r"   |\  Collections are supported on Linux with D-Bus backend.", file=sys.stderr)
    print(r"~~_|_\~~         Results may vary on other operating systems.", file=sys.stderr)

try:
    import dbus
except:
    print("~^~_~^~~ dbus module not found.", file=sys.stderr)
    print(" ~~~^^~", file=sys.stderr)
try:
    import secretstorage
except:
    print("~~^~~_~^~ secretstorage module not found.", file=sys.stderr)
    print("~__~~~^^", file=sys.stderr)

import argparse
import json
import os
import getpass
from contextlib import closing
from typing import Dict, List, Optional, Union
 
__VERSION__ = '1.0.0'

ASCII_ART = r"""
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
"""


AUTHOR_INFO =   'https://github.com/circasee/keyraken'
DEFAULT_SEARCH_LOGIC = 'AND'
VERSION_INFO = f'~ Release [{__VERSION__}] the Keyraken! ~'
banner = lambda: print(ASCII_ART
                       + os.linesep + ' ' * (18 - len(__VERSION__)) + VERSION_INFO
                       + os.linesep)


########################################################################################################################
class KeyringManager:
    """Manage keyring items within a specified collection."""

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, collection_name: str, relock: Optional[bool] = False):
        """
        Initialize the KeyringManager instance.

        This constructor sets up a connection to the D-Bus Secret Service, locates or unlocks the 
        specified collection, and prepares the instance for further CRUD operations.

        :param collection_name: The name of the keyring collection to access.
        :param relock: Optional flag. If provided, the collection will be automatically relocked.
        """
        self._relock = relock
        self.connection = secretstorage.dbus_init()
        self.collection_name = collection_name
        self.collection = self.get_collection()

        # Ensure we close the D-Bus connection on exit
        # and also re-lock collection if specified.
        atexit.register(self._close)

    # ------------------------------------------------------------------------------------------------------------------
    def _close(self):
        if self._relock:
            self._lock()
        self.connection.close()

    # ------------------------------------------------------------------------------------------------------------------
    def _decode_attributes(self, attributes: Dict[str, str]) -> Dict[str, bytes]:
        """
        Decode attributes from UTF-8 strings to bytes.

        :param attributes: The attributes to decode.
        :return: The decoded attributes.
        """
        return {k: (bytes(v, 'utf-8') if isinstance(v, str) else v) for k, v in attributes.items()}

    # ------------------------------------------------------------------------------------------------------------------
    def _encode_attributes(self, attributes: Dict[str, Union[str, bytes]]) -> Dict[str, str]:
        """
        Encode attributes to UTF-8 strings.

        :param attributes: The attributes to encode.
        :return: The encoded attributes.
        """
        return {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in attributes.items()}

    # ------------------------------------------------------------------------------------------------------------------
    def _lock(self):
        if not self._locked:
            self.collection.lock()

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def _locked(self):
        return self.collection.is_locked()

    # ------------------------------------------------------------------------------------------------------------------
    def _unlock(self):
        if self._locked:
            print("Collection is locked. The Secret Service controls the prompt.", file=sys.stderr)
            print("Unlocking will continue via service provided GUI.", file=sys.stderr)
            # https://secretstorage.readthedocs.io/en/latest/collection.html#secretstorage.collection.Collection.unlock
            dismissed = self.collection.unlock()
            if dismissed:
                print("Unlock prompt was dismissed by user.", file=sys.stderr)
            if self._locked:
                raise ValueError(f"Collection '{self.collection_name}' is still locked. Try again.")

    # ------------------------------------------------------------------------------------------------------------------
    def create_item(self, item_label: str, attributes: Dict[str, Union[str, bytes]], secret: str):
        """
        Create a new item in the keyring collection.

        :param item_label: The label of the item.
        :param attributes: The attributes of the item.
        :param secret: The secret/password of the item.
        """
        encoded_attributes = self._encode_attributes(attributes)
        return self.collection.create_item(item_label, encoded_attributes, secret, replace=False) # Strict no-replace

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def create_new_collection(collection_name: str, lock: Optional[bool] = False, alias: Optional[str] = ''):
        """Creates a new keyring collection with the given name and optional password."""
        with closing(secretstorage.dbus_init()) as connection:
            collection = secretstorage.create_collection(
                connection,
                label=collection_name,
                alias=alias
            )
            if lock:
                collection.lock()  # secretstorage Prompt
        return collection

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def decode_bytes(dct: Dict[str, Union[str, bytes]]) -> Dict[str, Union[str, bytes]]:
        """
        Decode UTF-8 strings to bytes from JSON strings.

        :param dct: The dictionary to decode.
        :return: The decoded dictionary.
        """
        for key, value in dct.items():
            if isinstance(value, str):
                try:
                    dct[key] = bytes(value, 'utf-8')
                except ValueError:
                    pass
        return dct

    # ------------------------------------------------------------------------------------------------------------------
    def delete_item(
        self,
        attributes: Optional[Dict[str, Union[str, bytes]]] = None,
        label: Optional[str] = None,
        path: Optional[str] = None,
        logic: str = 'AND',
        delete_attributes: Optional[Dict[str, Union[str, bytes]]] = None
    ):
        """
        Delete an item or specific attributes of an item from the keyring collection.

        :param attributes: The attributes to search for.
        :param label: The label of the item.
        :param path: The path of the item.
        :param logic: The logic for searching items ('AND' or 'OR').
        :param delete_attributes: Specific attributes to delete from the item.
        :raises ValueError: If the item is not found.
        """
        items = self.search_items(attributes, label, path, logic)
        if items:
            item = items[0]
            if delete_attributes:
                encoded_delete_attributes = self._encode_attributes(delete_attributes)
                current_attributes = item.get_attributes()
                for attr in encoded_delete_attributes:
                    if attr in current_attributes:
                        del current_attributes[attr]
                item.set_attributes(current_attributes)
            else:
                item.delete()
        else:
            raise ValueError("Item not found")

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def encode_bytes(obj: Union[str, bytes]) -> str:
        """
        Encode bytes to UTF-8 strings for JSON serialization.

        :param obj: The object to encode.
        :return: The encoded object.
        :raises TypeError: If the object is not JSON serializable.
        """
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    # ------------------------------------------------------------------------------------------------------------------
    def get_collection(self) -> secretstorage.Collection:
        """
        Retrieve and unlock the keyring collection.

        :param password: The password to unlock the collection.
        :return: The unlocked collection.
        :raises ValueError: If the collection is not found or cannot be unlocked.
        """
        collections = secretstorage.get_all_collections(self.connection)
        for collection in collections:
            if collection.get_label() == self.collection_name:
                return collection
        raise ValueError(f"Collection '{self.collection_name}' not found")

    # ------------------------------------------------------------------------------------------------------------------
    def list_items(self) -> List[Dict[str, Union[str, bytes]]]:
        """
        List all items in the keyring collection.

        :return: A list of all items with their labels, attributes, and paths.
        """
        items = self.collection.get_all_items()
        item_list = []
        for item in items:
            item_list.append({
                "label": item.get_label(),
                "attributes": self._decode_attributes(item.get_attributes()),
                "path": item.item_path
            })
        return item_list

    # ------------------------------------------------------------------------------------------------------------------
    def read_item(
        self,
        attributes: Optional[Dict[str, Union[str, bytes]]] = None,
        label: Optional[str] = None,
        path: Optional[str] = None,
        logic: str = 'AND',
        multiple: bool = False
    ) -> Optional[Union[Dict[str, Union[str, bytes]], List[Dict[str, Union[str, bytes]]]]]:
        """
        Read an item from the keyring collection.

        :param attributes: The attributes to search for.
        :param label: The label of the item.
        :param path: The path of the item.
        :param logic: The logic for searching items ('AND' or 'OR').
        :param multiple: Whether to return multiple results as a JSON array.
        :return: The found item(s) or None if not found.
        """
        items = self.search_items(attributes, label, path, logic)
        if items:
            if multiple:
                result = [{
                    "label": item.get_label(), 
                    "attributes": self._decode_attributes(item.get_attributes()), 
                    "secret": item.get_secret()} 
                    for item in items
                ]
                return result
            else:
                item = items[0]
                return {
                    "label": item.get_label(),
                    "attributes": self._decode_attributes(item.get_attributes()),
                    "secret": item.get_secret()
                }
        else:
            return None

    # ------------------------------------------------------------------------------------------------------------------
    def search_items(
        self,
        attributes: Optional[Dict[str, Union[str, bytes]]] = None,
        label: Optional[str] = None,
        path: Optional[str] = None,
        logic: str = 'AND'
    ) -> List[secretstorage.Item]:
        """
        Search for items in the keyring collection.

        :param attributes: The attributes to search for.
        :param label: The label of the item.
        :param path: The path of the item.
        :param logic: The logic for searching items ('AND' or 'OR').
        :return: A list of matched items.
        """
        if attributes is None:
            attributes = {}
        encoded_attributes = self._encode_attributes(attributes)
        items = self.collection.get_all_items()
        matched_items = []
        for item in items:
            item_attributes = item.get_attributes()
            matches_attributes = all(item_attributes.get(k) == v for k, v in encoded_attributes.items())
            matches_label = (label is None) or (label == item.get_label())
            matches_path = (path is None) or (path == item.item_path)

            if logic == 'AND':
                if matches_attributes and matches_label and matches_path:
                    matched_items.append(item)
            elif logic == 'OR':
                if matches_attributes or matches_label or matches_path:
                    matched_items.append(item)
        return matched_items

    # ------------------------------------------------------------------------------------------------------------------
    def update_item(
        self,
        attributes: Optional[Dict[str, Union[str, bytes]]] = None,
        new_secret: Optional[str] = None,
        new_attributes: Optional[Dict[str, Union[str, bytes]]] = None,
        label: Optional[str] = None,
        path: Optional[str] = None,
        logic: str = 'AND',
        merge: bool = True
    ):
        """
        Update an item in the keyring collection.

        :param attributes: The attributes to search for.
        :param new_secret: The new secret/password of the item.
        :param new_attributes: The new attributes of the item.
        :param label: The label of the item.
        :param path: The path of the item.
        :param logic: The logic for searching items ('AND' or 'OR').
        :param merge: Whether to merge with existing attributes (default: True).
        :raises ValueError: If the item is not found.
        """
        items = self.search_items(attributes, label, path, logic)
        if items:
            item = items[0]
            if new_secret:
                item.set_secret(new_secret)
            if new_attributes:
                encoded_new_attributes = self._encode_attributes(new_attributes)
                if merge:
                    current_attributes = item.get_attributes()
                    merged_attributes = {**current_attributes, **encoded_new_attributes}
                    item.set_attributes(merged_attributes)
                else:
                    item.set_attributes(encoded_new_attributes)
        else:
            raise ValueError("Item not found")

########################################################################################################################
def main():
    retcode = 0
    
    parser = argparse.ArgumentParser(description=f"Keyraken: The Keyring Kraken CLI ({AUTHOR_INFO})", add_help=False)
    parser.add_argument("--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("--unlock", action="store_true", help="Unlock the collection via service prompt")
    parser.add_argument("--relock", action="store_true", help="Relock the collection if unlocked")

    subparsers = parser.add_subparsers(dest="command")

    # Create item
    create_parser = subparsers.add_parser("create", help="Create a new item in the collection")
    create_parser.add_argument("collection", help="Name of the keyring collection")
    create_parser.add_argument("label", help="Label of the item")
    create_parser.add_argument("--attributes", nargs='?', default='{}', help="Attributes of the item in JSON format")
    create_parser.add_argument("--secret", default='', help="Secret/password of the item")

    # Read item
    read_parser = subparsers.add_parser("read", help="Read an item")
    read_parser.add_argument("collection", help="Name of the keyring collection")
    read_parser.add_argument("--attributes", nargs='?', default='{}', help="Attributes of the item in JSON format")
    read_parser.add_argument("--label", help="Label of the item")
    read_parser.add_argument("--path", help="Path of the item")
    read_parser.add_argument("--logic", choices=['AND', 'OR'], default=DEFAULT_SEARCH_LOGIC, 
                             help=f"Logic for searching items (default: {DEFAULT_SEARCH_LOGIC})")
    read_parser.add_argument("--multiple", action='store_true', help="Return multiple results as a JSON array")

    # Update item
    update_parser = subparsers.add_parser("update", help="Update an item")
    update_parser.add_argument("collection", help="Name of the keyring collection")
    update_parser.add_argument("--attributes", nargs='?', default='{}', help="Attributes of the item in JSON format")
    update_parser.add_argument("--new_secret", help="New secret/password of the item")
    update_parser.add_argument("--new_attributes", help="New attributes of the item in JSON format")
    update_parser.add_argument("--label", help="Label of the item")
    update_parser.add_argument("--path", help="Path of the item")
    update_parser.add_argument("--logic", choices=['AND', 'OR'], default=DEFAULT_SEARCH_LOGIC, 
                               help=f"Logic for searching items (default: {DEFAULT_SEARCH_LOGIC})")
    update_parser.add_argument("--replace", action='store_true', 
                               help="Replace existing attributes with new ones (default: merge)")

    # Delete item
    delete_parser = subparsers.add_parser("delete", help="Delete an item or specific attributes of an item")
    delete_parser.add_argument("collection", help="Name of the keyring collection")
    delete_parser.add_argument("--attributes", nargs='?', default='{}', help="Attributes of the item in JSON format")
    delete_parser.add_argument("--label", help="Label of the item")
    delete_parser.add_argument("--path", help="Path of the item")
    delete_parser.add_argument("--logic", choices=['AND', 'OR'], default=DEFAULT_SEARCH_LOGIC, 
                               help=f"Logic for searching items (default: {DEFAULT_SEARCH_LOGIC})")
    delete_parser.add_argument("--delete_attributes", help="Specific attributes to delete from the item in JSON format")

    # List items
    list_parser = subparsers.add_parser("list", help="List all items")
    list_parser.add_argument("collection", help="Name of the keyring collection")

    # New collection
    new_parser = subparsers.add_parser("new", help="Create a new keyring collection")
    new_parser.add_argument("collection", help="Name of the new keyring collection")
    new_parser.add_argument("--password", action='store_true', 
                            help="Lock the keyring by setting a password via service provided GUI prompt.")

    args = parser.parse_args()

    check_prompt_for_secret = lambda s: s or (
        getpass.getpass("Enter secret (input will be hidden): ") if s == '' else None
    )

    if args.help or not any(vars(args).values()):
        banner()
        parser.print_help()
        return 1

    # ------------------------------------------------------------------------------------------------------------------
    if args.command == "new":
        if KeyringManager.create_new_collection(args.collection, lock=bool(args.password)):
            print(f"Keyring collection '{args.collection}' created successfully")
        else:
            print(f"Failed to create keyring collection: '{args.collection}'")
            retcode = 1
        return retcode

    # ..................................................................................................................
    manager = KeyringManager(args.collection, relock=args.relock)
    if manager._locked:
        print(f"Keyring collection '{args.collection}' is locked. Attempt unlock with --unlock.", file=sys.stderr)
        if not args.unlock:
            return 2
        manager._unlock()

    # ------------------------------------------------------------------------------------------------------------------
    if args.command == "create":
        attributes = json.loads(args.attributes, object_hook=KeyringManager.decode_bytes)
        secret = check_prompt_for_secret(args.secret)

        result = manager.create_item(args.label, attributes, secret)

        if result:
            print("Item created successfully")
        else:
            print("Failed to create item")
            retcode = 1

    # ------------------------------------------------------------------------------------------------------------------
    elif args.command == "read":
        attributes = json.loads(args.attributes, object_hook=KeyringManager.decode_bytes)
        result = manager.read_item(attributes, args.label, args.path, args.logic, args.multiple)

        if result:
            print(json.dumps(result, indent=2, default=KeyringManager.encode_bytes))
        else:
            print("Item not found", file=sys.stderr)
            retcode = 1

    # ------------------------------------------------------------------------------------------------------------------
    elif args.command == "update":
        attributes = json.loads(args.attributes, object_hook=KeyringManager.decode_bytes)
        merge = not args.replace
        new_attributes = None
        new_secret = check_prompt_for_secret(args.new_secret)

        if args.new_attributes:
            new_attributes = json.loads(args.new_attributes, object_hook=KeyringManager.decode_bytes)

        try:
            manager.update_item(attributes, new_secret, new_attributes, args.label, args.path, args.logic, merge)
            print("Item updated successfully")
        except ValueError as e:
            print(e)
            retcode = 1

    # ------------------------------------------------------------------------------------------------------------------
    elif args.command == "delete":
        attributes = json.loads(args.attributes, object_hook=KeyringManager.decode_bytes)
        delete_attributes = None
        
        if args.delete_attributes:
            delete_attributes = json.loads(args.delete_attributes, object_hook=KeyringManager.decode_bytes)

        try:
            manager.delete_item(attributes, args.label, args.path, args.logic, delete_attributes)
            print("Item deleted successfully")
        except ValueError as e:
            print(e)
            retcode = 1

    # ------------------------------------------------------------------------------------------------------------------
    elif args.command == "list":
        items = manager.list_items()

        if items:
            print(json.dumps(items, indent=2, default=KeyringManager.encode_bytes))
        else:
            print("No items found")
            retcode = 1

    # ------------------------------------------------------------------------------------------------------------------
    else:
        parser.print_help()
        retcode = 1

    return retcode


########################################################################################################################
########################################################################################################################
########################################################################################################################
if __name__ == "__main__":
    sys.exit(main())
