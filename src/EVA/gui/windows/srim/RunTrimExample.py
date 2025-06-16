import matplotlib.pyplot as plt

import numpy as np
from scipy.optimize import curve_fit
import scipy.constants as sc
from scipy.interpolate import interp1d
import os  # used to execute external


# test bit from pysrim website
'''from srim import Ion, Layer, Target, TRIM
#import srim

# Construct a 3MeV Nickel ion
ion = Ion('Ni', energy=3.0e6)

# Construct a layer of nick 20um thick with a displacement energy of 30 eV
layer = Layer({
        'Ni': {
            'stoich': 1.0,
            'E_d': 30.0,
            'lattice': 0.0,
            'surface': 3.0
        }}, density=8.9, width=20000.0)

# Construct a target of a single layer of Nickel
target = Target([layer])

# Initialize a TRIM calculation with given target and ion for 25 ions, quick calculation
trim = TRIM(target, ion, number_ions=25, calculation=1)

# Specify the directory of SRIM.exe
# For windows users the path will include C://...
srim_executable_directory = 'c:/srim2013/'

# takes about 10 seconds on my laptop
results = trim.run(srim_executable_directory)
# If all went successfull you should have seen a TRIM window popup and run 25 ions!
# results is `srim.output.Results` and contains all output files parsed


'''

from srim import TRIM, Ion, Layer, Target, Material
#from srim.output import Results


# from degrader_dictionary2 import *


"""
    Calculates the stopping profile of muons in a sample.

    Needs srim to be installed goto www.srim.org


"""

def RunTRIM_Start():
    temp='asdg'
    SimPara = TRIMInit()
    SettingUp_TRIM()

def TRIMInit():

    """
        Initialises the 'DepthCalcLayersIntensity' class properties in the Mantid algorithm,
        including the input parameters such as sample thickness, materials and
        simulation type that are needed to calculate the profile.

    """

    # all length scales are in mm

    # target input
    #self.declareProperty("Sample Name", "Cu", direction=Direction.Input,doc="Sample Name")
    SimPara = {}
    print('hello')
    SimPara['SampleName'] = "Cu"

    #self.declareProperty("Sample Thickness (mm)", 5.0, direction=Direction.Input,doc="Target thickness in mm.")

    SimPara['SampleThickness'] = 1.0

    #self.declareProperty("Sample Density (g/cm^2)", 8.96, direction=Direction.Input)

    SimPara['SampleDensity'] = 8.96

    # Momentum Sim input
    #self.declareProperty("Simulation Type", "Both", StringListValidator(["Both", "Mono", "Momentum Spread"]),
    # direction=Direction.Input)

    SimPara['SimType'] = "MomSpread"

    #self.declareProperty("Momentum", 27.0, direction=Direction.Input, doc="in MeV/c")

    SimPara['Mom'] = 27.0

    #self.declareProperty("Momentum spread", 4.0, direction=Direction.Input, doc="in %")

    SimPara['MomSpread'] = 4.0

    #self.declareProperty("Scan Momentum", "No", StringListValidator(["No", "Yes"]),direction=Direction.Input)

    SimPara['ScanMom'] = False

    #self.declareProperty("Min Momentum", 15.0, direction=Direction.Input, doc="in MeV/c")

    SimPara['MinMom'] = 15.0

    #self.declareProperty("Max Momentum", 30.0, direction=Direction.Input, doc="in MeV/c")

    SimPara['MaxMom'] = 30.0

    #self.declareProperty("Step Momentum", 5.0, direction=Direction.Input, doc="in MeV/c")

    SimPara['StepMom'] = 5.0

    #self.declareProperty("SRIM.exe directory", "C:/SRIM-2013", direction=Direction.Input)

    SimPara['SRIMdir'] = "C:/SRIM2013"

    #self.declareProperty("TRIM output directory", "C:/SRIM-2013/SRIM Outputs", direction=Direction.Input)

    SimPara['TRIMOutputDir'] = "C:/SRIM2013/SRIM Outputs"

    #self.declareProperty("Stats for final run", 1000, direction=Direction.Input)

    SimPara['Stats'] = 1000

    return SimPara


def fermifunc(x, b, c, d):

    """
        Function that returns a standard logistic function. Called a fermi function.
    """

    return 1 / (1 + np.exp(-c * (x - b))) + d

def inversefermi(x, b, c, d):

    """
        Retruns the inverse of a logistic function.
    """

    return b - (1 / c) * np.log((1 / (x - d)) - 1)

def gaussian(x, amp, mean, sigma):

    """
        Function that returns the standard Gaussian distribution with mean,
        standard deviation and Gaussian amplitude as input parameters.
    """

    return amp * np.exp(-0.5 * ((x - mean) ** 2) / (sigma ** 2))

def exp(x, a, b):

    """
        Returns an exponential function which passes through (0,0.)
    """
    return np.exp(a * x - b) + -np.exp(-b)

def invexp(x, a, b):

    """
        Returns inverse of an exponential function that passes through (0,0).
    """

    return (1 / a) * (np.log(x + np.exp(-b)) + b)

def matdef(mat, rho, width):
    """
            Define material for simulation
    """
    # temp designation

    thickness = 0.5

    matlayer1 = Layer.from_formula(mat, density=rho, width=thickness * 1e7, phase=0)
    sample = Target([matlayer1])

    return sample

def matdef2(mat, rho, thickness):

    """
            Define material for simulation
    """

    LayerThickness = [0.05, 0.067, 0.05, thickness]
    LayerLabels = ['Window', 'air (compressed)', 'Al', 'Cu', 'Total']
    print(LayerLabels)

    beamwindow = Layer({'H': {'stoich': 8, 'E_d': 10, 'lattice': 3, 'surface': 2
                                  },
                            'C': {'stoich': 10, 'E_d': 28.0, 'lattice': 3.0,
                                  'surface': 7.41
                                  },
                            'O': {'stoich': 4, 'E_d': 28.0, 'lattice': 3.0,
                                  'surface': 2.0}},
                           density=1.4, width=LayerThickness[0] * 1e7, phase=0)

    # sample.append(beamwindow)

    air = Layer({'C': {'stoich': 1.24e-2, 'E_d': 28.0, 'lattice': 3.0,
                           'surface': 7.41
                           },
                     'O': {'stoich': 23.1781, 'E_d': 28.0, 'lattice': 3.0,
                           'surface': 2.0
                           },
                     'N': {'stoich': 75.5268, 'E_d': 28.0, 'lattice': 3.0,
                           'surface': 2.0
                           },
                     'Ar': {'stoich': 1.2827, 'E_d': 5.0, 'lattice': 1.0,
                            'surface': 2.0}}, density=1500 * 1.20479e-3, width=LayerThickness[1] * 1e7,
                    # air layer compressed from 150mm to 0.1mm to optimise bins
                    phase=1)

    # sample.append(air)

    Al_sample_holder = Layer.from_formula('Al', density=2.7, width=LayerThickness[2] * 1e7,
                                              phase=0)  # 0.016 mm = 160000Athick sample holder

    # sample.append(Al_sample_holder)

    matlayer1 = Layer.from_formula(mat, density=rho, width=LayerThickness[3] * 1e7, phase=0)

    # sample.append(matlayer1)
    sample = Target([beamwindow, air, Al_sample_holder, matlayer1])
    print(beamwindow)
    print(air)
    print(Al_sample_holder)
    print(sample)

    return sample, LayerThickness, LayerLabels

def iondef(Mom):
    # muon properties
    muM = 105.6583745  # mass o muon in MeV/c^2
    muMA = muM / 931.5  # mass of muon in atomic mass units
    # kintetic energy associatd with the momentum (relitavistic)
    Ek = np.sqrt(105.6583745 ** 2 + Mom ** 2) - 105.6583745

    print('Momentum=' + str(Mom) + ' Energy=' + str(Ek))

    # corresponding SRIM muon ion definitions
    muon_ion = Ion('H', Ek * 1e6,
                       muMA)  # define muon as Hydrogen ion with mass of muon, with a given kinetic energy

    return muon_ion

def RunTRIM(target, muon_ion, number_muon, SRIMdirectory, output_directory):
    # Run TRIM and output results in x1, y1, e1

    trimsim = TRIM(target, muon_ion, number_ions=number_muon, calculation=1)

    trimdataoutput = trimsim.run(SRIMdirectory)  # Simulation run by executing SRIM.exe in directory

    TRIM.copy_output_files(SRIMdirectory,
                           output_directory)  # ouput files from SRIM copied to desired output directory

    trimdata = trimdataoutput.range

    x1 = list(trimdata.depth / 1e7)  # muon ranges, converted from angstroms to mm.

    y1 = list(trimdata.ions)  # SRIM has weird units for y axis

    e1 = list(trimdata.ions)

    return x1, y1, e1

'''def SaveToWorkspace(x1, y1, e1, Name_WS, Title_WS, ):
    # Save results to a workspace of your choice

    WS_Temp = CreateWorkspace(x1, y1, DataE=e1, UnitX='Depth/mm', YUnitLabel='Number of Muons',
                              WorkspaceTitle=Title_WS)
    WS_Temp.getAxis(0).setUnit("Label").setLabel("Depth", "mm")
    NameA = 'WS_Temp'
    NameB = Name_WS
    RenameWorkspace(InputWorkspace=NameA, OutputWorkspace=NameB, OverwriteExisting=True)
    return'''

def BeamParameters():
    # defines momentum spread (using RIKEN is negative muon)
    # % momentum bite
    mombite = 4.0
    return mombite

'''def CreateMultiDimWorkspace(x1, y1, e1, NumDim, Name_WS, Title_WS):
    # creates a MultiDim workspace from the results of a TRIm Calc
    WS_Temp = CreateWorkspace(x1, y1, e1, WorkspaceTitle=Title_WS, UnitX='Depth/mm',
                              YUnitLabel='Number of muons', NSpec=NumDim)
    WS_Temp.getAxis(0).setUnit("Label").setLabel("Depth", "mm")
    NameA = 'WS_Temp'
    NameB = Name_WS
    RenameWorkspace(InputWorkspace=NameA, OutputWorkspace=NameB, OverwriteExisting=True)
    return'''

'''def CreateSumSpectra(Name_WS, NewName_WS):
    # Create a Summed Spectra with a name NewName_WS from a multi def workspace
    WS_Temp = SumSpectra(Name_WS)
    NameA = 'WS_Temp'
    NameB = NewName_WS
    RenameWorkspace(InputWorkspace=NameA, OutputWorkspace=NameB, OverwriteExisting=True)
    return'''

def CorrectToCounts(thickness, y1, TotalSimCounts):
    finalbins = thickness / 100.0
    for i in range(len(y1)):
        y1[i] = y1[i] * finalbins * TotalSimCounts
    return y1

def CalcProfileWithMomBite(sample, Mom, NFinal, Mombite, SRIMdirectory, output_directory):
    # Calculate the stopping profile for a nomial momentum with a % momentum bite defined
    # in BeamParameters

    sigmastep = 12  # 12 runs per momentum
    MomSigma = 0.01 * Mombite * Mom

    xres = []
    yres = []
    eres = []
    WriteWKSP = False

    for i in range(sigmastep + 1):
        P = Mom - 3 * MomSigma + i * 0.5 * MomSigma  # momentum for each iteration

        # Number of simulated muons dependent on Gaussian distribution of muon momentum

        NE = NFinal * (1.0 / (np.sqrt(2.0 * np.pi) * MomSigma)) * np.exp(
            -0.5 * (P - Mom) ** 2 / (MomSigma ** 2))
        print('Number of Counts', NE)

        x1, y1, e1, Temp_WS = CalcProfileWithMonoMom(sample, P, NE, SRIMdirectory, output_directory, WriteWKSP)

        xres.extend(x1)
        yres.extend(y1)
        eres.extend(e1)

    wksp_str = ''

    '''Name_WS = 'TRIM_' + mat + '_' + str(Mom) + '_' + str(Mombite)
    Title_WS = 'TRIM Calculation for with a momentum of ' + str(Mom) + ', ' + str(
        Mombite) + '% into ' + mat + ' Counts = ' + str(NE)
    CreateMultiDimWorkspace(xres, yres, eres, sigmastep + 1, Name_WS, Title_WS)

    Temp_WS = ADS.retrieve(Name_WS)'''
    length = sigmastep + 1
    #axis = mantid.api.TextAxis.create(length)
    for i in range(length):
        P = Mom - 3 * MomSigma + i * 0.5 * MomSigma
        #axis.setLabel(i, str(P) + ' MeV/c')
    #Temp_WS.replaceAxis(1, axis)

    '''Name_WS_sum = 'TRIM_' + mat + '_' + str(Mom) + '_' + str(Mombite) + '_Sum'
    WS_Temp = CreateSumSpectra(Name_WS, Name_WS_sum)'''

    # FitPeakGauss(Name_WS)
    Name_WS_sum = 'umm'

    return Name_WS_sum

def CalcProfileWithMonoMom(sample, Mom, NFinal, SRIMdirectory, output_directory, SaveWKSP):
    # Calculate the stopping profile for a monochromatic momentum

    muon_ion = iondef(Mom)

    mat = 'Cu'

    Name_WS = 'TRIM_' + mat + '_' + str(Mom)
    Title_WS = 'TRIM Calculation for a mono momentum of ' + str(Mom) + ' into ' + mat + ' Counts = ' + str(
        NFinal)

    x1, y1, e1 = RunTRIM(sample, muon_ion, NFinal, SRIMdirectory, output_directory)

    thickness = 0.5

    y1 = CorrectToCounts(thickness, y1, NFinal)

    if (SaveWKSP):
        print('SaveWKSP=', SaveWKSP)
        #SaveToWorkspace(x1, y1, e1, Name_WS, Title_WS)

    return x1, y1, e1, Name_WS

def FitPeakGauss(WS_Name):
    # Need to get the workspace back
    # does not work yet
    # wsMax = MaxMin(WS_Name)

    # print('Max Value',wsMax.readY(0))
    # FitGaussian(WS_Name)

    return

def my_range(start, end, step):
    # sets a reange of momenta
    while start <= end:
        yield start
        start += step

def ScanMom(MomMin, MomMax, MomStep, Mombite, sample, NFinal, Simtype, SRIMdirectory, output_directory):
    # Scans the stopping profile fro a range of momenta
    for MomScan in my_range(MomMin, MomMax, MomStep):

        print(MomScan)
        if Simtype == "Both" or Simtype == "Mono":
            writeWKSP = True
            del1, del2, del3, Name_WS = CalcProfileWithMonoMom(sample, MomScan, NFinal, SRIMdirectory,
                                                               output_directory, writeWKSP)
            #Plot_Results(Name_WS, LayerThickness, LayerLabels)
            #Name_WS_Com = CreateLayerWKSP(Name_WS, LayerThickness, LayerLabels)
            #Plot_Results_Com(Name_WS_Com, LayerThickness, LayerLabels)
            #SumComWKSP(Name_WS_Com, LayerLabels)
        if Simtype == "Both" or Simtype == "Momentum Spread":
            Name_WS = CalcProfileWithMomBite(sample, MomScan, NFinal, Mombite, SRIMdirectory, output_directory)
            #Plot_Results(Name_WS, LayerThickness, LayerLabels)
            #Plot_Results(Name_WS, LayerThickness, LayerLabels)
            #Name_WS_Com = CreateLayerWKSP(Name_WS, LayerThickness, LayerLabels)
            #Plot_Results_Com(Name_WS_Com, LayerThickness, LayerLabels)
            #SumComWKSP(Name_WS_Com, LayerLabels)

def layerSeparation():
    return

'''def Plot_Results(Name_WS, LayerThickness, LayerLabels):

    Temp_WS = ADS.retrieve(Name_WS)

    fig, axes = plt.subplots(edgecolor='#ffffff', num=Name_WS, subplot_kw={'projection': 'mantid'})
    print('here', len(LayerThickness))
    axes.plot(Temp_WS, color='#1f77b4', label=Name_WS, specNum=1)
    axes.set_title(Name_WS)
    axes.set_xlabel('Depth ($mm$)')
    axes.set_ylabel('Number of Muons')
    axes.legend().set_draggable(True)

    sumthickness = 0.0
    for i in range(len(LayerThickness)):
        sumthickness = sumthickness + LayerThickness[i]
        plt.axvline(x=sumthickness, color='k', linestyle='--')
        plt.text(sumthickness, 3, LayerLabels[i], horizontalalignment='left', rotation='vertical')

    fig.show()

    return

def Plot_Results_Com(Name_WkSp_Com, LayerThickness, LayerLabels):

    Temp_WS = ADS.retrieve(Name_WkSp_Com)

    fig, axes = plt.subplots(edgecolor='#ffffff', num=Name_WkSp_Com, subplot_kw={'projection': 'mantid'})
    print('here', len(LayerThickness))
    for i in range(1, len(LayerLabels)):
        print(i)
        axes.plot(Temp_WS, label=LayerLabels[i - 1], specNum=i)

    axes.set_title(Name_WkSp_Com)
    axes.set_xlabel('Depth ($mm$)')
    axes.set_ylabel('Number of Muons')
    axes.legend().set_draggable(True)

    sumthickness = 0.0
    for i in range(len(LayerThickness)):
        print(LayerThickness[i])
        print(LayerLabels[i])
        sumthickness = sumthickness + LayerThickness[i]
        plt.axvline(x=sumthickness, color='k', linestyle='--')
        plt.text(sumthickness, 50, LayerLabels[i], horizontalalignment='left', rotation='vertical')
        # plt.Annotation

    fig.show()

    return

def CreateLayerWKSP(Name_WS, LayerThickness, LayerLabels):
    Temp_WS = ADS.retrieve(Name_WS)

    nbins = len(Temp_WS.readX(0))
    output_ws = WorkspaceFactory.create("Workspace2D", NVectors=len(LayerThickness) + 1, XLength=nbins,
                                        YLength=nbins)

    for j in range(len(LayerThickness) + 1):
        for i in range(nbins):
            output_ws.dataX(j)[i] = Temp_WS.readX(0)[i]

    for i in range(nbins):
        # print(len(LayerThickness),i)
        output_ws.dataY(len(LayerThickness))[i] = Temp_WS.readY(0)[i]
    # output_ws.dataX=Temp_WS.dataX

    boundaryIndex = []
    boundaryIndex.append(0)
    sumthickness = 0.0
    binsize = Temp_WS.readX(0)[2] - Temp_WS.readX(0)[1]
    for i in range(len(LayerThickness)):
        sumthickness = sumthickness + LayerThickness[i]
        boundaryIndex.append(int(round(sumthickness / binsize)))

    for i in range(len(LayerThickness)):
        output_ws.dataY(i)[boundaryIndex[i]:boundaryIndex[i + 1]] = Temp_WS.readY(0)[
                                                                    boundaryIndex[i]:boundaryIndex[i + 1]]

    length = len(LayerThickness) + 1
    axis = mantid.api.TextAxis.create(length)
    output_ws.getAxis(0).setUnit("Label").setLabel("Depth", "mm")
    # output_ws.getAxis(1).setUnit("Label").setLabel("Number of muons", "")
    for i in range(length):
        axis.setLabel(i, LayerLabels[i])
    output_ws.replaceAxis(1, axis)

    # produce the workspace
    output_ws_name = Name_WS + '_com'
    print('outputworkspacename', output_ws_name)
    mtd.addOrReplace(output_ws_name, output_ws)

    return output_ws_name


def SumComWKSP(Name_WkSp_Com, LayerLabels):

    Temp_WS = ADS.retrieve(Name_WkSp_Com)
    # Integrate 10 spectra over all X values
    intg = Integration(Temp_WS)
    intg2 = Integration(Temp_WS)
    length = len(LayerLabels)

    # Check the result
    print('The result workspace has {0} spectra'.format(intg.getNumberHistograms()))

    for i in range(len(LayerLabels)):
        print('% in', LayerLabels[i], ' is {0}'.format(100.0 * intg.readY(i)[0] / intg.readY(length - 1)[0]))
        intg2.dataY(i)[0] = 100.0 * intg.readY(i)[0] / intg.readY(length - 1)[0]

    NameB = Name_WkSp_Com + '_Area'
    RenameWorkspace(InputWorkspace=intg, OutputWorkspace=NameB, OverwriteExisting=True)
    NameB = Name_WkSp_Com + '_Area_Percent'
    RenameWorkspace(InputWorkspace=intg2, OutputWorkspace=NameB, OverwriteExisting=True)
    return'''

def SettingUp_TRIM():


    #mat = self.getProperty("Sample Name").value  # sample chemical formuloa string
    mat = 'Cu'
    #rho = self.getProperty("Sample Density (g/cm^2)").value  # sample density
    rho = 6.4
    #thickness = self.getProperty("Sample Thickness (mm)").value  # sample thickness
    thickness = 5.0

    # Simulation setup
    #NFinal = self.getProperty("Stats for final run").value
    NFinal = 1000
    #Mom = self.getProperty("Momentum").value  # Mean Momentum
    Mom = 27.0
    #Mombite = self.getProperty("Momentum spread").value  # Momentum spread 4% for RIKEN
    Mombite = 4.0
    #Simtype = self.getProperty("Simulation Type").value
    Simtype = 'Mono'

    #ScanMomFlag = self.getProperty("Scan Momentum").value
    ScanMomFlag = 'No'

    #ScanMinMom = self.getProperty("Min Momentum").value
    ScanMinMom = 20.0
    #ScanMaxMom = self.getProperty("Max Momentum").value
    ScanMaxMom = 30.0
    #ScanStepMom = self.getProperty("Step Momentum").value
    ScanStepMom = 2.0

    # SRIM directories "C:/SRIM2013/SRIM Outputs" "C:/SRIM2013"
    #SRIMdirectory = self.getProperty("SRIM.exe directory").value  # SRIM.exe directory
    SRIMdirectory = 'C:/SRIM2013'
    #output_directory = self.getProperty("TRIM output directory").value  # SRIM ouput file directory
    output_directory = 'C:/SRIM2013/SRIM Outputs'

    sample, LayerThickness, LayerLabels = matdef2(mat, rho, thickness)

    print(" Simulation Type: ", Simtype)

    if Simtype == "Both" or Simtype == "Mono":
        WriteWKSP = True
        del1, del2, del3, Name_WS = CalcProfileWithMonoMom(sample, Mom, NFinal, SRIMdirectory, output_directory,
                                                           WriteWKSP)
        #Plot_Results(Name_WS, LayerThickness, LayerLabels)
        #Name_WS_Com = CreateLayerWKSP(Name_WS, LayerThickness, LayerLabels)
        #Plot_Results_Com(Name_WS_Com, LayerThickness, LayerLabels)
        #SumComWKSP(Name_WS_Com, LayerLabels)

    if Simtype == "Both" or Simtype == "Momentum Spread":
        Name_WS = CalcProfileWithMomBite(sample, Mom, NFinal, Mombite, SRIMdirectory, output_directory)

        #Plot_Results(Name_WS, LayerThickness, LayerLabels)

        #Name_WS_Com = CreateLayerWKSP(Name_WS, LayerThickness, LayerLabels)

        #Plot_Results_Com(Name_WS_Com, LayerThickness, LayerLabels)

        #SumComWKSP(Name_WS_Com, LayerLabels)

    if ScanMomFlag == "Yes":
        ScanMom(ScanMinMom, ScanMaxMom, ScanStepMom, Mombite, sample, NFinal, Simtype, SRIMdirectory,
                output_directory)

    return


