import os
import yaml
from tkinter import *
import tkinter as tk
from tkinter import Tk, messagebox, filedialog, ttk
from PIL import Image, ImageTk
from tkinter.simpledialog import askstring
import glob
import sys
import convert  
from pathlib import Path
import regex as re
import convert_yolo 


# Colors for bounding boxes
COLORS = ['red', 'blue', 'olive', 'teal', 'cyan', 'green', 'black', 'purple', 'orange', 'brown', 'crimson', 'yellow']

# def load_config(file_path):
#     """Load configuration from a YAML file."""
#     try:
#         with open(file_path, 'r') as file:
#             return yaml.safe_load(file)
#     except Exception as e:
#         messagebox.showerror("Error", f"Failed to load config: {e}")
#         return {}

# def load_main_config():
#     current_dir = os.getcwd()
#     base_dir = os.path.basename(current_dir)
#     if 'main_config.yaml' in os.listdir(current_dir):
#         config_path = 'main_config.yaml'
#     else:
#         config_path = f"./{base_dir}/main_config.yaml"

#     with open(config_path, 'r') as file:
#         all_info_services = yaml.safe_load(file)
#     current_directory = os.path.join(os.getcwd(), config_path)
#     with open(current_directory, 'r') as file:
#         all_info_services = yaml.safe_load(file)
#         #print(all_info_services)
#     return all_info_services

class LabelTool:

    def __init__(self, master, dir_imgs, dir_out, dir_yolo_out, image_extensions):
        """Initialize the annotation tool."""
        self.parent = master
        self.parent.title("YOLO Annotator")
        self.parent.resizable(width=FALSE, height=FALSE)  # Disable window resizing

        # Initialize state (keep your existing code)
        self.imageDir = dir_imgs
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = dir_out
        self.yoloOut = dir_yolo_out
        self.image_extensions = image_extensions
        self.cur = 0
        self.total = 0
        self.category = ''
        self.imagename = ''
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.selected_bbox = None
        self.bbox_cnt = 0
        self.tkimg = None
        self.labelfilename = ''
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'
        self.classcnt = 0
        self.zoom_level = 1.0
        self.original_img = None
        self.STATE = {'click': 0, 'x': 0, 'y': 0}
        self.class_to_color = {}
        self.class_list_from_file = {'color': []}
        self.last_b_box = []
        # Default threshold value
        self.min_bbox_size = 10

        # GUI components
        """Set up the GUI components."""

        # Main frame
        self.frame = tk.Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=True)

        # Configure grid weights for resizing
        self.frame.columnconfigure(1, weight=1)  # Main canvas area
        self.frame.columnconfigure(4, weight=0)  # Right panel
        self.frame.rowconfigure(1, weight=1)     # Main content area

        # Load Image button
        self.ldProjBtn = tk.Button(self.frame, text="Load Image", bg='#84a59d', relief='flat', command=self.loadDir)
        self.ldProjBtn.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=5)


        # Add a delete button to the UI
        self.delete_button = tk.Button(self.frame, text="Delete Image",bg='#f28482', relief='flat', command=self.delete_current_image)
        self.delete_button.grid(row=6, column=0, sticky=tk.EW, padx=5, pady=5)

        # Clear Annotation button
        self.clearResBtn = tk.Button(self.frame, text="Clear Annotation", bg='#f28482', relief='flat', command=self.clear_prev_annotation)
        self.clearResBtn.grid(row=7, column=0, sticky=tk.EW, padx=5, pady=5)

        # # Canvas frame with scrollbars
        # canvas_frame = tk.Frame(self.frame, bd=2, relief=tk.SUNKEN)
        # canvas_frame.grid(row=1, column=1, columnspan=3, rowspan=4, sticky=tk.NSEW, padx=5, pady=5)
        # canvas_frame.rowconfigure(0, weight=1)
        # canvas_frame.columnconfigure(0, weight=1)

         # Create a frame to hold the scrollbars and canvas
        frame = Frame(self.frame)
        frame.grid(row=1, column=1, columnspan=3, rowspan=4, sticky=W + N)

        # Create horizontal and vertical scrollbars
        self.hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        self.vbar = tk.Scrollbar(frame, orient=tk.VERTICAL)

        # Main panel for labeling
        self.mainPanel = tk.Canvas(frame, cursor='tcross', bg='white',
                                xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.mainPanel.grid(row=0, column=0, sticky=tk.NSEW)

        # Pack the scrollbars
        self.hbar.grid(row=1, column=0, sticky=tk.EW)
        self.vbar.grid(row=0, column=1, sticky=tk.NS)

        # Configure the scrollbars to control the canvas
        self.hbar.config(command=self.mainPanel.xview)
        self.vbar.config(command=self.mainPanel.yview)

        # Control panel
        self.ctrPanel = tk.Frame(self.frame, bd=1, relief=tk.RIDGE)
        self.ctrPanel.grid(row=7, column=1, columnspan=4, sticky=tk.EW, padx=5, pady=5)

        # Coordinate display
        self.disp = tk.Label(self.ctrPanel, text="x: 0, y: 0")
        self.disp.pack(side=tk.LEFT, padx=5)

        # Event bindings
        self.mainPanel.bind("<MouseWheel>", self.zoom)
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Button-3>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.mainPanel.bind('v', self.pasteLastBbox)
        self.mainPanel.bind('b', self.pasteLastBboxFile)
        self.mainPanel.bind("a", self.prevImage)
        self.mainPanel.bind("d", self.nextImage)
        self.mainPanel.bind("r", self.clearBBoxShortcut)
        self.mainPanel.bind("q", self.close_program)

                # Add the button and entry field for setting threshold in the same row
        self.entryThreshold = Entry(self.frame, width=5)
        self.entryThreshold.grid(row=0, column=2, sticky=W, padx=(10, 5))

        self.btnSetThreshold = Button(self.frame, text='Set Threshold', bg='#4cc9f0', fg='white',
                                    relief='raised', command=self.setThreshold)
        self.btnSetThreshold.grid(row=0, column=3, sticky=W+E, padx=(5, 50))

        # Add two buttons for adding and deleting classes in the same row
        self.btnAddClass = Button(self.frame, text='Add Class', bg='#4cc9f0', fg='white', relief='raised', command=self.addNewClass)
        self.btnAddClass.grid(row=0, column=4, sticky=W+E, padx=(50, 135))

        self.btnDeleteClass = Button(self.frame, text='Delete Class', bg='#f28482', fg='white', relief='raised', command=self.deleteClass)
        self.btnDeleteClass.grid(row=0, column=4, sticky=W+E, padx=(150, 55))

        # Class selection and listbox area
        right_panel = tk.Frame(self.frame, bd=2, relief=tk.GROOVE)
        right_panel.grid(row=1, column=4, rowspan=4, sticky=tk.NSEW, padx=5, pady=5)

        # Class combobox
        self.classname = tk.StringVar()
        self.classcandidate = ttk.Combobox(right_panel, state='readonly', textvariable=self.classname)
        self.classcandidate.pack(fill=tk.X, padx=5, pady=5)
        self.loadClassCandidates()

        # Bounding box listbox
        self.listbox = tk.Listbox(right_panel)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                # Bind the listbox selection event
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # Add a label for total bounding boxes
        self.totalBboxLabel = tk.Label(right_panel, text='Total BBoxes: 0')
        self.totalBboxLabel.pack(fill=tk.X, padx=5, pady=5)

        self.btnDel = Button(self.frame, text='Clear', bg='#c1121f', fg='white', relief='groove', command=self.delBBox)
        self.btnDel.grid(row=5, column=4, sticky=W+E+N)
        self.btnClear = Button(self.frame, text='ClearAll', bg='#c1121f', fg='white', relief='groove', command=self.clearBBox)
        self.btnClear.grid(row=6, column=4, sticky=W+E+N)

        # Control panel buttons
        self.conv2YoloBtn = tk.Button(self.ctrPanel, text='Convert YOLO', bg='#83C5BE', relief='flat', width=15, command=self.convert2Yolo)
        self.conv2YoloBtn.pack(side=tk.LEFT, padx=5, pady=3)

        self.resetChkBtn = tk.Button(self.ctrPanel, text='ResetCheckpoint', bg='#C9ADA7', relief='flat', width=15, command=self.resetCheckpoint)
        self.resetChkBtn.pack(side=tk.LEFT, padx=5, pady=3)

        self.loadChkBtn = tk.Button(self.ctrPanel, text='LoadCheckpoint', bg='#C9ADA7', relief='flat', width=15, command=self.loadCheckpoint)
        self.loadChkBtn.pack(side=tk.LEFT, padx=5, pady=3)

        self.skipBtn = tk.Button(self.ctrPanel, text='Skip', width=10, bg='#f28482', relief='flat', command=self.skipImage)
        self.skipBtn.pack(side=tk.LEFT, padx=5, pady=3)

        self.prevBtn = tk.Button(self.ctrPanel, text='<< Prev', width=10, bg='#669BBC', relief='flat', command=self.prevImage)
        self.prevBtn.pack(side=tk.LEFT, padx=5, pady=3)

        self.nextBtn = tk.Button(self.ctrPanel, text='Next >>', width=10, bg='#669BBC', relief='flat', command=self.nextImage)
        self.nextBtn.pack(side=tk.LEFT, padx=5, pady=3)

        self.progLabel = tk.Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=tk.LEFT, padx=5)

        # Example panel
        self.egPanel = tk.Frame(self.frame, bd=2, relief=tk.GROOVE, bg='#f0f0f0')
        self.egPanel.grid(row=1, column=0, rowspan=5, sticky=tk.NS, padx=5, pady=5)

        self.tmpLabel2 = tk.Label(self.egPanel, text="Key Shortcut :\na : Prev\nd : Next\nr : Delete BB\nv : Paste Last BB\nb: Paste last BB from prev image\nRight Click : Delete BB\n1-9 : Select Class \n q:Quit program")
        self.tmpLabel2.pack(side=tk.TOP, padx=5, pady=5)

        self.tmpLabel3 = tk.Label(self.egPanel, text="\nBasic Usage :\n1.Load Image\n2.Annotate\n3.Convert Yolo")
        self.tmpLabel3.pack(side=tk.TOP, padx=5, pady=5)

        self.egLabels = []
        for i in range(3):
            self.egLabels.append(tk.Label(self.egPanel))
            self.egLabels[-1].pack(side=tk.TOP, padx=5, pady=5)

        self.parent.protocol("WM_DELETE_WINDOW", self.on_close)


    def on_close(self):
        """Called when the annotator window is closed."""
        if not self.imagename:  # Check if there are images to save
            print("No images left to process. Closing window.")
            self.parent.destroy()
            return

        self.saveImage()  # Ensure annotations are saved
        self.convert2Yolo()  # Convert to YOLO format
        print("Annotations saved and converted to YOLO format.")
        self.parent.destroy()  # Close the window


    def delete_current_image(self):
        """Deletes the currently loaded image and its associated files after confirmation."""
        # Get the base directory where the script is located
        base_dir = Path(__file__).resolve().parent

        if not self.imagename:
            messagebox.showwarning("Warning", "No image selected to delete.")
            return

        # Ask for confirmation before deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete '{self.imagename}' and all related files?"
        )
        if not confirm:
            return

        # Get file names
        image_name = self.imagename
        base_name, _ = os.path.splitext(image_name)  # Remove extension
        print(f"Base name: '{base_name}'")

        # Define file paths with glob patterns to catch all variations
        file_patterns = [
            base_dir / "input_dir" / f"{base_name}.*",
            base_dir / "yolo_output_dir" / f"{base_name}.*",
            base_dir / "annotation_dir" / f"{base_name}.txt",
            base_dir / "yolo_output_dir" / f"{base_name}.txt",
        ]

        # Delete all matching files
        deleted_files = []
        for pattern in file_patterns:
            matched_files = glob.glob(str(pattern))  # Convert Path to string for glob
            if not matched_files:
                print(f"No files found for pattern: {pattern}")
            for filepath in matched_files:
                try:
                    os.remove(filepath)
                    deleted_files.append(filepath)
                    print(f"Deleted: {filepath}")
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")

        # Only proceed if the main image file was deleted
        main_image_path = base_dir / "input_dir" / image_name
        if str(main_image_path) not in deleted_files:
            messagebox.showerror("Error", f"Failed to delete the main image file: {main_image_path}")
            return

        # Remove the deleted image from the list and update counters
        try:
            self.imageList.pop(self.cur - 1)
            self.total = len(self.imageList)

            # Handle case when no images left
            if self.total == 0:
                self.handle_no_images()
                return

            # Adjust current position if we deleted the last image
            if self.cur > self.total:
                self.cur = self.total

            # Load the appropriate image
            self.loadImage()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update image list: {str(e)}")
            # Refresh the entire image list as fallback
            self.refresh_image_list()
            if self.imageList:
                self.loadImage()

    def handle_no_images(self):
        """Handle case when no images remain"""
        self.mainPanel.delete("all")
        self.imagename = None
        self.cur = 0
        self.total = 0
        self.progLabel.config(text="0000/0000")
        messagebox.showinfo("Info", "No more images to annotate")
        self.clearBBox()

    def refresh_image_list(self):
        """Refresh the image list from disk"""
        image_dir = base_dir / ('input_dir')
        self.imageList = sorted([
            os.path.join(image_dir, f) for f in os.listdir(image_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        ])
        self.total = len(self.imageList)


    def loadDir(self):
        """Load images from the active brand's letterbox_ref directory."""
        
        self.category = 'Sample'  # Ensure category is set
        self.imageDir = base_dir / "input_dir"

        # Check if the directory exists
        if not self.imageDir.exists():
            messagebox.showinfo("Error", f"Directory {self.imageDir} does not exist!")
            return
        
        # Convert Path object to string for compatibility
        self.imageDir = str(self.imageDir)
        
        # Load images
        self.imageList = []
        for ext in self.image_extensions:
            self.imageList.extend(glob.glob(str(Path(self.imageDir) / f'*{ext}')))
        
        if not self.imageList:
            messagebox.showinfo("Error", "No images found in the specified directory with the specified extensions!")
            return
        
        self.cur = 1
        self.total = len(self.imageList)
        
        # Set output directory
        self.outDir = base_dir/ "result_annotation"
        self.outDir.mkdir(parents=True, exist_ok=True)
        
        self.loadImage()  # Load the first image
        
        messagebox.showinfo("Info", f"{self.total} images loaded from {self.category}")


    def loadImage(self):
        """Load the current image and fit it to the canvas."""
        imagepath = self.imageList[self.cur - 1]
        self.original_img = Image.open(imagepath)

         # Convert the image to a Tkinter-compatible format
        self.tkimg = ImageTk.PhotoImage(self.original_img, master=self.parent)

        # Get image original dimensions
        img_width, img_height = self.original_img.size

        # Automatically adjust canvas size to image size
        self.mainPanel.config(width=img_width, height=img_height)
        self.mainPanel.config(scrollregion=(0, 0, self.tkimg.width(), self.tkimg.height()))

        # Convert the image to a Tkinter-compatible format
        self.tkimg = ImageTk.PhotoImage(self.original_img, master=self.parent)

        # Clear the canvas before placing a new image
        self.mainPanel.delete("all")

        # Display the image in the canvas
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)

        # Prevent canvas resizing when the window is maximized
        self.mainPanel.update_idletasks()  # Ensure layout updates before locking size
        
        # Reset zoom level to 1.0 (no zoom)
        self.zoom_level = 1.0

        # Set the image name and label file name
        self.imagename = os.path.split(imagepath)[-1]
        labelname = re.split('.jpg|.png|.JPG|.jpeg|.JPEG', self.imagename)[0] + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)

        # Update progress label
        self.progLabel.config(text=f"{self.cur:04d}/{self.total:04d}")

        # Clear and reload bounding boxes
        self.clearBBox()
        self.loadBBox()



    def update_image(self):
        """Resize the image and redraw bounding boxes based on zoom level."""
        if self.original_img is None:
            return

        # Compute new image dimensions
        new_width = int(self.original_img.width * self.zoom_level)
        new_height = int(self.original_img.height * self.zoom_level)

        # Resize the image
        resized_img = self.original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(resized_img, master=self.parent)

        # Clear the canvas and redraw the image
        self.mainPanel.delete("all")
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=tk.NW)
        self.mainPanel.config(scrollregion=(0, 0, new_width, new_height))

        # Redraw bounding boxes
        self.redraw_bboxes()


    def redraw_bboxes(self):
        """Redraw bounding boxes scaled by the current zoom level."""
        self.bboxIdList = []
        for bbox in self.bboxList:
            x1, y1, x2, y2, label = bbox

            # Ensure coordinates are numbers
            x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))

            # Scale coordinates by zoom level
            x1_scaled = x1 * self.zoom_level
            y1_scaled = y1 * self.zoom_level
            x2_scaled = x2 * self.zoom_level
            y2_scaled = y2 * self.zoom_level

            # Draw bounding box
            idx = self.get_class_index(label)
            tmpId = self.mainPanel.create_rectangle(x1_scaled, y1_scaled, x2_scaled, y2_scaled, width=2, outline=COLORS[idx])
            self.bboxIdList.append(tmpId)


    def zoom(self, event):
        """Handle mouse wheel zooming."""
        if event.delta > 0:
            factor = 1.1
        else:
            factor = 0.9

        new_zoom = self.zoom_level * factor
        new_zoom = max(1, min(new_zoom, 4.0))
        factor = new_zoom / self.zoom_level
        self.zoom_level = new_zoom

        # Get the current mouse position relative to the canvas
        x = self.mainPanel.canvasx(event.x)
        y = self.mainPanel.canvasy(event.y)

        # Calculate the original image coordinates before zoom
        orig_x = x / self.zoom_level
        orig_y = y / self.zoom_level

        # Update the image and redraw bounding boxes
        self.update_image()

        # Calculate the new mouse position after zoom
        new_x = orig_x * self.zoom_level
        new_y = orig_y * self.zoom_level

        # Adjust the scroll position to keep the mouse pointer over the same image point
        visible_width = self.mainPanel.winfo_width()
        visible_height = self.mainPanel.winfo_height()

        desired_left = (new_x - visible_width / 2) / (self.original_img.width * self.zoom_level)
        desired_top = (new_y - visible_height / 2) / (self.original_img.height * self.zoom_level)

        # Ensure the scroll position stays within bounds
        desired_left = max(0, min(desired_left, 1))
        desired_top = max(0, min(desired_top, 1))

        self.mainPanel.xview_moveto(desired_left)
        self.mainPanel.yview_moveto(desired_top)



    def loadBBox(self):
        """Load bounding boxes from the annotation file."""
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        continue
                    tmp = line.split()
                    self.bboxList.append(tuple(tmp))
                    idx = self.get_class_index(tmp[-1])
                    x1 = int(float(tmp[0]) * self.zoom_level)
                    y1 = int(float(tmp[1]) * self.zoom_level)
                    x2 = int(float(tmp[2]) * self.zoom_level)
                    y2 = int(float(tmp[3]) * self.zoom_level)
                    tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=COLORS[idx])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(tk.END, f"{tmp[4]} : ({int(float(tmp[0]))}, {int(float(tmp[1]))}) -> ({int(float(tmp[2]))}, {int(float(tmp[3]))})")
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[idx])



    def setThreshold(self):
        """Set the user-defined threshold for bounding box size."""
        try:
            value = int(self.entryThreshold.get())
            if value > 0:
                self.min_bbox_size = value
            else:
                self.min_bbox_size = 10  # Reset to default if invalid input
        except ValueError:
            self.min_bbox_size = 10  # Reset to default if non-numeric input

        print(f"Threshold set to: {self.min_bbox_size}")

    def on_select(self, event):
        """Handle listbox selection event."""
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            self.highlight_bbox(selected_index)

    def highlight_bbox(self, index):
        """Highlight the selected bounding box."""
        # Reset all bounding boxes to their original color
        for i, bbox_id in enumerate(self.bboxIdList):
            idx = self.get_class_index(self.bboxList[i][-1])
            self.mainPanel.itemconfig(bbox_id, outline=COLORS[idx], width=2)

        # Highlight the selected bounding box
        selected_bbox_id = self.bboxIdList[index]
        self.mainPanel.itemconfig(selected_bbox_id, outline="yellow", width=2)  # Change color and width as needed

    def mouseClick(self, event):
        """Handle mouse click events for Bounding Box Mode only."""
        self.display_no_class_message()

        if self.tkimg:
            # Convert mouse position to canvas coordinates (adjust for scroll position)
            x_canvas = self.mainPanel.canvasx(event.x)
            y_canvas = self.mainPanel.canvasy(event.y)

            # Convert to original image coordinates (before zoom)
            x_orig = x_canvas / self.zoom_level
            y_orig = y_canvas / self.zoom_level

            if event.num == 1:  # Left Click
                if self.STATE['click'] == 0:
                    # First click: Store the starting coordinates
                    self.STATE['x'], self.STATE['y'] = x_orig, y_orig
                else:
                    # Second click: Calculate bounding box coordinates
                    x1 = min(self.STATE['x'], x_orig)
                    y1 = min(self.STATE['y'], y_orig)
                    x2 = max(self.STATE['x'], x_orig)
                    y2 = max(self.STATE['y'], y_orig)

                    if abs(x2 - x1) > self.min_bbox_size and abs(y2 - y1) > self.min_bbox_size:
                        # Append the bounding box to the list
                        self.bboxList.append((x1, y1, x2, y2, self.currentLabelclass))

                        # Get class index for color
                        idx = self.get_class_index(self.currentLabelclass)

                        # Scale coordinates for display
                        x1_canvas = x1 * self.zoom_level
                        y1_canvas = y1 * self.zoom_level
                        x2_canvas = x2 * self.zoom_level
                        y2_canvas = y2 * self.zoom_level

                        # Draw the bounding box on the canvas
                        self.bboxId = self.mainPanel.create_rectangle(
                            x1_canvas, y1_canvas, x2_canvas, y2_canvas,
                            width=2, outline=COLORS[idx]
                        )
                        self.bboxIdList.append(self.bboxId)

                        # Add the bounding box to the listbox
                        self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (
                                self.currentLabelclass, x1, y1, x2, y2))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[idx])

                        # Reset the state
                        self.bboxId = None
                    else:
                        self.update_image()
                # Toggle the click state
                self.STATE['click'] = 1 - self.STATE['click']
                self.totalBboxLabel.config(text=f'Total BBoxes: {len(self.bboxList)}')

            elif event.num == 3:  # Right Click
                self.removeBBox(event)

    def removeBBox(self, event):
        """Remove a bounding box."""
        x = self.mainPanel.canvasx(event.x)
        y = self.mainPanel.canvasy(event.y)
        selected_bbox_id = None
        
        # Match original's bounding box check logic
        for bbox_id in self.bboxIdList:
            bbox_coords = self.mainPanel.coords(bbox_id)
            if len(bbox_coords) >= 4:  # Safety check
                lx, ly, rx, ry = bbox_coords[0], bbox_coords[1], bbox_coords[2], bbox_coords[3]
                if lx <= x <= rx and ly <= y <= ry:
                    selected_bbox_id = bbox_id
                    break
        
        if selected_bbox_id:
            # Use pop() instead of del for safer removal
            bbox_index = self.bboxIdList.index(selected_bbox_id)
            self.mainPanel.delete(selected_bbox_id)
            self.bboxIdList.pop(bbox_index)
            self.bboxList.pop(bbox_index)
            self.listbox.delete(bbox_index)
            
            # Update total count display
            self.totalBboxLabel.config(text=f'Total BBoxes: {len(self.bboxList)}')
            
            # Update the image and redraw bounding boxes
            self.update_image()


    def mouseMove(self, event):
        """Handle mouse move events with zoom adjustments."""
        
        self.display_no_class_message()

        # Convert mouse position to canvas coordinates (adjust for scroll position)
        x_canvas = self.mainPanel.canvasx(event.x)
        y_canvas = self.mainPanel.canvasy(event.y)

        # Convert to original image coordinates (before zoom)
        x_orig = x_canvas / self.zoom_level
        y_orig = y_canvas / self.zoom_level

        # Update coordinates display
        self.disp.config(text=f"x: {int(x_orig)}, y: {int(y_orig)}")

        # Handle crosshair lines (keep them on the scaled image)
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, y_canvas, self.tkimg.width() * self.zoom_level, y_canvas, width=2)

            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(x_canvas, 0, x_canvas, self.tkimg.height() * self.zoom_level, width=2)

        # Handle bounding box drawing
        if self.STATE['click'] == 1:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)

            self.index = self.get_class_index(self.currentLabelclass)

            # Do NOT divide `STATE['x'], STATE['y']` by zoom_level again
            x1_orig = self.STATE['x']
            y1_orig = self.STATE['y']

            # Convert back to canvas coordinates for drawing
            x1_canvas = x1_orig * self.zoom_level
            y1_canvas = y1_orig * self.zoom_level
            x2_canvas = x_orig * self.zoom_level
            y2_canvas = y_orig * self.zoom_level

            # Draw bounding box using correct canvas coordinates
            self.bboxId = self.mainPanel.create_rectangle(
                x1_canvas, y1_canvas, x2_canvas, y2_canvas,
                width=2, outline=COLORS[self.index]
            )


    def saveImage(self):
        """Save the current image annotations."""
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(self.labelfilename), exist_ok=True)

            # Debugging: Print the file path and bounding box list
            
            #print(f"Bounding boxes to save: {self.bboxList}")

            # Open the file for writing
            with open(self.labelfilename, 'w') as f:
                # Write the total number of bounding boxes
                f.write(f"{len(self.bboxList)}\n")

                # Write each bounding box
                for bbox in self.bboxList:
                    # Ensure all elements in the bounding box are strings
                    bbox_str = ' '.join(map(str, bbox))
                    f.write(bbox_str + '\n')

            print("Annotations saved successfully.")
        except Exception as e:
            # Log any errors that occur
            print(f"Error saving annotations: {e}")


 #--------------Function to choose which class you want to switch----------------------------------------------------------------
    def setClass(self, event):
        """ Sets class

        Args:
            event (event): Generated event
        """        
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to :',self.currentLabelclass)
        self.index = self.get_class_index(self.currentLabelclass)
        print(self.index)
        self.mainPanel.focus_set() # focus
            
    def setClassShortcut(self, event):
        """ Set class Shortcut

        Args:
            event (event): Generated event
        """        
        if event.char.isdigit():
            idx = int(event.char) - 1
            if 0 <= idx < len(self.cla_can_temp):
                self.classcandidate.current(idx)
                self.currentLabelclass = self.classcandidate.get()
                self.index = self.get_class_index(self.currentLabelclass)
                # print(self.index)
                print('set label class to:', self.currentLabelclass)
            else:
                messagebox.showerror("Error", "Invalid class index")

    #--------------------------------------------------------------------------------------------------------------------------------


        #-------------------------------------------------Convert the bbox to yolo format----------------------------------------------------------------
    def convert2Yolo(self, event = None):
        """ Converts bbox coordinates to yolo format

        Args:
            event (event, optional): Generated format. Defaults to None.
        """       
        self.saveImage()

        if (self.category == ''):
            messagebox.showinfo("Error", "Please Annotate Image first")
        else:
            # outpath = "./Result_YOLO/" + self.category +'/'
            os.makedirs(self.yoloOut, exist_ok=True)
            convert_yolo.Convert2Yolo(str(self.outDir / ''), self.yoloOut, self.category, self.cla_can_temp, self.imageDir)

            messagebox.showinfo("Info", "YOLO data format conversion done")

    
       #----------------------function to display no class --------------------------------
    def display_no_class_message(self):
        """ opens popup if no classes are avilable.
        """        
        if not self.cla_can_temp:
            confirmation = messagebox.askyesno("Warning", "No classes available. Want to create a new class?")
            if confirmation:
                self.addNewClass()
            return
    #------------------------------------------------------------------------------
    #Get BBox paste
    def getLastBboxSize(self):
        """ Get bbox of last drawn bbox

        Returns:
            int: returns width and height of last bbox
        """        
        if self.bboxList:
            # Retrieve the last bounding box from the list
            last_bbox = self.bboxList[-1]

            # Extract coordinates
            x1, y1, x2, y2, _ = last_bbox

            # Convert coordinates to integers
            x1, y1, x2, y2 = int(float(x1)), int(float(y1)), int(float(x2)), int(float(y2))

            # Calculate and return the size
            width = x2 - x1
            height = y2 - y1
            return width, height,_
        else:
            return None
    
    

    
    #added from old code
    def pasteLastBbox(self, event):
        """ Paste last selected bbox

        Args:
            event (event): generated event
        """        
        if self.tkimg:
            if not self.bboxList:
                messagebox.showerror("Error", "No bounding boxes available to paste.")
                return
            try:
                # Refresh the canvas
                self.mainPanel.update_idletasks()

                size = self.getLastBboxSize()
                if size is None:
                    return

                # Calculate x, y coordinates
                x, y = self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y)

                # Check if bounding box is outside image boundaries
                if x < 0 or y < 0 or x + size[0] > self.tkimg.width() or y + size[1] > self.tkimg.height():
                    messagebox.showwarning("Warning", "Bounding box cannot be drawn outside the image.")
                    return

                x1, y1 = x, y
                x2, y2 = x1 + size[0], y1 + size[1]

                # Draw the bounding box
                self.bboxList.append((x1, y1, x2, y2, size[2]))
                idx_1 = self.get_class_index(size[2])
                self.bboxId= self.mainPanel.create_rectangle(int(x1), int(y1), int(x2), int(y2), width=2, outline=COLORS[idx_1])
                self.bboxIdList.append(self.bboxId)

                self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (
                    size[2], x1, y1, x2, y2))
                self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[idx_1])

                # Update the total bbox label
                self.totalBboxLabel.config(text='Total BBoxes: {}'.format(len(self.bboxList)))

            except Exception as e:
                messagebox.showerror("Error", str(e))
    #----------------------------------------------------------------Function to paste last bbox from previous list----------------------------------------------------------------
    def pasteLastBboxFile(self, event):
        """ Paste last BBox file

        Args:
            event (event): Generated event
        """            
        if self.tkimg:
            try:
                # Refresh the canvas
                self.mainPanel.update_idletasks()

                size = self.last_b_box
                if len(size) == 0:
                    messagebox.showerror("Error", "No bounding boxes available to paste.")
                    return

                # Calculate x, y coordinates
                x, y = self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y)

                # Check if bounding box is outside image boundaries
                if x < 0 or y < 0 or x + size[0] > self.tkimg.width() or y + size[1] > self.tkimg.height():
                    messagebox.showwarning("Warning", "Bounding box cannot be drawn outside the image.")
                    return

                x1, y1 = x, y
                x2, y2 = x1 + size[0], y1 + size[1]

                # Draw the bounding box
                self.bboxList.append((x1, y1, x2, y2, size[2]))
                idx_1 = self.get_class_index(size[2])
                tmpId = self.mainPanel.create_rectangle(int(x1), int(y1), int(x2), int(y2), width=2, outline=COLORS[idx_1])
                self.bboxIdList.append(tmpId)

                self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (
                    size[2], x1, y1, x2, y2))
                self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[idx_1])

                # Update the total bbox label
                self.totalBboxLabel.config(text='Total BBoxes: {}'.format(len(self.bboxList)))

            except Exception as e:
                messagebox.showerror("Error", str(e))

    def clearBBoxShortcut(self, event):
        """ Keyboard shortcut for deleting bbox

        Args:
            event (event): Generated event
        """        
        if self.bboxList:
            answer = messagebox.askquestion("Clear Bbox", "Are you sure you want to clear all Bbox?")
            
            if answer == "yes":
                for idx in range(len(self.bboxIdList)):
                    self.mainPanel.delete(self.bboxIdList[idx])

                self.listbox.delete(0, len(self.bboxList))
                self.bboxIdList = []
                self.bboxList = []
        else:
            messagebox.showinfo("Nothing to Delete", "No Bbox to delete.")

    def addNewClass(self):
        """ Add new class and set it as the current class. """
        
        if len(self.cla_can_temp) >= len(COLORS):
            messagebox.showwarning("Warning", "Class limit exceeded!")
            return

        new_class = askstring("Add New Class", "Enter the name of the new class:")
        if new_class:
            if new_class in self.cla_can_temp:
                messagebox.showwarning("Warning", f"Class '{new_class}' already exists!")
                return

            # Append the new class to file and list
            with open(os.path.join(self.imageDir, self.classcandidate_filename), 'a') as class_file:
                class_file.write(f"{new_class}\n")

            self.cla_can_temp.append(new_class)
            self.classcnt += 1

            # Update class dropdown (Combobox)
            self.classcandidate['values'] = self.cla_can_temp
            self.classcandidate.current(self.classcnt - 1)  # Select the newly added class
            self.currentLabelclass = self.classcandidate.get()
            self.index = self.classcnt - 1  # Set the index of the new class

            messagebox.showinfo("Info", f"Class '{new_class}' added successfully!")

        self.mainPanel.focus_set()  # Refocus main panel


    def deleteClass(self):
        """Delete class~
        """        
        if not self.cla_can_temp:
            messagebox.showwarning("Warning", "No classes available!")
            return
        selected_class = self.classcandidate.get()  
        if selected_class:
            confirmation = messagebox.askyesno("Confirmation", f"Do you want to delete the class '{selected_class}'?")
            if confirmation:
                # Remove the class from the list and update the Combobox
                self.cla_can_temp.remove(selected_class)
                with open(os.path.join(self.imageDir,self.classcandidate_filename), 'w') as class_file:
                    class_file.write("\n".join(self.cla_can_temp))
            
                self.classcnt -= 1
                self.classcandidate['values'] = self.cla_can_temp
                if self.classcnt > 0:
                    self.classcandidate.current(0)
                    self.currentLabelclass = self.classcandidate.get()
                else:
                    self.currentLabelclass = ''
                    self.classcandidate.set("No classes available")

            
                messagebox.showinfo("Info", f"Class '{selected_class}' deleted successfully!")
                # self.delete_lines_with_class(self.labelfilename,selected_class)
                self.delete_bbox_by_class(selected_class)

                # Update the image after deleting the class
                self.update_image()

        else:
            messagebox.showwarning("Warning", "No class selected!")
        
        self.mainPanel.focus_set() # focus
    
    def delete_bbox_by_class(self, deleted_class):
        """ Removes bbox associated with certain class.

        Args:
            deleted_class (list): List of bbox data
        """        
        # Remove bounding boxes associated with the deleted class
        indices_to_delete = []
        for i in range(len(self.bboxList) - 1, -1, -1):
            if self.bboxList[i][-1] == deleted_class:
                # Remove the bounding box from the list and the canvas
                indices_to_delete.append(i)
                self.mainPanel.delete(self.bboxIdList[i])
                del self.bboxIdList[i]
                self.listbox.delete(i)

        # Delete corresponding lines from self.bboxList
        for index in indices_to_delete:
            del self.bboxList[index]

        # Update the image after deleting bounding boxes
        self.update_image()

    def loadClassCandidates(self):
        """Load class candidates from the class file."""
        class_file_path = os.path.join(self.imageDir, self.classcandidate_filename)

        if os.path.exists(class_file_path):
            with open(class_file_path) as cf:
                self.cla_can_temp = [line.strip() for line in cf.readlines()]

            if self.cla_can_temp:
                self.classcandidate['values'] = self.cla_can_temp
                self.classcandidate.current(0)
                self.currentLabelclass = self.classcandidate.get()  # Initialize selected class
                self.parent.bind('<Key>', self.setClassShortcut)  # Bind keyboard shortcut
                self.classcandidate.bind('<<ComboboxSelected>>', self.setClass)  # Bind combobox selection change
            else:
                # Handle case where class list is empty
                self.classcandidate.set("No classes available")
                self.classcandidate['values'] = ["No classes available"]
                self.currentLabelclass = None
        else:
            # Handle case where class candidate file does not exist
            self.classcandidate.set("Class file not found")
            self.classcandidate['values'] = ["Class file not found"]
            self.currentLabelclass = None


    def get_class_index(self, class_name):
        """Get the index of a class."""
        try:
            return self.cla_can_temp.index(class_name)
        except ValueError:
            return 0


    #--------------------------Delete Selected BBox ------------------------
    def delBBox(self):
        """ Delete specific bbox
        """        
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)
        self.mainPanel.focus_set() # focus
        self.update_image()
    #----------------------------------------------------------------



    def clearBBox(self):
        """ Clear bbox
        """        
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
        self.mainPanel.focus_set() #focus
        self.update_image()

    # ------------close program ------------------

    def close_program(self, event=None):
        """ Closing program

        Args:
            event (_type_, optional): closing event. Defaults to None.
        """        
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.parent.destroy()


#-------------------------------function is used to resume the annotation process from the image index specified in the "log/checkpoint.txt" file-----------------------
    def loadCheckpoint(self, event = None):
        """Loads any specific checkpoint

        Args:
            event (event, optional): Generated event. Defaults to None.
        """        
        checkpoint = 0
        with open("log/checkpoint.txt","r") as checkpointFile:
            checkpoint = checkpointFile.read()
        if 1 <= int(checkpoint) and int(checkpoint) <= self.total:
            self.cur = int(checkpoint)
            self.loadImage()
    #----------------------------------------------------------------To Reset Checkpoint----------------------------------------------------------------
    def resetCheckpoint(self, event=None):
        """ Resets checkpoint

        Args:
            event (event, optional): Generated event. Defaults to None.
        """        
        if self.cur == 0 or self.cur==1:
            print("Already at the first image. No need to reset.")
            # You can display a messagebox or any other appropriate warning mechanism.
        else:
            with open("log/checkpoint.txt", "w") as checkpointFile:
                checkpointFile.write("1")
            # Load the image associated with the reset checkpoint
            self.cur = 1
            self.loadImage()

    #--------------------------------------------------------------------------------------------------------------------------------
    def skipImage(self, event = None):
        """Skips image

        Args:
            event (event, optional): Generated event. Defaults to None.
        """        
        # self.bboc_cnt = 0
        #os.remove(self.imageList[self.cur - 1])
        print(self.imageList[self.cur - 1]+" is skipped.")
        with open("log/skipped.txt",'a') as skippedFile:
            skippedFile.write("{}\n".format(self.imageList[self.cur - 1]))
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()


    #-----------------------------Previous Image Load, next Image Load, skip Image, or which index image you want to load----------------------------------------------------------------,
    def prevImage(self, event=None):
        """ Method to go to previous image

        Args:
            event (event, optional): Generated event. Defaults to None.
        """        
        # self.bboc_cnt = 0
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()
        else:
            messagebox.showinfo("Info", "Already at the first image")

    def nextImage(self, event=None):
        """ Method to go to next Image

        Args:
            event (event, optional): Generated event. Defaults to None.
        """        
        # self.bboc_cnt = 0
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            size = self.getLastBboxSize()
            self.last_b_box = [size[0], size[1], size[2]] if size is not None else []
            self.loadImage()
        else:
            messagebox.showinfo("Info", "Already at the last image")
            # Optionally, you can reset the checkpoint to the first image
            # self.resetCheckpoint()

    #--------------Function to clear all previous annotated text files-----------------------
    def clear_prev_annotation(self):
        """ Clear all annotated data.
        """        
        answer = messagebox.askquestion("Clear Annotation", "Are you sure you want to clear all previous Annotation?")
        if answer == "yes":
            self.delete_current_bbox_also()
            for filename in os.listdir(self.outDir):
                file_path = os.path.join(self.outDir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

            for filename in os.listdir(self.yoloOut):
                file_path = os.path.join(self.yoloOut, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)


    def delete_current_bbox_also(self):
        """ Delete current bbox also
        """        
        for idx in range(len(self.bboxIdList)):
                    self.mainPanel.delete(self.bboxIdList[idx])

        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []
    #----------------------------------------------------------------------------------------

#--------------------If we have drawn bbox previously then it will retrieve that bbox----------------------------------------------------------------
    
        # Add this function to the LabelTool class for adding a new class if it doesn't already exist
    def addNewClass_(self, new_class):
        """ Adds new class

        Args:
            new_class (str): Class name
        """        
        if len(self.cla_can_temp) >= (len(COLORS)):
            messagebox.showwarning("Warning", f"Class limit exceed!!")
            return
        else:
            create_new_class = messagebox.askyesno("Found New Class", f"Do you want to add a new class '{new_class}'?")
            if create_new_class:
                if self.classcnt == 0:
                    with open(os.path.join(self.imageDir,self.classcandidate_filename), 'a') as class_file:
                        class_file.write(f"{new_class}\n")

                    self.cla_can_temp.append(new_class)
                    self.classcnt += 1
                    self.classcandidate['values'] = self.cla_can_temp
                    self.classcandidate.current(self.classcnt - 1)
                    self.currentLabelclass = self.classcandidate.get()
                    self.index = int(self.classcnt-1)
                    messagebox.showinfo("Info", f"Class '{new_class}' added successfully!")
                else:
                    with open(os.path.join(self.imageDir,self.classcandidate_filename), 'a') as class_file:
                        class_file.write(f"{new_class}\n")

                    self.cla_can_temp.append(new_class)
                    self.classcnt += 1
                    self.classcandidate['values'] = self.cla_can_temp
                    self.classcandidate.current(self.classcnt - 1)
                    self.currentLabelclass = self.classcandidate.get()
                    self.index = int(self.classcnt-1)
                    messagebox.showinfo("Info", f"Class '{new_class}' added successfully!")
            else:
                # User chose not to create the new class, so delete lines with this class from the file
                self.delete_lines_with_class(self.labelfilename, new_class)

    def delete_lines_with_class(self, filename, class_name):
        """ Deletes lines with class

        Args:
            filename (str): File name
            class_name (str): Class Name
        """        
        with open(filename, 'r') as file:
            lines = file.readlines()

        with open(filename, 'w') as file:
            for line in lines:
                if class_name not in line:
                    file.write(line)
    
    def check_and_create_new_classes(self, class_list_from_file):
        """ Check and create new classes

        Args:
            class_list_from_file (list): list of classes

        Returns:
            None: if not new classs
        """        
        new_classes = set(class_list_from_file) - set(self.cla_can_temp)
        if new_classes:
            # print(f"New classes found: {', '.join(new_classes)}")

            for new_class in new_classes:
                self.addNewClass_(new_class)
            else:
                pass
                # print("No new classes created.")
        else:
            # print("No new classes found.")
            return None


    def return_all_class_list_from_file(self):
        """ Returns all class list from file
        """        
        class_list_from_file = []
        if os.path.exists(self.labelfilename):
            unique_classes = set()
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        continue
                    class_name = line.split()[-1]
                    unique_classes.add(class_name)

            class_list_from_file = list(unique_classes)

        self.check_and_create_new_classes(class_list_from_file) #Function called to check if class exists or not

        

    #----------------------------------------------------------------------------------------


def run_annotator(img_dir, out_dir, yolo_out_dir):
    """Run the annotator GUI."""
    image_extensions = ['jpg', 'png','jpeg', 'bmp']
    
    root = Tk()
    tool = LabelTool(root, img_dir, out_dir, yolo_out_dir, image_extensions)
    root.resizable(width =  True, height = True)
    root.mainloop()

if __name__ == '__main__':
    # Get the base directory where the script is located
    base_dir = Path(__file__).resolve().parent

    # Define input/output directories using base_dir
    img_dir = base_dir / ('input_dir')
    out_dir = base_dir / ('result_annotation')
    yolo_out_dir = base_dir / ('yolo_output_dir')

    # Ensure directories exist
    for directory in [img_dir, out_dir, yolo_out_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Get image extensions
    image_extensions =  ['jpg', 'png', 'jpeg', 'bmp']

    print("base_dir is :", base_dir)
    print("img-dir inside main annotator:", img_dir)
    print("out-dir inside main annotator:", out_dir)
    print("yolo-out-dir inside main annotator:", yolo_out_dir)

    # Initialize GUI
    root = Tk()
    tool = LabelTool(root, img_dir, out_dir, yolo_out_dir, image_extensions)
    root.resizable(width=True, height=True)
    root.attributes("-topmost", True)
    root.mainloop()