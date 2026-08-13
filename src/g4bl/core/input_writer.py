from g4bl.core.shapes import Shape

class InputWriter:
    def __init__(self, targets: list[Shape], beam_off: bool, muon_num: int, momentum: float, mom_err: float, optional_params: dict = None, instance: str = ""):
        self.targets = targets
        self.muon_num = muon_num
        self.momentum = momentum
        self.mom_err = mom_err
        self.optional_params = optional_params
        self.instance = instance
        self.input_string = ""
        if not beam_off:
            self.beam_block()
        self.material_block()

    def beam_block(self):
        # current default parameters for the port 4 beam, optionally can be overriden IF nceessary but other parameters are REQUIRED. 
        params = {
            "particle": "mu-",
            "spot_size": 15.0,
            "splay": 0,
            "splayX": 0,
            "splayY": 0,
        }
        # required parameters
        params["muon_num"] = self.muon_num
        params["momentum"] = self.momentum
        params["mom_err"] = self.mom_err
        if self.optional_params is not None:
            params.update(self.optional_params)

        beam_lines = [
            f"param -unset particles={params['particle']}",
            f"param -unset stats={params['muon_num']}",
            "param -unset firstEvent=1",
            f"param -unset P_inj={params['momentum']}",
            f"param -unset spot={params['spot_size']}",
            f"param -unset splay={params['splay']}",
            f"param -unset splayX={params['splayX']}",
            f"param -unset splayY={params['splayY']}",
            f"param -unset bite={params['mom_err']}",
            "physics FTFP_BERT spinTracking=1",
            (
                "beam gaussian "
                "particle=$particles "
                "nEvents=$stats "
                "firstEvent=$firstEvent "
                "beamX=0 beamY=0 beamZ=-0.01 "
                "meanMomentum=$P_inj "
                "sigmaX=$spot sigmaY=$spot "
                "sigmaXp=$splay sigmaYp=$splay "
                "sigmaP=$bite*$P_inj"
            ),
            "particlecolor mu-='0,1,0' e-='1,0,0' gamma='0,0,1'",
            f"beamlossntuple test file=out_file{self.instance}.txt require=PDGid==13 format=ascii\n",
        ]
        self.input_string = "\n".join(beam_lines)

    def material_block(self):
        if self.targets is None:
            return ""
        material_lines = []
        for target in self.targets:
            # shapes only create their input strings at this point to conserve memory. place_shape also creates sample position member.
            material_lines.append(target.place_shape())
        self.input_string += "\n".join(material_lines)

    @staticmethod
    def edit_custom_file(custom_file, p_inj, bite, stats):
        with open(custom_file, "r") as f:
            lines = f.readlines()

        with open(custom_file, "w") as f:
            for line in lines:
                if line.startswith("param -unset P_inj="):
                    f.write(f"param -unset P_inj={p_inj}\n")
                elif line.startswith("param -unset stats="):
                    f.write(f"param -unset stats={stats}\n")
                elif line.startswith("param -unset bite="):
                    f.write(f"param -unset bite={bite}\n")
                else:
                    f.write(line)