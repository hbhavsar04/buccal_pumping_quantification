// Row-normalize a kymograph and display as a new image you can measure
// Opens a normalized duplicate alongside the original

if (nImages == 0) {
    exit("No image open. Please open a kymograph first.");
}

if (selectionType() != 5) {
    exit("No line ROI detected. Please draw a line on the image first.");
}

imageTitle = getTitle();
run("KymographBuilder", "input=" + imageTitle);

// Work on the current image
originalTitle = getTitle();
originalID = getImageID();

// Duplicate to work on
run("Duplicate...", "title=[" + originalTitle + "_rownorm]");
normID = getImageID();

w = getWidth();
h = getHeight();

// Convert to 32-bit so we can store 0.0-1.0 float values
run("32-bit");

for (row = 0; row < h; row++) {
    rowMin =  1e9;
    rowMax = -1e9;

    // First pass: find min and max of this row
    for (col = 0; col < w; col++) {
        v = getPixel(col, row);
        if (v < rowMin) rowMin = v;
        if (v > rowMax) rowMax = v;
    }

    range = rowMax - rowMin;
    if (range == 0) range = 1; // flat row: leave as zero

    // Second pass: normalize
    for (col = 0; col < w; col++) {
        v = getPixel(col, row);
        setPixel(col, row, (v - rowMin) / range);
    }
}

// Set display range to 0-1 and apply a LUT for visibility
setMinAndMax(0, 1);
run("Enhance Contrast", "saturated=0");

// Optional: apply a LUT that makes bright/dim easier to see
// Comment out if you prefer grayscale
run("Green Fire Blue");

print("Row normalization complete: " + originalTitle + "_rownorm");
print("Each row now spans 0.0 (dimmest) to 1.0 (brightest)");
print("Draw a line and run the profile exporter macro as usual.");