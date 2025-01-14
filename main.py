import sys
from PyQt5.QtWidgets import QApplication
from frontend.main_view import HDF5Viewer
import qt_material

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
            viewer = HDF5Viewer(filepath)
        else:
            viewer = HDF5Viewer()
    except Exception as e:
        viewer = HDF5Viewer()
    qt_material.apply_stylesheet(app, theme='light_blue.xml')
    viewer.show()
    exit_code = app.exec_()
    sys.exit(exit_code)