// Wall-mountable case for 64x32 RGB LED Matrix with Raspberry Pi 4 + Bonnet

// ==================== Configuration Variables ====================
// Main case dimensions
case_width = 280;     // Overall width
case_height = 150;    // Overall height
case_depth = 35;      // Overall depth

// LED matrix dimensions
matrix_width = 256;
matrix_height = 128;
matrix_depth = 12;

// Raspberry Pi 4 + Bonnet dimensions
pi_width = 85;
pi_height = 56;
pi_depth = 18;
pi_mount_x_offset = 10; // Offset from left wall
pi_mount_y_offset = 10; // Offset from bottom

// Speaker cutout
speaker_width = 40;
speaker_height = 15;
speaker_offset_x = 10;  // Distance from left edge
speaker_offset_y = (case_height - speaker_height) / 2;

// Button cutout
button_diameter = 12;
button_offset_x = case_width - 10; // Distance from right edge
button_offset_y = case_height / 2; // Centered vertically

// Keyhole mounting slots
keyhole_spacing = 200;
keyhole_diameter = 5;   // Hole for #8 screw
keyhole_slot_length = 8;
keyhole_offset_y = 20;  // Distance from top

// Cable entry hole
cable_width = 15;
cable_height = 8;
cable_offset_x = (case_width - cable_width) / 2;
cable_offset_y = 5;

// Ventilation slots
vent_width = 5;
vent_spacing = 5;
num_vents = floor((case_width - 20) / (vent_width + vent_spacing));

// ==================== Main Assembly ====================
module case_body() {
    difference() {
        // Main body
        rounded_cube([case_width, case_height, case_depth], radius=2);

        // Hollow out inside (leave 3mm wall thickness)
        translate([3, 3, 3]) 
            cube([case_width - 6, case_height - 6, case_depth - 3]);

        // LED matrix cutout
        translate([(case_width - matrix_width) / 2, 
                   (case_height - matrix_height) / 2, 
                   3]) 
            cube([matrix_width, matrix_height, matrix_depth]);

        // Speaker grill
        translate([speaker_offset_x, speaker_offset_y, 3])
            cube([speaker_width, speaker_height, case_depth]);

        // Button cutout
        translate([button_offset_x, button_offset_y, -1])
            cylinder(h=case_depth + 2, d=button_diameter, $fn=50);

        // Cable entry
        translate([cable_offset_x, -1, cable_offset_y])
            cube([cable_width, 3, cable_height]);

        // Ventilation slots
        for (i = [0:num_vents - 1]) {
            translate([10 + i * (vent_width + vent_spacing), case_height - 3, case_depth - 5])
                cube([vent_width, 3, 3]);
        }

        // Keyhole mounting slots
        keyhole_mounting_slots();
    }
}

// ==================== Modules ====================

// Rounded cube module for smoother edges
module rounded_cube(size, radius) {
    hull() {
        for (x = [0, size.x - radius], y = [0, size.y - radius])
            translate([x, y, 0]) cylinder(h = size.z, r = radius, $fn=20);
    }
}

// Keyhole mounting slots
module keyhole_mounting_slots() {
    for (x = [(case_width - keyhole_spacing) / 2, (case_width + keyhole_spacing) / 2]) {
        translate([x, keyhole_offset_y, -1]) {
            // Circular hole
            cylinder(h = case_depth + 2, d = keyhole_diameter, $fn=50);
            // Slot extension
            translate([-keyhole_diameter/2, -keyhole_slot_length, 0])
                cube([keyhole_diameter, keyhole_slot_length, case_depth + 2]);
        }
    }
}

// Mounting posts for Raspberry Pi
module pi_mounting_posts() {
    post_radius = 3;
    post_height = 10;
    hole_diameter = 2.5;
    hole_depth = 8;

    for (offset = [
        [0, 0],
        [pi_width, 0],
        [0, pi_height],
        [pi_width, pi_height]
    ]) {
        translate([pi_mount_x_offset + offset[0], pi_mount_y_offset + offset[1], 3])
            difference() {
                cylinder(h = post_height, r = post_radius, $fn=20);
                translate([0, 0, -1])
                    cylinder(h = hole_depth, d = hole_diameter, $fn=30);
            }
    }
}

// ==================== Assemble the Case ====================
difference() {
    case_body();
    pi_mounting_posts();
}