from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def format_date_long(date_str):
    """
    Converts 'YYYY-MM-DD' or datetime to '24th June 2025' format.
    """
    if isinstance(date_str, datetime):
        dt = date_str
    else:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return str(date_str)
    day = dt.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {dt.strftime('%B %Y')}"

def generate_invoice_image(
    output_path=None,
    image_size=(700, 900),
    logo_path="logo.png",
    watermark_path="watermark.png",
    fields=None,
    table_data=None
):
    if fields is None:
        fields = {
            "Name": "John Doe",
            "Order Number": "ORD12345",
            "Date": "2025-05-03",
            "Phone": "+44 1234 567890",
            "Bill Number": "BILL-0001"
        }

    if table_data is None:
        table_data = []

    # --- Dynamic output path and invoice name ---
    customer_name = fields.get("Name", "Customer")
    date_val = fields.get("Date", "")
    address_val = fields.get("Address", "")  # New: get address from fields
    date_long = format_date_long(date_val)
    invoice_filename = f"{customer_name} {date_long}.png".replace(":", "-").replace("/", "-")
    bills_dir = "bills"
    os.makedirs(bills_dir, exist_ok=True)
    output_path = output_path or os.path.join(bills_dir, invoice_filename)
    # -------------------------------------------

    # Constants
    margin = 30
    image_width, image_height = image_size
    table_width = image_width - 2 * margin
    cell_height = 50
    header_fill = "#f2f2f2"
    total_fill = (250, 235, 215)
    border_color = "#333"
    bg_color = (250, 235, 215)
    font_size = 20
    

    # Font loading
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
        bold_font = ImageFont.truetype("arialbd.ttf", font_size)
    except:
        font = ImageFont.load_default()
        bold_font = font

    # Create image
    img = Image.new("RGB", (image_width, image_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Centered logo
    try:
        logo = Image.open(logo_path).convert("RGBA")
        max_logo_width = int(image_width * 0.5)
        logo.thumbnail((max_logo_width, max_logo_width // 2))
        logo_x = (image_width - logo.width) // 2
        img.paste(logo, (logo_x, margin), logo)
    except Exception as e:
        print(f"Could not load logo: {e}")

    y_offset = margin + 200

    # Draw Bill Number on top right
    draw.text((image_width - margin - 200, margin), f"Bill No: {fields['Bill Number']}", fill="black", font=bold_font)

    # Two-line fields
    spacing = 250
    draw.text((margin, y_offset), f"Name: {fields['Name']}", fill="black", font=font)
    draw.text((margin + spacing, y_offset), f"Order #: {fields['Order Number']}", fill="black", font=font)
    y_offset += 40
    # Use long date format
    draw.text((margin, y_offset), f"Date: {date_long}", fill="black", font=font)
    draw.text((margin + spacing, y_offset), f"Phone: {fields['Phone']}", fill="black", font=font)
    y_offset += 40
    # Address field (new line)
    if address_val:
        draw.text((margin, y_offset), f"Address: {address_val}", fill="black", font=font)
        y_offset += 20
    y_offset += 20

    # Table layout
    headers = ["S.No", "Item", "Quantity", "Price", "Amount"]
    num_cols = len(headers)
    col_ratios = [0.1, 0.3, 0.15, 0.15, 0.3]
    col_widths = [int(table_width * r) for r in col_ratios]

    table_x = margin
    max_visible_rows = 8
    table_rows_area_height = (max_visible_rows + 2) * cell_height
    table_y = y_offset
    cell_fill = (250, 235, 215)  # Antique White
    header_fill = (240, 220, 200)  # Slightly darker to distinguish

    # Draw headers
    for i, header in enumerate(headers):
        cell_x = table_x + sum(col_widths[:i])
        draw.rectangle([cell_x, table_y, cell_x + col_widths[i], table_y + cell_height],
                       fill=header_fill, outline=border_color, width=1)
        draw.text((cell_x + 10, table_y + 15), header, fill="black", font=bold_font)

    # Draw rows (up to fixed number)
    total_amount = 0
    for row_index in range(max_visible_rows):
        row_y = table_y + (row_index + 1) * cell_height
        row = table_data[row_index] if row_index < len(table_data) else [""] * num_cols
        for col_index, cell in enumerate(row):
            cell_x = table_x + sum(col_widths[:col_index])
            draw.rectangle([cell_x, row_y, cell_x + col_widths[col_index], row_y + cell_height],
                       fill=cell_fill, outline="black", width=1)
            draw.text((cell_x + 10, row_y + 15), str(cell), fill="black", font=font)
        # Draw horizontal line (separator) after each row except the last one
        if row_index < max_visible_rows - 1:
            draw.line([(table_x, row_y + cell_height), 
                    (table_x + table_width, row_y + cell_height)], 
                    fill="black", width=1)  # Horizontal line
        # Sum total if data exists
        if row_index < len(table_data):
            try:
                amt = str(row[4]).replace("₹", "").replace("£", "")
                total_amount += float(amt)
            except:
                pass

    # Draw total row
    # total_y = table_y + (max_visible_rows + 1) * cell_height
    # for i in range(num_cols):
    #     cell_x = table_x + sum(col_widths[:i])
    #     fill = total_fill
    #     draw.rectangle([cell_x, total_y, cell_x + col_widths[i], total_y + cell_height],
    #                    fill=fill, outline=border_color, width=3)
    #     if i == 0:
    #         draw.text((cell_x + 10, total_y + 15), "Total Amount", fill="black", font=bold_font)
    #     elif i == 4:
    #         draw.text((cell_x + 10, total_y + 15), f"£{total_amount:.2f}", fill="black", font=bold_font)

    # TOTAL ROW - Two cells only
    total_y = table_y + (max_visible_rows + 1) * cell_height

    # Calculate X position for start of last column
    col_0_to_3_width = sum(col_widths[:4])
    col_4_width = col_widths[4]

    # First cell (spanning 4 columns)
    draw.rectangle(
        [table_x, total_y, table_x + col_0_to_3_width, total_y + cell_height],
        fill=total_fill,
        outline=border_color,
        width=2
    )
    draw.text((table_x + 10, total_y + 15), "Total Amount", fill="black", font=bold_font)

    # Second cell (last column only)
    cell_x = table_x + col_0_to_3_width
    draw.rectangle(
        [cell_x, total_y, cell_x + col_4_width, total_y + cell_height],
        fill=total_fill,
        outline=border_color,
        width=2
    )
    draw.text((cell_x + 10, total_y + 15), f"₹{total_amount:.2f}", fill="black", font=bold_font)


    # ---- Watermark to overlay on top of table ----

    watermark_width = int(image_width*0.8)
    watermark_height = int(image_height*0.6)
    try:
        watermark = Image.open(watermark_path).convert("RGBA")
        watermark = watermark.resize((watermark_width, watermark_height))
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: p * 0.15)  # 15% opacity
        watermark.putalpha(alpha)
        wm_x = (image_width - watermark_width) // 2
        wm_y = int(image_height * 0.30)  # shift down from top (e.g., 15% from top)

        # Paste *on top* of table (after drawing table structure)
        # img.paste(watermark, (table_x, table_y), watermark)
        print(f"Pasting watermark at: ({wm_x}, {wm_y}), size: ({watermark_width}, {watermark_height})")
        img.paste(watermark, (wm_x, wm_y), watermark)

    except Exception as e:
        print(f"Could not apply watermark: {e}")

    # Save result
    img.save(output_path)
    print(f"Invoice saved to {output_path}")

# Example usage (for testing only):
# generate_invoice_image(
#     fields={
#         "Name": "May",
#         "Order Number": "ORD789",
#         "Date": "2025-06-24",
#         "Phone": "+44 7000 000000",
#         "Bill Number": "BILL-9988"
#     },
#     table_data=[
#         ["1", "Milk", "2", "₹1.50", "₹3.00"],
#         ["2", "Bread", "1", "₹1.20", "₹1.20"]
#     ]
# )
