from g4bl.core.shapes import Shape

class InputWriter:
    def __init__(self, targets: list[Shape], beam_off: bool, muon_num: int, momentum: float, mom_err: float, optional_params: dict = None):
        self.targets = targets
        self.muon_num = muon_num
        self.momentum = momentum
        self.mom_err = mom_err
        self.optional_params = optional_params
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
                "beamX=0 beamY=0 beamZ=-10.0 "
                "meanMomentum=$P_inj "
                "sigmaX=$spot sigmaY=$spot "
                "sigmaXp=$splay sigmaYp=$splay "
                "sigmaP=$bite*$P_inj"
            ),
            "particlecolor mu-='0,1,0' e-='1,0,0' gamma='0,0,1'",
            "beamlossntuple test file=out_file require=PDGid==13 \n",
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
