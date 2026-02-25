from g4bl.core.input_writer import InputWriter
import subprocess
from pathlib import Path
from g4bl.core.shapes import Sphere, Cylinder, Slab
from EVA.gui.windows.g4bl.g4bl_model import G4blModel
from g4bl.core.plotting import plot_per_shape, plot_combined

from srim import plot
file = r"C:\Users\chend\Desktop\Projects\g4beamline\demo_outputs\demo_input_file.g4bl"
muon_num = 3000
momentum = 27
mom_err = 0.04
# spot_size = 25.0

def main(model, shapes, vis_mode=False, beam_off=True, plot_individual=True):
    model.clear_output_directory()
    with open(file, "w") as f:
        writer = InputWriter(shapes, beam_off, muon_num, momentum, mom_err)
        f.write(writer.input_string)
    proc, log_path = model.run_g4bl(input_file=file, mypath=r"C:\Users\chend\Desktop\Projects\g4beamline\demo_outputs", vis_mode=vis_mode)
    proc.wait()
    error_descriptions = model.extract_geometry_error_descriptions(log_path)
    print(error_descriptions)
    if not vis_mode and not beam_off:
        model.process_sample_files(shapes)
        if plot_individual:
            plot_per_shape(model.final_results)
        else:
            plot_combined(model.final_results, model=model)
    model.clear_output_directory()

def case1(vis_mode, beam_off, plot_individual = False): 
    model = G4blModel()
    shapes = [
    Sphere("s1", "G4_Si", (0, 0, 2), "1,0,0", radius=(0, 1.5), num_samples=50),
    Cylinder("c1", "G4_Al", (0, 0, 4), "0,1,0", radius=(0, .5), length=2, num_samples=20),
    Sphere("s2", "Pb", (0, 0, 6.5), "0,0,1", radius=(0, 1.5), num_samples=40)
    ]
    main(model, shapes=shapes, vis_mode=vis_mode, beam_off=beam_off)

def case2(vis_mode, beam_off, shift = 0, plot_individual = False): 
    model = G4blModel()
    model.x_shift = shift
    shapes = [
    Slab(name="Beamline_window", material="Be", color="1,0,0", thickness=0.05, num_samples=50),
    Slab(name="Air_compressed", material="Air", color="0,1,0", thickness=0.067, num_samples=50),
    Slab(name="Alum", material="Al", color="0,0,1", thickness=0.05, num_samples=50),
    Slab(name="Copp", material="Cu", color="1,1,0", thickness=0.5, num_samples=50),
    Slab(name="Alum2", material="Al", color="0,0,1", thickness=0.05, num_samples=50),
        ]
    model.stack_layer_boundaries(shapes)
    main(model,shapes=shapes, vis_mode=vis_mode, beam_off=beam_off, plot_individual=plot_individual)

# case1(vis_mode=False, beam_off=False, plot_individual=True) # simple case that looks like an O2 molecule i forgot what its called
# case1(vis_mode=True, beam_off=True)

# case2(vis_mode=False, beam_off=False) # layer slabs similar to default EVA trim settings
case2(vis_mode=False, beam_off=False, shift= 0.167) # use shift param to align x axis with the EVA defaults

# case2(vis_mode=True, beam_off=False)