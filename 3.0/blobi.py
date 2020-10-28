#!/usr/bin/env python3

# Blobi.py -- make text look puffy and 3-D.
# Copyright 2003, 2020 by Akkana Peck.
# Share and enjoy under the GPLv2 or later.

# IMPORTANT: This needs gimphelpers.py (available at the same
# place you got blobi.py) installed somewhere in your PYTHONPATH.

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
# from gi.repository import Gio

# goat-exercise imports these only if INTERACTIVE,
# but when I try that, I get an exception because Gtk isn't defined
# even though I don't call any of the Gtk functions.
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

import sys, os

from gimphelpers import run_plug_in


class BlobiPy (Gimp.PlugIn):
    ## Parameters ##
    __gproperties__ = {
        "blur": (float,
                    "Blur",
                    "Blur",
                    0.0, 100.0, 5.0,
                    GObject.ParamFlags.READWRITE),
    }

    def do_query_procedures(self):
        return [ "python-fu-blobipy" ]

    def do_create_procedure(self, name):
        """Register as a GIMP plug-in"""
        procedure = Gimp.ImageProcedure.new(self, name,
                                       Gimp.PDBProcType.PLUGIN,
                                       self.run, None)

        procedure.set_image_types("*");

        procedure.set_menu_label("_BlobiPy");
        procedure.set_icon_name(GimpUi.ICON_GEGL);
        procedure.add_menu_path('<Image>/Filters/Light and Shadow/');

        # Add parameters
        procedure.add_argument_from_property(self, "blur")

        procedure.set_documentation("Give a puffy, 3-D appearance",
                                    "Give a layer a puffy, 3-D appearance",
                                    name);
        procedure.set_attribution("Akkana Peck", "Akkana Peck", "2003,2020");

        return procedure

    def python_blobify(self, img, layer, blur):
        """The function that actually does the work"""

        img.undo_group_start()

        img.select_item(Gimp.ChannelOps.REPLACE, layer)

        Gimp.Selection.invert(img)

        c = Gimp.RGB()
        c.set(0, 0, 0)
        run_plug_in('script-fu-drop-shadow', img, layer, -3, -3, blur,
                    c, 80.0, False)

        # Gimp.get_pdb().run_procedure('script-fu-drop-shadow',
        #                              [ Gimp.RunMode.NONINTERACTIVE,
        #                                GObject.Value(Gimp.Image, img),
        #                                GObject.Value(Gimp.Drawable, layer),
        #                                GObject.Value(GObject.TYPE_DOUBLE, -3),
        #                                GObject.Value(GObject.TYPE_DOUBLE, -3),
        #                                GObject.Value(GObject.TYPE_DOUBLE,blur),
        #                                c,
        #                                GObject.Value(GObject.TYPE_DOUBLE, 80.0),
        #                                GObject.Value(GObject.TYPE_BOOLEAN,
        #                                              False)
        #                              ])

        Gimp.get_pdb().run_procedure('gimp-selection-none', [img])
        Gimp.Selection.none(img)

        img.undo_group_end()


    def run(self, procedure, run_mode, image, drawable, args, data):
        """Called when the user invokes the plug-in from the menu
           or as "Repeat", or when another plug-in calls it.
        """
        config = procedure.create_config()
        config.begin_run(image, run_mode, args)
        blur = config.get_property("blur")

        blur = args.index(0)
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("blobi.py")

            dialog = self.blob_dialog()

            while (True):
                response  = dialog.run()
                if response == Gtk.ResponseType.OK:
                    dialog.destroy()
                    blur = self.blurspin.get_value()
                    break
                else:
                    dialog.destroy()
                    return procedure.new_return_values(
                        Gimp.PDBStatusType.CANCEL, GLib.Error())

        # Gimp.RunMode.WITH_LAST_VALS should take care of itself

        print("Running with blur =", blur)
        self.python_blobify(image, drawable, blur)

        config.set_property('blur', blur)
        config.end_run(Gimp.PDBStatusType.SUCCESS)
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS,
                                           GLib.Error())

    # Eventually GIMP will create a parameter dialog automatically,
    # but until then, need to build it here.
    def blob_dialog(self):
        """Bring up a dialog prompting for blobipy options.
           Return (response, blur)
        """
        use_header_bar = Gtk.Settings.get_default().get_property(
            "gtk-dialogs-use-header")
        dialog = GimpUi.Dialog(use_header_bar=use_header_bar,
                               title="Give a puffy, 3-D appearance",
                               role="blobypy")

        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("_OK", Gtk.ResponseType.OK)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                       homogeneous=False, spacing=10)
        dialog.get_content_area().add(vbox)
        vbox.show()

        self.blurspin = Gtk.SpinButton.new_with_range(0., 50., 1.)
        self.blurspin.set_value(5)
        vbox.pack_start(self.blurspin, False, False, 0)
        self.blurspin.show()

        return dialog


Gimp.main(BlobiPy.__gtype__, sys.argv)
