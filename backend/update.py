from standard_lib import standard_output
from hypatia.legacy.sqlite import delete_test_database
from hypatia.legacy.db import ordered_outputs, update_one_norm


def legacy_update(skip_output: bool = False, test_mode: bool = True, output_list=ordered_outputs):
    delete_test_database(test_mode=test_mode, remove_compositions=True)
    from_scratch = False
    for norm in output_list:
        if not skip_output:
            nat_cat, output_star_data, target_star_data = standard_output(from_scratch=from_scratch,
                                                                          norm_key=norm,
                                                                          fast_update_gaia=True,
                                                                          from_pickle=False)
        from_scratch = False
        update_one_norm(norm=norm, test_mode=test_mode)


if __name__ == '__main__':
    # the catalogue running order is:
    # ["absolute", "anders89", "asplund05", "asplund09", "grevesse98", "lodders09", "original", "grevesse07"]
    legacy_update(skip_output=False, test_mode=False)
