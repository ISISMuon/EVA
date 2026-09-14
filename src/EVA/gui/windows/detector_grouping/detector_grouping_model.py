class DetectorGroupingModel:
    def __init__(self):
        return

    def load_profile(self, groups: dict) -> list:
        """
        Load a detector grouping profile from dict stored in config

        Args:
            groups: dictionary containing detector groups
        """

        detector_grouping_data = []
        for group_name, detectors in groups.items():
            detectors_str = ",".join(str(det) for det in detectors)
            detector_grouping_data.append([group_name, detectors_str])

        return detector_grouping_data
