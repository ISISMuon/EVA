from EVA.core.data_loading import load_data
from EVA.core.app import get_config


def read_multi_run(run_list):
    dir = get_config()["general"]["working_directory"]
    e_corr = get_config()["corrections"]["detector_specific"]
    norm = get_config()["corrections"]["normalisation"]
    binning = get_config()["corrections"]["binning"]

    result = [load_data.load_run(run_num, working_directory=dir, energy_corrections=e_corr,
                                 normalisation=norm, binning=binning) for run_num in run_list]

    runs, flags = list(zip(*result))

    # iterate through loaded runs to remove failed ones:
    blank_runs = []
    norm_failed_runs = []
    good_runs = []

    for i, run in enumerate(runs):
        if flags[i]["no_files_found"]:
            blank_runs.append(run)
        else:
            if flags[i]["norm_by_spills_error"]: # if normalisation failed, remove run
                norm_failed_runs.append(run)
            else:
                good_runs.append(run)

    return good_runs, blank_runs, norm_failed_runs

"""
def ReadMultiRun(RunList):
    #print('in ReadMultiRun')
    # keep current load_data safe
    flag = 0
    if globals.Normalise_do_not:
        try:
            tempx_GE1 = globals.x_GE1
            tempy_GE1 = globals.y_GE1
            tempx_GE2 = globals.x_GE2
            tempy_GE2 = globals.y_GE2
            tempx_GE3 = globals.x_GE3
            tempy_GE3 = globals.y_GE3
            tempx_GE4 = globals.x_GE4
            tempy_GE4 = globals.y_GE4
        except:
            print('Ooops')
    elif globals.Normalise_counts:
        try:
            tempx_GE1 = globals.x_GE1_Ncounts
            tempy_GE1 = globals.y_GE1_Ncounts
            tempx_GE2 = globals.x_GE2_Ncounts
            tempy_GE2 = globals.y_GE2_Ncounts
            tempx_GE3 = globals.x_GE3_Ncounts
            tempy_GE3 = globals.y_GE3_Ncounts
            tempx_GE4 = globals.x_GE4_Ncounts
            tempy_GE4 = globals.y_GE4_Ncounts
        except:
            print('Ooops')
    elif globals.Normalise_spill:
        try:
            tempx_GE1 = globals.x_GE1_NEvents
            tempy_GE1 = globals.y_GE1_NEvents
            tempx_GE2 = globals.x_GE2_NEvents
            tempy_GE2 = globals.y_GE2_NEvents
            tempx_GE3 = globals.x_GE3_NEvents
            tempy_GE3 = globals.y_GE3_NEvents
            tempx_GE4 = globals.x_GE4_NEvents
            tempy_GE4 = globals.y_GE4_NEvents
        except:
            print('Ooops')

    # load data
    datax_GE1 = []
    datay_GE1 = []
    datax_GE2 = []
    datay_GE2 = []
    datax_GE3 = []
    datay_GE3 = []
    datax_GE4 = []
    datay_GE4 = []

    lenRunList = len(RunList)

    for i in range(lenRunList):
        #print('i',RunList[i])
        load_data.load_data(RunList[i])
        #Normalise.Normalise()
        if globals.Normalise_do_not:
            try:
                datax_GE1.append(globals.x_GE1)
                datay_GE1.append(globals.y_GE1)
                datax_GE2.append(globals.x_GE2)
                datay_GE2.append(globals.y_GE2)
                datax_GE3.append(globals.x_GE3)
                datay_GE3.append(globals.y_GE3)
                datax_GE4.append(globals.x_GE4)
                datay_GE4.append(globals.y_GE4)
            except:
                print('Ooops')
        elif globals.Normalise_counts:
            try:
                datax_GE1.append(globals.x_GE1_Ncounts)
                datay_GE1.append(globals.y_GE1_Ncounts)
                datax_GE2.append(globals.x_GE2_Ncounts)
                datay_GE2.append(globals.y_GE2_Ncounts)
                datax_GE3.append(globals.x_GE3_Ncounts)
                datay_GE3.append(globals.y_GE3_Ncounts)
                datax_GE4.append(globals.x_GE4_Ncounts)
                datay_GE4.append(globals.y_GE4_Ncounts)

            except:
                print('Ooops')
        elif globals.Normalise_spill:
            try:
                datax_GE1.append(globals.x_GE1_NEvents)
                datay_GE1.append(globals.y_GE1_NEvents)
                datax_GE2.append(globals.x_GE2_NEvents)
                datay_GE2.append(globals.y_GE2_NEvents)
                datax_GE3.append(globals.x_GE3_NEvents)
                datay_GE3.append(globals.y_GE3_NEvents)
                datax_GE4.append(globals.x_GE4_NEvents)
                datay_GE4.append(globals.y_GE4_NEvents)
            except:
                print('Ooops')

        # raise flag if any detectors failed to load
        if not all([globals.flag_d_GE1, globals.flag_d_GE2, globals.flag_d_GE3, globals.flag_d_GE4]):
            flag = 1

    if globals.Normalise_do_not:
        try:
            globals.x_GE1 = tempx_GE1
            globals.y_GE1 = tempy_GE1
            globals.x_GE2 = tempx_GE2
            globals.y_GE2 = tempy_GE2
            globals.x_GE3 = tempx_GE3
            globals.y_GE3 = tempy_GE3
            globals.x_GE4 = tempx_GE4
            globals.y_GE4 = tempy_GE4
        except:
            print('Ooops')
    elif globals.Normalise_counts:
        try:
            globals.x_GE1_Ncounts = tempx_GE1
            globals.y_GE1_Ncounts = tempy_GE1
            globals.x_GE2_Ncounts = tempx_GE2
            globals.y_GE2_Ncounts = tempy_GE2
            globals.x_GE3_Ncounts = tempx_GE3
            globals.y_GE3_Ncounts = tempy_GE3
            globals.x_GE4_Ncounts = tempx_GE4
            globals.y_GE4_Ncounts = tempy_GE4
        except:
            print('Ooops')
    elif globals.Normalise_spill:
        try:
            globals.x_GE1_NEvents = tempx_GE1
            globals.y_GE1_NEvents = tempy_GE1
            globals.x_GE2_NEvents = tempx_GE2
            globals.y_GE2_NEvents = tempy_GE2
            globals.x_GE3_NEvents = tempx_GE3
            globals.y_GE3_NEvents = tempy_GE3
            globals.x_GE4_NEvents = tempx_GE4
            globals.y_GE4_NEvents = tempy_GE4
        except:
            print('Ooops')


    return flag, datax_GE1, datay_GE1, datax_GE2, datay_GE2, datax_GE3, datay_GE3, datax_GE4, datay_GE4

"""
