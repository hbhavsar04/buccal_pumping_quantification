outputDir = "/Users/msbl/Desktop/Hayden/kymograph_output/";

// Check a line ROI is drawn
if (selectionType() != 5) {
    exit("No line ROI detected. Please draw a line on the image first.");
}

// Get profile and image name
profile = getProfile();
title = getTitle();
baseName = substring(title, 0, lastIndexOf(title, "."));
outputPath = outputDir + baseName + "_profile.txt";

// Save
f = File.open(outputPath);
File.append("x\tintensity", outputPath);
for (j = 0; j < profile.length; j++) {
    File.append(j + "\t" + profile[j], outputPath);
}
File.close(f);

print("Saved: " + outputPath);