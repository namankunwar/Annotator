# -*- coding: utf-8 -*-

import os
from os import walk, getcwd
from PIL import Image
import re, shutil
    

def convert(size, box):
    """ Converts bbox format

    Args:
        size (int): size to convert to
        box (list): list of bbox coordinates

    Returns:
        tuple: return tuple of bbox coordinate in format of yolo
    """    
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

def search_img(search_string, dir_path):
    """ Search image 

    Args:
        search_string (str): string to search
        dir_path (str): path of dir

    Returns:
        image: returns image
    """    
    files = os.listdir(dir_path)
    matching_files = [file for file in files if search_string in file]
    return matching_files[0]


# def Convert2Yolo(mypath, outpath, project, classes, imageDir):
#     """ Converts annotated text file to YOLO format

#     Args:
#         mypath (str): annotated file path
#         outpath (str): output directory for YOLO output
#         project (str): project name
#         classes (list): list of classes
#         imageDir (str): image directory
#     """
#     # Ensure the input directory exists
#     if not os.path.exists(mypath):
#         raise FileNotFoundError(f"Input directory '{mypath}' does not exist!")

#     # Ensure the output directory exists
#     os.makedirs(outpath, exist_ok=True)

#     """ Get input text file list """
#     txt_name_list = []
#     for (dirpath, dirnames, filenames) in walk(mypath):
#         txt_name_list.extend(filenames)
#         break

#     """ Process each text file """
#     for txt_name in txt_name_list:
#         # Construct the full path to the input text file
#         txt_path = os.path.join(mypath, txt_name)
#         if not os.path.exists(txt_path):
#             print(f"Warning: File '{txt_path}' not found. Skipping.")
#             continue

#         """ Open input text file """
#         with open(txt_path, "r") as txt_file:
#             lines = txt_file.read().splitlines()  # Use splitlines() for cross-platform compatibility

#         """ Open output text file """
#         txt_outpath = os.path.join(outpath, re.split(r'\.jpg|\.png|\.bmp|\.jpeg', txt_name)[0] + ".txt")
#         with open(txt_outpath, "w") as txt_outfile:

#             """ Convert the data to YOLO format """
#             for line in lines:
#                 if not line.strip():  # Skip empty lines
#                     continue

#                 elems = line.split()
#                 if len(elems) < 5:  # Ensure the line has enough elements
#                     print(f"Warning: Invalid line in '{txt_path}': {line}")
#                     continue

#                 # Parse bounding box coordinates and class
#                 xmin, ymin, xmax, ymax, cls = elems[:5]
#                 if cls not in classes:
#                     print(f"Error: Class '{cls}' not found in classes list. Skipping file '{txt_path}'.")
#                     break

#                 """ Find and copy the corresponding image """
#                 img_name = search_img(os.path.splitext(txt_name)[0], imageDir)
#                 if not img_name:
#                     print(f"Warning: Image for '{txt_name}' not found. Skipping.")
#                     continue

#                 img_path = os.path.join(imageDir, img_name)
#                 destination_path = os.path.join(outpath, img_name)
#                 try:
#                     with open(img_path, "rb") as source_file, open(destination_path, "wb") as destination_file:
#                         destination_file.write(source_file.read())
#                 except FileNotFoundError:
#                     print(f"Warning: Image '{img_path}' not found. Skipping.")
#                     continue

#                 """ Normalize bounding box coordinates """
#                 try:
#                     with Image.open(img_path) as im:
#                         w, h = im.size
#                 except Exception as e:
#                     print(f"Warning: Failed to open image '{img_path}'. Skipping. Error: {e}")
#                     continue

#                 b = (float(xmin), float(xmax), float(ymin), float(ymax))
#                 bb = convert((w, h), b)

#                 # Normalize bounding box coordinates to [0, 1]
#                 bb_normalized = tuple(max(0.0, min(1.0, val)) for val in bb)

#                 """ Write to output file """
#                 txt_outfile.write(f"{cls} {' '.join(map(str, bb_normalized))}\n")

#         print(f"Processed: {txt_name}")

#     print("Conversion complete.")  

def Convert2Yolo(mypath, outpath, project, classes, imageDir):
    """Converts annotated text file to YOLO format and ensures all images are copied
    
    Args:
        mypath (str): annotated file path
        outpath (str): output directory for YOLO output
        project (str): project name
        classes (list): list of classes
        imageDir (str): image directory
    """
    # Ensure directories exist
    if not os.path.exists(mypath):
        raise FileNotFoundError(f"Input directory '{mypath}' does not exist!")
    if not os.path.exists(imageDir):
        raise FileNotFoundError(f"Image directory '{imageDir}' does not exist!")
    
    os.makedirs(outpath, exist_ok=True)

    # Get all image files in the image directory
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    all_images = [f for f in os.listdir(imageDir) if f.lower().endswith(image_extensions)]
    
    # Get all annotation files
    txt_name_list = []
    for (dirpath, dirnames, filenames) in os.walk(mypath):
        txt_name_list.extend(f for f in filenames if f.endswith('.txt'))
        break

    # Process each image (not just annotated ones)
    for img_name in all_images:
        base_name = os.path.splitext(img_name)[0]
        txt_name = base_name + '.txt'
        
        # Copy the image regardless of whether it has annotations
        img_path = os.path.join(imageDir, img_name)
        destination_img_path = os.path.join(outpath, img_name)
        
        try:
            # Copy image if it doesn't exist in output or is newer
            if not os.path.exists(destination_img_path) or \
               os.path.getmtime(img_path) > os.path.getmtime(destination_img_path):
                shutil.copy2(img_path, destination_img_path)
        except Exception as e:
            print(f"Warning: Failed to copy image '{img_name}'. Error: {e}")
            continue

        # Check if this image has annotations
        txt_path = os.path.join(mypath, txt_name)
        txt_outpath = os.path.join(outpath, base_name + ".txt")
        
        # Create empty txt file if no annotations exist
        if not os.path.exists(txt_path):
            open(txt_outpath, 'w').close()  # Create empty file
            print(f"Created empty annotation for: {img_name}")
            continue

        # Process annotations if they exist
        try:
            with open(txt_path, "r") as txt_file:
                lines = txt_file.read().splitlines()
        except Exception as e:
            print(f"Warning: Failed to read annotation file '{txt_name}'. Error: {e}")
            continue

        with open(txt_outpath, "w") as txt_outfile:
            has_valid_annotations = False
            
            for line in lines:
                if not line.strip():
                    continue

                elems = line.split()
                if len(elems) < 5:
                    print(f"Warning: Invalid line in '{txt_path}': {line}")
                    continue

                xmin, ymin, xmax, ymax, cls = elems[:5]
                if cls not in classes:
                    print(f"Error: Class '{cls}' not found in classes list. Skipping annotations for '{img_name}'.")
                    break

                try:
                    with Image.open(img_path) as im:
                        w, h = im.size
                except Exception as e:
                    print(f"Warning: Failed to open image '{img_path}'. Error: {e}")
                    break

                b = (float(xmin), float(xmax), float(ymin), float(ymax))
                bb = convert((w, h), b)
                bb_normalized = tuple(max(0.0, min(1.0, val)) for val in bb)

                txt_outfile.write(f"{cls} {' '.join(map(str, bb_normalized))}\n")
                has_valid_annotations = True

            if not has_valid_annotations:
                print(f"No valid annotations found for: {img_name} (created empty file)")

        print(f"Processed: {img_name}")

    print("Conversion complete. All images copied to output directory.")