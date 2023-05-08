#===========================================================================================
# Importing libraries

# On Windows, libraries that are not part of the core Python  distribution should be listed
# in an accompanying requirements.txt file. Note that FixPix deliberately installs the latest
# versions of libraries in the accompanying requirements.txt file and ignores any
# version specifications so by default you should make sure that your code is compatible
# with the latest distribution of a python library.
#
# If you require using a specific library version, the library should be packaged with 
# the fixpix plugin module (use pip install -t <module-path> and use relative imports)
#===========================================================================================

# All FixPix plugins can assume the following modules are installed:
# PIL
# numpy
# loguru
# urllib3
# psutil
# requests

from PIL import Image, ImageDraw
from loguru import logger # All FixPix Home plugins can assume loguru is installed 
import os

g_bp = os.path.dirname(os.path.abspath(__file__))

# The following defines what will be seen in the process image dialog for this plugin
def module_info():
   
    module_info = {
        'module':'PolkaDots',  # The name of this plugin
        'module_id':'polkadots',
        'version':'1.2',              # The version of this plugin. Changing this to a
                                      # higher number will indicate in the UI that an
                                      # update is available
        
        'category':'Artistic',        # The general category this plugin belongs to
                                      # (free text that will be in parenthesis. )
        'features':[                  # An array of features this plugin supports
                                      # typically it will include only one element
            {
              "feature_name":"Polka Dots",  # The name of the feature as it will be
                                            # seen in the UI
              "feature_webui":{                  
                  "pagename":"PolkaDots.html",  # When a reference to a UI page exists
                  "init_params":{}              # optional parameters: "init_params"
                                                # will be passed to the javaScript init_webui 
                                                # function in the file specified in the
                                                # above "pagename" parameter
              },
              "feature_params":{} # default feature invoke params
                                  # if "feature_webui" does not exist
                                  # irrelevant if "feature_webui" exists
            }
        ]
    }
       
    return module_info

# This informs the fixpix framework what resources (if exist) can be used for this
# feature. The return value is a set of either {'cpu'}, {'cuda'} or {'cuda', 'cpu'}
def supported_devices():
    return {'cpu'}

# The estimated maximim memory requirements that this plugin requires (in GB)
# This is used by the platform to stall processing of this feature until enough memory
# is available
def required_memory():
    return 0.5

def process(args):
    # A request to launch the process. The args arguments is a dict that must contain:
    #   'pparams': the parameters to run the process with.
    #   'devid': the id of the device to use (-1 for cpu, 0 onwards for gpu device)
    #   'process_files_info': A list of dicts containing the following keys:
    #      'src_img_path'      The source image
    #      'dst_img_path'      The name of the destination file (without extension)
    #      'process'           The type of process performed on the source image
    #      'started'           The timestamp when the process was started
    #      'placeholder_path'  Path of placeholder this info will be written to
    #                          It is the responsibility of this module to delete
    #                          this file when processing is completed
    #      'selection_dir'     The directory where the input files were selected from
    #
    #   properties in args which are functions:
    #
    #         'qrfunc'  - qrfunc(img) a function to stamp a QR code on the PIL image.
    #                     Returns the stamped PIL Image. 
    #  'PIL_downsample' - PIL_downsample(img, area) - reduce the PIL <img> to maximum 
    #                     <area> pixels while keeping the original aspect ratio.
    #                     Returns the resized PIL image.
    #   'get_avail_mem' - get_avail_mem(devid): returns available memory in GB for
    #                     the given device id

    errorlog = args['error_log']
    qrfunc = args['qrfunc']
    params = args['pparams']
    logger.debug(f"PicTricks pparam={str(params)}")    
    for reqinfo in args['process_files_info']:
        inpath = reqinfo['src_img_path']
        outdir = reqinfo['dst_img_path']
        background_color = tuple(params["background_color"])
        dots_color = tuple(params["dots_color"])
        
        # image processing goes here
        try:
            outpath =  f'{outdir}.png'
            im_out = make_polka(inpath, background_color, dots_color)
            qrfunc(im_out)  # place the qr code in the bottom right corner
            im_out.save(outpath)
        except Exception as e:
            logger.exception(e)
            errorlog.add_error(inpath, str(e))
                
        os.unlink(reqinfo['placeholder_path'])    

# https://www.analytics-link.com/post/2019/07/11/creating-pop-art-using-opencv-and-python
# Adapted in seconds from cv2 to PIL with the help of the amazing chatGPT

def make_polka(filepath, bg_color, dots_color):
    # set the max dots (on the longest side of the image)
    max_dots = 120

    # import the image as greyscale
    original_image = Image.open(filepath).convert('L')

    # extract dimensions
    original_image_width, original_image_height = original_image.size
    calc_width = int(original_image_height*(max_dots/original_image_width))
    
    # downsize to number of dots
    if original_image_height == max(original_image_height,original_image_width):
        downsized_image = original_image.resize((calc_width, max_dots))
    else:
        downsized_image = original_image.resize((max_dots,calc_width))

    # extract dimensions of new image
    downsized_image_width, downsized_image_height = downsized_image.size

    # set how big we want our final image to be
    multiplier = 10

    # set the size of our blank canvas
    blank_img_height = downsized_image_height * multiplier
    blank_img_width = downsized_image_width * multiplier

    # set the padding value so the dots start in frame (rather than being off the edge
    padding = int(multiplier/2)

    # create canvas containing just the background colour
    blank_image = Image.new('RGB', ((blank_img_width), (blank_img_height)), bg_color)

    # create a draw object on the blank image
    draw = ImageDraw.Draw(blank_image)

    # run through each pixel and draw the circle on our blank canvas
    for y in range(0, downsized_image_height):
        for x in range(0, downsized_image_width):
            # get the pixel value and compute the radius of the circle
            pixel_value = downsized_image.getpixel((x, y))
            radius = int((0.6 * multiplier) * ((255 - pixel_value) / 255))
            # compute the center of the circle and draw it on the image
            center_x = (x * multiplier) + padding
            center_y = (y * multiplier) + padding
            draw.ellipse([(center_x - radius, center_y - radius),
                          (center_x + radius, center_y + radius)],
                          fill=dots_color)

    # save our image
    return blank_image
