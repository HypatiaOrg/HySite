"""
Nat's Test Space

The current code below takes the input file (no spaces between commas, often a "planets_" file from NEA)
and creates a mini-sources by matching only to those stars while still retaining all of the tools and
stats of the main Hypatia sources. To execute, run this file in the terminal. Might need to move this to
standard_lib at some point.
"""
import os

import numpy as np
import matplotlib.pyplot as plt

from hypatia.plots.histograms import get_hist_bins
from standard_lib import standard_output
from hypatia.pipeline.nat_cat import NatCat
from hypatia.pipeline.star.stats import autolabel
from hypatia.config import histo_dir, hydata_dir, norm_keys_default


def mdwarf_output(target_list: list[str] | list[tuple[str, ...]] | str | os.PathLike | None = None,
                 catalogs_file_name: str = os.path.join(hydata_dir, 'subsets', 'mdwarf_subset_catalog_file.csv'), # 'reference_data', 'catalog_file.csv'
                 refresh_exo_data=False, norm_keys: list[str] = None,
                 params_list_for_stats: list[str] = None, star_types_for_stats: list[str] = None,
                 parameter_bound_filter: list[tuple[str, int | float | str, int| float | str]] = None,
                 mongo_upload: bool = True):
    if params_list_for_stats is None:
        params_list_for_stats = ["dist", "logg", 'Teff', "SpType", 'st_mass', 'st_rad', "disk"]
    if star_types_for_stats is None:
        star_types_for_stats = ['gaia dr2', "gaia dr1", "hip", 'hd', "wds"]
    if parameter_bound_filter is None:
        parameter_bound_filter = [("Teff", 2300.0, 4000.), ("logg", 3.5, 6.0), ("dist", 0.0, 30.0)]
    nat_cat = NatCat(params_list_for_stats=params_list_for_stats,
                     star_types_for_stats=star_types_for_stats,
                     catalogs_from_scratch=True, verbose=True, catalogs_verbose=True,
                     get_abundance_data=True, get_exo_data=True, refresh_exo_data=refresh_exo_data,
                     target_list=target_list,
                     catalogs_file_name=catalogs_file_name)
    dist_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                parameter_bound_filter=parameter_bound_filter,
                                                star_data_stats=False,
                                                reduce_abundances=False)

    exo_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                               parameter_bound_filter=None,
                                               has_exoplanet=True,
                                               star_data_stats=False,
                                               reduce_abundances=False)
    # sort by is the data a target star
    target_output = nat_cat.make_output_star_data(is_target=True)
    output_star_data = dist_output + exo_output + target_output
    # optional 2nd filtering step
    # Check mission elements: {'C','N','O','F','Na','Mg','Si','Cl','K','Ca','Ti'} -- True
    # Both Mg and Si measurements: {'Mg','Si'} -- False
    # Also look at target overlap
    output_star_data.filter(target_catalogs=None, or_logic_for_catalogs=True,
                            catalogs_return_only_targets=False,
                            target_star_name_types=None, and_logic_for_star_names=True,
                            target_params=None, and_logic_for_params=True,
                            target_elements=None, or_logic_for_element=True,
                            element_bound_filter=None,  # filtering happens before normalization
                            min_catalog_count=None,
                            parameter_bound_filter=None,
                            parameter_match_filter=None,
                            at_least_fe_and_another=True,
                            remove_nlte_abundances=True,
                            keep_complement=False,
                            is_target=None)
    output_star_data.normalize(norm_keys=norm_keys)
    output_star_data.filter(element_bound_filter=None)  # filter after normalization, and logic
    output_star_data.do_stats(params_set=nat_cat.params_list_for_stats,
                              star_name_types=nat_cat.star_types_for_stats)

    if mongo_upload:
        output_star_data.reduce_elements()
        output_star_data.find_available_attributes()
        output_star_data.export_to_mongo(catalogs_file_name=nat_cat.catalogs_file_name)
    output_star_data.pickle_myself()
    return nat_cat, output_star_data, target_output

# the nonMs are being manually added back in, not removed
# these need to be removed: 'LP 714-47', 'HD 97101', 'HD 168442'
# nonMs = ['HD 88230', 'HD 178126', 'LHS 104', 'LHS 170', 'LHS 173', 'LHS 236', 'LHS 343', 'LHS 467', 'LHS 1138', 'LHS 1482','LHS 1819','LHS 1841', 'LHS 2161', 'LHS 2463', 'LHS 2715', 'LHS 2938', 'LHS 3084', 'HIP 27928', 'G 39-36', 'HIP 37798', 'HIP 67308', 'LHS 1229', 'HD 11964B', 'HD 18143B', 'HD 285804', 'BD-01 293B', 'BD+17 719C', 'BD+24 0004B', 'GJ 129', 'GJ 1177B', '2MASS 2203769-2452313', 'HD 35155', 'HD 49368', 'HD 120933', 'HD 138481', 'HD 10380', 'HD 10824', 'HD 15656', 'HD 20468', 'HD 20644', 'HD 23413', 'HD 29065', 'HD 52960', 'HD 58972', 'HD 62721', 'HD 88230', 'HD 218792', 'HD 223719', 'HD 225212', 'HD 6860', 'HD 18191', 'HD 18884', 'HD 30959', 'HD 35155', 'HD 44478', 'HD 49368', 'HD 71250', 'HD 112300', 'HD 119228', 'HD 120933', 'HD 138481', 'HD 147923', 'HD 216386', 'HD 224935', 'HD 10380', 'HD 10824', 'HD 15656', 'HD 20468', 'HD 20644', 'HD 23413', 'HD 29065', 'HD 52960', 'HD 58972', 'HD 60522', 'HD 62721', 'HD 88230', 'HD 218792', 'HD 223719', 'HD 225212']
all_params = set()

test_norm_keys = list(norm_keys_default)
test_refresh_exo_data = False
test_from_scratch = True
test_from_pickled_cat = False
target_list_file = "hypatia/HyData/target_lists/hypatia_mdwarf_cut_justnames.csv"
#target_list = os.path.join(ref_dir, 'hypatia_mdwarf_cut_justnames.csv')

nat_cat, output_star_data, target_star_data = mdwarf_output(norm_keys=test_norm_keys,
                                                            target_list=target_list_file,
                                                            refresh_exo_data=test_refresh_exo_data)
stats = target_star_data.stats

run_sak_check = False
#Run this to load the data for the SAKHMET target stars
def sakhmet_overlap(sak_check: bool = run_sak_check):
    if sak_check:
        sak_target_list = os.path.join(hydata_dir, 'target_lists/Sakhmet-survey-stars.csv')
        snat_cat, soutput_star_data, starget_star_data = standard_output(from_scratch=True, norm_keys=test_norm_keys,
                                                                        target_list=sak_target_list,
                                                                        fast_update_gaia=True,
                                                                        from_pickled_output = False)

        #SAKHMET targets to check the overlap with the mission elements for the plot; 1 overlap for O at last check = orange line on plot
        sak_targs = ["2MASS J05114046-4501051","2MASS J01524908-2226055","2MASS J05083500-1810178","2MASS J09213761-6016551","2MASS J11352695-3232232","2MASS J13550260-2905257","2MASS J00513400-2254361","2MASS J09442986-4546351","2MASS J12375231-5200055","2MASS J06393764-5536349","2MASS J09394631-4104029","2MASS J15011648-4339311","2MASS J02135359-3202282","2MASS J11093138-2435548","2MASS J05064991-2135091","2MASS J14131288-5644314","2MASS J07541090-2518116","2MASS J04472266-2750295","2MASS J11170748-2748485","2MASS J05004714-5715255","2MASS J09583428-4625300","2MASS J05554318-2651233","2MASS J11431977-5150255","2MASS J23301341-2023271","2MASS J04533119-5551372","2MASS J09492776-5520086","2MASS J03075577-2813108","2MASS J10415183-3638001","2MASS J09360161-2139371","2MASS J22384530-2036519","2MASS J09162066-1837329","2MASS J02500975-5308204","2MASS J03015142-1635356","2MASS J11314655-4102473","2MASS J02110221-3540146","2MASS J05172292-3521545","2MASS J22382467-2921139","2MASS J01213447-4139226","2MASS J04534995-1746235","2MASS J11152072-1808362","2MASS J03355969-4430453","2MASS J05474051-3619425","2MASS J23141659-1938393","2MASS J11072772-1917293","2MASS J03231588-4959389","2MASS J01372081-4911443","2MASS J04060196-6405369","2MASS J06240446-2658462","2MASS J01384349-4514314","2MASS J03080663-2445347","2MASS J10240700-6359549","2MASS J06521707-2623145","2MASS J07303932-4424009","2MASS J03164779-2125260","2MASS J14105747-3117253","2MASS J10011079-3023249","2MASS J13002579-3436243","2MASS J22143835-2141535","2MASS J10264731-6254054","2MASS J22233334-5713146","2MASS J02464286-2305119","2MASS J02032076-2113427","2MASS J02003830-5558047","2MASS J12021315-3800286","2MASS J00215604-3124215","2MASS J05565616-4655539","2MASS J06315111-4332026","2MASS J14291857-4627496","2MASS J07072291-2127271","2MASS J15290720-1722545","2MASS J01384388-4514467","2MASS J11160680-3010415","2MASS J23032085-4943339","2MASS J04472312-2750358","2MASS J02522213-6340475","2MASS J12355841-4556202","2MASS J07243425-1753321","2MASS J15104047-5248189","2MASS J10222461-6010377","2MASS J12100559-1504156","2MASS J06045215-3433360","2MASS J08271183-4459215","2MASS J13254887-2822263","2MASS J05432664-3041452","2MASS J00413051-3337317","2MASS J04522441-1649219","2MASS J00582789-2751251","2MASS J04533054-5551318","2MASS J10423011-3340162","2MASS J13455074-1758047","2MASS J03325585-4442070","2MASS J07532037-3326322","2MASS J14110874-6155469","2MASS J02273036-3054355","2MASS J22445794-3315015","2MASS J13011965-6311422","2MASS J05032009-1722245","2MASS J01171538-3542569","2MASS J05263603-4220178","2MASS J08405781-4614305","2MASS J00490173-5008419","2MASS J12245243-1814303","2MASS J05184752-2123364","2MASS J08471933-4652439","2MASS J06215384-2243241","2MASS J01143421-5356316","2MASS J06090772-4953170","2MASS J09241731-4005443","2MASS J10451668-3048268","2MASS J23101566-2555530","2MASS J23380819-1614100","2MASS J08405923-2327232","2MASS J06334998-5831426","2MASS J02191003-3646413","2MASS J11160018-5732513","2MASS J13303438-5259411","2MASS J12111179-1957376","2MASS J06091922-3549311","2MASS J05305719-5330521","2MASS J01071358-3225466","2MASS J07384089-2113276","2MASS J05404867-3323162","2MASS J13523649-5055177","2MASS J23200751-6003545","2MASS J22485296-2850026","2MASS J15305186-5851353","2MASS J15463191-4714003","2MASS J01322625-2154172","2MASS J03033668-2535329","2MASS J04210050-3551207","2MASS J00160199-4815392","2MASS J23081954-1524354","2MASS J03180400-3024113","2MASS J05332802-4257205","2MASS J23544630-2146282","2MASS J07000950-2847022","2MASS J02164119-3059181","2MASS J04091567-5322254","2MASS J08095807-5258054","2MASS J01531133-2105433","2MASS J10394540-4430368","2MASS J06131330-2742054","2MASS J15103572-4258368","2MASS J06352229-5737349","2MASS J02052361-2804116","2MASS J15420677-1928167","2MASS J06074375-2544414","2MASS J06380166-3759078","2MASS J03122972-3805204","2MASS J23361587-4835006","2MASS J08142257-2542187","2MASS J06255610-6003273","2MASS J22480446-2422075","2MASS J04221249-5726011","2MASS J00012581-1656541","2MASS J05543040-1942056","2MASS J10415064-3637507","2MASS J10563892-1552540","2MASS J11000281-3506367","2MASS J13354218-1815123","2MASS J23002355-3107113","2MASS J10453930-1906508","2MASS J23170018-2323461","2MASS J11343803-2352146","2MASS J09444731-1812489","2MASS J07080702-2248471","2MASS J07184418-2616172","2MASS J08383373-2843261","2MASS J10305083-3546393","2MASS J01214538-4642518","2MASS J07380970-3112192","2MASS J15244849-4929473","2MASS J13351149-4821258","2MASS J11143809-2732287","2MASS J13312239-3611342","2MASS J02395066-3407557","2MASS J12153072-3948426","2MASS J23184619-6115125","2MASS J02342120-5305366","2MASS J06105288-4324178","2MASS J01482616-5658414","2MASS J10114501-2425339","2MASS J06174711-3401118","2MASS J03023801-1809587","2MASS J14005697-3147498","2MASS J02125096-1741123","2MASS J06383370-4620293","2MASS J03082452-2410232","2MASS J23254206-4536351","2MASS J00231851-5053380","2MASS J12384914-3822527","2MASS J15120793-3941539","2MASS J03184548-4051343","2MASS J13304092-2039030","2MASS J00395880-4415117","2MASS J00081737-5705528","2MASS J10210813-1743382","2MASS J12092343-2646469","2MASS J01425576-4212124","2MASS J12423950-3620310","2MASS J15120816-3941593","2MASS J15283140-3308061","2MASS J04353618-2527347","2MASS J23003338-2357097","2MASS J13130939-4130396","2MASS J12404633-4333595","2MASS J08481567-4413480","2MASS J23003657-2358101","2MASS J06394106-3659024","2MASS J22250500-4752461","2MASS J11324124-2651559","2MASS J09585058-3553039","2MASS J00313696-3606504","2MASS J11453443-2021124","2MASS J13591045-1950034","2MASS J05172143-4252473","2MASS J14164754-4453210","2MASS J01220441-3337036","2MASS J00213729-4605331","2MASS J22464517-6318053","2MASS J03173505-2741472","2MASS J10093625-1750277","2MASS J10012381-3850245","2MASS J11211745-3446497","2MASS J04241156-2356365","2MASS J09373473-2547156","2MASS J23415077-4244557","2MASS J06240393-4605159","2MASS J14402075-4836585","2MASS J10583513-3108382","2MASS J11321898-1658071","2MASS J09260557-6319461","2MASS J08320059-5839290","2MASS J03253966-4259118","2MASS J04283571-2510088","2MASS J08472279-4047381","2MASS J10195126-4148457","2MASS J11211723-3446454","2MASS J22324192-2059354","2MASS J22512369-3419359","2MASS J09512334-1744243","2MASS J12304489-4622431","2MASS J23381743-4131037","2MASS J09423573-1914045","2MASS J15493833-4736340","2MASS J02365171-5203036","2MASS J02375278-5845110","2MASS J07205204-6210118","2MASS J14395877-5654455","2MASS J23574554-4548551","2MASS J22394404-3204180","2MASS J15244578-1707389","2MASS J15313988-2916278","2MASS J13275397-2657013","2MASS J09162598-6204160","2MASS J12133287-2555240","2MASS J22485448-5418515","2MASS J02222560-3433184","2MASS J02054859-3010361","2MASS J04022354-6121395","2MASS J02110295-3540044","2MASS J15480325-5811119","2MASS J07492391-3548271","2MASS J03355876-4507483","2MASS J22524813-2847422","2MASS J10362843-2827153","2MASS J01452133-3957204","2MASS J02340367-3033399","2MASS J00571247-6415240","2MASS J10515889-3201200","2MASS J13162758-3256169","2MASS J10093664-1748248","2MASS J01091250-2441209","2MASS J13432925-5249514","2MASS J11114705-5620234","2MASS J07203020-4055327","2MASS J13044379-6215263","2MASS J13525350-1820165","2MASS J14252913-4113323","2MASS J11541839-3733097","2MASS J22451043-2306179","2MASS J00452814-5137339","2MASS J03141813-2309297","2MASS J22481735-3647233","2MASS J00052498-5002529","2MASS J02395671-3828001","2MASS J23432682-3446577","2MASS J01551106-3205250","2MASS J15000953-2905275","2MASS J15082343-2351371","2MASS J14493338-2606205","2MASS J00454435-4732567","2MASS J02414730-5259306","2MASS J06445365-1631117","2MASS J02173414-5359204","2MASS J09183254-3125550","2MASS J03574906-3754038","2MASS J13445511-4535187","2MASS J13004995-3522179","2MASS J07552391-1529533","2MASS J07210816-2452223","2MASS J09484855-3513340","2MASS J11515536-2729104","2MASS J07065772-5353463","2MASS J15363450-3754223","2MASS J02175673-3537009","2MASS J01430325-3840074","2MASS J10263826-1651183","2MASS J10172689-5354265","2MASS J00200837-1703409","2MASS J11205990-1701485","2MASS J04534057-2124147","2MASS J11412152-3624346","2MASS J11322232-4627567","2MASS J22382544-2921244","2MASS J12174675-3904047","2MASS J02534689-6135184","2MASS J22554384-3022392","2MASS J05475019-3419138","2MASS J00432603-4117337","2MASS J14133236-6207333","2MASS J09223972-1856017","2MASS J08532867-3924409","2MASS J10374532-2746388","2MASS J04464970-6034109","2MASS J15500679-4525213","2MASS J02111797-6313413","2MASS J04364086-2721180","2MASS J05531299-4505119","2MASS J05084435-4530078","2MASS J10442131-6112384","2MASS J03111537-4631033","2MASS J09395912-5027235","2MASS J06271343-2550529","2MASS J15202039-1958310","2MASS J11410969-3856133","2MASS J05154667-3117456","2MASS J12043659-3816249","2MASS J05502140-2808488","2MASS J00043643-4044020","2MASS J11293463-3133289","2MASS J12111697-1958213","2MASS J04422244-5459385","2MASS J23483610-2739385","2MASS J11293479-3133263","2MASS J04530132-5643432","2MASS J23595135-3406422","2MASS J00251465-6130483","2MASS J03040452-2022433","2MASS J12072738-3247002","2MASS J07361202-5155213","2MASS J13193255-4245301","2MASS J07232075-6006132","2MASS J09581823-2942342","2MASS J23241131-1745504","2MASS J09483601-3831187","2MASS J07401183-4257406","2MASS J06374033-3009187","2MASS J09424960-6337560","2MASS J13233804-2554449","2MASS J13382562-2516466","2MASS J02543316-5108313","2MASS J23414357-5156372","2MASS J10342468-2819189","2MASS J01300506-2545082","2MASS J09444537-3632379","2MASS J22450004-3315258","2MASS J06320879-2701578","2MASS J04224772-1758239","2MASS J23333672-4213219","2MASS J07181403-5229297","2MASS J08224744-5726530","2MASS J03504517-4826160","2MASS J03292151-3844029","2MASS J12410327-4655234","2MASS J14172590-4018154","2MASS J04593230-6153042","2MASS J22032712-5038382","2MASS J01232479-3045339","2MASS J15095591-2359002","2MASS J05445704-2136561","2MASS J12063910-4427535","2MASS J09164398-2447428","2MASS J12471005-2222369","2MASS J00492903-6102326","2MASS J14024670-2431502","2MASS J02363272-3436312","2MASS J12383713-2703348","2MASS J11035593-5258385","2MASS J05484520-4555421","2MASS J01244748-2615153","2MASS J02133742-3512238","2MASS J05263869-4419478","2MASS J12135547-6238568","2MASS J00090428-2707196","2MASS J22475328-3351264","2MASS J08571420-1935035","2MASS J15540080-4303097","2MASS J22495368-5140123","2MASS J00393579-3816584","2MASS J06134717-2354250","2MASS J08163748-4212259","2MASS J02081809-3732203","2MASS J06454204-4216054","2MASS J05274593-2848040","2MASS J04363984-2722057","2MASS J03312709-2351301","2MASS J02163510-3058073","2MASS J11525821-3519047","2MASS J09201528-4917533","2MASS J14035157-4241528","2MASS J14493159-2606322","2MASS J10401845-2930228","2MASS J14092718-3055490","2MASS J15325031-5410276","2MASS J01331729-5141395","2MASS J04102815-5336078","2MASS J10222501-6010293","2MASS J23553241-5124336","2MASS J11295624-4242253","2MASS J00155808-1636578","2MASS J02172869-3213158","2MASS J23074670-2754229","2MASS J07253847-3158160","2MASS J23411633-2507106","2MASS J04480066-5041255","2MASS J13425569-4356565","2MASS J06243759-2801490","2MASS J08593169-4726097","2MASS J01553215-1531215","2MASS J13004334-5209409","2MASS J04142488-6227375","2MASS J00091993-2114411","2MASS J12315745-5032433","2MASS J05532281-3434402","2MASS J15404341-5101357","2MASS J14550632-4147248","2MASS J05075978-4744135","2MASS J11554911-3816491","2MASS J14170146-2051530","2MASS J11234697-5257393","2MASS J03531971-3703587","2MASS J22372480-2804504","2MASS J09365617-2526259","2MASS J02141859-3033472","2MASS J07381900-3408289","2MASS J10522635-2241154","2MASS J22404307-4359003","2MASS J04504153-3116296","2MASS J06342590-5234399","2MASS J11463269-4029476","2MASS J01402677-1534191","2MASS J01410363-4338099","2MASS J06164468-1635297","2MASS J13132406-5715536","2MASS J04212639-2054054","2MASS J06162084-3509125","2MASS J00421695-3643053","2MASS J01335800-1738235","2MASS J06123673-4729329","2MASS J13200391-3524437","2MASS J04423751-2146570","2MASS J12020780-6034086","2MASS J23272868-3754115","2MASS J23521054-1939159","2MASS J13092037-4009264","2MASS J06042035-5518468","2MASS J22021626-4210329","2MASS J07565395-4538145"]

        overlap_name = []
        overlap_data = []
        for star in sak_targs:
           check = soutput_star_data.get_single_star_data(star)
           if check:
               overlap_name.append(star)
               overlap_data.append(check)
        print("Number of SAKHMET stars in Hypatia: ", len(overlap_name))
        return overlap_name, overlap_data

#Since Tsuji16b has absolute data and no Fe, it's not being read in -- this checks the overlap with other datasets to manually add into histogram
run_tsuji_check = False
def tsuji_overlap(run_tsuji: bool = run_tsuji_check):
    if run_tsuji:
        tsuji_targs = ["GJ 15A","GJ 54.1","GJ 105B","GJ 166C","GJ 176","GJ 179","GJ 205","GJ 212","GJ 229","GJ 231.1B","GJ 250B","GJ 273","GJ 324B","GJ 338A","GJ 338B","GJ 380","GJ 406","GJ 411","GJ 412A","GJ 436","GJ 526","GJ 581","GJ 611B","GJ 649","GJ 686","GJ 687","GJ 725A","GJ 725B","GJ 752B","GJ 768.1 C","GJ 777B","GJ 783.2B","GJ 797B","GJ 809","GJ 820B","GJ 849","GJ 873","GJ 876","GJ 880","GJ 884","GJ 1002","GJ 1245B","G 102-4","HIP 12961","HIP 57050","HIP 79431","2MASS J02530084+1652532","LP 412-31","2MASSI J1835379+325954"]
        tsu_data = []
        tsu_name = []

        for star in tsuji_targs:
           check = target_star_data.get_single_star_data(star)
           if check:
               tsu_name.append(star)
               tsu_data.append(check)
        print("Number of stars that overlap with Tsuji data:", len(tsu_name))
        print("Number of stars to be added to C and O:", 49-len(tsu_name))

# No more need to add in Tsuji abundances, Abia was a bad idea
def mdwarf_histogram(self):
    ordered_list_of_bins = get_hist_bins(available_bins=self.available_bins,
                                         is_element_id="each elemental abundance" in self.description)
    if 'Fe' in ordered_list_of_bins:
        ordered_list_of_bins.remove('Fe')
    hits = [0]
    hits.extend([self.__getattribute__(bin_name) for bin_name in ordered_list_of_bins[1:]])
    ordered_list_of_bins.insert(2, '13C')
    hits.insert(2, 2)
    ordered_list_of_bins.insert(5, 'F')
    hits.insert(5, 0)
    ordered_list_of_bins.remove('NLTE_Sr_II')
    hits.pop(-2)
    print(ordered_list_of_bins)
    print(hits)
    baseline_hits = [0, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    threshold_hits = [0, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    base_plus_hits = [sum(x) for x in zip(baseline_hits, hits)]
    thresh_plus_hits = [sum(x) for x in zip(threshold_hits, hits)]
    ind = np.arange(len(ordered_list_of_bins))
    width = 0.8
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    total_num = self.__getattribute__('Fe')
    rects_base = plt.bar(ind, base_plus_hits, width, color='firebrick', label="SAKHMET Mission (+300 M-Dwarfs)")
    rects_thresh = plt.bar(ind, thresh_plus_hits, width, color='salmon', label="Threshold Mission (+125 M-Dwarfs)")
    rects_data = plt.bar(ind, hits, width, color="grey", label="Current Data for "+str(total_num)+" M-Dwarfs")
    ax.set_xlabel('Spectroscopic Abundances for M-Dwarfs (excluding Fe)', fontsize=15)
    ax.set_ylabel('Number of Stars with Measured Element X', fontsize=14)
    ax.set_ylim([0.0, np.max(baseline_hits) + 600.])
    ax.set_xlim([0.0, float(len(ordered_list_of_bins))])
    ax.set_xticks(ind)
    ax.set_xticklabels(tuple([name.replace('_', '') for name in ordered_list_of_bins]), fontsize=13)
    ax.legend(loc='upper left', scatterpoints=1, fontsize=12)
    #ax.text(50, 9000, "FGKM-type Stars Within 500pc: " + str(np.max(hits)), fontsize=20, fontweight='bold',
    #        color='#4E11B7')
    #ax.text(50, 8000, "Literature Sources: +230", fontsize=20, fontweight='bold', color='#4E11B7')
    #ax.text(50, 7000, "Number of Elements/Species: " + str(len(ordered_list_of_bins) - 1), fontsize=20,
    #       fontweight='bold', color='#4E11B7')
    autolabel(rects_data)
    # plt.title(self.description)
    # ax.show()
    ax.set_aspect('auto')
    name = "mdwarf24-bigHist-" + str(total_num) + ".pdf"
    file_name = os.path.join(histo_dir, name)
    fig.savefig(file_name)
    print("Number of elements", len(ordered_list_of_bins))
    return ordered_list_of_bins, rects_base, rects_thresh


mdwarf_histogram(stats.star_count_per_element)
# Note to self: To run this, run directly in a Python terminal
