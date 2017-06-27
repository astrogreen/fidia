
from typing import List

import fidia

__all__ = ['get_all_known_object_names_in_any_archive']

def get_all_known_object_names_in_any_archive():
    # type: () -> List[str]
    """Get all known objects in FIDIA (i.e. already ingested), and return a list of their object_ids"""
    all_objects = []
    for archive in fidia.known_archives.all:
        all_objects.extend(archive.contents)
    return all_objects

def get_dictionary_of_known_archives():
    """Get a dictionary containing information about all known archives."""

    result = dict()
    for archive in fidia.known_archives.all:
        result[archive.archive_id] = {
            "archive_id": archive.archive_id
        }
    return result

def get_top_level_traits_for_archive(archive_id):

    archive = fidia.known_archives.by_id[archive_id]

    result = []

    for mapping in archive.trait_mappings.values():
        result.append({
                "type": mapping.name,
                "key": str(mapping.trait_key)
        })

    return result

if __name__ == '__main__':

    def print_call(command, *args, **kwargs):
        print("_" * 80)
        print(command.__name__ + "(" +
              ", ".join([repr(a) for a in args]) +
              ", ".join([k + "=" + repr(v) for k, v in kwargs]) +
              ")\n")
        print(command(*args, **kwargs))


    print_call(get_all_known_object_names_in_any_archive)

    print_call(get_dictionary_of_known_archives)

    print_call(get_top_level_traits_for_archive, "ExampleArchive")
