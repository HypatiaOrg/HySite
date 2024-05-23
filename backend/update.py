from standard_lib import standard_output
from hypatia.legacy.sqlite import delete_test_database
from hypatia.legacy.db import ordered_outputs, update_one_norm


def legacy_update(test_mode: bool = True, output_list: list[str] = None, mongo_upload: bool = False):
    if output_list is None:
        output_list = list(ordered_outputs)
    abs_list = []
    if "absolute" in output_list:
        output_list.remove("absolute")
        abs_list.append("absolute")
    full_list = abs_list + output_list
    delete_test_database(test_mode=test_mode, remove_compositions=True)
    output = standard_output(do_legacy=True, from_scratch=False, refresh_exo_data=False,
                             norm_keys=list(output_list), mongo_upload=mongo_upload)
    print('full_list:', full_list)
    for norm_key in full_list:
        update_one_norm(norm_key, test_mode=test_mode)
    return output


if __name__ == '__main__':
    nat_cat, output_star_data, target_star_data = legacy_update(test_mode=False)
