



"""iterate over all individual streamlines in this tract"""
import os

import numpy as np


def get_tracts(fn):
    with open(fn, 'rb') as fid:
        header = {}
        while True:
            line = fid.readline().decode("utf-8")
            if "END" in line:
                break
            if ":" in line:
                k, v = line.split(":")
                header[k] = v.strip()

        data_offset = int(header['file'].split()[1])
        fid.seek(data_offset, os.SEEK_SET)

        dtype = np.dtype('<f4')
        coordinate_size = 3 * dtype.itemsize
        # Make buffer_size an integer and a multiple of coordinate_size.
        buffer_size = int(10 * 1024 * 1024 * coordinate_size)
        buffer_size += coordinate_size - (buffer_size % coordinate_size)

        eof = False
        leftover = np.empty((0, 3), dtype='<f4')
        n_streams = 0

        while not eof:
            buff = bytearray(buffer_size)
            n_read = fid.readinto(buff)
            eof = n_read != buffer_size
            if eof:
                buff = buff[:n_read]

            raw_values = np.frombuffer(buff, dtype=dtype)

            # Convert raw_values into a list of little-endian triples (for x,y,z coord)
            coords = raw_values.astype('<f4', copy=False).reshape((-1, 3))

            # Find stream delimiter locations (all NaNs)
            delims = np.where(np.isnan(coords).all(axis=1))[0]

            # Recover leftovers, which can't have delimiters in them
            if leftover.size:
                delims += leftover.shape[0]
                coords = np.vstack((leftover, coords))

            begin = 0
            for delim in delims:
                pts = coords[begin:delim]
                if pts.size:
                    yield pts
                    n_streams += 1
                begin = delim + 1

            # The rest becomes the new leftover.
            leftover = coords[begin:]

        if not (leftover.shape == (1, 3) and np.isinf(leftover).all()):
            if n_streams == 0:
                msg = "Cannot find a streamline delimiter. This file might be corrupted."
            else:
                msg = "Expecting end-of-file marker 'inf inf inf'"
            raise Exception(msg)


def load_tck(filepath, tract_point_count=-1, radius=1, in_mm=True):
    import time
    import bpy


    to_meters = 1.0 / 1000.
    if not in_mm:
        to_meters = 1.0

    for ob in bpy.context.selected_objects:
        ob.select_set(False)

    start_time = time.time()
    base = bpy.path.display_name_from_filepath(filepath)
    curve = bpy.data.curves.new(base, "CURVE")

    curve.bevel_depth = radius * to_meters

    for tract in get_tracts(filepath):
        if tract_point_count > 1 and tract_point_count < tract.shape[0]:
            # make sure we include the last point always
            index = np.linspace(0, tract.shape[0] - 2, tract_point_count - 1).astype(np.int32)
            index = np.append(index, [tract.shape[0] - 1])
            tract = tract[index, :]

        # logging.info ( f"size is {t.shape}")
        polyline = curve.splines.new('NURBS')  # 'POLY''BEZIER''BSPLINE''CARDINAL''NURBS'
        polyline.points.add(tract.shape[0] - 1)
        for idx in range(tract.shape[0]):
            polyline.points[idx].co = tract[idx, :].tolist() + [1]
            # logging.info ( f"polyline point {idx}: {polyline.points[idx].co}")
        polyline.use_endpoint_u = True

    object = bpy.data.objects.new(base, curve)
    object.show_bounds = True
    object.scale = [to_meters, to_meters, to_meters]

    bpy.context.collection.objects.link(object)
    bpy.context.view_layer.objects.active = object
    object.select_set(True)

    print("\nSuccessfully imported %r in %.3f sec" % (filepath, time.time() - start_time))

    return {'FINISHED'}


def load(operator, context, props, filepath=""):
    return load_tck(filepath, tract_point_count=props.skip_points, radius=props.radius, in_mm=props.in_mm)