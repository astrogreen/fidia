
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

def get_detailed_object_information_for_all_objects_in_any_archive():
    """Get all known objects with extra information for each.

    Though we'll have to do benchmarking and some other work, but this is
    probably 10x-100x slower than the previous function.

    """

    all_objects = []
    for archive in fidia.known_archives.all:
        for object_id in archive.contents:
            # @TODO: Replace with an actual astro_object from the archive? Must this be serialized?
            all_objects.append({
                "object_id": object_id,
                "adcid_id": "adcid_id",
                "archive": archive.archive_id
            })
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
            "key": str(mapping.trait_key),
            "pretty_name": mapping.pretty_name,
            "short_description": mapping.short_description,
            "long_description": mapping.long_descrription
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

    print_call(get_detailed_object_information_for_all_objects_in_any_archive)

    print_call(get_dictionary_of_known_archives)

    print_call(get_top_level_traits_for_archive, "ExampleArchive")

