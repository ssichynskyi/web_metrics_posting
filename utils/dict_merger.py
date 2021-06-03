from collections.abc import Mapping


def merge_dicts(main: dict, complement: dict) -> dict:
    """Merges two dicts recursively.

    Idea:
        unlike basic dict.update() on key match this function
        doesn't simply replace old value with new.
        Instead, if value is dictionary executes recursively
        and updates inner keys as shown by example

    Examples:
        main = {
            'name': 'Alex',
            'work': {'address': 'ugly street'},
            'hobbies': ['basketball', 'football'],
            'skills': ['programming', 'testing']
        }
        complement = {
            'name': 'Bobby',
            'work': {'address': 'beauty street', 'employed': True},
            'hobbies': ['spearfishing'],
            'skills': 'documenting code',
            'sex': 'Male'
        }
        pprint.pprint(merge_dicts(main, complement))
        >>
        {'hobbies': ['basketball', 'football', 'spearfishing'],
         'name': 'Bobby',
         'sex': 'Male',
         'skills': ['programming', 'teesting', 'documenting code'],
         'work': {'address': 'beauty street', 'employed': True}}

    Args:
        main: a dict to merge to
        complement: a dict to merge (values of this dict are preferred over those of main)

    Returns:
        merged dict using above mentioned logic

    """
    if not complement:
        return main

    for k, v in complement.items():
        if isinstance(v, Mapping):
            result = merge_dicts(main.get(k, {}), v)
            main[k] = result
        else:
            try:
                is_main_value_list = isinstance(main[k], list)
            except KeyError:
                is_main_value_list = False
            if is_main_value_list and isinstance(v, list):
                main[k].extend(complement[k])
            elif is_main_value_list and not isinstance(v, list) and v:
                main[k].append(complement[k])
            else:
                main[k] = v
    return main
