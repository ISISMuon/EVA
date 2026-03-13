from PyQt6.QtWidgets import QTableWidgetItem


class TrimFitPresenter:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.view.layer_table.update_contents(self.format_model_layers(), round_to=4)
        self.view.layer_table.append_row()
        self.view.plot.update_plot(self.model.fig, self.model.ax)

        self.view.momentum_line_edit.setText("20")

        self.view.layer_table.cellClicked.connect(self.on_cell_clicked)
        self.view.fit_button.clicked.connect(self.start_fit)

    def start_fit(self):
        """
        Gets all simulation parameters from user and starts the simulation
        Returns:

        """

        self.model.momentum = float(self.view.momentum_line_edit.text())

        try:
            self.model.start_trim_simulation()
        except Exception as e:
            self.view.display_error_message(message=f"SRIM error: {e}")
            raise e

        self.view.trim_plot.update_plot(
            *self.model.plot_components(
                momentum_index=0, momentum=str(self.model.momentum)
            )
        )

    def format_model_layers(self) -> list[list[str | float]]:
        """
        Formats the layers in TrimFitModel to a format compatible with the BaseTable's update_contents() method.

        Returns:
            Formatted array containing the layer data in TrimFitModel.
        """
        return [
            [layer["name"], layer["thickness"], layer.get("density", " ")]
            for layer in self.model.input_layers
        ]

    def on_cell_clicked(self, row: int):
        """
        Adds a row to the table when cell in last row is clicked

        Args:
            row: row number
        """
        table = self.view.layer_table
        if row == table.rowCount() - 1:  # if cell on last row is edited
            self.view.layer_table.append_row()

    def get_layers(self) -> list[dict] | None:
        """
        Gets layers from table and restructures them to fit the format required by TrimFitModel

        Returns: Restructured layers
        """
        layers = self.view.layer_table.get_contents()
        structured_layers = []

        for layer in layers:
            if layer[0] == "":
                # skip rows where sample name is blank - assume the whole row is empty
                continue

            try:
                name = layer[0]
                thickness = float(layer[1])

            except ValueError:
                self.view.display_error_message(message="Invalid layers in table.")
                return

            layer_dict = {"name": name, "thickness": thickness}

            # layer density is allowed to be empty for 'Beamline Window' and 'Air (compressed)'
            try:
                layer_dict["density"] = float(layer[2])

            except ValueError:
                if not (name == "Beamline Window" or name == "Air (compressed)"):
                    self.view.display_error_message(
                        message=f"Invalid density for '{name}'."
                    )
                    return

            structured_layers.append(layer_dict)

        return structured_layers
