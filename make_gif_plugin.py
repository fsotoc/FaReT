#!/usr/bin/env python

from gimpfu import *
import os

def make_gif(paths=['$HOME/makehuman/frames/'], names="$HOME/makehuman/MH_G_{0:04d}.gif", fps=33.333333):
    if type(paths)==str:
        paths = [paths]
    # make GIFs from every folder provided
    for i,path in enumerate(paths):
        files = sorted(os.listdir(path))
        image = None
        drawable = None
        # make the transparent background black when it is flattened
        pdb.gimp_context_set_default_colors()
        pdb.gimp_context_swap_colors()
        for f in files:
            name = os.path.join(path, f)
            if image is None:
                image = pdb.file_png_load(name, name)
                layer = pdb.gimp_image_get_layer_by_name(image, "Background")
                pdb.gimp_layer_flatten(layer)
                drawable = pdb.gimp_image_get_active_drawable(image)
            else:
                layer = pdb.gimp_file_load_layer(image, name)
                pdb.gimp_layer_flatten(layer)
                pdb.gimp_image_insert_layer(image, layer, None, -1)
        filename = names.format(i)
        pdb.gimp_image_convert_indexed(image, NO_DITHER, MAKE_PALETTE, 255, False, True, "")
        pdb.file_gif_save(image, None, filename, filename, False, True, fps, 2)

register('python_fu_make_gif',
                'Generate GIF',
                'Generate GIF',
                'Jason Hays',
                'Jason Hays',
                '2018',
                'Make-GIF', '',
                [(PF_STRING, 'basedir', 'base directory for images', '$HOME/makehuman/frames/'),
                 (PF_STRING, 'outdir', 'output format', '$HOME/makehuman/MH_G_{0:04d}.gif'),
                 (PF_FLOAT, 'fps', 'Time Per Frame (ms)', 33.333333)],
                [], make_gif, menu="<Image>/Filters")

main()
