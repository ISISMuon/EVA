class BaseDialog(object):
    def __init__(self, view, model, presenter, **kwargs):
        self.view = view
        self.model = model
        self.presenter = presenter

        self.kwargs = kwargs

    def show(self):
        self.view.show()

    def exec(self):
        self.view.exec()

    def showMaximized(self):
        self.view.showMaximized()

    def layout(self):
        return self.view.layout()
