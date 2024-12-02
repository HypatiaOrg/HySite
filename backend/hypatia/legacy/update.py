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
    delete_test_database(test_mode=test_mode, remove_compositions=True)
    output = standard_output(do_legacy=True, from_scratch=True, refresh_exo_data=False,
                             norm_keys=output_list, mongo_upload=mongo_upload)
    for norm_key in output_list + abs_list:
        update_one_norm(norm_key, test_mode=test_mode)
    return output


if __name__ == '__main__':
    nat_cat, output_star_data, target_star_data = legacy_update(test_mode=False, mongo_upload=True)