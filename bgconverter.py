from PIL import Image

def change_background(image_path, output_path):
    # Open the image
    img = Image.open(image_path).convert("RGBA")

    # Define the colors
    white = (255, 255, 255, 255)  # white color (RGBA)
    antique_white = (250, 235, 215, 255)  # antique white color (RGBA)

    # Create a new image with a transparent background
    img_data = img.getdata()

    # Create a new list to hold the modified pixel data
    new_img_data = []

    for item in img_data:
        # Change all white (or near-white) pixels to antique white
        if item[:3] == white[:3]:  # compare RGB values
            new_img_data.append(antique_white)  # replace with antique white
        else:
            new_img_data.append(item)

    # Update the image with the new pixel data
    img.putdata(new_img_data)

    # Save the modified image
    img.save(output_path,format="PNG")

# Example usage
# change_background('wedaa_logo_circle.jpeg', 'wedaa_logo_circle_aw.png')
change_background('wedaa_logo.jpeg', 'wedaa_logo_aw.png')
